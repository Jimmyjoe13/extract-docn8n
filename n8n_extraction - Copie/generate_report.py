import glob
import os
import json
import time
import csv

output_dir = r"C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output"

# Charger le CSV pour connaître le nombre total d'URLs et les données des URLs
total_urls = 0
urls_data = []
batch_groups = {}
with open("integrations_urls.csv", 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        urls_data.append(row)
        batch_group = row.get('batch_group')
        if batch_group:
            batch_groups.setdefault(batch_group, []).append(row['url_complete'])
    total_urls = len(urls_data)

# Génération du rapport final
def generate_final_report():
    """Génère un rapport complet de l'extraction"""
    
    report = {
        "total_urls": total_urls,
        "files_extracted": len(glob.glob(os.path.join(output_dir, "integrations", "*.txt"))),
        "success_rate": 0,
        "total_size_mb": 0,
        "extraction_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "batches_completed": {}
    }
    
    # Calculer la taille totale
    total_size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(output_dir, "integrations", "*.txt")))
    report["total_size_mb"] = round(total_size / (1024*1024), 2)
    
    # Calculer le taux de succès
    report["success_rate"] = round(report["files_extracted"] / report["total_urls"] * 100, 1)
    
    # Analyser les lots
    for batch, urls_in_batch in batch_groups.items():
        batch_files_count = 0
        for url in urls_in_batch:
            filename_slug = url.split("/")[-1].replace(".", "_").replace("-", "_")
            # Vérifier si un fichier correspondant existe dans le répertoire d'intégrations
            # On doit être plus flexible ici car le slugify peut changer le nom
            # On va chercher si le nom de fichier contient le slug de l'URL
            for existing_file in glob.glob(os.path.join(output_dir, "integrations", "*.txt")):
                if filename_slug in os.path.basename(existing_file):
                    batch_files_count += 1
                    break # Passer au fichier suivant une fois trouvé
        report["batches_completed"][batch] = f"{batch_files_count}/{len(urls_in_batch)}"
    
    print("=== RAPPORT FINAL ===")
    print(f"URLs totales: {report['total_urls']}")
    print(f"Fichiers extraits: {report['files_extracted']}")
    print(f"Taux de succès: {report['success_rate']}%")
    print(f"Taille totale: {report['total_size_mb']} MB")
    print(f"Heure d'extraction: {report['extraction_time']}")
    
    print("\nRépartition par lots:")
    for batch, stats in report["batches_completed"].items():
        print(f"  {batch}: {stats}")
    
    # Sauvegarder le rapport
    with open("extraction_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\nRapport sauvegardé dans: extraction_report.json")
    return report

# Générer le rapport
final_report = generate_final_report()
