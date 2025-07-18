#!/bin/bash
# Script de lancement complet pour l'extraction des URLs restantes n8n
# Automatise tout le processus de A à Z

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
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

log_step() {
    echo -e "${BLUE}${BOLD}[ÉTAPE]${NC} $1"
}

# Affichage du titre
echo -e "${BLUE}${BOLD}"
echo "██████╗ ███████╗██╗   ██╗██╗██████╗  ██████╗ ███████╗    ███╗   ██╗ █████╗ ███╗   ██╗"
echo "██╔══██╗██╔════╝██║   ██║██║██╔══██╗██╔═══██╗██╔════╝    ████╗  ██║██╔══██╗████╗  ██║"
echo "██████╔╝███████╗██║   ██║██║██████╔╝██║   ██║███████╗    ██╔██╗ ██║╚█████╔╝██╔██╗ ██║"
echo "██╔══██╗╚════██║██║   ██║██║██╔══██╗██║   ██║╚════██║    ██║╚██╗██║██╔══██╗██║╚██╗██║"
echo "██║  ██║███████║╚██████╔╝██║██║  ██║╚██████╔╝███████║    ██║ ╚████║╚█████╔╝██║ ╚████║"
echo "╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═══╝ ╚════╝ ╚═╝  ╚═══╝"
echo -e "${NC}"
echo ""
echo -e "${BLUE}${BOLD}=== EXTRACTION DES 160 URLs RESTANTES ===${NC}"
echo ""

# Vérifier les arguments
WORKERS=${1:-15}
MODE=${2:-"priority"}

log_info "Configuration: $WORKERS workers, mode $MODE"

# Étape 1: Lancer l'extraction complète
log_step "1/1 - Lancement du processus d'extraction complet"

log_info "Lancement du script Python principal..."
log_info "Ce script va gérer la vérification, l'extraction et la génération du rapport."

# Exécuter le script Python principal
python n8n_full_extraction.py

extraction_result=$?

if [ $extraction_result -eq 0 ]; then
    log_info "Processus d'extraction complet terminé avec succès ✓"
else
    log_error "Processus d'extraction complet échoué (code: $extraction_result)"
    exit $extraction_result
fi

# Les étapes 2 à 6 sont maintenant gérées par n8n_full_extraction.py
# Le rapport final est généré par n8n_full_extraction.py

# Affichage final (peut être simplifié car le script Python logue déjà beaucoup)
echo ""
echo -e "${GREEN}${BOLD}🎉 EXTRACTION TERMINÉE AVEC SUCCÈS !${NC}"
echo ""
echo -e "${BLUE}=== RÉSUMÉ FINAL ===${NC}"
echo "Consultez les logs ci-dessus pour les détails de l'extraction."
echo "Un rapport détaillé (extraction_report.json) a été généré dans le dossier output/."
echo ""
echo -e "${BLUE}=== PROCHAINES ÉTAPES ===${NC}"
echo "1. Ouvrez le fichier 'n8n_extraction/output/extraction_report.json' pour voir le rapport détaillé."
echo "2. Les fichiers extraits se trouvent dans 'n8n_extraction/output/'."
echo "3. Si vous avez 'pandoc' installé, vous pouvez convertir les fichiers en PDF comme suit :"
echo "   pandoc n8n_extraction/output/api/*.txt -o n8n_extraction/api_docs.pdf"
echo "4. Pour archiver les résultats :"
echo "   tar -czf n8n_extraction/extraction_n8n_complete_$(date +%Y%m%d).tar.gz n8n_extraction/output/ n8n_extraction/logs/ n8n_extraction/extraction_report.json n8n_extraction/README.md"
echo ""
echo -e "${GREEN}Tous les outils de documentation n8n sont maintenant extraits ! 🚀${NC}"

# Désactiver l'environnement virtuel
deactivate 2>/dev/null || true
