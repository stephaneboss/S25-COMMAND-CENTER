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
- Cockpit public stable: https://s25.smajor.org ✅ (+ fallback: https://trinity-s25-proxy.trinitys25steph.workers.dev)
- Origin Akash public courant: http://fpog7pbvepbkrfae1529ics23k.ingress.cap-test-compute.com
- DSEQ: 25883220 | Provider: provider.cap-test-compute.com
- Role: cockpit public courant derriere le Worker, build 8978177 et status mesh corrige
- Doctrine: endpoint public stable devant Akash, pas de dependance laptop pour TRINITY
- Domaines LIVE (2026-03-13):
  - `smajor.org` ✅ LIVE — landing + facade publique
  - `app.smajor.org` ✅ LIVE — Next.js 6 portails (Overview/Clients/Admin/Staff/Vendors/AI/Omega)
  - `s25.smajor.org` ✅ FIX DEPLOYE — trinity-worker ORIGIN_BASE corrige vers DSEQ 25883220
  - `api.smajor.org` ✅ LIVE — trinity-s25-proxy, routes /api/* + business registry
  - `merlin.smajor.org` ✅ LIVE — merlin-s25-proxy vers MERLIN MCP DSEQ 25878071

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
- Domaine public: https://merlin.smajor.org ✅ LIVE (health ok:true confirme 2026-03-13)
- Etat: handshake public OK, conteneur running
- Limite actuelle: Gemini Interactions + mcp_server reste bloque cote Google

### Akash (KIMI Web3 Intel LIVE 2026-03-13)
- Service: kimi-web3-activated
- DSEQ: 25920459
- Etat: LIVE — intel BTC/USDT + AKT/USDT, scan 60s autonome
- Bail: ~2 jours restants au 2026-03-13 — recharger AKT
- Proxy: smajor.org/api/agents/kimi/intel ✅ actif
- Note: migre hors tunnel manuel, endpoint Akash direct

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

### Wallet creator S25
- Adresse publique maitre: `REDACTED_WALLET_ADDRESS`
- Custody: Google Secret Manager
- Secret runtime: `s25-master-seed`
- Principal runtime autorise: `merlin-agent@gen-lang-client-0046423999.iam.gserviceaccount.com`
- Doctrine: la seed reste en coffre Google, seule l'adresse publique remonte dans S25 Lumiere et smajor.org

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

### PHASE OMEGA — INFRASTRUCTURE PUBLIQUE (2026-03-13 ✅ COMPLETE)
1. [DONE] Subagents Claude Code integres
2. [DONE] Trinity vocal controller teste
3. [DONE] Memoire persistante centralisee (SHARED_MEMORY.md + agents_state.json)
4. [DONE] Cleanup Akash termine — base = 25878071 / 25883220 / 25882621 / 25838342 / 25708774
5. [DONE] smajor.org LIVE — DNS + Cloudflare Worker smajor-hub
6. [DONE] app.smajor.org LIVE — Next.js 6 portails (Clients/Admin/Staff/Vendors/AI/Omega)
7. [DONE] merlin.smajor.org LIVE — proxy vers MERLIN MCP DSEQ 25878071
8. [DONE] KIMI Web3 LIVE — DSEQ 25920459, intel BTC/AKT actif
9. [DONE] trinity-worker ORIGIN_BASE corrige vers DSEQ 25883220 (fix 2026-03-13)
10. [DONE] agents_state.json synce — KIMI status live, infrastructure map

### PHASE SUIVANTE — PIPELINE + LIVE TRADING
11. [TODO] Recharger AKT — bail KIMI expire ~2 jours (2026-03-13)
12. [TODO] HA_TOKEN dans env vars Akash cockpit
13. [TODO] agent_loop.py -> DELL-LINUX Ollama (10.0.0.202:11434)
14. [TODO] Deployer oracle-agent + onchain-guardian sur Akash
15. [TODO] Pipeline end-to-end dry_run — KIMI -> ARKON -> MERLIN -> RiskGuardian
16. [TODO] MEXC Sunday series — live mode quand base saine
17. [TODO] Open WebUI MERLIN deploy (SDL MERLIN prepare, bid 250 uAKT)

---

## SEAL 2026-03-11

- Cockpit public officiel courant:
  - DSEQ `25883220`
  - origin `http://fpog7pbvepbkrfae1529ics23k.ingress.cap-test-compute.com`
  - front stable `https://trinity-s25-proxy.trinitys25steph.workers.dev`
- Build public valide:
  - `897817774194b374f4408a9edd84a5ca1c531bad`
- Etat public valide:
  - `pipeline_status = MESH_READY`
  - `arkon5_action = READY`
  - `missions_active >= 5`
- Handshake multi-agent valide:
  - mission `mission-09e3b85db8`
  - chaine `TRINITY -> MERLIN -> COMET`
  - HA preserve comme chaine laterale, pas comme point de verite principal
- MERLIN MCP:
  - handshake public OK sur `25878071`
  - feedback de fin de journee ecrit via MCP
- Seal runtime:
  - mission `mission-09e3b85db8` archivee en `completed`
  - `comet_intel` public = `Mission mission-09e3b85db8 -> completed`
  - `status` public reste `MESH_READY`
