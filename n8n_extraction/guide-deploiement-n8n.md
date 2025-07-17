Guide de déploiement étape par étape
Étape 1 : Préparation de l'environnement
Vérification des prérequis
bash
# Vérifier Python 3.8+ 
python --version
# ou
python3 --version

# Vérifier pip
pip --version
Création de l'environnement virtuel
bash
# Créer l'environnement
python -m venv venv_n8n_extraction

# Activer l'environnement
# Windows:
venv_n8n_extraction\Scripts\activate
# Linux/macOS:
source venv_n8n_extraction/bin/activate
Étape 2 : Installation des dépendances
bash
# Installation des bibliothèques requises
pip install aiohttp html2text tqdm lxml asyncio

# Ou utiliser le fichier requirements.txt
pip install -r requirements.txt
requirements.txt
Fichier généré
Étape 3 : Configuration initiale
Structure des répertoires
bash
# Créer la structure
mkdir -p n8n_extraction/{output,logs,scripts,tests}
cd n8n_extraction

# Copier le script
cp n8n_bulk_text_dump_updated.py scripts/

# Rendre exécutable (Linux/macOS)
chmod +x scripts/n8n_bulk_text_dump_updated.py
Étape 4 : Tests préliminaires
Test avec les URLs LangChain Agent IA
bash
# Test priorité 1 uniquement
python scripts/n8n_bulk_text_dump_updated.py \
  --categories langchain_agent \
  --workers 5 \
  --output ./output/test_langchain

# Vérifier les résultats
ls -la output/test_langchain/
Test avec toutes les catégories prioritaires
bash
# Test des 4 catégories prioritaires
python scripts/n8n_bulk_text_dump_updated.py \
  --categories langchain_agent,workflows,other,code \
  --workers 10 \
  --output ./output/test_priority

# Surveiller les logs
tail -f n8n_extraction.log
Étape 5 : Déploiement en production
Extraction complète des catégories prioritaires
bash
# Configuration optimisée
python scripts/n8n_bulk_text_dump_updated.py \
  --categories langchain_agent,workflows,other,code \
  --workers 20 \
  --output ./output/priority_docs \
  --sitemap https://docs.n8n.io/sitemap.xml
Traitement des intégrations par lots
bash
# Intégrations en phase séparée
python scripts/n8n_bulk_text_dump_updated.py \
  --categories integrations \
  --workers 15 \
  --output ./output/integrations_docs
