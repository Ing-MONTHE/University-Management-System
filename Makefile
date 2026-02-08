# =============================================================================
# Makefile pour University Management System
# =============================================================================
# Usage: make <commande>
# Exemple: make help
# =============================================================================

.PHONY: help install install-dev install-prod migrate makemigrations \
        createsuperuser runserver shell test test-cov clean collectstatic \
        dev prod check lint format

# Variables
PYTHON := python
PIP := pip
MANAGE := $(PYTHON) manage.py

# Par défaut, afficher l'aide
.DEFAULT_GOAL := help

# Couleurs pour le terminal
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Affiche ce message d'aide
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)📚 University Management System - Commandes disponibles$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"

# =============================================================================
# Installation et configuration
# =============================================================================

install: ## Installe les dépendances de base
	@echo "$(BLUE)📦 Installation des dépendances de base...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Installation terminée$(NC)"

install-dev: ## Installe les dépendances de développement
	@echo "$(BLUE)📦 Installation des dépendances de développement...$(NC)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✅ Installation terminée$(NC)"

install-prod: ## Installe les dépendances de production
	@echo "$(BLUE)📦 Installation des dépendances de production...$(NC)"
	$(PIP) install -r requirements-prod.txt
	@echo "$(GREEN)✅ Installation terminée$(NC)"

setup-env: ## Crée le fichier .env depuis .env.example
	@if [ ! -f .env ]; then \
		echo "$(BLUE)📝 Création du fichier .env...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✅ Fichier .env créé$(NC)"; \
		echo "$(YELLOW)⚠️  N'oubliez pas de configurer vos variables !$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Le fichier .env existe déjà$(NC)"; \
	fi

# =============================================================================
# Base de données
# =============================================================================

migrate: ## Applique les migrations
	@echo "$(BLUE)🔄 Application des migrations...$(NC)"
	$(MANAGE) migrate
	@echo "$(GREEN)✅ Migrations appliquées$(NC)"

makemigrations: ## Crée de nouvelles migrations
	@echo "$(BLUE)📝 Création des migrations...$(NC)"
	$(MANAGE) makemigrations
	@echo "$(GREEN)✅ Migrations créées$(NC)"

showmigrations: ## Affiche l'état des migrations
	@echo "$(BLUE)📋 État des migrations :$(NC)"
	$(MANAGE) showmigrations

migrate-app: ## Applique les migrations d'une app spécifique (usage: make migrate-app APP=core)
	@echo "$(BLUE)🔄 Application des migrations pour $(APP)...$(NC)"
	$(MANAGE) migrate $(APP)
	@echo "$(GREEN)✅ Migrations appliquées pour $(APP)$(NC)"

reset-db: ## Réinitialise la base de données (ATTENTION: supprime toutes les données)
	@echo "$(YELLOW)⚠️  ATTENTION: Cette commande va SUPPRIMER toutes les données !$(NC)"
	@read -p "Êtes-vous sûr ? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)🗑️  Réinitialisation de la base de données...$(NC)"; \
		$(MANAGE) flush --noinput; \
		echo "$(GREEN)✅ Base de données réinitialisée$(NC)"; \
	else \
		echo "$(YELLOW)❌ Annulé$(NC)"; \
	fi

# =============================================================================
# Gestion des utilisateurs
# =============================================================================

createsuperuser: ## Crée un superutilisateur
	@echo "$(BLUE)👤 Création d'un superutilisateur...$(NC)"
	$(MANAGE) createsuperuser

# =============================================================================
# Serveur de développement
# =============================================================================

runserver: ## Démarre le serveur de développement
	@echo "$(BLUE)🚀 Démarrage du serveur de développement...$(NC)"
	$(MANAGE) runserver

runserver-prod: ## Démarre le serveur avec les settings de production
	@echo "$(BLUE)🚀 Démarrage du serveur (mode production)...$(NC)"
	$(MANAGE) runserver --settings=config.settings.production

run: runserver ## Alias pour runserver

shell: ## Ouvre un shell Django
	@echo "$(BLUE)🐚 Ouverture du shell Django...$(NC)"
	$(MANAGE) shell

shell-plus: ## Ouvre un shell Django amélioré (nécessite django-extensions)
	@echo "$(BLUE)🐚 Ouverture du shell Django (shell_plus)...$(NC)"
	$(MANAGE) shell_plus --ipython

# =============================================================================
# Tests
# =============================================================================

test: ## Exécute tous les tests
	@echo "$(BLUE)🧪 Exécution des tests...$(NC)"
	$(MANAGE) test --settings=config.settings.test

test-app: ## Exécute les tests d'une app spécifique (usage: make test-app APP=core)
	@echo "$(BLUE)🧪 Exécution des tests pour $(APP)...$(NC)"
	$(MANAGE) test apps.$(APP) --settings=config.settings.test

test-cov: ## Exécute les tests avec couverture de code (nécessite pytest)
	@echo "$(BLUE)🧪 Exécution des tests avec couverture...$(NC)"
	pytest --cov=apps --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Rapport de couverture généré dans htmlcov/index.html$(NC)"

test-parallel: ## Exécute les tests en parallèle
	@echo "$(BLUE)🧪 Exécution des tests en parallèle...$(NC)"
	$(MANAGE) test --parallel --settings=config.settings.test

