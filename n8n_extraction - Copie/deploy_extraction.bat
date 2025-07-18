@echo off
REM Script de déploiement automatique pour l'extraction des intégrations n8n
REM Destination: C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output

echo ===============================================
echo EXTRACTION DES INTEGRATIONS N8N - AUTOMATIQUE
echo ===============================================

REM Définir les chemins
set "DESTINATION_DIR=C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output"
set "WORK_DIR=%~dp0"

echo Repertoire de travail: %WORK_DIR%
echo Destination: %DESTINATION_DIR%

REM Vérifier Python
echo.
echo [1/6] Verification de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)
echo Python trouvé: 
python --version

REM Installer les dépendances
echo.
echo [2/6] Installation des dépendances...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERREUR: Installation des dépendances échouée
    pause
    exit /b 1
)

REM Vérifier les fichiers requis
echo.
echo [3/6] Verification des fichiers requis...
if not exist "integrations_urls.csv" (
    echo ERREUR: Fichier integrations_urls.csv introuvable
    pause
    exit /b 1
)
if not exist "integrations_scraper.py" (
    echo ERREUR: Fichier integrations_scraper.py introuvable
    pause
    exit /b 1
)
echo Fichiers requis trouvés

REM Vérifier les fichiers existants dans la destination
echo.
echo [4/6] Verification des fichiers existants...
if exist "%DESTINATION_DIR%\integrations" (
    echo Dossier integrations trouvé dans la destination
    for /f %%i in ('dir /b /s "%DESTINATION_DIR%\integrations\*.txt" 2^>nul ^| find /c /v ""') do set "existing_files=%%i"
    if !existing_files! gtr 0 (
        echo Fichiers existants trouvés: !existing_files!
        echo Ces fichiers seront ignorés pour éviter les doublons
    ) else (
        echo Aucun fichier existant trouvé
    )
) else (
    echo Aucun dossier integrations trouvé - extraction complète
)

REM Demander confirmation
echo.
echo [5/6] Confirmation d'extraction...
echo Prêt à extraire 832 URLs d'intégrations
echo Destination: %DESTINATION_DIR%
echo Temps estimé: 4-5 heures (selon la connexion)
echo.
set /p "confirm=Continuer? (o/n): "
if /i not "%confirm%"=="o" (
    echo Extraction annulée
    pause
    exit /b 0
)

REM Lancer l'extraction
echo.
echo [6/6] Lancement de l'extraction...
echo Début: %time%
python integrations_scraper.py --csv integrations_urls.csv --output "%DESTINATION_DIR%" --workers 6 --skip-existing

REM Vérifier le résultat
if %errorlevel% equ 0 (
    echo.
    echo ===============================================
    echo EXTRACTION TERMINEE AVEC SUCCES
    echo ===============================================
    echo Fin: %time%
    echo.
    echo Vérification des résultats:
    for /f %%i in ('dir /b /s "%DESTINATION_DIR%\integrations\*.txt" 2^>nul ^| find /c /v ""') do echo Fichiers générés: %%i
    echo.
    echo Logs disponibles dans: integrations_extraction.log
    echo Statistiques dans: %DESTINATION_DIR%\extraction_stats.txt
) else (
    echo.
    echo ===============================================
    echo EXTRACTION ECHOUEE
    echo ===============================================
    echo Vérifiez les logs dans: integrations_extraction.log
)

echo.
echo Appuyez sur une touche pour continuer...
pause >nul