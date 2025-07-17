#!/bin/bash

# Script de test automatisé pour l'extraction de documentation n8n

echo "--- Lancement des tests d'extraction ---"

# Activer l'environnement virtuel
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    source venv_n8n_extraction/bin/activate
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv_n8n_extraction/Scripts/activate
else
    echo "Système d'exploitation non reconnu. Veuillez activer l'environnement manuellement."
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "Erreur: Impossible d'activer l'environnement virtuel. Assurez-vous que setup_quick.sh a été exécuté."
    exit 1
fi

SCRIPT_PATH="scripts/n8n_bulk_text_dump_updated.py"
OUTPUT_BASE="./output"

# Nettoyer les anciens résultats de test
echo "Nettoyage des anciens répertoires de test..."
rm -rf "${OUTPUT_BASE}/test_langchain"
rm -rf "${OUTPUT_BASE}/test_priority"
rm -rf "${OUTPUT_BASE}/test_all"
echo "Nettoyage terminé."

# Test 1: Extraction LangChain Agent IA uniquement (priorité 1)
echo "--- Test 1: Extraction LangChain Agent IA uniquement ---"
python "$SCRIPT_PATH" \
  --categories langchain_agent \
  --workers 5 \
  --output "${OUTPUT_BASE}/test_langchain" \
  --sitemap https://docs.n8n.io/sitemap.xml

if [ $? -ne 0 ]; then
    echo "Test 1 échoué."
    deactivate
    exit 1
fi
echo "Test 1 terminé. Vérification des fichiers générés :"
ls -la "${OUTPUT_BASE}/test_langchain/"
echo "Nombre de fichiers LangChain extraits : $(find "${OUTPUT_BASE}/test_langchain" -type f | wc -l)"

# Test 2: Extraction des catégories prioritaires
echo "--- Test 2: Extraction des catégories prioritaires (langchain_agent, workflows, other, code) ---"
python "$SCRIPT_PATH" \
  --categories langchain_agent,workflows,other,code \
  --workers 10 \
  --output "${OUTPUT_BASE}/test_priority" \
  --sitemap https://docs.n8n.io/sitemap.xml

if [ $? -ne 0 ]; then
    echo "Test 2 échoué."
    deactivate
    exit 1
fi
echo "Test 2 terminé. Vérification des fichiers générés :"
ls -la "${OUTPUT_BASE}/test_priority/"
echo "Nombre total de fichiers prioritaires extraits : $(find "${OUTPUT_BASE}/test_priority" -type f | wc -l)"

# Test 3: Extraction complète avec toutes les catégories (optionnel, peut prendre du temps)
echo "--- Test 3: Extraction complète avec toutes les catégories (peut prendre du temps) ---"
echo "Pour exécuter ce test, décommentez les lignes ci-dessous dans le script."
# python "$SCRIPT_PATH" \
#   --categories langchain_agent,workflows,other,code,hosting,user_management,integrations \
#   --workers 15 \
#   --output "${OUTPUT_BASE}/test_all" \
#   --sitemap https://docs.n8n.io/sitemap.xml

# if [ $? -ne 0 ]; then
#     echo "Test 3 échoué."
#     deactivate
#     exit 1
# fi
# echo "Test 3 terminé. Vérification des fichiers générés :"
# ls -la "${OUTPUT_BASE}/test_all/"
# echo "Nombre total de fichiers extraits : $(find "${OUTPUT_BASE}/test_all" -type f | wc -l)"


echo "--- Tous les tests automatisés terminés ! ---"

deactivate
echo "Environnement virtuel désactivé."
