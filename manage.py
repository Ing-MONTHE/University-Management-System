#!/usr/bin/env python
"""
Utilitaire en ligne de commande Django pour les tâches administratives.

Ce script permet d'exécuter les commandes Django management.
L'environnement est défini par la variable DJANGO_SETTINGS_MODULE.

Usage:
    python manage.py <commande> [options]

Exemples:
    python manage.py runserver
    python manage.py migrate
    python manage.py test
"""
import os
import sys


def main():
    """Exécute les tâches administratives Django."""
    # Définit l'environnement par défaut sur développement
    # Peut être surchargé par la variable d'environnement DJANGO_SETTINGS_MODULE
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Êtes-vous sûr qu'il est installé et "
            "disponible dans votre variable d'environnement PYTHONPATH ? "
            "Avez-vous oublié d'activer votre environnement virtuel ?"
        ) from exc
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()