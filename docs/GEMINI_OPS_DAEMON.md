# Gemini Ops Daemon

## But

Sortir la surveillance Gemini hors du laptop.

Le daemon tourne dans `merlin-mesh` et surveille:
- l'API Gemini de base
- `Interactions` simple
- `Interactions + mcp_server`
- l'etat du bridge MCP live

## Fichier

- `agents/gemini_ops_daemon.py`

## Ce qu'il fait

Tous les `GEMINI_OPS_POLL_SECONDS`:
- teste `generateContent`
- teste `interactions_basic`
- teste `interactions_mcp`
- resume le blocage probable
- heartbeat `MERLIN`
- ecrit l'etat dans `intel.gemini_ops`
- ecrit un snapshot dans `intel.merlin_feedback`

## Variables

- `RUN_GEMINI_OPS_DAEMON=true`
- `GEMINI_OPS_POLL_SECONDS=600`
- `GEMINI_INTERACTION_MODEL=gemini-2.5-flash`
- `GEMINI_MCP_ENDPOINT=https://<merlin-mcp-ingress>/mcp`
- `RUN_GEMINI_MEMORY_REBUILD=false`

## Runtime vise

Le daemon doit vivre:
- dans `deploy_merlin_mesh.yaml`
- dans le fallback compose
- pas sur le laptop comme process manuel

## Valeur S25

- le projet Gemini est surveille en continu
- le blocage `Interactions + MCP` n'est plus une surprise
- COMET et TRINITY peuvent relire cet etat dans le cockpit
- le laptop redevient une station d'admin, pas la base du monitoring
