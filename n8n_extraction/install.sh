#!/bin/bash
# Installation automatique pour l'extraction des URLs restantes n8n

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│                                                             │"
echo "│  🚀 INSTALLATION AUTOMATIQUE n8n URLs RESTANTES            │"
echo "│                                                             │"
echo "│  Installe et configure tous les outils nécessaires         │"
echo "│  pour extraire les 160 URLs restantes de la doc n8n        │"
echo "│                                                             │"
echo "└─────────────────────────────────────────────────────────────┘"
echo -e "${NC}"

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

# Vérifier si le script est exécuté avec bash
if [ -z "$BASH_VERSION" ]; then
    log_error "Ce script doit être exécuté avec bash"
    exit 1
fi

# Obtenir le répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "Répertoire d'installation: $SCRIPT_DIR"

# Étape 1: Vérifier Python
log_info "Vérification de Python..."
if ! command -v python &> /dev/null; then # Utiliser 'python' au lieu de 'python3'
    log_error "Python n'est pas installé ou n'est pas dans le PATH de Git Bash"
    log_error "Veuillez installer Python 3.8+ et vous assurer qu'il est accessible via la commande 'python' avant de continuer"
    exit 1
fi

PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')") # Utiliser 'python'
log_info "Python $PYTHON_VERSION détecté ✓"

# Étape 2: Vérifier pip
log_info "Vérification de pip..."
if ! command -v pip &> /dev/null; then # Utiliser 'pip' au lieu de 'pip3'
    log_error "pip n'est pas installé"
    log_error "Veuillez installer pip avant de continuer"
    exit 1
fi

log_info "pip détecté ✓"

# Étape 3: Créer un environnement virtuel
log_info "Configuration de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    log_info "Création de l'environnement virtuel..."
    python -m venv venv # Utiliser 'python'
fi

# Activer l'environnement virtuel
log_info "Activation de l'environnement virtuel..."
if [ -f "venv/Scripts/activate" ]; then # Vérifier d'abord le chemin Windows
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then # Puis le chemin Linux/macOS
    source venv/bin/activate
else
    log_error "Fichier d'activation de l'environnement virtuel non trouvé."
    exit 1
fi

# Étape 4: Installer les dépendances
log_info "Installation des dépendances Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    log_warning "requirements.txt non trouvé, installation manuelle..."
    pip install aiohttp html2text tqdm lxml requests
fi

log_info "Dépendances installées ✓"

# Étape 5: Vérifier les fichiers principaux
log_info "Vérification des fichiers principaux..."

