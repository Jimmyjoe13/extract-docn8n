# Script PowerShell d'extraction des intégrations n8n
# Avec monitoring en temps réel et gestion avancée

param(
    [string]$OutputDir = "C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output",
    [int]$Workers = 6,
    [string]$Batch = "",
    [switch]$SkipExisting = $true
)

# Configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Couleurs
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorText {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Colors[$Color]
}

function Test-Prerequisites {
    Write-ColorText "=== VÉRIFICATION DES PRÉREQUIS ===" "Header"
    
    # Vérifier Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✅ Python trouvé: $pythonVersion" "Success"
        } else {
            throw "Python introuvable"
        }
    } catch {
        Write-ColorText "❌ Python n'est pas installé ou pas dans le PATH" "Error"
        Write-ColorText "Veuillez installer Python 3.8+ depuis https://python.org" "Warning"
        exit 1
    }
    
    # Vérifier les fichiers requis
    $requiredFiles = @("integrations_urls.csv", "integrations_scraper.py", "requirements.txt")
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-ColorText "✅ Fichier trouvé: $file" "Success"
        } else {
            Write-ColorText "❌ Fichier manquant: $file" "Error"
            exit 1
        }
    }
    
    # Vérifier le dossier de destination
    if (!(Test-Path $OutputDir)) {
        Write-ColorText "📁 Création du dossier de destination: $OutputDir" "Info"
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }
    
    Write-ColorText "✅ Tous les prérequis sont satisfaits" "Success"
}

function Install-Dependencies {
    Write-ColorText "=== INSTALLATION DES DÉPENDANCES ===" "Header"
    
    try {
        pip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✅ Dépendances installées avec succès" "Success"
        } else {
            throw "Installation échouée"
        }
    } catch {
        Write-ColorText "❌ Erreur lors de l'installation des dépendances" "Error"
        exit 1
    }
}

function Get-ExistingFiles {
    $integrationsDir = Join-Path $OutputDir "integrations"
    if (Test-Path $integrationsDir) {
        $existingFiles = Get-ChildItem -Path $integrationsDir -Filter "*.txt" -Recurse
        return $existingFiles.Count
    }
    return 0
}

function Show-ExtractionPlan {
    Write-ColorText "=== PLAN D'EXTRACTION ===" "Header"
    
    $existingCount = Get-ExistingFiles
    
    Write-ColorText "📊 URLs totales à traiter: 832" "Info"
    Write-ColorText "📁 Destination: $OutputDir" "Info"
    Write-ColorText "⚙️ Workers: $Workers" "Info"
    Write-ColorText "🔄 Ignorer fichiers existants: $SkipExisting" "Info"
    
    if ($existingCount -gt 0) {
        Write-ColorText "📋 Fichiers existants trouvés: $existingCount" "Warning"
        Write-ColorText "   Ces fichiers seront ignorés pour éviter les doublons" "Warning"
    }
    
    if ($Batch) {
        Write-ColorText "📦 Lot spécifique: $Batch" "Info"
    } else {
        Write-ColorText "📦 Traitement: Tous les lots" "Info"
    }
    
    Write-ColorText "⏱️ Temps estimé: 4-5 heures" "Info"
}

function Start-RealTimeMonitoring {
    $integrationsDir = Join-Path $OutputDir "integrations"
    
    # Fonction de monitoring en arrière-plan
    $monitoringScript = {
        param($integrationsDir)
        
        $initialCount = 0
        if (Test-Path $integrationsDir) {
            $initialCount = (Get-ChildItem -Path $integrationsDir -Filter "*.txt" -Recurse).Count
        }
        
        while ($true) {
            Start-Sleep -Seconds 30
            
            if (Test-Path $integrationsDir) {
                $currentCount = (Get-ChildItem -Path $integrationsDir -Filter "*.txt" -Recurse).Count
                $progress = [math]::Round(($currentCount / 832) * 100, 1)
                
                Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] 📈 Fichiers: $currentCount/832 ($progress%)" -NoNewline -ForegroundColor Cyan
                
                if ($currentCount -eq 832) {
                    Write-Host "`n✅ Extraction terminée!" -ForegroundColor Green
                    break
                }
            }
        }
    }
    
    # Démarrer le monitoring en arrière-plan
    Start-Job -ScriptBlock $monitoringScript -ArgumentList $integrationsDir | Out-Null
}

