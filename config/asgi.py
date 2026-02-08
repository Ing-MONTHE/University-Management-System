"""
Configuration ASGI pour le projet University Management System.

Ce module expose l'application ASGI comme une variable de niveau module nommée ``application``.

Pour plus d'informations sur ce fichier, voir :
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/

ASGI permet le support des WebSockets, HTTP/2 et autres protocoles asynchrones.

Serveurs ASGI supportés :
- Daphne (recommandé pour Django Channels)
- Uvicorn
- Hypercorn

Exemple de démarrage avec Uvicorn :
    uvicorn config.asgi:application --host 0.0.0.0 --port 8000
"""

import os
from django.core.asgi import get_asgi_application

# Définit l'environnement par défaut sur production pour ASGI
# En production, assurez-vous que DJANGO_SETTINGS_MODULE est défini
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_asgi_application()