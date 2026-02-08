#!/bin/bash
# =============================================================================
# Script de démarrage rapide pour l'environnement de développement
# =============================================================================
# Usage: ./scripts/dev-setup.sh
# =============================================================================

set -e  # Arrêter en cas d'erreur

echo "======================================================================"
echo "🚀 Configuration de l'environnement de développement"
echo "======================================================================"

# Couleurs pour le terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages colorés
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier Python
info "Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 n'est pas installé"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
success "Python trouvé : $PYTHON_VERSION"

# Vérifier si on est dans le bon dossier
if [ ! -f "manage.py" ]; then
    error "Ce script doit être exécuté depuis la racine du projet"
    exit 1
fi

# Créer l'environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    info "Création de l'environnement virtuel..."
    python3 -m venv venv
    success "Environnement virtuel créé"
else
    warning "L'environnement virtuel existe déjà"
fi

# Activer l'environnement virtuel
info "Activation de l'environnement virtuel..."
source venv/bin/activate
success "Environnement virtuel activé"

# Mettre à jour pip
info "Mise à jour de pip..."
pip install --upgrade pip > /dev/null 2>&1
success "Pip mis à jour"

# Installer les dépendances
info "Installation des dépendances de développement..."
pip install -r requirements-dev.txt
success "Dépendances installées"

# Créer le fichier .env si nécessaire
if [ ! -f ".env" ]; then
    info "Création du fichier .env..."
    cp .env.example .env
    success "Fichier .env créé"
    warning "⚠️  N'oubliez pas de configurer vos variables dans .env"
else
    warning "Le fichier .env existe déjà"
fi

# Créer le dossier logs
info "Création du dossier logs..."
mkdir -p logs
success "Dossier logs créé"

# Demander si l'utilisateur veut créer la base de données
echo ""
read -p "$(echo -e ${BLUE})Voulez-vous configurer la base de données maintenant ? (y/n) $(echo -e ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Application des migrations..."
    python manage.py migrate
    success "Migrations appliquées"
    
    echo ""
    read -p "$(echo -e ${BLUE})Voulez-vous créer un superutilisateur ? (y/n) $(echo -e ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python manage.py createsuperuser
    fi
fi

# Afficher les informations finales
echo ""
echo "======================================================================"
success "Configuration terminée avec succès !"
echo "======================================================================"
echo ""
echo "Pour démarrer le serveur de développement :"
echo "  1. Activez l'environnement virtuel : source venv/bin/activate"
echo "  2. Lancez le serveur : python manage.py runserver"
echo ""
echo "URLs utiles :"
echo "  - API : http://localhost:8000/api/"
echo "  - Admin : http://localhost:8000/admin/"
echo "  - Documentation : http://localhost:8000/api/schema/swagger-ui/"
echo ""
echo "======================================================================"