# =============================================================================
# Fichiers statiques et média
# =============================================================================

collectstatic: ## Collecte les fichiers statiques
	@echo "$(BLUE)📦 Collecte des fichiers statiques...$(NC)"
	$(MANAGE) collectstatic --noinput
	@echo "$(GREEN)✅ Fichiers statiques collectés$(NC)"

# =============================================================================
# Qualité du code
# =============================================================================

lint: ## Vérifie le code avec flake8
	@echo "$(BLUE)🔍 Vérification du code avec flake8...$(NC)"
	flake8 apps/ config/

format: ## Formate le code avec black et isort
	@echo "$(BLUE)🎨 Formatage du code...$(NC)"
	black apps/ config/
	isort apps/ config/
	@echo "$(GREEN)✅ Code formaté$(NC)"

format-check: ## Vérifie le formatage sans modifier les fichiers
	@echo "$(BLUE)🔍 Vérification du formatage...$(NC)"
	black apps/ config/ --check
	isort apps/ config/ --check-only

check: ## Exécute toutes les vérifications Django
	@echo "$(BLUE)✅ Vérification de la configuration Django...$(NC)"
	$(MANAGE) check
	@echo "$(GREEN)✅ Aucun problème détecté$(NC)"

check-deploy: ## Vérifie la configuration pour le déploiement
	@echo "$(BLUE)✅ Vérification de la configuration de déploiement...$(NC)"
	$(MANAGE) check --deploy --settings=config.settings.production

# =============================================================================
# Nettoyage
# =============================================================================

clean: ## Nettoie les fichiers temporaires
	@echo "$(BLUE)🧹 Nettoyage des fichiers temporaires...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

clean-migrations: ## Supprime tous les fichiers de migration (ATTENTION!)
	@echo "$(YELLOW)⚠️  ATTENTION: Cette commande va supprimer tous les fichiers de migration !$(NC)"
	@read -p "Êtes-vous sûr ? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)🗑️  Suppression des migrations...$(NC)"; \
		find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete; \
		find apps -path "*/migrations/*.pyc" -delete; \
		echo "$(GREEN)✅ Migrations supprimées$(NC)"; \
	else \
		echo "$(YELLOW)❌ Annulé$(NC)"; \
	fi

# =============================================================================
# Production
# =============================================================================

prod-setup: install-prod migrate collectstatic ## Configure l'environnement de production
	@echo "$(GREEN)✅ Environnement de production configuré$(NC)"

gunicorn: ## Démarre Gunicorn avec la configuration
	@echo "$(BLUE)🚀 Démarrage de Gunicorn...$(NC)"
	gunicorn -c gunicorn_config.py config.wsgi:application

gunicorn-dev: ## Démarre Gunicorn en mode développement
	@echo "$(BLUE)🚀 Démarrage de Gunicorn (mode dev)...$(NC)"
	gunicorn config.wsgi:application --bind 0.0.0.0:8000 --reload

# =============================================================================
# Utilitaires
# =============================================================================

logs: ## Affiche les logs de développement
	@tail -f logs/development.log

logs-prod: ## Affiche les logs de production
	@tail -f logs/production.log

backup-db: ## Crée un backup de la base de données
	@echo "$(BLUE)💾 Création du backup de la base de données...$(NC)"
	$(MANAGE) dumpdata --indent 2 > backup_$(shell date +%Y%m%d_%H%M%S).json
	@echo "$(GREEN)✅ Backup créé$(NC)"

restore-db: ## Restaure la base de données depuis un fichier (usage: make restore-db FILE=backup.json)
	@echo "$(BLUE)📥 Restauration de la base de données...$(NC)"
	$(MANAGE) loaddata $(FILE)
	@echo "$(GREEN)✅ Base de données restaurée$(NC)"

generate-secret: ## Génère une nouvelle SECRET_KEY
	@echo "$(BLUE)🔐 Génération d'une nouvelle SECRET_KEY :$(NC)"
	@$(PYTHON) -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

show-urls: ## Affiche toutes les URLs de l'application
	@echo "$(BLUE)📋 URLs de l'application :$(NC)"
	$(MANAGE) show_urls 2>/dev/null || $(MANAGE) shell -c "from django.urls import get_resolver; print('\n'.join(str(p) for p in get_resolver().url_patterns))"

# =============================================================================
# Docker (si utilisé)
# =============================================================================

docker-build: ## Construit l'image Docker
	@echo "$(BLUE)🐳 Construction de l'image Docker...$(NC)"
	docker-compose build

docker-up: ## Démarre les conteneurs Docker
	@echo "$(BLUE)🐳 Démarrage des conteneurs...$(NC)"
	docker-compose up -d

docker-down: ## Arrête les conteneurs Docker
	@echo "$(BLUE)🐳 Arrêt des conteneurs...$(NC)"
	docker-compose down

docker-logs: ## Affiche les logs Docker
	@docker-compose logs -f

# =============================================================================
# Informations
# =============================================================================

info: ## Affiche les informations sur l'environnement
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)📊 Informations sur l'environnement$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Django: $(shell $(MANAGE) version)"
	@echo "Settings: $(shell $(PYTHON) -c 'import os; print(os.getenv("DJANGO_SETTINGS_MODULE", "Non défini"))')"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"