required_files=(
    "scripts/n8n_bulk_text_dump_updated.py" # Nom du script principal mis à jour
    "extract_remaining.sh"
    "verify_extraction.py"
    "README.md"
    "urls_to_extract.csv" # Nom du fichier CSV mis à jour
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    log_error "Fichiers manquants:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    log_error "Veuillez vous assurer que tous les fichiers sont présents"
    exit 1
fi

log_info "Tous les fichiers requis sont présents ✓"

# Étape 6: Rendre les scripts exécutables
log_info "Configuration des permissions..."
chmod +x extract_remaining.sh
chmod +x scripts/n8n_bulk_text_dump_updated.py # Chemin et nom du script principal mis à jour
chmod +x verify_extraction.py

log_info "Permissions configurées ✓"

# Étape 7: Créer la structure de répertoires
log_info "Création de la structure de répertoires..."
mkdir -p output/{api,courses,user_management,hosting,non_categorized,langchain_agent,workflows,code,integrations,other} # Toutes les catégories
mkdir -p logs

log_info "Structure créée ✓"

# Étape 8: Test de connectivité
log_info "Test de connectivité vers n8n..."
if curl -Is https://docs.n8n.io/sitemap.xml | head -1 | grep -q "200 OK"; then
    log_info "Connectivité vers n8n OK ✓"
else
    log_warning "Problème de connectivité vers n8n (peut être temporaire)"
fi

# Étape 9: Test des dépendances Python
log_info "Test des dépendances Python..."
python -c "import aiohttp, html2text, tqdm, lxml; print('✓ Toutes les dépendances sont disponibles')" || { # Utiliser 'python'
    log_error "Erreur avec les dépendances Python"
    exit 1
}

# Étape 10: Afficher un résumé des URLs à traiter
log_info "Analyse des URLs à traiter..."
if [ -f "urls_to_extract.csv" ]; then
    # Utiliser awk pour compter les URLs par catégorie
    # La première ligne est l'en-tête, donc on commence à partir de la deuxième ligne (NR > 1)
    # On compte les lignes où le premier champ (category) correspond
    api_count=$(awk -F',' 'NR > 1 && $1 == "api" {count++} END {print count}' urls_to_extract.csv)
    courses_count=$(awk -F',' 'NR > 1 && $1 == "courses" {count++} END {print count}' urls_to_extract.csv)
    user_mgmt_count=$(awk -F',' 'NR > 1 && $1 == "user_management" {count++} END {print count}' urls_to_extract.csv)
    hosting_count=$(awk -F',' 'NR > 1 && $1 == "hosting" {count++} END {print count}' urls_to_extract.csv)
    non_cat_count=$(awk -F',' 'NR > 1 && $1 == "non_categorized" {count++} END {print count}' urls_to_extract.csv)
    
    echo ""
    echo -e "${BLUE}=== URLS À TRAITER ===${NC}"
    echo "📚 API: ${api_count:-0} URLs" # Utiliser :-0 pour afficher 0 si vide
    echo "🎓 Courses: ${courses_count:-0} URLs"
    echo "👥 User Management: ${user_mgmt_count:-0} URLs"
    echo "🏗️  Hosting: ${hosting_count:-0} URLs"
    echo "📄 Non catégorisées: ${non_cat_count:-0} URLs"
    echo ""
    total_urls=$((api_count + courses_count + user_mgmt_count + hosting_count + non_cat_count))
    echo "📊 Total: $total_urls URLs"
fi

# Étape 11: Afficher les commandes disponibles
echo ""
echo -e "${GREEN}🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !${NC}"
echo ""
echo -e "${BLUE}=== COMMANDES DISPONIBLES ===${NC}"
echo ""
echo "🔍 Vérifier les fichiers déjà extraits:"
echo "   python3 verify_extraction.py"
echo ""
echo "🚀 Lancer l'extraction (recommandé):"
echo "   ./extract_remaining.sh priority"
echo ""
echo "📊 Extraire toutes les catégories:"
echo "   ./extract_remaining.sh all"
echo ""
echo "🎯 Extraire une catégorie spécifique:"
echo "   ./extract_remaining.sh api"
echo "   ./extract_remaining.sh courses"
echo "   ./extract_remaining.sh user_management"
echo "   ./extract_remaining.sh hosting"
echo "   ./extract_remaining.sh non_categorized"
echo ""
echo "📋 Voir l'aide:"
echo "   ./extract_remaining.sh --help"
echo ""
echo "📖 Lire le guide complet:"
echo "   cat README.md"
echo ""

# Étape 12: Proposer un test rapide
echo -e "${YELLOW}=== TEST RAPIDE ===${NC}"
echo ""
read -p "Voulez-vous lancer un test rapide (extraction de 5 URLs API) ? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Lancement du test rapide..."
    # Utiliser le chemin relatif correct pour le script extract_remaining.sh
    ./extract_remaining.sh api 5
    
    # Vérifier les résultats
    if [ -d "output/api" ] && [ "$(find output/api -maxdepth 1 -type f -name "*.txt" | wc -l)" -gt 0 ]; then
        log_info "Test rapide réussi ✓"
        echo "Fichiers créés dans output/api/"
        # Utiliser find pour lister les fichiers de manière compatible Windows/Linux
        find output/api -maxdepth 1 -type f -name "*.txt"
    else
        log_warning "Test rapide échoué, vérifiez les logs"
    fi
fi

# Étape 13: Informations finales
echo ""
echo -e "${GREEN}=== INFORMATIONS FINALES ===${NC}"
echo ""
echo "📁 Répertoire d'installation: $SCRIPT_DIR"
echo "🐍 Environnement virtuel: $SCRIPT_DIR/venv"
echo "📄 Fichiers de sortie: $SCRIPT_DIR/output/"
echo "📊 Logs: $SCRIPT_DIR/logs/"
echo ""
echo "💡 Pour utiliser l'environnement virtuel:"
echo "   source venv/bin/activate"
echo ""
echo "🆘 En cas de problème:"
echo "   1. Vérifiez les logs d'extraction"
echo "   2. Lancez: python3 verify_extraction.py"
echo "   3. Consultez le README.md"
echo ""
echo -e "${GREEN}Bon scraping ! 🚀${NC}"

# Désactiver l'environnement virtuel
deactivate 2>/dev/null || true
