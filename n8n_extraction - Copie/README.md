# Extracteur d'intégrations n8n

## Vue d'ensemble

Ce script permet d'extraire automatiquement **832 URLs d'intégrations** de la documentation n8n et de sauvegarder le contenu dans des fichiers `.txt` dans le dossier de destination.

## Fichiers fournis

- `integrations_scraper.py` - Script Python principal d'extraction
- `integrations_urls.csv` - Liste des 832 URLs à traiter (organisées en 18 lots)
- `requirements.txt` - Dépendances Python nécessaires
- `deploy_extraction.bat` - Script automatique Windows (CMD)
- `deploy_extraction.ps1` - Script automatique PowerShell avancé
- `README.md` - Ce fichier d'instructions

## Prérequis

- **Python 3.8+** installé et dans le PATH
- **Connexion internet** stable
- **Espace disque** : ~500 MB pour tous les fichiers
- **Temps** : 4-5 heures selon la connexion

## Déploiement rapide

### Option 1 : Script automatique (Recommandé)

```batch
# Double-cliquer sur le fichier
deploy_extraction.bat
```

### Option 2 : PowerShell avancé

```powershell
# Exécuter dans PowerShell
.\deploy_extraction.ps1
```

### Option 3 : Manuel

```batch
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'extraction
python integrations_scraper.py --csv integrations_urls.csv --output "C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output" --workers 6 --skip-existing
```

## Configuration

### Paramètres du script

```python
--csv              # Fichier CSV des URLs (par défaut: integrations_urls.csv)
--output           # Dossier de destination (par défaut: ./output)
--workers          # Nombre de téléchargements simultanés (par défaut: 8)
--batch            # Traiter un lot spécifique (ex: batch_01)
--skip-existing    # Ignorer les fichiers existants (par défaut: True)
```

### Exemples d'utilisation

```batch
# Extraction complète
python integrations_scraper.py --csv integrations_urls.csv --output "C:\path\to\output"

# Traiter un lot spécifique
python integrations_scraper.py --csv integrations_urls.csv --batch batch_01

# Avec plus de workers (attention à la bande passante)
python integrations_scraper.py --csv integrations_urls.csv --workers 12

# Forcer la re-extraction (ignorer les fichiers existants)
python integrations_scraper.py --csv integrations_urls.csv --skip-existing False
```

## Organisation des lots

Les 832 URLs sont organisées en **18 lots** de ~50 URLs chacun :

- `batch_02` : 6 URLs
- `batch_03` à `batch_18` : 50 URLs chacun
- `batch_19` : 26 URLs

## Structure de sortie

```
output/
└── integrations/
    ├── integrations_.txt
    ├── integrations_builtin_app_nodes_.txt
    ├── integrations_builtin_app_nodes_n8n_nodes_base_airtable_.txt
    ├── integrations_builtin_app_nodes_n8n_nodes_base_asana_.txt
    └── ... (832 fichiers au total)
```

## Monitoring en temps réel

### Vérifier la progression

```batch
# Compter les fichiers générés
dir "C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output\integrations\*.txt" /s | find /c ".txt"

# Voir les logs
tail -f integrations_extraction.log
```

### PowerShell - Monitoring avancé

```powershell
# Surveillance continue
while ($true) {
    $count = (Get-ChildItem "C:\Users\Administrateur\Desktop\jimmy gay\Projet Windsurf\extract-docn8n\n8n_extraction - Copie\output\integrations" -Filter "*.txt" -Recurse).Count
    $progress = [math]::Round(($count / 832) * 100, 1)
    Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] Fichiers: $count/832 ($progress%)" -NoNewline
    Start-Sleep -Seconds 10
}
```

## Gestion des erreurs

### Problèmes courants

1. **Timeout de connexion**
   - Réduire `--workers` à 4 ou 6
   - Vérifier la connexion internet

2. **Erreurs HTTP 429 (Too Many Requests)**
   - Réduire `--workers` à 2 ou 3
   - Ajouter des pauses entre les requêtes

3. **Fichiers corrompus**
   - Relancer avec `--skip-existing False`
   - Vérifier l'espace disque

### Reprise après interruption

Le script ignore automatiquement les fichiers existants. Pour reprendre :

```batch
# Relancer le même script
python integrations_scraper.py --csv integrations_urls.csv --output "C:\path\to\output"
```

## Logs et statistiques

### Fichiers générés

- `integrations_extraction.log` - Logs détaillés
- `extraction_stats.txt` - Statistiques finales
- `output/integrations/` - Fichiers extraits

### Exemple de statistiques

```
Extraction terminée: 2025-01-18 15:30:45
Total URLs: 832
Succès: 825
Échecs: 7
Ignorés: 0
Taux de succès: 99.2%
```

## Optimisations

### Performance

- **Workers** : 6-8 pour une connexion normale, 12+ pour une connexion rapide
- **Batch processing** : Traiter par lots de 50 URLs
- **Skip existing** : Activé par défaut pour éviter les doublons

### Qualité

- **Retry automatique** : 3 tentatives par URL
- **Timeout** : 30 secondes par requête
- **Validation** : Vérification de la taille des fichiers

## Traitement par lots

### Traiter un lot spécifique

```batch
python integrations_scraper.py --csv integrations_urls.csv --batch batch_01
```

### Traiter plusieurs lots

```batch
for /L %%i in (1,1,18) do (
    python integrations_scraper.py --csv integrations_urls.csv --batch batch_%%i
)
```

## Vérification des résultats

### Contrôle qualité

```batch
# Vérifier la taille des fichiers
for /r "output\integrations" %%f in (*.txt) do (
    if %%~zf LSS 100 echo Fichier suspect: %%f
)

# Compter les fichiers par taille
powershell "Get-ChildItem 'output\integrations' -Filter '*.txt' | Group-Object {if ($_.Length -lt 100) {'Vide'} elseif ($_.Length -lt 1000) {'Petit'} else {'Normal'}} | Select Name, Count"
```

### Validation du contenu

```batch
# Vérifier les métadonnées
findstr /L "# URL:" "output\integrations\*.txt" | find /c "URL:"
```

## Dépannage

### Problèmes d'installation

```batch
# Vérifier Python
python --version

# Vérifier pip
pip --version

# Installer les dépendances manuellement
pip install aiohttp html2text tqdm
```

### Problèmes d'exécution

```batch
# Vérifier les permissions
icacls "output" /grant %USERNAME%:F

# Vérifier l'espace disque
dir "output" /-c
```

## Résultats attendus

Après une extraction réussie, vous devriez avoir :

- **832 fichiers .txt** dans `output/integrations/`
- **Taux de succès** > 95%
- **Taille totale** ~500 MB
- **Temps d'extraction** 4-5 heures

## Support

En cas de problème :

1. Vérifier les logs dans `integrations_extraction.log`
2. Consulter les statistiques dans `extraction_stats.txt`
3. Relancer l'extraction avec `--skip-existing False`
4. Réduire le nombre de workers si problèmes de connexion

## Commandes de maintenance

```batch
# Nettoyer les logs
del integrations_extraction.log

# Nettoyer les fichiers temporaires
del extraction_stats.txt

# Supprimer tous les fichiers d'intégrations
rmdir /s /q "output\integrations"
```