import glob
import os
import json
import time
import csv

output_dir = r"C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output"

# Charger le CSV pour connaître le nombre total d'URLs
total_urls = 0
with open("integrations_urls.csv", 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader, None) # Sauter l'en-tête
    total_urls = sum(1 for row in reader)

# Fonction de gestion des erreurs et reprise automatique
def handle_extraction_errors():
    """Gère les erreurs et reprend l'extraction si nécessaire"""
    
    # Vérifier les logs d'erreur
    if os.path.exists("integrations_extraction.log"):
        with open("integrations_extraction.log", "r", encoding="utf-8", errors='ignore') as f:
            log_content = f.read()
            
        # Compter les erreurs
        error_count = log_content.count("ERROR")
        warning_count = log_content.count("WARNING")
        
        print(f"Erreurs détectées: {error_count}")
        print(f"Avertissements: {warning_count}")
        
        if error_count > 0:
            print("Erreurs détectées dans les logs:")
            error_lines = [line for line in log_content.split('\n') if 'ERROR' in line]
            for error in error_lines[-5:]:  # Afficher les 5 dernières erreurs
                print(f"  {error}")
    
    # Compter les fichiers réussis
    final_files = glob.glob(os.path.join(output_dir, "integrations", "*.txt"))
    success_rate = len(final_files) / total_urls * 100
    
    print(f"Taux de succès: {success_rate:.1f}%")
    
    # Décision de reprise
    if success_rate < 95:
        print("Taux de succès insuffisant. Relancement recommandé...")
        return False
    else:
        print("Extraction terminée avec succès!")
        return True

# Exécuter la gestion des erreurs
extraction_success = handle_extraction_errors()
