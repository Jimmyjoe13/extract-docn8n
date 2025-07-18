#!/bin/bash

# Script d'automatisation pour l'extraction des URLs restantes n8n

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonction de logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Obtenir le répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activer l'environnement virtuel
# Activer l'environnement virtuel
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then # Pour Windows
    source venv/Scripts/activate
else
    log_error "Environnement virtuel non trouvé. Exécutez ./install.sh d'abord."
    exit 1
fi

PYTHON_SCRIPT="scripts/n8n_bulk_text_dump_updated.py"
OUTPUT_DIR="./output"
SITEMAP_URL="https://docs.n8n.io/sitemap.xml"
WORKERS=15 # Nombre de workers par défaut

# Catégories définies dans le script Python (doivent correspondre)
ALL_CATEGORIES="api,courses,user_management,hosting,non_categorized,langchain_agent,workflows,code,integrations,other"
PRIORITY_CATEGORIES="api,courses,user_management,hosting,non_categorized"

show_help() {
    echo "Utilisation: $0 [option] [workers]"
    echo ""
    echo "Options:"
    echo "  all                     : Extrait toutes les catégories définies."
    echo "  priority                : Extrait les catégories à haute priorité (API, Courses, User Management, Hosting, Non catégorisées)."
    echo "  api                     : Extrait uniquement la catégorie 'api'."
    echo "  courses                 : Extrait uniquement la catégorie 'courses'."
    echo "  user_management         : Extrait uniquement la catégorie 'user_management'."
    echo "  hosting                 : Extrait uniquement la catégorie 'hosting'."
    echo "  non_categorized         : Extrait uniquement la catégorie 'non_categorized'."
    echo "  langchain_agent         : Extrait uniquement la catégorie 'langchain_agent'."
    echo "  workflows               : Extrait uniquement la catégorie 'workflows'."
    echo "  code                    : Extrait uniquement la catégorie 'code'."
    echo "  integrations            : Extrait uniquement la catégorie 'integrations'."
    echo "  other                   : Extrait uniquement la catégorie 'other'."
    echo "  [workers]               : Nombre de workers concurrents (par défaut: 15)."
    echo "  --help                  : Affiche cette aide."
    echo ""
    echo "Exemples:"
    echo "  $0 all"
    echo "  $0 priority 20"
    echo "  $0 api"
}

if [ "$#" -eq 0 ] || [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

CATEGORY_ARG=""
case "$1" in
    all)
        CATEGORY_ARG="--categories $ALL_CATEGORIES"
        ;;
    priority)
        CATEGORY_ARG="--categories $PRIORITY_CATEGORIES"
        ;;
    api|courses|user_management|hosting|non_categorized|langchain_agent|workflows|code|integrations|other)
        CATEGORY_ARG="--categories $1"
        ;;
    *)
        log_error "Option invalide: $1"
        show_help
        exit 1
        ;;
esac

# Gérer le nombre de workers si spécifié
if [ -n "$2" ] && [[ "$2" =~ ^[0-9]+$ ]]; then
    WORKERS="$2"
fi

log_info "Lancement de l'extraction pour les catégories: ${CATEGORY_ARG} avec ${WORKERS} workers..."
log_info "Sortie vers: ${OUTPUT_DIR}"
log_info "Sitemap: ${SITEMAP_URL}"

python "$PYTHON_SCRIPT" \
  $CATEGORY_ARG \
  --workers "$WORKERS" \
  --output "$OUTPUT_DIR" \
  --sitemap "$SITEMAP_URL"

log_info "Extraction terminée."

deactivate 2>/dev/null || true # Désactiver l'environnement virtuel
