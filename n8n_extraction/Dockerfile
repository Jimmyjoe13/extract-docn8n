# Utiliser une image Python officielle comme base
FROM python:3.9-slim-buster

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt et installer les dépendances
COPY n8n_extraction/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY n8n_extraction/scripts/ /app/scripts/
COPY n8n_extraction/output/ /app/output/
COPY n8n_extraction/logs/ /app/logs/
COPY n8n_extraction/tests/ /app/tests/
COPY n8n_extraction/setup_quick.sh .
COPY n8n_extraction/test_extraction_langchain.sh .
COPY n8n_extraction/resume-ameliorations.md .
COPY n8n_extraction/guide-deploiement-n8n.md .
COPY n8n_extraction/README-langchain-priority.md .

# Créer les répertoires de sortie et de logs si ce n'est pas déjà fait par le script
RUN mkdir -p output logs

# Commande par défaut pour exécuter le script
# Cette commande peut être surchargée lors du déploiement sur Railway.app
CMD ["python", "scripts/n8n_bulk_text_dump_updated.py", "--categories", "langchain_agent,workflows,other,code", "--workers", "20", "--output", "./output", "--sitemap", "https://docs.n8n.io/sitemap.xml"]
