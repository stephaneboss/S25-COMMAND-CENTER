# 🧠 CLAUDE_CONTEXT.md — Mémoire Persistante Claude
> Dernière mise à jour: 2026-04-09
> Projet: S25 Lumière — Autonomous Multi-Agent Crypto Trading
> Major: Stef Boss (stephaneboss) | excavaneige@gmail.com

---

## 📌 PROTOCOLE DÉMARRAGE SESSION — LIRE EN PREMIER

1. Lire ce fichier (CLAUDE_CONTEXT.md)
2. Lire la mémoire MASTER sur Google Drive:
   👉 https://docs.google.com/document/d/1ztAi7FxXG6ZTLhqaSQX46CQJz5vMvWaNtLEM5sIVkZE/edit
   (MEMOIRE IA PERSISTANTE - Stephane Major - NE PAS SUPPRIMER)
3. Lire dernière conversation TRINITY: chatgpt.com > Trinity S25 Lumière Commander
4. Vérifier état live: https://s25.smajor.org
5. Continuer les workstreams actifs

---

## 🎯 MON RÔLE
**CLAUDE = Builder / Deploy + WS5 Claude Subagents**
- Architecture, code backend, Docker, manifests Akash
- oracle-agent et onchain-guardian (WS5)
- PRs, refactoring, Dockerfile, tests CI

---

## 🏗️ INFRASTRUCTURE AKASH (état 2026-04-09)

| DSEQ | Type | Statut |
|------|------|--------|
| 25883220 | Cockpit public (RTX?) | 🟢 LIVE |
| 25878071 | merlin-mesh officiel | 🟢 LIVE |
| 25838342 | Cockpit principal historique | conservé |
| 25822281 | Cockpit secondaire | conservé |
| 25882621 | Cockpit secondaire v2 | créé |
| 25708774 | GPU module | conservé |
| 26182802 | RTX 4090 @$0.42/h | ⚠️ EN COURS |

**V3 Migration en cours:**
- SDL V2 prêt: RTX 3090Ti @$0.30/h — AWAITING WALLET SIGNATURE (Stef via Keplr)
- Étape 1 (STEF): Signer le déploiement SDL V2 sur console.akash.network
- Étape 2 (COMET): Récupérer nouvel ingress, update DNS smajor.org

---

## 📋 WORKSTREAMS ACTIFS

### WS1 — Runtime Akash (Owner: Codex)
- ✅ Cockpit public 25883220 stable
- ✅ Worker endpoint stable
- ⏳ Nettoyer dépendances HA (HA ne doit plus être source de vérité)

### WS2 — GPT/TRINITY (Owner: Codex)
- ✅ spec x-openai-isConsequential: false
- ✅ Backend status corrigé
- ⏳ Republier UI GPT + vérifier vocal TRINITY lit MESH_READY

### WS3 — Gemini/MERLIN (Owner: Codex + Claude)
- ✅ MCP Bridge live: da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
- ✅ Writeback MCP direct fonctionne
- ⏳ Brancher retrieval à TRINITY/MERLIN, débloquer quota Google

### WS4 — KIMI (Owner: Codex) ← PRIORITÉ 1
- ⚠️ Encore dépendant d'un tunnel manuel
- ⏳ Endpoint stable KIMI → api.smajor.org/api/agents/kimi/intel
- ⏳ Couper tunnel Cloudflare

### WS5 — Claude Subagents (Owner: CLAUDE ← MOI)
- ✅ Runtimes Python posés (oracle-agent, onchain-guardian)
- ✅ Contrats cockpit posés
- ⏳ Tuning sources + enrichissement risk model

### WS6 — Provider Intel (Owner: Codex + COMET + MERLIN)
- ✅ Doctrine provider intelligence posée
- ⏳ Armer mission COMET provider-watch

---

## 🔥 PRIORITÉS IMMÉDIATES (selon TRINITY 2026-04-09)

1. **PRIORITÉ 1** — Supprimer tunnel Cloudflare KIMI → connecter vers api.smajor.org
2. **PRIORITÉ 3B** — HA devient secondaire (visu/automation), S25 API = source de vérité
3. **PRIORITÉ 2** — Redéployer MERLIN sur Akash (merlin.smajor.org stable)
4. **BONUS** — COMET poids 0.5→0.65, consensus >=2 agents

---

## 🤖 AGENTS

| Agent | Rôle | Endpoint | Statut |
|-------|------|----------|--------|
| CLAUDE | Builder/Deploy/WS5 | Cowork Anthropic | 🟢 |
| TRINITY (GPT) | Vocal+Guide+GOUV4 | trinity-s25-proxy.trinitys25steph.workers.dev | 🟢 |
| MERLIN (Gemini) | Orchestrateur HA + MCP | merlin.smajor.org/mcp | 🟢 |
| COMET (Perplexity) | Watchman Radar | cloud | 🟢 |
| ARKON-5 (Gemini) | Analyseur Trading | Akash | 🟢 |
| KIMI Web3 | Signaux crypto | ⚠️ tunnel → à migrer | 🟡 |
| Gemini Orchestrator | Orchestration | Google | ⚠️ needs realignment |

---

## 🌐 ENDPOINTS

