Résultats attendus
Avec cette configuration, vous obtiendrez :

50-80 fichiers LangChain Agent IA (priorité #1, nouveauté)

20 fichiers workflows (priorité #2)

135 fichiers autres (priorité #3)

38 fichiers code (priorité #4)

930 fichiers intégrations (priorité #7, optionnel)

Commandes essentielles récapitulatives
bash
# 1. Configuration rapide
./setup_quick.sh

# 2. Extraction prioritaire LangChain + essentiels
python n8n_bulk_text_dump_updated.py \
  --categories langchain_agent,workflows,other,code \
  --workers 20 \
  --output ./output

# 3. Surveillance
tail -f n8n_extraction.log

# 4. Vérification
find output -name "*.txt" | wc -l
Le script est maintenant parfaitement adapté pour extraire en priorité absolue toute la documentation des nodes LangChain Agent IA de n8n, avec une automatisation complète et un déploiement simplifié !
