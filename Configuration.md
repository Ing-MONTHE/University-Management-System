# 📚 Guide de Configuration Multi-Environnement

Ce document explique comment utiliser la nouvelle structure de configuration multi-environnement du système de gestion universitaire.

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Structure des fichiers](#structure-des-fichiers)
3. [Environnement de développement](#environnement-de-développement)
4. [Environnement de production](#environnement-de-production)
5. [Environnement de test](#environnement-de-test)
6. [Variables d'environnement](#variables-denvironnement)
7. [Commandes utiles](#commandes-utiles)
8. [FAQ](#faq)

---

## 🎯 Vue d'ensemble

Le projet utilise maintenant une structure de configuration modulaire qui permet de gérer facilement plusieurs environnements :

- **Development** : Pour le développement local avec des paramètres de debug activés
- **Production** : Pour le déploiement en production avec sécurité renforcée
- **Test** : Pour l'exécution des tests unitaires et d'intégration

### Avantages de cette approche

✅ **Sécurité** : Séparation claire entre dev et prod  
✅ **Flexibilité** : Chaque environnement a sa propre configuration  
✅ **Maintenabilité** : Code organisé et facile à maintenir  
✅ **Scalabilité** : Facile d'ajouter de nouveaux environnements (staging, etc.)  

---

## 📁 Structure des fichiers

```
config/
├── __init__.py
├── settings/
│   ├── __init__.py          # Documentation du package
│   ├── base.py              # Configuration commune à tous les environnements
│   ├── development.py       # Configuration pour le développement
│   ├── production.py        # Configuration pour la production
│   └── test.py              # Configuration pour les tests
├── urls.py
├── wsgi.py                  # Point d'entrée WSGI (production par défaut)
└── asgi.py                  # Point d'entrée ASGI (production par défaut)

.env.example                 # Template des variables d'environnement
.env                         # Fichier de configuration (à créer, non versionné)
manage.py                    # Utilise development par défaut
```

### Description des fichiers

#### `base.py`
Contient tous les paramètres communs :
- Applications installées
- Middleware
- Templates
- Configuration JWT
- Configuration REST Framework
- Paramètres d'internationalisation

#### `development.py`
Hérite de `base.py` et ajoute/surcharge :
- DEBUG = True
- Base de données locale
- CORS permissif
- Logging verbeux
- Django Debug Toolbar (optionnel)
- Tokens JWT avec durée de vie longue

#### `production.py`
Hérite de `base.py` et ajoute/surcharge :
- DEBUG = False
- Sécurité renforcée (HTTPS, HSTS, etc.)
- Cache Redis
- Email SMTP
- Logging en fichiers
- WhiteNoise pour les fichiers statiques
- Tokens JWT avec durée de vie courte

#### `test.py`
Hérite de `base.py` et ajoute/surcharge :
- Base de données en mémoire (SQLite)
- Cache en mémoire
- Email en mémoire
- Password hasher rapide
- Logging minimal

---

## 🚀 Environnement de développement

### Configuration initiale

1. **Créer le fichier .env**
   ```bash
   cp .env.example .env
   ```

2. **Éditer le fichier .env**
   ```env
   # Environnement
   DJANGO_SETTINGS_MODULE=config.settings.development
   
   # Sécurité
   SECRET_KEY=votre-cle-secrete-de-dev
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
   
   # JWT
   JWT_ACCESS_TOKEN_LIFETIME=120
   JWT_REFRESH_TOKEN_LIFETIME=30
   ```

3. **Créer l'environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

4. **Installer les dépendances de développement**
   ```bash
   pip install -r requirements-dev.txt
   ```

5. **Créer la base de données**
   ```bash
   # PostgreSQL
   createdb university_db
   
   # Ou utilisez SQLite en modifiant DB_ENGINE dans .env
   ```

6. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

7. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

8. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

### Vérification

L'application devrait afficher au démarrage :
```
======================================================================
🚀 ENVIRONNEMENT DE DÉVELOPPEMENT CHARGÉ
======================================================================
DEBUG: True
DATABASE: django.db.backends.postgresql - university_db
ALLOWED_HOSTS: ['localhost', '127.0.0.1', '[::1]', '0.0.0.0']
======================================================================
```

### Accès

- **API** : http://localhost:8000/api/
- **Admin** : http://localhost:8000/admin/
- **Documentation API** : http://localhost:8000/api/schema/swagger-ui/

### Outils de développement recommandés

```bash
# Debug Toolbar (déjà configuré mais commenté dans development.py)
pip install django-debug-toolbar

# IPython pour un shell amélioré
python manage.py shell_plus --ipython

# Voir toutes les requêtes SQL
# Dans .env, ajouter : DB_LOG_LEVEL=DEBUG
```

---

## 🔒 Environnement de production

### Configuration initiale

1. **Créer le fichier .env de production**
   ```env
   # Environnement
   DJANGO_SETTINGS_MODULE=config.settings.production
   
   # Sécurité (IMPORTANT!)
   SECRET_KEY=votre-cle-secrete-forte-et-unique-pour-production
   DEBUG=False
   ALLOWED_HOSTS=votredomaine.com,www.votredomaine.com
   
   # Base de données
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=university_db_prod
   DB_USER=db_user_prod
   DB_PASSWORD=mot-de-passe-fort
   DB_HOST=db.example.com
   DB_PORT=5432
   
   # CORS
   CORS_ALLOWED_ORIGINS=https://votredomaine.com,https://www.votredomaine.com
   
   # Cache (Redis)
   REDIS_URL=redis://redis.example.com:6379/1
   
   # Email
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=votre-email@example.com
   EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
   DEFAULT_FROM_EMAIL=noreply@votredomaine.com
   
   # Sécurité
   SECURE_SSL_REDIRECT=True
   SECURE_HSTS_SECONDS=31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS=True
   SECURE_HSTS_PRELOAD=True
   
   # Administrateurs
   ADMIN_NAME=Administrateur
   ADMIN_EMAIL=admin@votredomaine.com
   
   # JWT (durées plus courtes pour la sécurité)
   JWT_ACCESS_TOKEN_LIFETIME=15
   JWT_REFRESH_TOKEN_LIFETIME=7
   ```

2. **Installer les dépendances de production**
   ```bash
   pip install -r requirements-prod.txt
   ```

3. **Générer une SECRET_KEY forte**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Collecter les fichiers statiques**
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Appliquer les migrations**
   ```bash
   python manage.py migrate --noinput
   ```

6. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

### Déploiement avec Gunicorn

```bash
# Installation
pip install gunicorn gevent

# Démarrage basique
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Configuration recommandée
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class gevent \
  --timeout 60 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile /var/log/gunicorn/access.log \
  --error-logfile /var/log/gunicorn/error.log \
  --log-level info \
  --daemon
```

### Configuration Nginx (exemple)

```nginx
server {
    listen 80;
    server_name votredomaine.com www.votredomaine.com;
    
    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votredomaine.com www.votredomaine.com;
    
    ssl_certificate /etc/letsencrypt/live/votredomaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votredomaine.com/privkey.pem;
    
    client_max_body_size 10M;
    
    location /static/ {
        alias /path/to/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /path/to/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service (exemple)

```ini
# /etc/systemd/system/university-mgmt.service
[Unit]
Description=University Management System
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/University-Management-System-main
Environment="PATH=/path/to/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/path/to/venv/bin/gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable university-mgmt
sudo systemctl start university-mgmt
sudo systemctl status university-mgmt
```

### Vérifications de sécurité

```bash
# Vérifier la configuration Django
python manage.py check --deploy

# Analyser les vulnérabilités
pip install safety
safety check

# Scanner le code
pip install bandit
bandit -r apps/
```

---

## 🧪 Environnement de test

### Exécution des tests

```bash
# Tous les tests
python manage.py test --settings=config.settings.test

# Ou simplement (si DJANGO_SETTINGS_MODULE est défini)
python manage.py test

# Tests avec verbosité
python manage.py test --verbosity=2

# Tests en parallèle
python manage.py test --parallel

# Tests avec conservation de la DB
python manage.py test --keepdb

# Tests spécifiques
python manage.py test apps.core.tests
python manage.py test apps.core.tests.TestUserModel
```

### Tests avec Pytest

```bash
# Installation
pip install pytest pytest-django pytest-cov

# Exécution
pytest

# Avec couverture de code
pytest --cov=apps --cov-report=html

# Tests spécifiques
pytest apps/core/tests/

# Avec parallélisation
pytest -n auto
```

### Configuration pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --nomigrations
    --reuse-db
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
```

---

## 🔧 Variables d'environnement

### Variables obligatoires

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DJANGO_SETTINGS_MODULE` | Module de configuration | `config.settings.development` |
| `SECRET_KEY` | Clé secrète Django | `django-insecure-...` |
| `DEBUG` | Mode debug | `True` / `False` |
| `ALLOWED_HOSTS` | Hôtes autorisés | `localhost,127.0.0.1` |
| `DB_ENGINE` | Moteur de BDD | `django.db.backends.postgresql` |
| `DB_NAME` | Nom de la BDD | `university_db` |
| `DB_USER` | Utilisateur BDD | `postgres` |
| `DB_PASSWORD` | Mot de passe BDD | `postgres` |
| `DB_HOST` | Hôte BDD | `localhost` |
| `DB_PORT` | Port BDD | `5432` |

### Variables optionnelles (mais recommandées)

| Variable | Description | Défaut | Production |
|----------|-------------|--------|------------|
| `LANGUAGE_CODE` | Code langue | `fr-fr` | `fr-fr` |
| `TIME_ZONE` | Fuseau horaire | `Africa/Douala` | `Africa/Douala` |
| `PAGE_SIZE` | Pagination API | `20` | `20` |
| `JWT_ACCESS_TOKEN_LIFETIME` | Durée token accès (min) | `60` | `15` |
| `JWT_REFRESH_TOKEN_LIFETIME` | Durée token refresh (jours) | `7` | `7` |
| `CORS_ALLOWED_ORIGINS` | Origines CORS | Vide | Requis |
| `MEDIA_URL` | URL média | `/media/` | `/media/` |
| `MEDIA_ROOT` | Dossier média | `media` | `media` |

### Variables de production uniquement

| Variable | Description | Requis |
|----------|-------------|--------|
| `EMAIL_HOST` | Serveur SMTP | ✅ |
| `EMAIL_PORT` | Port SMTP | ✅ |
| `EMAIL_HOST_USER` | Utilisateur SMTP | ✅ |
| `EMAIL_HOST_PASSWORD` | Mot de passe SMTP | ✅ |
| `DEFAULT_FROM_EMAIL` | Email expéditeur | ✅ |
| `REDIS_URL` | URL Redis | ✅ |
| `SECURE_SSL_REDIRECT` | Redirection HTTPS | ⚠️ |
| `SECURE_HSTS_SECONDS` | Durée HSTS | ⚠️ |
| `ADMIN_NAME` | Nom admin | ⚠️ |
| `ADMIN_EMAIL` | Email admin | ⚠️ |

---

## 📝 Commandes utiles

### Gestion de projet

```bash
# Créer une nouvelle app
python manage.py startapp nouvelle_app apps/nouvelle_app

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic

# Shell interactif
python manage.py shell

# Shell amélioré (avec django-extensions)
python manage.py shell_plus --ipython
```

### Développement

```bash
# Lancer le serveur
python manage.py runserver

# Lancer sur un port spécifique
python manage.py runserver 8080

# Lancer sur toutes les interfaces
python manage.py runserver 0.0.0.0:8000

# Voir les requêtes SQL
python manage.py runserver --settings=config.settings.development
# (avec DB_LOG_LEVEL=DEBUG dans .env)
```

### Base de données

```bash
# Afficher les migrations
python manage.py showmigrations

# Annuler une migration
python manage.py migrate app_name migration_name

# Réinitialiser une app
python manage.py migrate app_name zero

# Créer un dump de la BDD
python manage.py dumpdata > backup.json

# Charger un dump
python manage.py loaddata backup.json

# Créer un dump d'une app spécifique
python manage.py dumpdata core --indent 2 > core_dump.json
```

### Tests et qualité

```bash
# Lancer les tests
python manage.py test

# Avec couverture
pytest --cov=apps --cov-report=html

# Vérifier le code
flake8 apps/
black apps/ --check
isort apps/ --check-only
pylint apps/

# Formater le code
black apps/
isort apps/

# Type checking
mypy apps/

# Vérification de sécurité
python manage.py check --deploy
safety check
bandit -r apps/
```

### Production

```bash
# Vérifier la configuration
python manage.py check --deploy

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Créer un cache des templates
python manage.py createcachetable

# Nettoyer les sessions expirées
python manage.py clearsessions

# Nettoyer les tokens JWT expirés
python manage.py flushexpiredtokens
```

---

## ❓ FAQ

### Comment changer d'environnement ?

**Méthode 1 : Variable d'environnement**
```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py runserver
```

**Méthode 2 : Option --settings**
```bash
python manage.py runserver --settings=config.settings.production
```

**Méthode 3 : Fichier .env**
```env
DJANGO_SETTINGS_MODULE=config.settings.production
```

### Comment ajouter un nouvel environnement (staging) ?

1. Créer `config/settings/staging.py` :
   ```python
   from .production import *
   
   # Surcharger les paramètres pour staging
   DEBUG = True
   ALLOWED_HOSTS = ['staging.example.com']
   ```

2. Utiliser :
   ```bash
   export DJANGO_SETTINGS_MODULE=config.settings.staging
   ```

### Les migrations ne fonctionnent pas

```bash
# Vérifier le module de settings
echo $DJANGO_SETTINGS_MODULE

# Ou forcer le module
python manage.py migrate --settings=config.settings.development

# Vérifier la connexion à la BDD
python manage.py dbshell
```

### Erreur "SECRET_KEY not configured"

```bash
# Générer une nouvelle clé
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Ajouter dans .env
SECRET_KEY=la-cle-generee
```

### Comment utiliser SQLite au lieu de PostgreSQL ?

Dans `.env` :
```env
# Commenter/supprimer les lignes PostgreSQL
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=university_db
# ...

# Modifier le fichier development.py pour décommenter la config SQLite
```

### Comment activer Django Debug Toolbar ?

Dans `config/settings/development.py`, décommenter :
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1', 'localhost']
```

Puis :
```bash
pip install django-debug-toolbar
```

### Comment gérer les fichiers média en production ?

**Option 1 : Serveur local (non recommandé)**
```python
# Dans production.py, les fichiers sont dans media/
```

**Option 2 : AWS S3 (recommandé)**
```bash
pip install boto3 django-storages
```

```python
# Dans production.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
```

### Comment activer le monitoring avec Sentry ?

```bash
pip install sentry-sdk
```

Dans `production.py` :
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

Dans `.env` :
```env
SENTRY_DSN=https://votre-sentry-dsn@sentry.io/123456
```

---

## 📚 Ressources supplémentaires

- [Documentation Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [WhiteNoise](http://whitenoise.evans.io/)
- [Gunicorn](https://docs.gunicorn.org/)
- [The Twelve-Factor App](https://12factor.net/)

---

## 📞 Support

Pour toute question ou problème :
1. Vérifiez cette documentation
2. Consultez les logs : `logs/development.log` ou `logs/production.log`
3. Vérifiez votre fichier `.env`
4. Contactez l'équipe de développement

---

**Dernière mise à jour** : Février 2026  
**Version** : 1.0.0
