import subprocess
import threading
import time
import glob
import os
import csv
import sys # Ajouter l'importation de sys

output_dir = r"C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output"

# Charger le CSV pour connaître le nombre total d'URLs
# Utilisation du module csv standard
total_urls = 0
with open("integrations_urls.csv", 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    # Sauter l'en-tête
    next(reader, None)
    total_urls = sum(1 for row in reader)

def monitor_progress():
    """Fonction de monitoring en arrière-plan"""
    while True:
        try:
            current_files = glob.glob(os.path.join(output_dir, "integrations", "*.txt"))
            print(f"[MONITORING] Fichiers extraits: {len(current_files)}/{total_urls}")
            time.sleep(60)  # Vérifier toutes les minutes
        except Exception as e:
            print(f"[MONITORING ERROR] {e}")
            break

# Démarrer le monitoring
monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
monitor_thread.start()

# Commande principale d'extraction
cmd = [
    sys.executable, "integrations_scraper.py",
    "--csv", "integrations_urls.csv",
    "--output", output_dir,
    "--workers", "6",
    "--skip-existing"
]

print("Démarrage de l'extraction...")
print(f"Commande: {' '.join(cmd)}")

# Exécuter avec capture des logs
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"Code de retour: {result.returncode}")
print("STDOUT:", result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
