"""
Package de configuration Django multi-environnement.

Ce package contient les paramètres de configuration pour différents environnements :
- base.py : Configuration commune à tous les environnements
- development.py : Configuration pour l'environnement de développement
- production.py : Configuration pour l'environnement de production
- test.py : Configuration pour les tests

Pour spécifier l'environnement, définir la variable DJANGO_SETTINGS_MODULE :
- Développement : config.settings.development
- Production : config.settings.production
- Tests : config.settings.test
"""