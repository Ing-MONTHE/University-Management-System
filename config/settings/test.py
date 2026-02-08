"""
Configuration pour l'environnement de tests.

Ce fichier contient les paramètres spécifiques pour l'exécution des tests.
Il hérite de la configuration de base et optimise les performances des tests.
"""

from .base import *
from decouple import config

# Debug désactivé pour les tests
DEBUG = False

# Hôtes autorisés pour les tests
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Base de données en mémoire pour les tests (plus rapide)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Base de données en mémoire
        'ATOMIC_REQUESTS': True,
    }
}

# Alternative : PostgreSQL pour les tests (plus proche de la production)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('TEST_DB_NAME', default='test_university_db'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default='postgres'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#         'TEST': {
#             'NAME': 'test_university_db',
#         }
#     }
# }

# Cache en mémoire locale pour les tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Email backend pour les tests (en mémoire)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Désactiver les migrations pour accélérer les tests
# Décommenter si vous voulez désactiver les migrations pendant les tests
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# 
# MIGRATION_MODULES = DisableMigrations()

# Hasher de mots de passe plus rapide pour les tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# CORS permissif pour les tests
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Logging minimal pour les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'CRITICAL',  # N'afficher que les erreurs critiques
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'CRITICAL',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    },
}

# Désactiver la collecte des fichiers statiques pendant les tests
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Paramètres de sécurité désactivés pour les tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# JWT avec durée de vie courte pour les tests
from datetime import timedelta
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=5)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(minutes=10)

# REST Framework - Configuration optimisée pour les tests
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'

# Désactiver la pagination pour simplifier les tests
REST_FRAMEWORK['PAGE_SIZE'] = None

# Media files pour les tests
MEDIA_ROOT = BASE_DIR / 'test_media'
MEDIA_URL = '/test_media/'

# Désactiver les templates debug
TEMPLATES[0]['OPTIONS']['debug'] = False

# Configuration de coverage pour les tests
# Installation requise : pip install coverage
COVERAGE_MODULE_EXCLUDES = [
    'tests$',
    'settings$',
    'urls$',
    'locale$',
    'migrations',
    '__pycache__',
    'manage.py',
    'wsgi.py',
    'asgi.py',
]

# Options de test personnalisées
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Parallélisation des tests (optionnel)
# Décommenter pour exécuter les tests en parallèle
# TEST_RUNNER = 'django.test.runner.DiscoverRunner'
# Utiliser : python manage.py test --parallel

# Keepdb - Conserver la base de données de test entre les exécutions
# Utiliser : python manage.py test --keepdb

# Verbosité des tests
# Utiliser : python manage.py test --verbosity=2

print("=" * 70)
print("🧪 ENVIRONNEMENT DE TEST CHARGÉ")
print("=" * 70)
print(f"DEBUG: {DEBUG}")
print(f"DATABASE: {DATABASES['default']['ENGINE']} (en mémoire)")
print(f"PASSWORD_HASHER: MD5 (rapide pour les tests)")
print("=" * 70)