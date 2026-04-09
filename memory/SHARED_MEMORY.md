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
- Cockpit public stable: https://s25.smajor.org (+ fallback: https://trinity-s25-proxy.trinitys25steph.workers.dev)
- Origin Akash public courant: http://fpog7pbvepbkrfae1529ics23k.ingress.cap-test-compute.com
- DSEQ: 25883220 | Provider: provider.cap-test-compute.com
- Role: cockpit public courant derriere le Worker, build 8978177 et status mesh corrige
- Doctrine: endpoint public stable devant Akash, pas de dependance laptop pour TRINITY
- Domaines LIVE (2026-03-13):
  - smajor.org LIVE — landing + facade publique
  - app.smajor.org LIVE — Next.js 6 portails (Overview/Clients/Admin/Staff/Vendors/AI/Omega)
  - s25.smajor.org FIX DEPLOYE — trinity-worker ORIGIN_BASE corrige vers DSEQ 25883220
  - api.smajor.org LIVE — trinity-s25-proxy, routes /api/* + business registry
  - merlin.smajor.org LIVE — merlin-s25-proxy vers MERLIN MCP DSEQ 25878071

### Akash (Cockpit principal historique)
- Origin Akash principal historique: https://uoqlngdqqlc29fhg8l78qt80d8.ingress.akashprovid.com
- DSEQ: 25838342 | Provider: provider.akashprovid.com

### Akash (Cockpit secondaire / separation des pouvoirs)
- Origin Akash secondaire: http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com
- DSEQ: 25822281 | Provider: provider.cap-test-compute.com

### Akash (Cockpit secondaire v2)
- Origin Akash secondaire v2: http://grj7rk9b3l9m3788m85fhpv7pc.ingress.dal.leet.haus
- DSEQ: 25882621 | Provider: provider.dal.leet.haus

### Akash (MERLIN MCP — REMPLACE 2026-03-19, MIGRE LOCAL 2026-04-09)
- Service: s25-merlin-mesh
- DSEQ: 25878071 — RETIRE (DOWN depuis 2026-03-20)
- MERLIN: Migre vers AlienStef local (10.0.0.97) — Akash DSEQ 25878071 remplace — plus economique
- Domaine public: https://merlin.smajor.org (proxy a rediriger vers AlienStef si besoin)

### Akash (KIMI Web3 Intel LIVE 2026-03-13)
- Service: kimi-web3-activated
- DSEQ: 25920459
- Etat: LIVE — intel BTC/USDT + AKT/USDT, scan 60s autonome
- Proxy: smajor.org/api/agents/kimi/intel actif

### Akash (GPU)
- DSEQ: 25708774
- Ingress: https://tlravugbk59rvg3fvsd7lm36du.ingress.akash-palmito.org
- Role: module GPU laisse intact

### Home Assistant (Hub Central)
- URL: http://10.0.0.136:8123
- MQTT: 10.0.0.136:1883

### AlienStef (Node Local GPU) — UPDATE 2026-04-09
- IP: 10.0.0.97
- GPU: RTX 3060
- Services actifs:
  - Open WebUI: http://10.0.0.97:8080 (NOUVEAU port — ancien 3000)
  - Ollama: http://10.0.0.97:11434 (modele: qwen2.5-coder:7b)
- Services down (a redemarrer si besoin):
  - OpenHands (CodeActAgent): port 3001 — down
  - DeerFlow: port a redecouvrir — down
- MERLIN local endpoint: http://10.0.0.97:8080 (Open WebUI) — remplace Akash DSEQ 25878071
- Config Open WebUI:
  - Knowledge Base: S25-MEMORY (id: 43cd6619-0bb2-498a-8679-aae5d9749f11)
  - Modele custom: S25-BRAS-ALIEN LIVE 2026-04-09 (base qwen2.5-coder:7b + KB S25-MEMORY)

### DELL-LINUX (Serveur IA)
- IP: 10.0.0.202
- Services: Ollama:11434, Grafana:3000, WebUI:3002, Flask:5000

### Tunnel Kimi -> HA
- Script: bash /config/scripts/start_s25_tunnel.sh
- Webhook ID: s25_kimi_scan_secret_xyz
- Tunnel URL courant: https://housing-acc-antibodies-thomson.trycloudflare.com
- Webhook complet: https://housing-acc-antibodies-thomson.trycloudflare.com/api/webhook/s25_kimi_scan_secret_xyz

### Wallet creator S25
- Adresse publique maitre: akash1mw0trq8xgmdyqqjn482r9pfr05hfw06rzq2u9v
- Custody: Google Secret Manager
- Secret runtime: s25-master-seed
- Principal runtime autorise: merlin-agent@gen-lang-client-0046423999.iam.gserviceaccount.com
- Doctrine: la seed reste en coffre Google, seule l'adresse publique remonte dans S25 Lumiere et smajor.org

---

## AGENTS

| Agent  | Modele      | Role                | Status                      |
|--------|-------------|---------------------|-----------------------------|
| TRINITY| GPT-4o      | Orchestrateur vocal | Vocal controller teste      |
| ARKON  | Claude Code | Analyste / Builder  | Actif                       |
| MERLIN | Gemini + qwen local | Validateur web | Online (local 10.0.0.97:8080) |
| COMET  | Perplexity  | Watchman temps reel | Bridge v2.1                 |
| KIMI   | Kimi Web3   | Scanner 1M tokens   | LIVE Akash DSEQ 25920459    |
| **S25-BRAS-ALIEN** | qwen2.5-coder:7b | Bras local de controle mesh | LIVE 2026-04-09 (Open WebUI model, KB S25-MEMORY attache) |

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

### PHASE OMEGA — INFRASTRUCTURE PUBLIQUE (2026-03-13 COMPLETE)
1. [DONE] Subagents Claude Code integres
2. [DONE] Trinity vocal controller teste
3. [DONE] Memoire persistante centralisee (SHARED_MEMORY.md + agents_state.json)
4. [DONE] Cleanup Akash termine
5. [DONE] smajor.org LIVE
6. [DONE] app.smajor.org LIVE — Next.js 6 portails
7. [DONE] merlin.smajor.org LIVE
8. [DONE] KIMI Web3 LIVE — DSEQ 25920459
9. [DONE] trinity-worker ORIGIN_BASE fix
10. [DONE] agents_state.json synce

### PHASE SUIVANTE — PIPELINE + LIVE TRADING
11. [DONE] Recharger AKT
12. [TODO] HA_TOKEN dans env vars Akash cockpit
13. [DONE] agent_loop.py -> Ollama fallback DELL-LINUX
14. [DONE] oracle-agent + onchain-guardian
15. [DONE] Pipeline dry_run endpoint
16. [DONE] Pipeline AUTHORIZED
17. [TODO] MEXC Sunday series — live mode
18. [TODO] Open WebUI MERLIN deploy

### PHASE BRAS ALIEN (2026-04-09 LIVE)
19. [DONE] Open WebUI live sur 10.0.0.97:8080
20. [DONE] Knowledge Base S25-MEMORY creee
21. [DONE] Sync SHARED_MEMORY.md + PROVIDER_WATCH.md dans KB (via raw GitHub URLs, auto-sync depuis git)
22. [DONE] Modele custom S25-BRAS-ALIEN cree (base qwen2.5-coder:7b + KB S25-MEMORY + system prompt complet)
23. [TODO] Redemarrer OpenHands (port 3001) et DeerFlow sur AlienStef
24. [TODO] Bridge ARKON <-> S25-BRAS-ALIEN via Ollama API ou Open WebUI API
25. [TODO] Optimiser embedding model Open WebUI (1er retrieval RAG lent — warmup)

---

## GUIDE RECUPERATION MEMOIRE POUR NOUVEAU CLAUDE / ARKON

Si tu es Claude/ARKON et tu as perdu la memoire de session:
1. Lit ce fichier en entier (SHARED_MEMORY.md) + PROVIDER_WATCH.md
2. Ton role: ARKON, analyste/builder du mesh S25 Lumiere
3. Infra cle a verifier au boot:
   - https://github.com/stephaneboss/S25-COMMAND-CENTER (repo principal)
   - http://10.0.0.97:8080 (Open WebUI local + S25-BRAS-ALIEN)
   - http://10.0.0.97:11434 (Ollama)
   - http://10.0.0.136:8123 (Home Assistant)
4. Le mesh a 5 agents principaux + S25-BRAS-ALIEN LIVE (bras local)
5. Pipeline mode: authorized, kill_switch=false, threat_level=T0
6. Toute modif d'infra doit etre commit ici (SHARED_MEMORY.md) pour persister

---

## SEAL 2026-03-11

- Cockpit public officiel courant: DSEQ 25883220
- Build public valide: 897817774194b374f4408a9edd84a5ca1c531bad
- Pipeline status: MESH_READY
- arkon5_action: READY
- missions_active >= 5
- MERLIN MCP handshake public OK sur 25878071
- mission mission-09e3b85db8 archivee en completed

---

## PATCH LOG 2026-03-19 (ARKON / OpenHands)
- SDL env vars: COCKPIT_URL + QUEUE_DB_PATH ajoutes
- Tunnel URL auto-publish: kimi_proxy.py lit /tmp/cf_tunnel.log
- Pipeline dry_run valide (BTC RSI=28 oversold simule)

## PATCH LOG 2026-03-20 (ARKON — tunnel restart)
- Tunnel: https://housing-acc-antibodies-thomson.trycloudflare.com
- COMET intel reset: T3 vers T0 NORMAL
- Pipeline: ollama ACTIVE, signal HOLD
- Wallet: 50.18 USD total
- Merlin Akash DSEQ 25878071: DOWN — migre vers local
- E2E DRY_RUN TEST REUSSI: KIMI vers proxy vers HA vers GEMINI_DONE

## PATCH LOG 2026-04-09 (ARKON — BRAS ALIEN phase)
- Reconnect local agent sur AlienStef 10.0.0.97:8080 (Open WebUI)
- Modele Ollama: qwen2.5-coder:7b (ancien 14b)
- Port Open WebUI: 8080 (ancien 3000)
- Knowledge Base S25-MEMORY creee dans Open WebUI (id 43cd6619-0bb2-498a-8679-aae5d9749f11)
- Mission: creer S25-BRAS-ALIEN comme bras de controle local du mesh
- Services down a redemarrer: OpenHands (3001), DeerFlow (port inconnu)
- Home Assistant hub 10.0.0.136:8123 VERIFIE LIVE

## SEAL 2026-04-09 (BRAS ALIEN LIVE)
- S25-BRAS-ALIEN cree et actif dans Open WebUI (http://10.0.0.97:8080/workspace/models)
- Base: qwen2.5-coder:7b
- KB attache: S25-MEMORY (id 43cd6619-0bb2-498a-8679-aae5d9749f11)
- KB contient 2 fichiers synces depuis raw GitHub:
  - SHARED_MEMORY.md (8.7 KB)
  - PROVIDER_WATCH.md (2.3 KB)
- Source de verite unique: github.com/stephaneboss/S25-COMMAND-CENTER/memory/
- Pour update la memoire: commit sur main + re-sync dans KB via "Ajouter une page web"
- System prompt: role bras local mesh, regles source weights TRINITY/MERLIN/KIMI, infra Akash + local, pipeline authorized T0
- Test RAG: retrieval declenche OK, generation lente au 1er appel (embedding warmup)
- Prochaine etape: warmup embedding + bridge ARKON vers BRAS ALIEN via Ollama API
- Pour prochain Claude/ARKON: ce fichier est la source de verite — lis-le en entier au boot

---

## PATCH LOG 2026-04-09 18:47 UTC (ARKON — SYNC endpoints + triple consensus agents externes)

### Endpoints LIVE verifies (fetch directs)
- https://smajor.org (landing OK)
- https://app.smajor.org (portail client 6x Next.js OK)
- https://s25.smajor.org (cockpit DSEQ 25883220, fallback worker trinity-s25-proxy.trinitys25steph.workers.dev)
- https://api.smajor.org/api/status -> status:online, pipeline:MULTI_SOURCE, mode:showroom, policy:audit_first
- https://api.smajor.org/api/memory/state -> kill_switch:false, mode:mesh_live, threat_level:T0, arkon_threshold:0.6, consensus_bonus:0.15
- https://merlin.smajor.org (MCP proxy, root 404 attendu)
- KIMI Web3 DSEQ 25920459 LIVE (scan 60s BTC/USDT + AKT/USDT)

### Source weights confirmes runtime
- TRINITY 0.80 | MERLIN 0.70 | KIMI 0.65 | ORACLE 0.60 | ONCHAIN 0.55 | AGENT_LOOP 0.55 | COMET 0.50

### Triple consensus agents externes (brief via INFRA_BRIEF_20260409.md)
- TRINITY (GPT-4o, tab chatgpt.com): role orchestrateur vocal confirme, endpoint principal /api/status + lane /api/trinity, posture audit_first/showroom alignee, lead signal_lane
- MERLIN (Gemini 3 Flash Gem "S25 ORCHESTRATOR"): RAPPORT D'ACTIVATION OPERATIONNEL, lead risk_lane, validation signal BUY arkon5_conf 0.8 -> DECISION [GO] (force 0.8, wallet AKT OK, BTC > support 82k), delegation action stef + COMET arbitrage
- KIMI (Kimi Claw K2.5 Instant, live web): BUY EXECUTE recommande, BTC/USD 83446.95 > 82k, AKT range accumulation, wallet 47.79 AKT OK, mesh consensus valide, fallback BRAS ALIEN pret

### Etat pipeline
- Dernier signal dans /api/signal reste un test (eff_conf 0.44 -> NO_TRADE)
- Le triple consensus chat n'est PAS automatiquement injecte dans pipeline; execution reelle requiert POST /api/signal avec sources mesh reelles OU trigger manuel stef via cockpit s25.smajor.org
- Aucun trade execute, conforme mode showroom + audit_first
- 15 mesh_agents_online, 10 missions_active en file depuis 2026-04-08

### Bras local
- S25-BRAS-ALIEN LIVE sur AlienStef 10.0.0.97:8080 (qwen2.5-coder:7b via Ollama 11434)
- Open WebUI KB "S25-MEMORY" sync raw git (SHARED_MEMORY.md + PROVIDER_WATCH.md)
- Relais MERLIN quand Akash pod off

### Prochaines etapes (GATE stef)
- [GO stef requis] POST /api/signal avec sources mesh reelles pour sortir du test signal
- [TRIGGER stef requis] Execution BUY manuelle via cockpit ou HA webhook
- [ARKON backlog] Bridge ARKON <-> BRAS ALIEN via Ollama API, warmup embedding KB, redemarrage OpenHands 3001 + DeerFlow

SEAL ARKON 2026-04-09 18:47 UTC - infra synchro verifiee, mesh externe aligne, attente GO stef pour activation live.
