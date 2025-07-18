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
    'api': {
        'patterns': [
            r'/api/',
            r'/api-reference/',
            r'/authentication/',
            r'/pagination/',
            r'/using-api-playground/',
        ],
        'priority': 1
    },
    'courses': {
        'patterns': [r'/courses/'],
        'priority': 1
    },
    'user_management': {
        'patterns': [
            r'/user-management/',
            r'/rbac/',
            r'/saml/',
            r'/sso/',
            r'/2fa/',
            r'/projects/',
            r'/permissions/',
        ],
        'priority': 1
    },
    'hosting': {
        'patterns': [
            r'/hosting/',
            r'/configuration/',
            r'/architecture/',
            r'/environment-variables/',
            r'/installation/',
            r'/docker/',
            r'/npm/',
            r'/scaling/',
            r'/performance/',
            r'/security/',
            r'/monitoring/',
            r'/aws/',
            r'/azure/',
            r'/gcp/',
        ],
        'priority': 1
    },
    'non_categorized': {
        'patterns': [
            r'/credentials/',
            r'/embed/',
            r'/flow-logic/',
            r'/manage-cloud/', # Renommé de 'cloud' pour être plus précis
            r'/source-control-environments/',
            r'/privacy-security/',
            r'/release-notes/', # Ajouté car souvent non catégorisé
            r'/insights/', # Ajouté
            r'/video-courses/', # Ajouté
            r'/help-community/', # Ajouté
            r'/choose-n8n/', # Ajouté
            r'/1-0-migration-checklist/', # Ajouté
            r'/advanced-ai/evaluations/', # Ajouté
            r'/advanced-ai/examples/', # Ajouté
            r'/advanced-ai/intro-tutorial/', # Ajouté
            r'/advanced-ai/rag-in-n8n/', # Ajouté
            r'/advanced-ai/', # Ajouté
            r'/data/', # Ajouté
            r'/log-streaming/', # Ajouté
            r'/license-key/', # Ajouté
            r'/glossary/', # Déjà présent dans 'other', mais déplacé ici
            r'/guides/', # Déjà présent dans 'other', mais déplacé ici
            r'/documentation/', # Déjà présent dans 'other', mais déplacé ici
        ],
        'priority': 1
    },
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
        'priority': 2 # Priorité ajustée
    },
    'workflows': {
        'patterns': [r'/workflows/'],
        'priority': 3 # Priorité ajustée
    },
    'code': {
        'patterns': [r'/code/', r'/expressions/', r'/transformations/'],
        'priority': 4 # Priorité ajustée
    },
    'integrations': {
        'patterns': [r'/integrations/'],
        'priority': 5 # Priorité ajustée
    },
    'other': { # Cette catégorie sera moins utilisée car 'non_categorized' prend le relais
        'patterns': [], # Vide ou patterns très génériques si nécessaire
        'priority': 99 # Priorité très basse pour les URLs non capturées par les autres
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
        # Définir l'espace de noms pour XPath
        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        root = etree.fromstring(xml_content.encode('utf-8'))
        # Utiliser l'espace de noms dans la requête XPath
        for loc in root.xpath('//sitemap:loc', namespaces=ns):
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
        
        logging.info(f"Sitemap content fetched (first 500 chars): {sitemap_content[:500]}")

        all_urls = parse_sitemap_xml(sitemap_content)
        
        if not all_urls:
            logging.error("No URLs parsed from sitemap. Exiting.")
            return
        
        logging.info(f"Total URLs parsed from sitemap: {len(all_urls)}")
        logging.info(f"First 5 parsed URLs: {all_urls[:5]}")

        categorized_urls = []
        for url in all_urls:
            category, priority = categorize_url(url)
            if category in filtered_categories: # Only include URLs from selected categories
                categorized_urls.append({'url': url, 'category': category, 'priority': priority})
        
        if not categorized_urls:
            logging.error("No URLs matched selected categories after parsing. Check patterns or categories.")
            return

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
        await tqdm.gather(*tasks)

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
