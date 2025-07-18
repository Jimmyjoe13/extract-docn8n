#!/usr/bin/env python3
"""
Script d'extraction des URLs d'intégrations n8n
Traite les 832 URLs d'intégrations restantes et sauvegarde le contenu en fichiers .txt
"""

import csv
import os
import re
import sys
import time
import argparse
from pathlib import Path
from urllib.parse import urlparse
import html2text
import logging
from tqdm import tqdm
import requests
from concurrent.futures import ThreadPoolExecutor
import asyncio # Garder pour asyncio.run et Semaphore

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integrations_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegrationsExtractor:
    def __init__(self, csv_file, output_dir, workers=8, skip_existing=True):
        self.csv_file = csv_file
        self.output_dir = Path(output_dir)
        self.workers = workers
        self.skip_existing = skip_existing
        self.session = None
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_tables = False
        self.h2t.wrap_links = False
        self.h2t.wrap_list_items = False
        self.h2t.body_width = 0
        
        # Statistiques
        self.total_urls = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_files = 0
        
        # Créer les répertoires
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def slugify(self, text):
        """Convertir une URL en nom de fichier valide"""
        # Remplacer les caractères spéciaux
        text = re.sub(r'[^\w\s-]', '_', text)
        # Remplacer les espaces par des underscores
        text = re.sub(r'[-\s]+', '_', text)
        # Enlever les underscores multiples
        text = re.sub(r'_+', '_', text)
        # Nettoyer le début et fin
        text = text.strip('_')
        # Limiter la longueur
        if len(text) > 200:
            text = text[:200]
        return text
    
    def get_output_filename(self, url, chemin):
        """Générer le nom de fichier de sortie"""
        # Utiliser le chemin pour créer le nom de fichier
        filename = self.slugify(chemin.strip('/').replace('/', '_'))
        if not filename:
            filename = self.slugify(url)
        return f"{filename}.txt"
    
    def get_output_path(self, url, chemin):
        """Générer le chemin complet de sortie"""
        filename = self.get_output_filename(url, chemin)
        return self.output_dir / "integrations" / filename
    
    def should_skip_file(self, output_path):
        """Vérifier si le fichier doit être ignoré"""
        if not self.skip_existing:
            return False
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            if file_size > 100:  # Fichier existe et a du contenu
                return True
        return False
    
    def download_url(self, url, output_path, max_retries=3):
        """Télécharger une URL et sauvegarder le contenu"""
        headers = {
            'User-Agent': 'n8n-docs-extractor/1.0 (Python/requests)'
        }
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30, headers=headers)
                if response.status_code == 200:
                    content = response.text
                    
                    # Convertir HTML en texte
                    try:
                        text_content = self.h2t.handle(content)
                    except AssertionError as ae:
                        logger.error(f"Erreur d'analyse HTML pour {url}: {str(ae)}")
                        text_content = f"Erreur d'analyse HTML: {str(ae)}\n\n" + content # Sauvegarder le HTML brut en cas d'erreur
                    
                    # Ajouter les métadonnées
                    metadata = f"# URL: {url}\n# Extraction: {time.strftime('%Y-%m-%d %H:%M:%S')}\n# Status: {response.status_code}\n\n"
                    final_content = metadata + text_content
                    
                    # Sauvegarder
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(final_content)
                    
                    return True
                else:
                    logger.warning(f"HTTP {response.status_code} pour {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur tentative {attempt + 1}/{max_retries} pour {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponentiel
                    
        return False
    
    def process_url_sync(self, url_data):
        """Traiter une URL unique de manière synchrone"""
        url = url_data['url']
        chemin = url_data['chemin']
        output_path = self.get_output_path(url, chemin)
        
        # Vérifier si le fichier existe déjà
        if self.should_skip_file(output_path):
            logger.info(f"Fichier existant ignoré: {output_path.name}")
            self.skipped_files += 1
            return True
        
        # Télécharger
        success = self.download_url(url, output_path)
        if success:
            self.successful_downloads += 1
            logger.info(f"Téléchargé: {output_path.name}")
        else:
            self.failed_downloads += 1
            logger.error(f"Échec: {url}")
        
        return success
    
    def process_batch(self, batch_name=None):
        """Traiter un lot d'URLs"""
        # Charger les URLs du CSV
        urls_to_process = []
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if batch_name and row.get('batch_group') != batch_name:
                    continue
                urls_to_process.append({
                    'url': row['url_complete'],
                    'chemin': row['chemin']
                })
        
        self.total_urls = len(urls_to_process)
        
        if self.total_urls == 0:
            logger.warning("Aucune URL à traiter")
            return
        
        logger.info(f"Traitement de {self.total_urls} URLs avec {self.workers} workers")
        if batch_name:
            logger.info(f"Lot spécifique: {batch_name}")
        
        # Utiliser ThreadPoolExecutor pour la concurrence
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Exécuter avec barre de progression
            results = list(tqdm(executor.map(self.process_url_sync, urls_to_process), 
                                total=len(urls_to_process), desc="Extraction"))
        
        # Statistiques finales
        self.print_statistics()
    
    def print_statistics(self):
        """Afficher les statistiques finales"""
        success_rate = (self.successful_downloads / self.total_urls * 100) if self.total_urls > 0 else 0
        
        print("\n" + "="*50)
        print("STATISTIQUES D'EXTRACTION")
        print("="*50)
        print(f"Total URLs traitées: {self.total_urls}")
        print(f"Téléchargements réussis: {self.successful_downloads}")
        print(f"Téléchargements échoués: {self.failed_downloads}")
        print(f"Fichiers ignorés (existants): {self.skipped_files}")
        print(f"Taux de succès: {success_rate:.1f}%")
        print("="*50)
        
        # Sauvegarder les stats dans un fichier
        with open(self.output_dir / "extraction_stats.txt", "w") as f:
            f.write(f"Extraction terminée: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total URLs: {self.total_urls}\n")
            f.write(f"Succès: {self.successful_downloads}\n")
            f.write(f"Échecs: {self.failed_downloads}\n")
            f.write(f"Ignorés: {self.skipped_files}\n")
            f.write(f"Taux de succès: {success_rate:.1f}%\n")

def main(): # Plus besoin d'async
    parser = argparse.ArgumentParser(description="Extracteur d'URLs d'intégrations n8n")
    parser.add_argument("--csv", default="integrations_urls.csv", help="Fichier CSV des URLs")
    parser.add_argument("--output", default="./output", help="Répertoire de sortie")
    parser.add_argument("--workers", type=int, default=8, help="Nombre de workers")
    parser.add_argument("--batch", help="Traiter un lot spécifique (ex: batch_01)")
    parser.add_argument("--skip-existing", action="store_true", default=True, help="Ignorer les fichiers existants")
    
    args = parser.parse_args()
    
    # Vérifier que le fichier CSV existe
    if not os.path.exists(args.csv):
        logger.error(f"Fichier CSV introuvable: {args.csv}")
        sys.exit(1)
    
    # Créer l'extracteur
    extractor = IntegrationsExtractor(
        csv_file=args.csv,
        output_dir=args.output,
        workers=args.workers,
        skip_existing=args.skip_existing
    )
    
    # Lancer l'extraction
    extractor.process_batch(args.batch) # Appel synchrone

if __name__ == "__main__":
    main() # Appel synchrone