| Service | URL stable | Statut |
|---------|-----------|--------|
| Cockpit public | https://s25.smajor.org | ✅ CIBLE |
| API business | https://api.smajor.org | ✅ CIBLE |
| MERLIN MCP | https://merlin.smajor.org/mcp | ✅ CIBLE |
| TRINITY proxy | https://trinity-s25-proxy.trinitys25steph.workers.dev | 🟢 LIVE |
| MERLIN MCP live | https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp | 🟢 LIVE |
| Home Assistant | http://10.0.0.136:8123 | 🔴 LAN only |
| Cockpit Akash | DSEQ 25883220 ingress | 🟢 LIVE |

> RÈGLE: Les agents pointent vers les endpoints STABLES (smajor.org), pas vers les URL Akash temporaires.

---

## 💾 MÉMOIRE PERSISTANTE SYSTÈME

| Source | Lien | Notes |
|--------|------|-------|
| **MASTER (Google Drive)** | https://docs.google.com/document/d/1ztAi7FxXG6ZTLhqaSQX46CQJz5vMvWaNtLEM5sIVkZE/edit | NE PAS SUPPRIMER |
| Backup Drive (13 fév) | https://docs.google.com/document/d/1irqVlNvbJ35lQ87tk48I4FEIVkSLlISFTHMY9bX5j04/edit | Backup |
| Ce fichier (GitHub) | CLAUDE_CONTEXT.md (ce repo) | Index léger |
| Drive folder Claude | https://drive.google.com/drive/folders/1dgTh_D3wp5U2Fk01aFAPKF2RXdgOO7LN | Dossier Claude |
| Drive S25 mem activation | https://drive.google.com/drive/folders/1HmOfRTULJN9slFoMonJOMaWO-j1-IBOr | Phase 2 |
| Drive health monitor | https://drive.google.com/drive/folders/1TYg4-s7fLcoV3D_mibdtOURHGHD-O9-H | Monitoring |
| memory/ (GitHub) | ./memory/ dans ce repo | State local |

---

## 🔐 SÉCURITÉ — RÈGLES NON NÉGOCIABLES

- **Wallet Keplr (STEF SEULEMENT)** = seule autorité pour transactions/deployments
- **Secrets** = jamais dans repo public
- **Drive mémoire** = NE PAS SUPPRIMER
- Aucun agent ne signe de façon autonome

---

## 🧭 DOCTRINE S25

> "L'agent est un maillon interchangeable, pas la source de vérité."
> "ZERO dépendance locale — tout sur Akash ou cloud stable."
> Score actuel: 80-85% S25 compliant. Objectif: 100%.

---
*Built by Claude for Major Stef — S25 Lumière Project 2026*# 🧠 CLAUDE_CONTEXT.md — Mémoire Persistante Claude
> Dernière mise à jour: 2026-04-09
> Projet: S25 Lumière — Autonomous Multi-Agent Crypto Trading
> Major: Stef Boss (stephaneboss)

---

## 🎯 MON RÔLE
**CLAUDE = Builder / Deploy** dans le système S25 Lumière.
Je construis, déploie et optimise l'infrastructure.

---

## 📋 PRIORITÉS EN COURS (2026-04-09)

### 🔥 PRIORITÉ 1 — Supprimer tunnel Cloudflare
- [ ] Couper tunnel Cloudflare KIMI → HA
- [ ] Connecter KIMI → https://api.smajor.org/api/agents/kimi/intel

### 🔥 PRIORITÉ 3B — HA secondaire
- [ ] HA devient visu/automation seulement
- [ ] S25 API = source de vérité
- HA actuel: http://10.0.0.136:8123 (LAN only)

### 🔥 PRIORITÉ 2 — MERLIN sur Akash
- [ ] MERLIN local (10.0.0.97) → merlin.smajor.org

### ⚙️ BONUS
- [ ] COMET poids: 0.5 → 0.65
- [ ] Consensus réel: EXECUTE si >=2 agents alignés

---

## 🤖 AGENTS
| Agent | Rôle | Statut |
|-------|------|--------|
| CLAUDE | Builder/Deploy | 🟢 |
| TRINITY (GPT) | Guide Projet + TTS | 🟢 |
| MERLIN (Gemini) | Orchestrateur HA | 🔴 LOCAL |
| COMET (Perplexity) | Watchman | 🟢 |
| ARKON-5 (Gemini) | Analyseur Trading | 🟢 |
| KIMI Web3 | Signaux | 🟡 |
| Gemini | Orchestrateur | 🟢 |

---

## 🌐 ENDPOINTS
- s25.smajor.org ✅
- api.smajor.org ✅
- merlin.smajor.org ⚠️
- HA: 10.0.0.136:8123 🔴 LAN
- Cockpit Akash: :7777

---

## 🧭 DOCTRINE
> "ZERO dépendance locale. L'agent = maillon interchangeable."
> Score S25 actuel: 80-85%. Objectif: 100%.

---

## 📌 DÉMARRAGE SESSION
1. Lire ce fichier
2. Vérifier https://s25.smajor.org
3. Lire dernière conv TRINITY: chatgpt.com > Trinity S25
4. Continuer priorités

*Built by Claude for Major Stef — S25 2026*
