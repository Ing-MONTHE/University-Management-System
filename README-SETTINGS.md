# 🔧 Restructuration Multi-Environnement - Guide Rapide

## ✨ Nouveautés

Votre projet Django a été restructuré avec une configuration multi-environnement professionnelle.

### 📁 Nouvelle Structure

```
config/
├── settings/
│   ├── __init__.py
│   ├── base.py           # ⚙️  Configuration commune
│   ├── development.py    # 🚀 Configuration développement
│   ├── production.py     # 🔒 Configuration production
│   └── test.py          # 🧪 Configuration tests
├── urls.py
├── wsgi.py
└── asgi.py

.env                      # 🔐 Vos variables d'environnement
.env.example             # 📋 Template de configuration
```

## 🚀 Démarrage Rapide

### 1️⃣ Configuration Initiale

```bash
# Créer le fichier .env
cp .env.example .env

# Éditer .env et configurer vos variables
nano .env  # ou vim, code, etc.
```

### 2️⃣ Installation (Développement)

```bash
# Installer les dépendances
pip install -r requirements-dev.txt

# Ou utiliser le script de setup
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh

# Ou utiliser le Makefile
make install-dev
make setup-env
```

### 3️⃣ Base de Données

```bash
# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Ou avec Makefile
make migrate
make createsuperuser
```

### 4️⃣ Lancer le Serveur

```bash
# Développement (par défaut)
python manage.py runserver

# Ou avec Makefile
make runserver
```

## 🔄 Changer d'Environnement

### Méthode 1 : Variable d'environnement

```bash
# Développement
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver

# Production
export DJANGO_SETTINGS_MODULE=config.settings.production
gunicorn config.wsgi:application
```

### Méthode 2 : Option --settings

```bash
# Développement
python manage.py runserver --settings=config.settings.development

# Tests
python manage.py test --settings=config.settings.test
```

### Méthode 3 : Fichier .env

```env
# Dans .env
DJANGO_SETTINGS_MODULE=config.settings.development
```

## 📝 Variables d'Environnement Essentielles

```env
# .env
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=votre-cle-secrete
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DB_ENGINE=django.db.backends.postgresql
DB_NAME=university_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🛠️ Commandes Utiles (Makefile)

```bash
make help              # Afficher toutes les commandes
make install-dev       # Installer dépendances de dev
make migrate           # Appliquer les migrations
make runserver         # Lancer le serveur
make test              # Exécuter les tests
make test-cov          # Tests avec couverture
make lint              # Vérifier le code
make format            # Formater le code
make clean             # Nettoyer les fichiers temporaires
```

## 🧪 Tests

```bash
# Tous les tests
python manage.py test --settings=config.settings.test

# Avec pytest et couverture
pytest --cov=apps --cov-report=html

# Ou avec Makefile
make test
make test-cov
```

## 🔒 Production

### Configuration

```env
# .env pour production
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=votre-cle-secrete-forte-et-unique
DEBUG=False
ALLOWED_HOSTS=votredomaine.com,www.votredomaine.com

# Base de données production
DB_ENGINE=django.db.backends.postgresql
DB_NAME=university_db_prod
DB_USER=db_user_prod
DB_PASSWORD=mot-de-passe-fort
DB_HOST=db.example.com
DB_PORT=5432

# Redis
REDIS_URL=redis://redis.example.com:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@example.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe
```

### Déploiement

```bash
# Installer dépendances production
pip install -r requirements-prod.txt

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate --noinput

# Démarrer avec Gunicorn
gunicorn -c gunicorn_config.py config.wsgi:application

# Ou avec Makefile
make install-prod
make prod-setup
make gunicorn
```

## 🏥 Vérification de Santé

```bash
# Exécuter le script de vérification
python scripts/health_check.py

# Vérifier la configuration Django
python manage.py check

# Vérifier pour le déploiement
python manage.py check --deploy
```

## 📚 Documentation Complète

Pour plus de détails, consultez :
- **[CONFIGURATION.md](CONFIGURATION.md)** : Guide complet de configuration
- **[.env.example](.env.example)** : Template des variables d'environnement
- **[gunicorn_config.py](gunicorn_config.py)** : Configuration Gunicorn

## 🔑 Points Importants

### Développement
- ✅ DEBUG activé
- ✅ Logs verbeux
- ✅ Base de données locale
- ✅ CORS permissif
- ✅ Tokens JWT longue durée

### Production
- 🔒 DEBUG désactivé
- 🔒 HTTPS obligatoire
- 🔒 Sécurité renforcée (HSTS, etc.)
- 🔒 Cache Redis
- 🔒 Logs en fichiers
- 🔒 Tokens JWT courte durée

### Tests
- 🧪 Base de données en mémoire
- 🧪 Cache en mémoire
- 🧪 Email en mémoire
- 🧪 Logs minimaux

## ❓ Questions Fréquentes

**Q: Comment générer une SECRET_KEY ?**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Ou
make generate-secret
```

**Q: Comment utiliser SQLite au lieu de PostgreSQL ?**
```env
# Dans .env, commenter les lignes PostgreSQL
# Décommenter la configuration SQLite dans development.py
```

**Q: Comment activer Django Debug Toolbar ?**
```bash
# Installer
pip install django-debug-toolbar

# Décommenter dans config/settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

## 🆘 Support

En cas de problème :
1. Vérifiez le fichier `.env`
2. Consultez les logs : `logs/development.log`
3. Exécutez le health check : `python scripts/health_check.py`
4. Consultez la documentation : `CONFIGURATION.md`

## 📦 Fichiers Fournis

- ✅ **config/settings/** : Configuration multi-environnement
- ✅ **.env.example** : Template de configuration
- ✅ **requirements-dev.txt** : Dépendances de développement
- ✅ **requirements-prod.txt** : Dépendances de production
- ✅ **gunicorn_config.py** : Configuration Gunicorn
- ✅ **Makefile** : Commandes utiles
- ✅ **scripts/dev-setup.sh** : Script de setup automatique
- ✅ **scripts/health_check.py** : Vérification de santé
- ✅ **CONFIGURATION.md** : Documentation complète
- ✅ **.gitignore** : Fichiers à ne pas versionner

---

**Version** : 1.0.0  
**Date** : Février 2026  
**Django** : 6.0.1  
**Python** : 3.11+