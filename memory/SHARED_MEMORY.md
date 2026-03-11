# S25 LUMIERE - SHARED MEMORY
# Source de verite centralisee pour tous les agents
# Accessible via GET /api/memory | Mis a jour via POST /api/memory

---

## VISION

**S25 Lumiere** = Serveur Web3 Multi-Agent Multi-Chain, AI-boosted
- But: leaders Web3, pas juste MEXC, multi-chain complet
- Infrastructure cible: Akash (decentralise)
- Base saine d'abord, puis expansion

---

## INFRASTRUCTURE

### Akash (Cockpit principal)
- Cockpit public stable: https://trinity-s25-proxy.trinitys25steph.workers.dev
- Origin Akash public courant: http://fpog7pbvepbkrfae1529ics23k.ingress.cap-test-compute.com
- DSEQ: 25883220 | Provider: provider.cap-test-compute.com
- Role: cockpit public courant derriere le Worker, build 8978177 et status mesh corrige
- Doctrine: endpoint public stable devant Akash, pas de dependance laptop pour TRINITY

### Akash (Cockpit principal historique)
- Origin Akash principal historique: https://uoqlngdqqlc29fhg8l78qt80d8.ingress.akashprovid.com
- DSEQ: 25838342 | Provider: provider.akashprovid.com
- Role: ancien cockpit principal conserve tant que la base 25883220 reste en observation

### Akash (Cockpit secondaire / separation des pouvoirs)
- Origin Akash secondaire: http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com
- DSEQ: 25822281 | Provider: provider.cap-test-compute.com
- Role: cockpit secondaire historique, utilise pour restaurer le contexte vers 25883220
- Note: l'ancien sandbox `25851041` a ete ferme pendant le cleanup du 10 mars 2026

### Akash (Cockpit secondaire v2)
- Origin Akash secondaire v2: http://grj7rk9b3l9m3788m85fhpv7pc.ingress.dal.leet.haus
- DSEQ: 25882621 | Provider: provider.dal.leet.haus
- Role: nouveau cockpit secondaire cree apres recharge AKT et cycle wallet stable
- Note: garder `25822281` tant que la bascule et les checks runtime ne sont pas valides

### Akash (MERLIN MCP LIVE 2026-03-10)
- Service: s25-merlin-mesh
- DSEQ: 25878071
- Provider: provider.akashprovid.com
- MCP ingress live: https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
- Etat: handshake public OK, conteneur running
- Limite actuelle: Gemini Interactions + mcp_server reste bloque cote Google

### Akash (GPU)
- DSEQ: 25708774
- Ingress: https://tlravugbk59rvg3fvsd7lm36du.ingress.akash-palmito.org
- Role: module GPU laisse intact

### Commandes operateur a retenir
- Test handshake MCP:
  - python scripts/test_merlin_mcp_handshake.py https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
- Test Gemini live:
  - python scripts/run_gemini_merlin_interaction.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
- Writeback MCP direct:
  - python scripts/write_merlin_mcp_feedback.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp --summary "MERLIN MCP bridge live on Akash. Public handshake validated on dseq 25878071."
- Preparation manifest Akash:
  - powershell -ExecutionPolicy Bypass -File scripts/prepare_merlin_mesh_deploy.ps1

### Home Assistant (Hub Central)
- URL: http://10.0.0.136:8123
- MQTT: 10.0.0.136:1883

### DELL-LINUX (Serveur IA)
- IP: 10.0.0.202
- Services: Ollama:11434, Grafana:3000, WebUI:3002, Flask:5000

### Tunnel Kimi -> HA
- Script: bash /config/scripts/start_s25_tunnel.sh
- Webhook ID: s25_kimi_scan_secret_xyz

---

## AGENTS

| Agent  | Modele      | Role                | Status                      |
|--------|-------------|---------------------|-----------------------------|
| TRINITY| GPT-4o      | Orchestrateur vocal | Vocal controller teste      |
| ARKON  | Claude Code | Analyste / Builder  | Actif                       |
| MERLIN | Gemini      | Validateur web      | Online                      |
| COMET  | Perplexity  | Watchman temps reel | Bridge v2.1                 |
| KIMI   | Kimi Web3   | Scanner 1M tokens   | A migrer hors tunnel manuel |

---

## SUBAGENTS CLAUDE CODE

| Subagent               | Role                         |
|------------------------|------------------------------|
| defi-liquidity-manager | Positions DeFi, APY, IL      |
| onchain-guardian       | Monitor on-chain, rug pulls  |
| oracle-agent           | Prix temps reel multi-source |
| code-validator         | Validation code avant deploy |
| smart-refactor         | Refactoring async/Flask      |
| auto-documenter        | Docs auto pipeline           |

---

## ENTITES HA S25

- input_text.ai_prompt - Prompt envoye a l'IA
- input_select.ai_model - Modele selectionne
- input_text.ai_model_actif - Status pipeline
- input_boolean.ai_auto_mode - Mode automatique
- sensor.s25_trinity_signal - Signal TRINITY -> HA

---

## ROADMAP ACTIVE

1. [DONE] Subagents Claude Code integres
2. [DONE] Trinity vocal controller teste
3. [IN PROGRESS] Memoire persistante centralisee
4. [TODO] Deployer oracle-agent + onchain-guardian sur Akash
5. [DONE] Cleanup Akash termine, base conservee = 25878071 / 25838342 / 25822281 / 25708774
6. [DONE] Nouveau cockpit public cree et hydrate: 25883220 -> provider.cap-test-compute.com
7. [DONE] Nouveau cockpit secondaire cree: 25882621 -> provider.dal.leet.haus
8. [TODO] HA_TOKEN dans env vars Akash
9. [TODO] KIMI sur endpoint stable public
10. [DONE] `api/status` public realigne avec l'etat mesh reel via 25883220
11. [TODO] agent_loop.py -> DELL-LINUX uniquement en fallback
12. [IN PROGRESS] Provider watch structure via COMET Work + snapshot local
