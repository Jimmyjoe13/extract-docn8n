import sys
import os
import subprocess

# Vérifier Python
print(f"Python version: {sys.version}")
assert sys.version_info >= (3, 8), "Python 3.8+ requis"

# Vérifier le répertoire de travail
work_dir = r"C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie"
assert os.path.exists(work_dir), f"Répertoire de travail non trouvé: {work_dir}"
os.chdir(work_dir)
print(f"Répertoire de travail: {os.getcwd()}")

# Vérifier les fichiers requis
required_files = ["integrations_urls.csv", "integrations_scraper.py", "requirements.txt"]
for file in required_files:
    assert os.path.exists(file), f"Fichier manquant: {file}"
print("Tous les fichiers requis sont présents")
