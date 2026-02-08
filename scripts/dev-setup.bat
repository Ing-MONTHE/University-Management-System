@echo off
REM =============================================================================
REM Script de démarrage rapide pour l'environnement de développement (Windows)
REM =============================================================================
REM Usage: scripts\dev-setup.bat
REM =============================================================================

echo ======================================================================
echo 🚀 Configuration de l'environnement de développement
echo ======================================================================
echo.

REM Vérifier Python
echo [INFO] Vérification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH
    pause
    exit /b 1
)
python --version
echo [OK] Python trouvé
echo.

REM Vérifier si on est dans le bon dossier
if not exist "manage.py" (
    echo [ERREUR] Ce script doit être exécuté depuis la racine du projet
    pause
    exit /b 1
)

REM Créer l'environnement virtuel si nécessaire
if not exist "venv" (
    echo [INFO] Création de l'environnement virtuel...
    python -m venv venv
    echo [OK] Environnement virtuel créé
) else (
    echo [ATTENTION] L'environnement virtuel existe déjà
)
echo.

REM Activer l'environnement virtuel
echo [INFO] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo [OK] Environnement virtuel activé
echo.

REM Mettre à jour pip
echo [INFO] Mise à jour de pip...
python -m pip install --upgrade pip >nul 2>&1
echo [OK] Pip mis à jour
echo.

REM Installer les dépendances
echo [INFO] Installation des dépendances de développement...
pip install -r requirements-dev.txt
echo [OK] Dépendances installées
echo.

REM Créer le fichier .env si nécessaire
if not exist ".env" (
    echo [INFO] Création du fichier .env...
    copy .env.example .env >nul
    echo [OK] Fichier .env créé
    echo [ATTENTION] N'oubliez pas de configurer vos variables dans .env
) else (
    echo [ATTENTION] Le fichier .env existe déjà
)
echo.

REM Créer le dossier logs
if not exist "logs" (
    echo [INFO] Création du dossier logs...
    mkdir logs
    echo [OK] Dossier logs créé
)
echo.

REM Demander si l'utilisateur veut créer la base de données
set /p DB_SETUP="Voulez-vous configurer la base de données maintenant ? (o/n) : "
if /i "%DB_SETUP%"=="o" (
    echo [INFO] Application des migrations...
    python manage.py migrate
    echo [OK] Migrations appliquées
    echo.
    
    set /p SUPERUSER="Voulez-vous créer un superutilisateur ? (o/n) : "
    if /i "%SUPERUSER%"=="o" (
        python manage.py createsuperuser
    )
)

echo.
echo ======================================================================
echo [OK] Configuration terminée avec succès !
echo ======================================================================
echo.
echo Pour démarrer le serveur de développement :
echo   1. Activez l'environnement virtuel : venv\Scripts\activate
echo   2. Lancez le serveur : python manage.py runserver
echo.
echo URLs utiles :
echo   - API : http://localhost:8000/api/
echo   - Admin : http://localhost:8000/admin/
echo   - Documentation : http://localhost:8000/api/schema/swagger-ui/
echo.
echo ======================================================================
echo.
pause