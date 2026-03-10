# S25 LUMIERE — SHARED MEMORY
# Source de verite centralisee pour tous les agents
# Accessible via GET /api/memory | Mis a jour via POST /api/memory

---

## VISION
**S25 Lumiere** = Serveur Web3 Multi-Agent Multi-Chain, AI-boosted
- But: Leaders Web3 — pas juste MEXC, multi-chain complet
- Infrastructure cible: Akash (decentralise)
- Base saine d'abord, puis expansion

---

## INFRASTRUCTURE

### Akash (Production)
- Cockpit public stable: https://trinity-s25-proxy.trinitys25steph.workers.dev
- Origin Akash corrige: http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com
- DSEQ: 25838342 | Provider: akashprovid.com | Cost: $0.48/mois
- Doctrine: endpoint public stable devant Akash, pas de dependance laptop pour TRINITY

### Akash (Sandbox — ACTIF 2026-03-09)
- S25-SANDBOX-MEMORY-v1: http://59cpn50vq1alv5ls5sdu37d7vs.ingress.akash.sthlm-host.top
- DSEQ: 25851041 | Provider: akash.sthlm-host.top | Cost: $0.37/mois
- Image: ghcr.io/stephaneboss/s25-command-center:main
- Memory API: /api/memory | /api/memory/state | /api/memory/ping

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

| Agent  | Modele     | Role                     | Status                        |
|--------|------------|--------------------------|-------------------------------|
| TRINITY| GPT-4o     | Orchestrateur vocal      | Vocal controller teste        |
| ARKON  | Claude Code| Analyste / Builder       | Actif                         |
| MERLIN | Gemini     | Validateur web           | Online                        |
| COMET  | Perplexity | Watchman temps reel      | Bridge v2.1                   |
| KIMI   | Kimi Web3  | Scanner 1M tokens        | A migrer hors tunnel manuel   |

---

## SUBAGENTS CLAUDE CODE

| Subagent               | Role                            |
|------------------------|---------------------------------|
| defi-liquidity-manager | Positions DeFi, APY, IL        |
| onchain-guardian       | Monitor on-chain, rug pulls     |
| oracle-agent           | Prix temps reel multi-source    |
| code-validator         | Validation code avant deploy    |
| smart-refactor         | Refactoring async/Flask         |
| auto-documenter        | Docs auto pipeline              |

---

## ENTITES HA S25

- input_text.ai_prompt       — Prompt envoye a l'IA
- input_select.ai_model      — Modele selectionne
- input_text.ai_model_actif  — Status pipeline
- input_boolean.ai_auto_mode — Mode automatique
- sensor.s25_trinity_signal  — Signal TRINITY -> HA

---

## ROADMAP ACTIVE

1. [DONE] Subagents Claude Code integres
2. [DONE] Trinity vocal controller teste
3. [IN PROGRESS] Memoire persistante centralisee
4. [TODO] Deployer oracle-agent + onchain-guardian sur Akash
5. [TODO] HA_TOKEN dans env vars Akash
6. [TODO] KIMI sur endpoint stable public
7. [TODO] Pipeline end-to-end dry_run
8. [TODO] agent_loop.py -> DELL-LINUX uniquement en fallback
9. [TODO] MEXC Sunday series live
10. [IN PROGRESS] Provider watch structure via COMET Work + snapshot local
