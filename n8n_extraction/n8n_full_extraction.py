import aiohttp
import asyncio
import argparse
import re
import os
import logging
import csv
import json
from pathlib import Path
from urllib.parse import urlparse
from html.parser import HTMLParser
from tqdm.asyncio import tqdm
import html2text
from lxml import etree
from datetime import datetime

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
            r'/embed/configuration/', # Ajouté pour correspondre à urls_to_extract.csv
            r'/embed/deployment/', # Ajouté pour correspondre à urls_to_extract.csv
            r'/hosting/',
            r'/hosting/cli-commands/',
            r'/hosting/community-edition-features/',
            r'/hosting/architecture/',
            r'/hosting/configuration/',
            r'/hosting/database-setup/',
            r'/hosting/docker/',
            r'/hosting/installation/',
            r'/hosting/logging-monitoring/',
            r'/hosting/scaling/',
            r'/hosting/securing/',
            r'/hosting/starter-kits/',
            r'/hosting/troubleshooting/',
            r'/hosting/update/',
            r'/hosting/upgrade/',
            r'/integrations/community-nodes/troubleshooting/', # Ajouté pour correspondre à urls_to_extract.csv
            r'/integrations/community-nodes/installation/', # Ajouté pour correspondre à urls_to_extract.csv
        ],
        'priority': 1
    },
    'non_categorized': {
        'patterns': [
            r'/sustainable-use-license/',
            r'/video-courses/',
            r'/credentials/',
            r'/embed/',
            r'/flow-logic/',
            r'/help-community/',
            r'/manage-cloud/',
            r'/privacy-security/',
            r'/source-control-environments/',
            r'/release-notes/',
            r'/insights/',
            r'/choose-n8n/',
            r'/1-0-migration-checklist/',
            r'/advanced-ai/evaluations/',
            r'/advanced-ai/examples/',
            r'/advanced-ai/intro-tutorial/',
            r'/advanced-ai/rag-in-n8n/',
            r'/advanced-ai/',
            r'/data/',
            r'/log-streaming/',
            r'/license-key/',
            r'/glossary/',
            r'/guides/',
            r'/documentation/',
            r'/api/', # Les URLs API sont déjà dans la catégorie 'api', mais si elles ne sont pas capturées, elles pourraient tomber ici.
            r'/courses/', # Idem pour courses
            r'/user-management/', # Idem pour user_management
            r'/hosting/', # Idem pour hosting
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
        'priority': 2
    },
    'workflows': {
        'patterns': [r'/workflows/'],
        'priority': 3
    },
    'code': {
        'patterns': [r'/code/', r'/expressions/', r'/transformations/'],
        'priority': 4
    },
    'integrations': {
        'patterns': [r'/integrations/'],
        'priority': 5
    },
    'other': {
        'patterns': [],
        'priority': 99
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
        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        root = etree.fromstring(xml_content.encode('utf-8'))
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
    return 'other', CATEGORIES['other']['priority']

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
            await asyncio.sleep(2 ** attempt)
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
    h.body_width = 0
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

class ExtractionVerifier:
    def __init__(self, output_dir='./output'):
        self.output_dir = Path(output_dir)
        self.existing_files = {}
        self.url_mapping = {}
        
    def slugify(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')
    
    def url_to_filename(self, url):
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            return "index"
        
        filename = self.slugify(path.replace('/', '_'))
        return filename
    
    def scan_existing_files(self):
        logging.info("🔍 Scan des fichiers existants...")
        
        if not self.output_dir.exists():
            logging.warning(f"Répertoire de sortie n'existe pas: {self.output_dir}. Création...")
            os.makedirs(self.output_dir, exist_ok=True)
        
        total_files = 0
        
        for category_dir in self.output_dir.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                self.existing_files[category_name] = []
                
                txt_files = list(category_dir.glob("*.txt"))
                
                for txt_file in txt_files:
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            first_line = f.readline().strip()
                            if first_line.startswith('# https://'):
                                source_url = first_line[2:].strip()
                                self.existing_files[category_name].append({
                                    'filename': txt_file.name,
                                    'filepath': str(txt_file),
                                    'source_url': source_url,
                                    'size': txt_file.stat().st_size,
                                    'modified': datetime.fromtimestamp(txt_file.stat().st_mtime)
                                })
                                self.url_mapping[source_url] = str(txt_file)
                                total_files += 1
                    except Exception as e:
                        logging.error(f"Erreur lecture fichier {txt_file}: {e}")
                
                if self.existing_files[category_name]:
                    logging.info(f"📁 {category_name}: {len(self.existing_files[category_name])} fichiers")
        
        logging.info(f"📊 Total de fichiers existants: {total_files}")
        return total_files
    
    def check_url_already_extracted(self, url):
        return url in self.url_mapping
    
    def get_expected_filename(self, url, category):
        filename = self.url_to_filename(url)
        expected_path = self.output_dir / category / f"{filename}.txt"
        return expected_path
    
    def verify_extraction_completeness(self, urls_to_extract):
        logging.info("\n🔍 Vérification de la complétude de l'extraction...")
        
        stats = {
            'total_urls': 0, # Sera mis à jour après le parcours des catégories
            'already_extracted': 0,
            'missing': 0,
            'to_extract': [],
            'missing_urls': []
        }
        
        for category, urls in urls_to_extract.items():
            stats['total_urls'] += len(urls)
            logging.info(f"\n📁 Catégorie: {category}")
            
            category_stats = {
                'total': len(urls),
                'extracted': 0,
                'missing': 0
            }
            
            for url in urls:
                if self.check_url_already_extracted(url):
                    category_stats['extracted'] += 1
                    stats['already_extracted'] += 1
                else:
                    expected_file = self.get_expected_filename(url, category)
                    
                    if expected_file.exists(): # Double vérification si le fichier existe physiquement
                        category_stats['extracted'] += 1
                        stats['already_extracted'] += 1
                    else:
                        category_stats['missing'] += 1
                        stats['missing'] += 1
                        stats['to_extract'].append({'category': category, 'url': url}) # Stocker comme dict
                        stats['missing_urls'].append(url)
            
            logging.info(f"   ✅ Extraites: {category_stats['extracted']}")
            logging.info(f"   ❌ Manquantes: {category_stats['missing']}")
            if category_stats['total'] > 0:
                logging.info(f"   📊 Taux: {category_stats['extracted']/category_stats['total']*100:.1f}%")
            else:
                logging.info("   📊 Taux: 0.0%")
        
        return stats
    
    def generate_extraction_report(self, stats):
        logging.info("\n" + "="*60)
        logging.info("📊 RAPPORT D'EXTRACTION")
        logging.info("="*60)
        
        logging.info(f"URLs totales à traiter: {stats['total_urls']}")
        logging.info(f"URLs déjà extraites: {stats['already_extracted']}")
        logging.info(f"URLs manquantes: {stats['missing']}")
        
        if stats['total_urls'] > 0:
            completion_rate = (stats['already_extracted'] / stats['total_urls']) * 100
            logging.info(f"Taux de complétude: {completion_rate:.1f}%")
        
        if stats['missing'] > 0:
            logging.info(f"\n❌ URLs manquantes ({stats['missing']}):")
            for i, item in enumerate(stats['to_extract'][:10], 1):
                logging.info(f"   {i}. [{item['category']}] {item['url']}")
            
            if len(stats['to_extract']) > 10:
                logging.info(f"   ... et {len(stats['to_extract']) - 10} autres URLs")
        
        report_file = self.output_dir / 'extraction_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': stats,
                'missing_urls': stats['missing_urls']
            }, f, indent=2, ensure_ascii=False)
        
        logging.info(f"\n📄 Rapport sauvegardé: {report_file}")
    
    def clean_empty_files(self):
        logging.info("\n🧹 Nettoyage des fichiers vides/corrompus...")
        
        cleaned_count = 0
        
        for category_dir in self.output_dir.iterdir():
            if category_dir.is_dir():
                for txt_file in category_dir.glob("*.txt"):
                    try:
                        if txt_file.stat().st_size == 0:
                            logging.info(f"🗑️  Suppression fichier vide: {txt_file}")
                            txt_file.unlink()
                            cleaned_count += 1
                        elif txt_file.stat().st_size < 100:
                            with open(txt_file, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if not content or len(content) < 50:
                                    logging.info(f"🗑️  Suppression fichier trop petit: {txt_file}")
                                    txt_file.unlink()
                                    cleaned_count += 1
                    except Exception as e:
                        logging.error(f"Erreur lors du nettoyage de {txt_file}: {e}")
        
        logging.info(f"🧹 Nettoyage terminé: {cleaned_count} fichiers supprimés")
        return cleaned_count

def load_urls_from_csv(filepath='urls_to_extract.csv'):
    urls_by_category = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) >= 2:
                    category = row[0].strip()
                    url = row[1].strip()
                    if category not in urls_by_category:
                        urls_by_category[category] = []
                    urls_by_category[category].append(url)
    except FileNotFoundError:
        logging.error(f"Erreur: Le fichier CSV '{filepath}' n'a pas été trouvé.")
        return None
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du CSV '{filepath}': {e}")
        return None
    return urls_by_category

async def main_full_extraction():
    logging.info("🚀 Début du processus d'extraction complet...")
    
    # Étape 1: Charger les URLs à partir du CSV
    urls_to_extract_from_csv = load_urls_from_csv('urls_to_extract.csv')
    if urls_to_extract_from_csv is None:
        logging.error("Impossible de charger les URLs depuis le CSV. Arrêt.")
        return

    # Étape 2: Initialiser le vérificateur et scanner les fichiers existants
    verifier = ExtractionVerifier()
    verifier.scan_existing_files()
    verifier.clean_empty_files() # Nettoyer avant de vérifier la complétude

    # Étape 3: Déterminer les URLs manquantes
    verification_stats = verifier.verify_extraction_completeness(urls_to_extract_from_csv)
    
    urls_to_process = []
    for item in verification_stats['to_extract']:
        urls_to_process.append({'url': item['url'], 'category': item['category'], 'priority': CATEGORIES.get(item['category'], {}).get('priority', 99)})
    
    if not urls_to_process:
        logging.info("✅ Aucune URL manquante à extraire. Le processus est terminé.")
        verifier.generate_extraction_report(verification_stats)
        return

    # Trier les URLs par priorité
    urls_to_process.sort(key=lambda x: x['priority'])

    logging.info(f"Traitement de {len(urls_to_process)} URLs par ordre de priorité")
    for cat, data in sorted(CATEGORIES.items(), key=lambda item: item[1]['priority']):
        count = sum(1 for item in urls_to_process if item['category'] == cat)
        if count > 0:
            logging.info(f"  - {cat}: {count} URLs")

    # Étape 4: Lancer l'extraction
    extraction_stats = {'success': 0, 'failed': 0, 'categories': {}}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url_info in urls_to_process:
            tasks.append(process_url(session, (url_info['url'], url_info['category']), verifier.output_dir, extraction_stats))

        logging.info("Extraction en cours...")
        await tqdm.gather(*tasks)

    # Étape 5: Générer le rapport final
    final_stats = {
        'total_urls': verification_stats['total_urls'],
        'already_extracted': verification_stats['already_extracted'], # Renommé
        'missing': len(urls_to_process), # Renommé, représente les URLs à extraire cette fois
        'to_extract': verification_stats['to_extract'], # Garder la liste originale des URLs à extraire
        'urls_successfully_extracted_this_run': extraction_stats['success'],
        'urls_failed_this_run': extraction_stats['failed'],
        'categories_extracted_this_run': extraction_stats['categories'],
        'missing_urls': [], # Sera mis à jour par une nouvelle vérification si nécessaire
        'final_success_rate': 0.0
    }

    # Re-scanner après l'extraction pour un rapport final précis
    verifier.scan_existing_files()
    final_verification_stats = verifier.verify_extraction_completeness(urls_to_extract_from_csv)
    final_stats['final_missing_urls'] = final_verification_stats['missing_urls']
    
    total_processed_final = final_verification_stats['already_extracted'] + final_verification_stats['missing']
    if total_processed_final > 0:
        final_stats['final_success_rate'] = (final_verification_stats['already_extracted'] / total_processed_final) * 100
    
    verifier.generate_extraction_report(final_stats)

    logging.info("\n=== RÉSULTATS DE L'EXTRACTION COMPLÈTE ===")
    logging.info(f"URLs totales dans le CSV: {final_stats['total_urls']}")
    logging.info(f"URLs déjà extraites avant cette exécution: {final_stats['already_extracted']}") # Nom de la clé mis à jour
    logging.info(f"URLs à extraire cette exécution: {final_stats['missing']}") # Nom de la clé mis à jour
    logging.info(f"URLs extraites avec succès cette exécution: {final_stats['urls_successfully_extracted_this_run']}")
    logging.info(f"URLs échouées cette exécution: {final_stats['urls_failed_this_run']}")
    logging.info(f"Taux de complétude final: {final_stats['final_success_rate']:.1f}%")
    if final_stats['missing_urls']: # Nom de la clé mis à jour
        logging.warning(f"Il reste {len(final_stats['missing_urls'])} URLs manquantes après cette exécution.")
    else:
        logging.info("Toutes les URLs ont été extraites avec succès !")

if __name__ == "__main__":
    asyncio.run(main_full_extraction())
