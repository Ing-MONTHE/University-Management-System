"""
Paramètres de configuration Django de base.

Ce fichier contient les paramètres communs à tous les environnements.
Les paramètres spécifiques à chaque environnement sont définis dans les fichiers
development.py, production.py et test.py qui héritent de cette configuration.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config
import os

# Chemin de base du projet
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Clé secrète utilisée pour le cryptage (doit être définie dans .env)
SECRET_KEY = config('SECRET_KEY')

# Application definition
# Liste des applications installées
INSTALLED_APPS = [
    # Applications Django par défaut
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Packages externes installés
    'rest_framework',              # Pour les API REST
    'rest_framework_simplejwt',    # Pour l'authentification JWT
    'corsheaders',                 # Pour autoriser le frontend à accéder à l'API
    'django_filters',              # Pour filtrer les données dans les vues
    'drf_spectacular',             # Pour la documentation de l'API
    'phonenumber_field',           # Pour gérer les numéros de téléphone

    # Nos applications
    'apps.core',                   # Module CORE (User, Role, Permission)
    'apps.academic',               # Module Academic
    'apps.students',               # Module Étudiant/Enseignant
    'apps.evaluations',            # Module Note et Évaluation
    'apps.schedule',               # Module Emplois du temps
    'apps.library',                # Module Bibliothèque
    'apps.attendance',             # Module Présence
    'apps.finance',                # Module Finance
    'apps.communications',         # Module Communication
    'apps.resources',              # Module Ressources et Équipements
    'apps.documents',              # Module Documents
    'apps.analytics',              # Module Analytics
]

# Middlewares Django
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',                # CORS (doit être en premier)
    'django.middleware.security.SecurityMiddleware',        # Sécurité
    'django.contrib.sessions.middleware.SessionMiddleware', # Sessions
    'django.middleware.common.CommonMiddleware',            # Middleware commun
    'django.middleware.csrf.CsrfViewMiddleware',           # Protection CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Authentification
    'django.contrib.messages.middleware.MessageMiddleware', # Messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Protection clickjacking
]

# Configuration des URLs
ROOT_URLCONF = 'config.urls'

# Configuration des templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Dossier des templates personnalisés
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Configuration WSGI
WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
# Validateurs de mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# Configuration de la langue et du fuseau horaire
LANGUAGE_CODE = config('LANGUAGE_CODE', default='fr-fr')
TIME_ZONE = config('TIME_ZONE', default='Africa/Douala')
USE_I18N = True
USE_TZ = True

# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'core.User'

# Configuration de Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': config('PAGE_SIZE', default=20, cast=int),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # Format de rendu par défaut
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Format de parsing par défaut
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    # Gestion des exceptions
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    # Gestion de la date/heure
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}

# Configuration JWT (Simple JWT)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME', default=7, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Configuration de la documentation API (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'University Management System API',
    'DESCRIPTION': 'API complète de gestion universitaire - Documentation interactive',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'SWAGGER_UI_FAVICON_HREF': None,
    'REDOC_DIST': 'SIDECAR',
    'SWAGGER_UI_DIST': 'SIDECAR',
}

# Configuration des fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    # BASE_DIR / 'static',  # Décommenter si vous avez un dossier static personnalisé
]

# Configuration des fichiers média (uploads)
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / config('MEDIA_ROOT', default='media')

# Configuration des logs (sera surchargée par environnement)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Type de champ par défaut pour les clés primaires
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration du format des numéros de téléphone
PHONENUMBER_DEFAULT_REGION = 'CM'  # Cameroun
PHONENUMBER_DB_FORMAT = 'NATIONAL'