# Akash Agent Deploy Plan

## Scope

Sortir `oracle-agent` et `onchain-guardian` du laptop pour les faire tourner comme workers autonomes du command center.

## Agents

### ORACLE

Fichier:
- [oracle_agent.py](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/agents/oracle_agent.py)

Role:
- valider les prix multi-source
- calculer une mediane
- detecter la derive entre sources
- ecrire ses snapshots dans `market` et `intel`
- mettre a jour les missions cible `ORACLE`

Variables utiles:
- `COCKPIT_URL`
- `S25_SHARED_SECRET`
- `ORACLE_POLL_SECONDS`
- `ORACLE_SYMBOLS`

### ONCHAIN_GUARDIAN

Fichier:
- [onchain_guardian.py](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/agents/onchain_guardian.py)

Role:
- lire DexScreener
- classifier le risque liquidite / volatilite
- stocker un snapshot dans `intel`
- mettre a jour les missions cible `ONCHAIN_GUARDIAN`

Variables utiles:
- `COCKPIT_URL`
- `S25_SHARED_SECRET`
- `ONCHAIN_POLL_SECONDS`
- `ONCHAIN_TOKEN_LIST`

## Contrats d'ecriture cockpit

Les deux agents utilisent:
- `POST /api/memory/ping`
- `POST /api/memory/state`
- `GET /api/missions`
- `POST /api/missions/update`

## Demarrage cible

Exemples:

```bash
python -m agents.oracle_agent
python -m agents.onchain_guardian
```

## Armer les missions

Oracle:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/arm_oracle_mission.ps1 -Symbol BTC
```

Guardian:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/arm_guardian_mission.ps1 -Token 0x...
```

## Done

- les agents tournent sans laptop
- `mesh/status` voit `ORACLE` et `ONCHAIN_GUARDIAN`
- `memory` conserve leurs snapshots
- les missions se mettent a jour automatiquement
