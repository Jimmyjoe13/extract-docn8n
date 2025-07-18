import glob
import os
import csv

output_dir = r"C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output"
existing_files = glob.glob(os.path.join(output_dir, "**", "*.txt"), recursive=True)
print(f"Fichiers existants: {len(existing_files)}")

integration_files = glob.glob(os.path.join(output_dir, "integrations", "*.txt"))
print(f"Fichiers intégrations existants: {len(integration_files)}")

total_urls = 0
with open("integrations_urls.csv", 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    total_urls = sum(1 for row in reader) - 1 # Soustraire l'en-tête

print(f"URLs totales à traiter: {total_urls}")
print(f"URLs restantes: {total_urls - len(integration_files)}")
