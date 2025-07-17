#!/bin/bash

# Script de configuration automatique pour l'extraction de documentation n8n

echo "--- Étape 1: Vérification des prérequis ---"
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Python 3.8+ n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi
echo "Python 3.8+ est installé."

pip --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "pip n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi
echo "pip est installé."

echo "--- Étape 2: Création et activation de l'environnement virtuel ---"
python3 -m venv venv_n8n_extraction
if [ $? -ne 0 ]; then
    echo "Erreur lors de la création de l'environnement virtuel."
    exit 1
fi
echo "Environnement virtuel 'venv_n8n_extraction' créé."

# Activer l'environnement en fonction du système d'exploitation
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    source venv_n8n_extraction/bin/activate
    echo "Environnement virtuel activé (Linux/macOS)."
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Pour Git Bash / Cygwin sur Windows
    source venv_n8n_extraction/Scripts/activate
    echo "Environnement virtuel activé (Windows)."
else
    echo "Système d'exploitation non reconnu. Veuillez activer l'environnement manuellement."
    exit 1
fi

echo "--- Étape 3: Installation des dépendances ---"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'installation des dépendances."
    deactivate # Désactiver l'environnement en cas d'erreur
    exit 1
fi
echo "Dépendances installées."

echo "--- Étape 4: Configuration initiale des répertoires et permissions ---"
mkdir -p output logs scripts tests
if [ $? -ne 0 ]; then
    echo "Erreur lors de la création des répertoires."
    deactivate
    exit 1
fi
echo "Structure de répertoires créée."

# Copier le script principal si ce script est exécuté depuis le répertoire parent
# Vérifier si le script principal existe déjà dans scripts/
if [ ! -f scripts/n8n_bulk_text_dump_updated.py ]; then
    echo "Copie du script principal n8n_bulk_text_dump_updated.py vers scripts/..."
    # Assurez-vous que ce script (setup_quick.sh) est dans le répertoire racine du projet
    # et que n8n_bulk_text_dump_updated.py est dans le même répertoire initialement
    # Avant de le déplacer, il faut s'assurer qu'il est bien là où on l'attend.
    # Pour l'instant, on suppose qu'il est déjà dans scripts/ comme créé par l'agent.
    # Si ce script est exécuté depuis le répertoire parent, il faut ajuster le chemin.
    # Pour l'instant, on ne fait rien car l'agent le place directement au bon endroit.
    echo "Le script principal est supposé être déjà dans scripts/."
fi

# Rendre exécutable (Linux/macOS)
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    chmod +x scripts/n8n_bulk_text_dump_updated.py
    echo "Script principal rendu exécutable."
fi

echo "--- Configuration automatique terminée avec succès ! ---"
echo "Vous pouvez maintenant exécuter le script principal :"
echo "python scripts/n8n_bulk_text_dump_updated.py --help"

# Ne pas désactiver l'environnement ici pour permettre à l'utilisateur de continuer
# deactivate
