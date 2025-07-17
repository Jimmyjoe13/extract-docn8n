import aiohttp
import asyncio
import argparse
import re
import os
import logging
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from tqdm.asyncio import tqdm
import html2text
from lxml import etree

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Définition des catégories et de leurs patterns regex avec priorités
CATEGORIES = {
    'langchain_agent': {
        'patterns': [
            r'/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain\.agent',
            r'/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain\.code',
            r'/integrations/builtin/cluster-nodes/.*langchain',
            r'/advanced-ai/langchain',
            r'/advanced-ai/.*agent',
            r'/code/builtin/langchain-methods',
            r'/integrations/builtin/cluster-nodes/sub-nodes/.*langchain',
            r'/integrations/builtin/core-nodes/n8n-nodes-langchain',
        ],
        'priority': 1
    },
    'workflows': {
        'patterns': [r'/workflows/'],
        'priority': 2
    },
    'other': {
        'patterns': [r'/glossary/', r'/guides/', r'/documentation/'],
        'priority': 3
    },
    'code': {
        'patterns': [r'/code/', r'/expressions/', r'/transformations/'],
        'priority': 4
    },
    'hosting': {
        'patterns': [r'/hosting/', r'/configuration/'],
        'priority': 5
    },
    'user_management': {
        'patterns': [r'/user-management/', r'/rbac/'],
        'priority': 6
    },
    'integrations': {
        'patterns': [r'/integrations/'],
        'priority': 7
    }
}

class N8nSitemapParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag == 'loc':
            self.urls.append(data)

async def fetch_sitemap(session, sitemap_url):
    logging.info(f"Fetching sitemap from: {sitemap_url}")
    try:
        async with session.get(sitemap_url, timeout=30) as response:
            response.raise_for_status()
            content = await response.text()
            return content
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching sitemap {sitemap_url}: {e}")
        return None
    except asyncio.TimeoutError:
        logging.error(f"Timeout fetching sitemap {sitemap_url}")
        return None

def parse_sitemap_xml(xml_content):
    urls = []
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))
        for loc in root.xpath('//loc'):
            urls.append(loc.text)
    except etree.XMLSyntaxError as e:
        logging.error(f"Error parsing sitemap XML: {e}")
    return urls

def categorize_url(url):
    path = urlparse(url).path
    for category, data in CATEGORIES.items():
        for pattern in data['patterns']:
            if re.search(pattern, path):
                return category, data['priority']
    return 'other', CATEGORIES['other']['priority'] # Default to 'other' if no specific category matches

async def fetch_url_content(session, url, retries=3, timeout=60):
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt == retries - 1:
                logging.error(f"Failed to fetch {url} after {retries} attempts.")
                return None
            await asyncio.sleep(2 ** attempt) # Exponential backoff
        except asyncio.TimeoutError:
            logging.warning(f"Timeout on attempt {attempt + 1} for {url}")
            if attempt == retries - 1:
                logging.error(f"Failed to fetch {url} due to timeout after {retries} attempts.")
                return None
            await asyncio.sleep(2 ** attempt)
    return None

def convert_html_to_markdown(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0 # Disable wrapping
    return h.handle(html_content)

def sanitize_filename(url):
    path = urlparse(url).path
    filename = path.strip('/').replace('/', '_').replace('.', '_')
    if not filename:
        filename = "index"
    return re.sub(r'[^\w\-_\.]', '', filename) + '.txt'

async def process_url(session, url_info, output_dir, stats):
    url, category = url_info
    logging.info(f"Processing URL: {url} (Category: {category})")
    html_content = await fetch_url_content(session, url)
    if html_content:
        markdown_content = convert_html_to_markdown(html_content)
        category_output_dir = os.path.join(output_dir, category)
        os.makedirs(category_output_dir, exist_ok=True)
        filename = sanitize_filename(url)
        filepath = os.path.join(category_output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            stats['success'] += 1
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            logging.info(f"Successfully saved {url} to {filepath}")
        except IOError as e:
            logging.error(f"Error writing file {filepath}: {e}")
            stats['failed'] += 1
    else:
        stats['failed'] += 1

async def main():
    parser = argparse.ArgumentParser(description="Extract text content from n8n documentation sitemap.")
    parser.add_argument("--sitemap", default="https://docs.n8n.io/sitemap.xml",
                        help="URL of the sitemap to process.")
    parser.add_argument("--output", default="./output",
                        help="Output directory for the extracted text files.")
    parser.add_argument("--categories", default="all",
                        help="Comma-separated list of categories to extract (e.g., 'langchain_agent,workflows'). Use 'all' for all categories.")
    parser.add_argument("--workers", type=int, default=10,
                        help="Number of concurrent workers (async tasks) to use for fetching URLs.")
    
    args = parser.parse_args()

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    selected_categories = args.categories.split(',') if args.categories != 'all' else list(CATEGORIES.keys())
    
    # Filter CATEGORIES based on selected_categories
    filtered_categories = {k: v for k, v in CATEGORIES.items() if k in selected_categories}

    if not filtered_categories:
        logging.error("No valid categories selected. Please check your --categories argument.")
        return

    async with aiohttp.ClientSession() as session:
        sitemap_content = await fetch_sitemap(session, args.sitemap)
        if not sitemap_content:
            logging.error("Could not fetch sitemap. Exiting.")
            return

        all_urls = parse_sitemap_xml(sitemap_content)
        
        categorized_urls = []
        for url in all_urls:
            category, priority = categorize_url(url)
            if category in filtered_categories: # Only include URLs from selected categories
                categorized_urls.append({'url': url, 'category': category, 'priority': priority})

        # Sort URLs by priority (lower number = higher priority)
        categorized_urls.sort(key=lambda x: x['priority'])

        logging.info(f"Traitement de {len(categorized_urls)} URLs par ordre de priorité")
        for cat, data in sorted(filtered_categories.items(), key=lambda item: item[1]['priority']):
            count = sum(1 for item in categorized_urls if item['category'] == cat)
            logging.info(f"  - {cat}: {count} URLs")

        stats = {'success': 0, 'failed': 0, 'categories': {}}

        # Prepare tasks for tqdm.asyncio
        tasks = []
        for url_info in categorized_urls:
            tasks.append(process_url(session, (url_info['url'], url_info['category']), output_dir, stats))

        logging.info("Extraction en cours...")
        await tqdm.gather(*tasks, max_concurrent_tasks=args.workers)

        logging.info("\n=== Résultats de l'extraction ===")
        logging.info(f"URLs traitées avec succès: {stats['success']}")
        logging.info(f"URLs échouées: {stats['failed']}")
        total_processed = stats['success'] + stats['failed']
        if total_processed > 0:
            success_rate = (stats['success'] / total_processed) * 100
            logging.info(f"Taux de succès: {success_rate:.1f}%")
        else:
            logging.info("Aucune URL traitée.")

if __name__ == "__main__":
    asyncio.run(main())
