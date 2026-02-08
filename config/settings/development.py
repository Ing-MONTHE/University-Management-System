"""
Configuration pour l'environnement de développement.

Ce fichier contient les paramètres spécifiques à l'environnement de développement local.
Il hérite de la configuration de base et la surcharge avec des paramètres adaptés au développement.
"""

from .base import *
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Hôtes autorisés (permissif en développement)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,[::1],0.0.0.0'
).split(',')

# Configuration de la base de données pour le développement
# Utilise PostgreSQL par défaut, mais peut être configuré pour SQLite
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='university_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='@dmin123'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        # Options de connexion pour PostgreSQL
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 60,  # Connexion persistante (60 secondes)
    }
}

# Alternative SQLite pour développement sans PostgreSQL
# Décommenter si vous préférez SQLite
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Configuration CORS pour le développement (permissive)
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173'
).split(',')

CORS_ALLOW_CREDENTIALS = True

# En développement, autoriser tous les headers et méthodes
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Configuration du cache (simple cache en mémoire pour le développement)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Email backend pour le développement (console)
# Les emails sont affichés dans la console au lieu d'être envoyés
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=1025, cast=int)
EMAIL_USE_TLS = False

# Ajout du Browsable API Renderer en développement
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',  # Interface navigable pour tester l'API
]

# Logging plus verbeux en développement
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': config('DB_LOG_LEVEL', default='INFO'),  # DEBUG pour voir les requêtes SQL
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Logs pour nos applications
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Création du dossier logs s'il n'existe pas
import os
LOGS_DIR = BASE_DIR / 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Django Debug Toolbar (optionnel mais recommandé pour le développement)
# Décommenter et installer django-debug-toolbar si vous souhaitez l'utiliser
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Configuration de session plus permissive en développement
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Désactiver HTTPS redirect en développement
SECURE_SSL_REDIRECT = False

# Paramètres de sécurité relaxés pour le développement
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Durée de vie des tokens JWT plus longue en développement (pour faciliter les tests)
from datetime import timedelta
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(
    minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=120, cast=int)  # 2 heures
)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(
    days=config('JWT_REFRESH_TOKEN_LIFETIME', default=30, cast=int)  # 30 jours
)

# Afficher les erreurs de template en développement
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

print("=" * 70)
print("🚀 ENVIRONNEMENT DE DÉVELOPPEMENT CHARGÉ")
print("=" * 70)
print(f"DEBUG: {DEBUG}")
print(f"DATABASE: {DATABASES['default']['ENGINE']} - {DATABASES['default']['NAME']}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print("=" * 70)