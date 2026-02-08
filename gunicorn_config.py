# =============================================================================
# Configuration Gunicorn pour la production
# =============================================================================
# Fichier: gunicorn_config.py
# Usage: gunicorn -c gunicorn_config.py config.wsgi:application
# =============================================================================

import multiprocessing
import os

# Bind
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')

# Workers
# Formule recommandée : (2 x CPU cores) + 1
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Type de worker
# - sync : worker synchrone (par défaut)
# - gevent : worker asynchrone basé sur gevent (recommandé pour I/O)
# - eventlet : worker asynchrone basé sur eventlet
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gevent')

# Nombre de threads par worker (si worker_class = 'gthread')
threads = int(os.getenv('GUNICORN_THREADS', 2))

# Timeout
# Temps maximum (en secondes) pour qu'un worker réponde
timeout = int(os.getenv('GUNICORN_TIMEOUT', 60))

# Graceful timeout
# Temps d'attente (en secondes) pour que les workers terminent proprement
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))

# Keepalive
# Durée de vie des connexions keep-alive
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 5))

# Max requests
# Nombre maximum de requêtes qu'un worker peut traiter avant de redémarrer
# Utile pour éviter les fuites mémoire
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))

# Max requests jitter
# Variation aléatoire pour éviter que tous les workers redémarrent en même temps
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 100))

# Preload app
# Charger l'application avant de forker les workers
# Économise de la mémoire mais peut causer des problèmes avec certaines bibliothèques
preload_app = os.getenv('GUNICORN_PRELOAD_APP', 'True').lower() == 'true'

# Daemon
# Exécuter en arrière-plan
daemon = os.getenv('GUNICORN_DAEMON', 'False').lower() == 'true'

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')  # - pour stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')    # - pour stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')  # debug, info, warning, error, critical

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'university_management_system'

# Server mechanics
# Fichier PID
pidfile = os.getenv('GUNICORN_PID_FILE', '/tmp/gunicorn.pid')

# User et group
user = os.getenv('GUNICORN_USER', None)
group = os.getenv('GUNICORN_GROUP', None)

# Umask
umask = int(os.getenv('GUNICORN_UMASK', '0'))

# Temporary directory
tmp_upload_dir = None

# Security
# Limite la taille du corps de la requête (en octets)
# 10 MB par défaut
limit_request_line = int(os.getenv('GUNICORN_LIMIT_REQUEST_LINE', 4094))
limit_request_fields = int(os.getenv('GUNICORN_LIMIT_REQUEST_FIELDS', 100))
limit_request_field_size = int(os.getenv('GUNICORN_LIMIT_REQUEST_FIELD_SIZE', 8190))

# Hooks
def on_starting(server):
    """
    Appelé juste avant que le master process soit initialisé.
    """
    print("=" * 70)
    print("🚀 Démarrage de Gunicorn")
    print("=" * 70)
    print(f"Workers: {workers}")
    print(f"Worker class: {worker_class}")
    print(f"Bind: {bind}")
    print(f"Timeout: {timeout}s")
    print("=" * 70)


def on_reload(server):
    """
    Appelé pour recharger la configuration.
    """
    print("🔄 Rechargement de la configuration Gunicorn")


def when_ready(server):
    """
    Appelé juste après que le server soit démarré.
    """
    print("✅ Gunicorn est prêt à accepter les connexions")


def pre_fork(server, worker):
    """
    Appelé juste avant qu'un worker soit forké.
    """
    pass


def post_fork(server, worker):
    """
    Appelé juste après qu'un worker soit forké.
    """
    print(f"👷 Worker {worker.pid} démarré")


def pre_exec(server):
    """
    Appelé juste avant qu'un nouveau master process soit créé.
    """
    print("🔄 Création d'un nouveau master process")


def worker_int(worker):
    """
    Appelé quand un worker reçoit un signal INT ou QUIT.
    """
    print(f"⚠️  Worker {worker.pid} reçoit un signal d'interruption")


def worker_abort(worker):
    """
    Appelé quand un worker est tué par timeout.
    """
    print(f"❌ Worker {worker.pid} a été tué (timeout)")


# =============================================================================
# NOTES D'UTILISATION
# =============================================================================
# 
# Démarrage basique :
# ------------------
# gunicorn -c gunicorn_config.py config.wsgi:application
# 
# Avec variables d'environnement :
# -------------------------------
# export GUNICORN_WORKERS=4
# export GUNICORN_WORKER_CLASS=gevent
# gunicorn -c gunicorn_config.py config.wsgi:application
# 
# Configuration recommandée pour production :
# -----------------------------------------
# GUNICORN_WORKERS=4
# GUNICORN_WORKER_CLASS=gevent
# GUNICORN_TIMEOUT=60
# GUNICORN_MAX_REQUESTS=1000
# GUNICORN_BIND=0.0.0.0:8000
# GUNICORN_ACCESS_LOG=/var/log/gunicorn/access.log
# GUNICORN_ERROR_LOG=/var/log/gunicorn/error.log
# 
# Rechargement gracieux :
# ----------------------
# kill -HUP <pid_du_master>
# 
# Arrêt gracieux :
# ---------------
# kill -TERM <pid_du_master>
# 
# =============================================================================