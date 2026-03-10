# Gemini MCP Bridge

## But

Donner a MERLIN / Gemini un vrai bridge MCP sur Akash, pas un simple appel ad hoc.

## Design

- serveur MCP Python `FastMCP`
- transport `streamable-http`
- outils seulement
- backend reel: cockpit S25
- boucle de writeback via `write_feedback`

## Fichiers

- `agents/merlin_mcp_bridge.py`
- `agents/merlin_feedback_loop.py`
- `agents/cockpit_client.py`

## Endpoint

- host: `0.0.0.0`
- port: `8000`
- path: `/mcp`

## Outils exposes

- `get_system_status`
- `get_shared_memory`
- `get_agents_state`
- `get_mesh_status`
- `get_router_report`
- `route_task`
- `get_missions`
- `create_mission`
- `write_feedback`
- `heartbeat`

## Boucle de retroaction

Le worker `merlin_feedback_loop.py`:
- relit `status`
- relit `mesh`
- relit `missions`
- ecrit un snapshot dans `intel.merlin_feedback`
- heartbeat MERLIN

## Runtime Akash

Variables:
- `RUN_MERLIN_MCP_BRIDGE=true`
- `RUN_MERLIN_FEEDBACK_LOOP=true`
- `MERLIN_MCP_PORT=8000`
- `MERLIN_MCP_PATH=/mcp`
- `MERLIN_FEEDBACK_SECONDS=300`

## Mode dedie recommande

Fichier:
- `akash/deploy_merlin_mesh.yaml`

Preparation operateur:
- `pwsh -File scripts/prepare_merlin_mesh_deploy.ps1`

Validation handshake:
- `pwsh -File scripts/test_merlin_mcp_handshake.ps1 -Endpoint "http://<ingress>/mcp"`

But:
- isoler MERLIN/Gemini du cockpit principal
- garder un module Akash leger, peu couteux, mais toujours online
- permettre un endpoint MCP stable sans gonfler le service central

## Role dans S25

- Gemini/MERLIN ne protege pas les serveurs par magie
- il obtient une surface de tools stable pour observer, missionner, relire et ecrire dans le mesh
- la protection vient ensuite de la boucle:
  - lecture etat
  - validation Gemini
  - writeback memory
  - mission / escalation

## Limite actuelle

Ce bridge expose le cockpit S25 a Gemini/MERLIN.
Il ne remplace pas encore un orchestrateur Gemini autonome complet.
La prochaine marche serait un client Gemini qui consomme ce MCP a distance et pousse ses verdicts dans `write_feedback`.
