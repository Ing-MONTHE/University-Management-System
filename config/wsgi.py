"""
Configuration WSGI pour le projet University Management System.

Ce module expose l'application WSGI comme une variable de niveau module nommée ``application``.

Pour plus d'informations sur ce fichier, voir :
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/

Serveurs WSGI supportés :
- Gunicorn (recommandé pour production)
- uWSGI
- mod_wsgi (Apache)

Exemple de démarrage avec Gunicorn :
    gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
"""

import os
from django.core.wsgi import get_wsgi_application

# Définit l'environnement par défaut sur production pour WSGI
# En production, assurez-vous que DJANGO_SETTINGS_MODULE est défini
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_wsgi_application()