function Start-Extraction {
    Write-ColorText "=== DÉBUT DE L'EXTRACTION ===" "Header"
    
    # Construire les arguments
    $arguments = @(
        "integrations_scraper.py",
        "--csv", "integrations_urls.csv",
        "--output", "`"$OutputDir`"",
        "--workers", $Workers
    )
    
    if ($Batch) {
        $arguments += "--batch", $Batch
    }
    
    if ($SkipExisting) {
        $arguments += "--skip-existing"
    }
    
    Write-ColorText "🚀 Lancement de l'extraction..." "Info"
    Write-ColorText "⏰ Début: $(Get-Date -Format 'HH:mm:ss')" "Info"
    
    # Démarrer le monitoring
    Start-RealTimeMonitoring
    
    # Lancer l'extraction
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $arguments -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-ColorText "`n✅ EXTRACTION TERMINÉE AVEC SUCCÈS" "Success"
        } else {
            Write-ColorText "`n❌ EXTRACTION ÉCHOUÉE" "Error"
            Write-ColorText "Vérifiez les logs dans: integrations_extraction.log" "Warning"
        }
    } catch {
        Write-ColorText "❌ Erreur lors du lancement de l'extraction: $($_.Exception.Message)" "Error"
        exit 1
    }
    
    # Arrêter les tâches de monitoring
    Get-Job | Stop-Job
    Get-Job | Remove-Job
}

function Show-FinalResults {
    Write-ColorText "=== RÉSULTATS FINAUX ===" "Header"
    
    $integrationsDir = Join-Path $OutputDir "integrations"
    $finalCount = Get-ExistingFiles
    
    Write-ColorText "📊 Fichiers générés: $finalCount" "Info"
    Write-ColorText "🏁 Fin: $(Get-Date -Format 'HH:mm:ss')" "Info"
    
    # Vérifier les logs
    if (Test-Path "integrations_extraction.log") {
        Write-ColorText "📋 Logs disponibles: integrations_extraction.log" "Info"
    }
    
    # Vérifier les statistiques
    $statsFile = Join-Path $OutputDir "extraction_stats.txt"
    if (Test-Path $statsFile) {
        Write-ColorText "📈 Statistiques: $statsFile" "Info"
    }
    
    # Calculer le taux de succès
    $successRate = [math]::Round(($finalCount / 832) * 100, 1)
    
    if ($successRate -gt 95) {
        Write-ColorText "🎉 Taux de succès: $successRate% - Excellent!" "Success"
    } elseif ($successRate -gt 80) {
        Write-ColorText "✅ Taux de succès: $successRate% - Très bon" "Success"
    } else {
        Write-ColorText "⚠️ Taux de succès: $successRate% - À améliorer" "Warning"
    }
}

function Show-QuickCommands {
    Write-ColorText "=== COMMANDES RAPIDES ===" "Header"
    
    Write-ColorText "Pour relancer l'extraction:" "Info"
    Write-ColorText "  .\deploy_extraction.ps1" "Info"
    
    Write-ColorText "Pour traiter un lot spécifique:" "Info"
    Write-ColorText "  .\deploy_extraction.ps1 -Batch 'batch_01'" "Info"
    
    Write-ColorText "Pour forcer la re-extraction:" "Info"
    Write-ColorText "  .\deploy_extraction.ps1 -SkipExisting:`$false" "Info"
    
    Write-ColorText "Pour surveiller en temps réel:" "Info"
    Write-ColorText "  Get-ChildItem '$OutputDir\integrations' -Filter '*.txt' | Measure-Object" "Info"
}

# === EXÉCUTION PRINCIPALE ===

Write-ColorText "🚀 EXTRACTEUR D'INTÉGRATIONS N8N" "Header"
Write-ColorText "Traitement de 832 URLs d'intégrations" "Info"
Write-ColorText "================================================" "Header"

# Étapes d'exécution
Test-Prerequisites
Install-Dependencies
Show-ExtractionPlan

# Demander confirmation
Write-ColorText "`n⚠️ Êtes-vous prêt à commencer l'extraction?" "Warning"
$confirmation = Read-Host "Tapez 'oui' pour continuer"

if ($confirmation -eq "oui") {
    Start-Extraction
    Show-FinalResults
    Show-QuickCommands
} else {
    Write-ColorText "❌ Extraction annulée par l'utilisateur" "Warning"
}

Write-ColorText "`n🏁 Script terminé" "Success"