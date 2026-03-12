# MERLIN Mirror Fleet

Cette brique prepare une flotte miroir Akash de 10 conteneurs pour `MERLIN / S25`, avec bootstrap Google Secret Manager et voie de confirmation MCP vers `merlin.smajor.org`.

## Pieces ajoutees

- `configs/mission_mirror_akash.example.json`
- `scripts/render_mirror_fleet_manifest.py`
- `agents/google_secret_manager_bootstrap.py`
- `scripts/confirm_merlin_mirror_authority.py`

## Doctrine

- `Akash` porte la flotte miroir.
- `Google Secret Manager` porte les secrets runtime quand l'autorite Google est etablie.
- `admin@merlin.ai` est traite comme email admin Workspace, pas comme service account GCP.
- Le vrai service account GCP doit etre fourni separement sous la forme `name@project.iam.gserviceaccount.com` ou via une configuration ADC/WIF.
- Le conteneur `mirror-01` est le conteneur test pour la pile trading.

## Rendu du manifest

```powershell
python C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\scripts\render_mirror_fleet_manifest.py --mission-file C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\configs\mission_mirror_akash.example.json
```

Pour injecter aussi le vrai `S25_SHARED_SECRET` depuis le vault local:

```powershell
python C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\scripts\render_mirror_fleet_manifest.py --mission-file C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\configs\mission_mirror_akash.example.json --use-live-shared-secret
```

## Bootstrap Google Secret Manager

Le bootstrapur attend:

- `GOOGLE_CLOUD_PROJECT`
- soit `GOOGLE_APPLICATION_CREDENTIALS`
- soit `GOOGLE_ADC_JSON_B64`
- `S25_GSM_SECRET_MAP_JSON` pour mapper les noms d'environnement vers les noms de secrets

Dry-run:

```powershell
python C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\agents\google_secret_manager_bootstrap.py --project-id <PROJECT_ID> --dry-run
```

Chargement reel:

```powershell
python C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\agents\google_secret_manager_bootstrap.py --project-id <PROJECT_ID> --output C:\temp\mirror-01.env
```

## Confirmation MCP vers MERLIN

```powershell
python C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\scripts\confirm_merlin_mirror_authority.py --mission-file C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git\configs\mission_mirror_akash.example.json --authority established
```

## Blocages reels

- Le fichier mission Drive `mission_mirrror_akash.jason/json` n'etait pas accessible dans cette session.
- Aucun credential Google reel n'etait present pour etablir l'autorite Secret Manager.
- Aucun vrai service account GCP n'etait fourni; `admin@merlin.ai` seul ne suffit pas pour l'API Secret Manager.
- Les cles de trading ne sont pas injectees ici sans autorite runtime explicite.
