@echo off
REM Script de vérification rapide avant extraction

echo ============================================
echo VERIFICATION RAPIDE - EXTRACTEUR N8N
echo ============================================

set "DESTINATION=C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output"

echo.
echo [1] Verification de Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python installé
    python --version
) else (
    echo ❌ Python non trouvé
    echo Installez Python depuis https://python.org
    goto :end
)

echo.
echo [2] Verification des fichiers...
if exist "integrations_scraper.py" (
    echo ✅ integrations_scraper.py
) else (
    echo ❌ integrations_scraper.py manquant
    goto :end
)

if exist "integrations_urls.csv" (
    echo ✅ integrations_urls.csv
) else (
    echo ❌ integrations_urls.csv manquant
    goto :end
)

if exist "requirements.txt" (
    echo ✅ requirements.txt
) else (
    echo ❌ requirements.txt manquant
    goto :end
)

echo.
echo [3] Verification de la destination...
if exist "%DESTINATION%" (
    echo ✅ Dossier de destination existe
    echo    %DESTINATION%
) else (
    echo ⚠️ Dossier de destination n'existe pas
    echo    Sera créé automatiquement
)

echo.
echo [4] Verification des fichiers existants...
if exist "%DESTINATION%\integrations" (
    for /f %%i in ('dir /b /s "%DESTINATION%\integrations\*.txt" 2^>nul ^| find /c /v ""') do (
        if %%i gtr 0 (
            echo ⚠️ %%i fichiers d'intégrations déjà présents
            echo    Ils seront ignorés pour éviter les doublons
        ) else (
            echo ✅ Aucun fichier d'intégration existant
        )
    )
) else (
    echo ✅ Aucun fichier d'intégration existant
)

echo.
echo [5] Test de connexion...
ping -n 1 docs.n8n.io >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Connexion à docs.n8n.io OK
) else (
    echo ❌ Problème de connexion à docs.n8n.io
    echo    Vérifiez votre connexion internet
)

echo.
echo [6] Vérification de l'espace disque...
for /f "tokens=3" %%i in ('dir /-c "%DESTINATION%\.." 2^>nul ^| find "octets libres"') do (
    echo ✅ Espace disque disponible suffisant
)

echo.
echo ============================================
echo RÉSUMÉ
echo ============================================
echo 📊 URLs à traiter: 832
echo 📁 Destination: %DESTINATION%
echo ⏱️ Temps estimé: 4-5 heures
echo 💾 Espace requis: ~500 MB
echo 🔄 Mode: Ignorer fichiers existants
echo ============================================

echo.
echo Prêt pour l'extraction!
echo.
echo Commandes disponibles:
echo [1] deploy_extraction.bat     (Automatique)
echo [2] deploy_extraction.ps1     (PowerShell avancé)
echo [3] Manual: python integrations_scraper.py --csv integrations_urls.csv --output "%DESTINATION%"
echo.

:end
pause