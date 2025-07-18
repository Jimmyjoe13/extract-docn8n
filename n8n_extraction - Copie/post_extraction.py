import glob
import os

output_dir = r"C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output"

# Actions à effectuer après l'extraction
def post_extraction_actions():
    """Actions recommandées après l'extraction"""
    
    print("\n=== ACTIONS POST-EXTRACTION ===")
    
    # Vérifier l'intégrité des fichiers
    empty_files = []
    for file in glob.glob(os.path.join(output_dir, "integrations", "*.txt")):
        if os.path.getsize(file) < 100:  # Fichiers de moins de 100 bytes
            empty_files.append(file)
    
    if empty_files:
        print(f"Fichiers potentiellement vides: {len(empty_files)}")
        for file in empty_files[:5]:  # Afficher les 5 premiers
            print(f"  {os.path.basename(file)}")
    else:
        print("Aucun fichier potentiellement vide détecté.")
    
    # Proposer des actions de conversion
    print("\nActions recommandées:")
    print("1. Convertir en PDF par lot:")
    print("   pandoc output/integrations/*.txt -o integrations_complete.pdf")
    
    print("2. Créer une archive:")
    print("   tar -czf integrations_extraction.tar.gz output/integrations/")
    
    print("3. Indexer pour recherche:")
    print("   # Utiliser ElasticSearch ou Whoosh pour indexation")
    
    print("4. Vérifier des URLs spécifiques:")
    print("   # Contrôler manuellement les intégrations critiques")

# Exécuter les actions post-extraction
post_extraction_actions()
