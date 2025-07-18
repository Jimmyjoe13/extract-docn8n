#!/usr/bin/env python
"""
Script de vérification des fichiers déjà extraits pour éviter les doublons
Analyse les fichiers existants et compare avec les URLs à traiter
"""

import os
import re
import csv # Ajout de l'importation du module csv
from pathlib import Path
from urllib.parse import urlparse
import json
from datetime import datetime

class ExtractionVerifier:
    def __init__(self, output_dir='./output'):
        self.output_dir = Path(output_dir)
        self.existing_files = {}
        self.url_mapping = {}
        
    def slugify(self, text):
        """Convertit un texte en slug utilisable comme nom de fichier"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')
    
    def url_to_filename(self, url):
        """Convertit une URL en nom de fichier attendu"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            return "index"
        
        # Remplacer les caractères spéciaux
        filename = self.slugify(path.replace('/', '_'))
        return filename
    
    def scan_existing_files(self):
        """Scan tous les fichiers existants dans le répertoire de sortie"""
        print("🔍 Scan des fichiers existants...")
        
        if not self.output_dir.exists():
            print(f"❌ Répertoire de sortie n'existe pas: {self.output_dir}")
            return
        
        total_files = 0
        
        for category_dir in self.output_dir.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                self.existing_files[category_name] = []
                
                txt_files = list(category_dir.glob("*.txt"))
                
                for txt_file in txt_files:
                    # Lire l'en-tête du fichier pour extraire l'URL source
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
                        print(f"❌ Erreur lecture fichier {txt_file}: {e}")
                
                if self.existing_files[category_name]:
                    print(f"📁 {category_name}: {len(self.existing_files[category_name])} fichiers")
        
        print(f"📊 Total de fichiers existants: {total_files}")
        return total_files
    
    def check_url_already_extracted(self, url):
        """Vérifie si une URL a déjà été extraite"""
        return url in self.url_mapping
    
    def get_expected_filename(self, url, category):
        """Retourne le nom de fichier attendu pour une URL"""
        filename = self.url_to_filename(url)
        expected_path = self.output_dir / category / f"{filename}.txt"
        return expected_path
    
    def verify_extraction_completeness(self, urls_to_extract):
        """Vérifie la complétude de l'extraction"""
        print("\n🔍 Vérification de la complétude de l'extraction...")
        
        stats = {
            'total_urls': len(urls_to_extract),
            'already_extracted': 0,
            'missing': 0,
            'to_extract': [],
            'missing_urls': []
        }
        
        for category, urls in urls_to_extract.items():
            print(f"\n📁 Catégorie: {category}")
            
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
                    
                    if expected_file.exists():
                        category_stats['extracted'] += 1
                        stats['already_extracted'] += 1
                    else:
                        category_stats['missing'] += 1
                        stats['missing'] += 1
                        stats['to_extract'].append((category, url))
                        stats['missing_urls'].append(url)
            
            print(f"   ✅ Extraites: {category_stats['extracted']}")
            print(f"   ❌ Manquantes: {category_stats['missing']}")
            print(f"   📊 Taux: {category_stats['extracted']/category_stats['total']*100:.1f}%")
        
        return stats
    
    def generate_extraction_report(self, stats):
        """Génère un rapport d'extraction"""
        print("\n" + "="*60)
        print("📊 RAPPORT D'EXTRACTION")
        print("="*60)
        
        print(f"URLs totales à traiter: {stats['total_urls']}")
        print(f"URLs déjà extraites: {stats['already_extracted']}")
        print(f"URLs manquantes: {stats['missing']}")
        
        if stats['total_urls'] > 0:
            completion_rate = (stats['already_extracted'] / stats['total_urls']) * 100
            print(f"Taux de complétude: {completion_rate:.1f}%")
        
        if stats['missing'] > 0:
            print(f"\n❌ URLs manquantes ({stats['missing']}):")
            for i, (category, url) in enumerate(stats['to_extract'][:10], 1):
                print(f"   {i}. [{category}] {url}")
            
            if len(stats['to_extract']) > 10:
                print(f"   ... et {len(stats['to_extract']) - 10} autres URLs")
        
        # Sauvegarder le rapport
        report_file = self.output_dir / 'extraction_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': stats,
                'missing_urls': stats['missing_urls']
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rapport sauvegardé: {report_file}")
    
    def clean_empty_files(self):
        """Nettoie les fichiers vides ou corrompus"""
        print("\n🧹 Nettoyage des fichiers vides/corrompus...")
        
        cleaned_count = 0
        
        for category_dir in self.output_dir.iterdir():
            if category_dir.is_dir():
                for txt_file in category_dir.glob("*.txt"):
                    try:
                        if txt_file.stat().st_size == 0:
                            print(f"🗑️  Suppression fichier vide: {txt_file}")
                            txt_file.unlink()
                            cleaned_count += 1
                        elif txt_file.stat().st_size < 100:  # Fichiers très petits
                            with open(txt_file, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if not content or len(content) < 50:
                                    print(f"🗑️  Suppression fichier trop petit: {txt_file}")
                                    txt_file.unlink()
                                    cleaned_count += 1
                    except Exception as e:
                        print(f"❌ Erreur lors du nettoyage de {txt_file}: {e}")
        
        print(f"🧹 Nettoyage terminé: {cleaned_count} fichiers supprimés")
        return cleaned_count

def load_urls_from_csv(filepath='urls_to_extract.csv'):
    """Charge les URLs et leurs catégories depuis un fichier CSV."""
    urls_by_category = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader) # Skip header row
            for row in reader:
                if len(row) >= 2:
                    category = row[0].strip()
                    url = row[1].strip()
                    if category not in urls_by_category:
                        urls_by_category[category] = []
                    urls_by_category[category].append(url)
    except FileNotFoundError:
        print(f"❌ Erreur: Le fichier CSV '{filepath}' n'a pas été trouvé.")
        return None
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV '{filepath}': {e}")
        return None
    return urls_by_category

def main():
    print("Début de l'exécution de verify_extraction.py") # Nouveau log
    
    # Charger les URLs depuis le fichier CSV
    urls_to_extract = load_urls_from_csv('urls_to_extract.csv')
    
    if urls_to_extract is None:
        print("Impossible de continuer sans la liste des URLs à extraire.")
        return

    # Créer le vérificateur
    verifier = ExtractionVerifier()
    print(f"Répertoire de sortie configuré: {verifier.output_dir}") # Nouveau log
    
    # Scanner les fichiers existants
    verifier.scan_existing_files()
    
    # Nettoyer les fichiers vides
    verifier.clean_empty_files()
    
    # Vérifier la complétude
    stats = verifier.verify_extraction_completeness(urls_to_extract)
    
    # Générer le rapport
    verifier.generate_extraction_report(stats)
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    if stats['missing'] == 0:
        print("✅ Toutes les URLs ont été extraites avec succès !")
    else:
        print(f"🔄 {stats['missing']} URLs restent à traiter")
        print("   Utilisez le script d'extraction pour traiter les URLs manquantes")
    
    print("\n🚀 COMMANDES SUIVANTES:")
    if stats['missing'] > 0:
        print("   # Extraire toutes les URLs manquantes")
        print("   ./extract_remaining.sh all")
        print()
        print("   # Extraire par catégorie")
        print("   ./extract_remaining.sh priority")

if __name__ == "__main__":
    # Utiliser 'python' pour l'exécution directe
    # Si ce script est appelé par un autre script shell, il utilisera l'interpréteur défini dans ce shell.
    # Pour une exécution directe, 'python' est plus courant sur Windows.
    main()
