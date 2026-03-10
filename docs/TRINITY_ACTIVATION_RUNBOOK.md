# TRINITY Activation Runbook

## But

Activer S25 jusqu'au mode operationnel stable en utilisant TRINITY comme commander, COMET comme watchman intel, KIMI comme scanner Web3, Akash comme cockpit public et Dell-Linux comme boucle locale IA.

## Etat cible

- TRINITY boot sans popup et lit `memory`, `mesh`, `router`, `missions`
- COMET alimente `GET /api/comet/feed`
- KIMI remonte ses scans via tunnel/Home Assistant
- Dell-Linux execute la boucle locale `agent_loop.py`
- Akash recoit `HA_TOKEN` et peut piloter Home Assistant
- le pipeline quitte `INIT` pour un cycle dry-run complet

## Endpoints utiles

- `GET /api/memory`
- `POST /api/memory/ping`
- `GET /api/mesh/status`
- `GET /api/router/report`
- `GET /api/missions`
- `POST /api/missions`
- `POST /api/missions/update`
- `GET /api/comet/feed`
- `POST /api/trinity`

## Ordre d'activation

### 1. Verifier le front TRINITY

Objectif:
- s'assurer que la GPT parle bien au Worker stable

Checks:
- `https://trinity-s25-proxy.trinitys25steph.workers.dev/api/version`
- `https://trinity-s25-proxy.trinitys25steph.workers.dev/api/mesh/status`
- `https://trinity-s25-proxy.trinitys25steph.workers.dev/api/router/report`

Attendu:
- `build_sha = d39003fff0126ed684dc6fcd4c9ef65743416d88`
- `mesh` en 200
- `router` en 200

### 2. Refaire le boot agent

Commande TRINITY:

```text
Status S25. Fais ton boot complet avec heartbeat, memory, mesh, router et missions puis donne le resume final.
```

Attendu:
- `Discussion terminee avec trinity-s25-proxy.trinitys25steph.workers.dev`
- lecture de `memory`, `mesh`, `router`
- resume avec priorites reelles

### 3. Armer COMET

Objectif:
- transformer COMET en source d'intel persistante via missions

Mission type:

```json
{
  "created_by": "TRINITY",
  "target": "COMET",
  "task_type": "market_news",
  "intent": "Scanner Akash, Cosmos, MEXC et memecoins 1m puis remonter les signaux critiques",
  "priority": "high",
  "context": {
    "cadence": "continuous",
    "topics": ["akash", "cosmos", "mexc", "memecoins", "rugpull", "whales"]
  }
}
```

Commande TRINITY recommandee:

```text
Mission COMET: market + web3 intel sur Akash, Cosmos, MEXC, memecoins et rugpull watch. Priorite haute.
```

Checks:
- `POST /api/missions`
- `GET /api/missions`
- `GET /api/comet/feed`

Helper local:

```powershell
pwsh -File scripts/arm_comet_mission.ps1
```

Attendu:
- mission `COMET` en `active`
- feed COMET non vide

### 4. Activer KIMI

Objectif:
- remettre le scanner Web3 online

Action Home Assistant:

```bash
bash /config/scripts/start_s25_tunnel.sh
```

Attendu:
- `KIMI` quitte `standby`
- tunnel visible dans le status

Post-check:
- `POST /api/memory/ping` avec `{"agent":"KIMI"}`
- `POST /api/memory/state` avec mise a jour `last_scan`, `status=online`

### 5. Brancher Dell-Linux

Objectif:
- lancer la boucle locale IA et Ollama

Machine:
- `10.0.0.202`

Commande:

```bash
python agent_loop.py
```

Attendu:
- Ollama disponible
- boucle agents locale active
- TRINITY peut citer Dell-Linux comme noeud pret

### 6. Injecter Home Assistant dans Akash

Objectif:
- autoriser les signaux TRINITY vers Home Assistant

Variable critique:
- `HA_TOKEN`

Autres variables a verifier:
- `HA_URL`
- `S25_SHARED_SECRET`
- `ALLOW_PUBLIC_ACTIONS=true`

Attendu:
- `ha = connected`
- signaux TRINITY vers HA possibles

### 7. Deployer les agents critiques Akash

Priorite:
- `oracle-agent`
- `onchain-guardian`

But:
- alimenter COMET et ARKON
- surveiller prix multi-source, whales, rug pulls

Attendu:
- nouvelles missions disponibles dans le cockpit
- hausse du flux intel COMET

### 8. Fermer la boucle dry-run

Objectif:
- sortir de `INIT` vers une boucle dry-run complete

Sequence:
1. KIMI scanne
2. COMET enrichit
3. MERLIN ou GOUV4 route
4. ARKON valide
5. HA recoit le signal
6. MEXC reste encore en `dry_run`

Attendu:
- `pipeline.active_model` non `INIT`
- `last_signal` renseigne
- menace et confiance remontees dans le status

## Prompt TRINITY recommande

```text
TRINITY, plan activation S25 complet. Reprends le boot, cree une mission COMET prioritaire, verifie KIMI, verifie Dell-Linux, rappelle les variables Akash manquantes et donne les 5 prochaines actions dans l'ordre.
```

## Definition de done

- Worker stable actif
- GPT live stable
- COMET missionne et feed non vide
- KIMI online
- Dell-Linux loop active
- `HA_TOKEN` injecte
- agents critiques Akash deploies
- pipeline dry-run complet
