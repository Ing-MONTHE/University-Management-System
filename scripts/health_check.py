#!/usr/bin/env python
"""
Script de vérification de santé du système.

Ce script vérifie que tous les composants essentiels sont correctement configurés.
Usage: python scripts/health_check.py
"""

import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.core.cache import cache

# Couleurs pour le terminal
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_header(message):
    """Affiche un en-tête formaté."""
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}{message:^70}{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")


def print_success(message):
    """Affiche un message de succès."""
    print(f"{GREEN}✅ {message}{NC}")


def print_error(message):
    """Affiche un message d'erreur."""
    print(f"{RED}❌ {message}{NC}")


def print_warning(message):
    """Affiche un message d'avertissement."""
    print(f"{YELLOW}⚠️  {message}{NC}")


def print_info(message):
    """Affiche un message d'information."""
    print(f"{BLUE}ℹ️  {message}{NC}")


def check_python_version():
    """Vérifie la version de Python."""
    print_info("Vérification de la version Python...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} - Version 3.11+ requise")
        return False


def check_django_version():
    """Vérifie la version de Django."""
    print_info("Vérification de la version Django...")
    import django
    version = django.VERSION
    if version[0] == 6:
        print_success(f"Django {django.get_version()}")
        return True
    else:
        print_error(f"Django {django.get_version()} - Version 6.x requise")
        return False


def check_environment():
    """Vérifie les variables d'environnement essentielles."""
    print_info("Vérification des variables d'environnement...")
    
    essential_vars = [
        'SECRET_KEY',
        'DEBUG',
        'ALLOWED_HOSTS',
    ]
    
    all_ok = True
    for var in essential_vars:
        value = getattr(settings, var, None)
        if value:
            if var == 'SECRET_KEY':
                print_success(f"{var}: {'*' * 20} (masqué)")
            else:
                print_success(f"{var}: {value}")
        else:
            print_error(f"{var}: Non défini")
            all_ok = False
    
    return all_ok


def check_database():
    """Vérifie la connexion à la base de données."""
    print_info("Vérification de la connexion à la base de données...")
    
    try:
        # Test de connexion
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        db_name = settings.DATABASES['default']['NAME']
        db_engine = settings.DATABASES['default']['ENGINE'].split('.')[-1]
        
        print_success(f"Connexion réussie ({db_engine}: {db_name})")
        
        # Vérifier les migrations
        print_info("Vérification des migrations...")
        try:
            from io import StringIO
            out = StringIO()
            call_command('showmigrations', '--plan', stdout=out)
            output = out.getvalue()
            
            if '[X]' in output or output.strip():
                print_success("Migrations présentes")
            else:
                print_warning("Aucune migration appliquée")
        except Exception as e:
            print_warning(f"Impossible de vérifier les migrations: {e}")
        
        return True
    except Exception as e:
        print_error(f"Erreur de connexion: {e}")
        return False


def check_cache():
    """Vérifie la connexion au cache."""
    print_info("Vérification du cache...")
    
    try:
        # Test de connexion au cache
        cache.set('health_check', 'ok', 10)
        value = cache.get('health_check')
        
        if value == 'ok':
            cache_backend = settings.CACHES['default']['BACKEND'].split('.')[-1]
            print_success(f"Cache fonctionnel ({cache_backend})")
            cache.delete('health_check')
            return True
        else:
            print_error("Le cache ne fonctionne pas correctement")
            return False
    except Exception as e:
        print_error(f"Erreur de cache: {e}")
        return False


def check_static_files():
    """Vérifie la configuration des fichiers statiques."""
    print_info("Vérification des fichiers statiques...")
    
    static_root = settings.STATIC_ROOT
    static_url = settings.STATIC_URL
    
    print_success(f"STATIC_URL: {static_url}")
    print_success(f"STATIC_ROOT: {static_root}")
    
    if os.path.exists(static_root):
        print_success("Dossier STATIC_ROOT existe")
    else:
        print_warning("Dossier STATIC_ROOT n'existe pas (exécutez collectstatic)")
    
    return True


def check_media_files():
    """Vérifie la configuration des fichiers média."""
    print_info("Vérification des fichiers média...")
    
    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    
    print_success(f"MEDIA_URL: {media_url}")
    print_success(f"MEDIA_ROOT: {media_root}")
    
    if os.path.exists(media_root):
        print_success("Dossier MEDIA_ROOT existe")
    else:
        print_warning("Dossier MEDIA_ROOT n'existe pas")
        try:
            os.makedirs(media_root)
            print_success("Dossier MEDIA_ROOT créé")
        except Exception as e:
            print_error(f"Impossible de créer MEDIA_ROOT: {e}")
    
    return True


def check_installed_apps():
    """Vérifie les applications installées."""
    print_info("Vérification des applications installées...")
    
    custom_apps = [app for app in settings.INSTALLED_APPS if app.startswith('apps.')]
    
    print_success(f"{len(custom_apps)} applications personnalisées installées:")
    for app in custom_apps:
        print(f"  • {app}")
    
    return True


def check_security_settings():
    """Vérifie les paramètres de sécurité."""
    print_info("Vérification des paramètres de sécurité...")
    
    checks = {
        'DEBUG': settings.DEBUG,
        'SECRET_KEY longueur': len(settings.SECRET_KEY) >= 50,
        'ALLOWED_HOSTS configuré': len(settings.ALLOWED_HOSTS) > 0,
    }
    
    if not settings.DEBUG:
        # Vérifications supplémentaires pour la production
        checks.update({
            'SECURE_SSL_REDIRECT': getattr(settings, 'SECURE_SSL_REDIRECT', False),
            'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
            'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
        })
    
    all_ok = True
    for check, value in checks.items():
        if check == 'DEBUG':
            if value:
                print_warning(f"{check}: {value} (désactivez en production)")
            else:
                print_success(f"{check}: {value}")
        elif value:
            print_success(f"{check}: OK")
        else:
            print_error(f"{check}: NON CONFIGURÉ")
            all_ok = False
    
    return all_ok


def check_jwt_settings():
    """Vérifie la configuration JWT."""
    print_info("Vérification de la configuration JWT...")
    
    try:
        from rest_framework_simplejwt.settings import api_settings as jwt_settings
        
        access_lifetime = jwt_settings.ACCESS_TOKEN_LIFETIME
        refresh_lifetime = jwt_settings.REFRESH_TOKEN_LIFETIME
        
        print_success(f"ACCESS_TOKEN_LIFETIME: {access_lifetime}")
        print_success(f"REFRESH_TOKEN_LIFETIME: {refresh_lifetime}")
        
        return True
    except Exception as e:
        print_error(f"Erreur JWT: {e}")
        return False


def main():
    """Fonction principale."""
    print_header("🏥 VÉRIFICATION DE SANTÉ DU SYSTÈME")
    
    print_info(f"Environnement: {os.getenv('DJANGO_SETTINGS_MODULE', 'Non défini')}")
    
    checks = [
        ("Version Python", check_python_version),
        ("Version Django", check_django_version),
        ("Variables d'environnement", check_environment),
        ("Base de données", check_database),
        ("Cache", check_cache),
        ("Fichiers statiques", check_static_files),
        ("Fichiers média", check_media_files),
        ("Applications installées", check_installed_apps),
        ("Paramètres de sécurité", check_security_settings),
        ("Configuration JWT", check_jwt_settings),
    ]
    
    results = []
    for name, check_func in checks:
        print_header(name)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print_error(f"Erreur lors de la vérification: {e}")
            results.append(False)
    
    # Résumé
    print_header("📊 RÉSUMÉ")
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\nVérifications réussies: {passed}/{total} ({percentage:.1f}%)\n")
    
    if all(results):
        print_success("✨ Tous les contrôles sont passés avec succès!")
        return 0
    elif passed >= total * 0.7:
        print_warning("⚠️  La plupart des contrôles sont passés, mais certains nécessitent attention")
        return 1
    else:
        print_error("❌ Plusieurs contrôles ont échoué. Veuillez corriger les erreurs")
        return 2


if __name__ == '__main__':
    sys.exit(main())
