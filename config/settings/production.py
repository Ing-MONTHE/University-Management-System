"""
Configuration pour l'environnement de production.

Ce fichier contient les paramètres spécifiques à l'environnement de production.
Il hérite de la configuration de base et applique des paramètres de sécurité renforcés.

⚠️ IMPORTANT : Vérifiez tous les paramètres de sécurité avant le déploiement.
"""

from .base import *
from decouple import config
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Hôtes autorisés (DOIT être configuré en production)
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Vérification que les ALLOWED_HOSTS sont configurés
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError(
        "ALLOWED_HOSTS doit être défini en production. "
        "Exemple : ALLOWED_HOSTS=example.com,www.example.com"
    )

# Configuration de la base de données pour la production
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c search_path=public',
        },
        'CONN_MAX_AGE': 600,  # Connexion persistante (10 minutes)
        'CONN_HEALTH_CHECKS': True,  # Vérification de l'état de la connexion
    }
}

# Configuration CORS stricte pour la production
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS').split(',')

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Toujours False en production

# Headers et méthodes CORS autorisés
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
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

# Configuration du cache (Redis recommandé pour la production)
# Installation requise : pip install django-redis
CACHES = {
    'default': {
        'BACKEND': config(
            'CACHE_BACKEND',
            default='django.core.cache.backends.redis.RedisCache'
        ),
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'university_mgmt',
        'TIMEOUT': 300,
    },
    # Cache pour les sessions
    'session': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/2'),
        'KEY_PREFIX': 'session',
        'TIMEOUT': 86400,  # 24 heures
    }
}

# Utiliser Redis pour les sessions en production
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# Configuration Email pour la production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Paramètres de sécurité renforcés pour la production
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Configuration des cookies sécurisés
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 heures

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Protection contre le clickjacking
X_FRAME_OPTIONS = 'DENY'

# Limitation du nombre de requêtes (optionnel, requiert django-ratelimit)
# INSTALLED_APPS += ['django_ratelimit']

# REST Framework - Pas de Browsable API en production
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

# Logging pour la production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module} {process:d} {thread:d} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'production.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Ne pas logger toutes les requêtes SQL en production
            'propagate': False,
        },
        # Logs pour nos applications
        'apps': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Création du dossier logs s'il n'existe pas
LOGS_DIR = BASE_DIR / 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Configuration des administrateurs (recevront les emails d'erreur)
ADMINS = [
    (config('ADMIN_NAME', default='Admin'), config('ADMIN_EMAIL', default='admin@example.com')),
]
MANAGERS = ADMINS

# Configuration des fichiers statiques pour la production
# Utiliser WhiteNoise pour servir les fichiers statiques
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuration pour les fichiers média en production
# Il est recommandé d'utiliser un service de stockage externe (AWS S3, Google Cloud Storage, etc.)
# Exemple avec django-storages pour AWS S3 :
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = 'public-read'

# Compression et optimisation
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# Désactiver les templates debug en production
TEMPLATES[0]['OPTIONS']['debug'] = False

# Durée de vie des tokens JWT en production (plus courte pour plus de sécurité)
from datetime import timedelta
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(
    minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=15, cast=int)  # 15 minutes
)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(
    days=config('JWT_REFRESH_TOKEN_LIFETIME', default=7, cast=int)  # 7 jours
)

# Vérifications de sécurité au démarrage
if DEBUG:
    import warnings
    warnings.warn(
        "⚠️  DEBUG est activé en production ! Ceci est un risque de sécurité majeur.",
        RuntimeWarning
    )

if SECRET_KEY == 'your-secret-key-here' or len(SECRET_KEY) < 50:
    raise ValueError(
        "SECRET_KEY non configurée ou trop courte pour la production. "
        "Générez une clé forte et sécurisée."
    )

print("=" * 70)
print("🔒 ENVIRONNEMENT DE PRODUCTION CHARGÉ")
print("=" * 70)
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"DATABASE: {DATABASES['default']['ENGINE']}")
print(f"SECURE_SSL_REDIRECT: {SECURE_SSL_REDIRECT}")
print(f"CACHE: {CACHES['default']['BACKEND']}")
print("=" * 70)