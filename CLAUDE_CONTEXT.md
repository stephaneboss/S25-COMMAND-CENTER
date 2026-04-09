# 🧠 CLAUDE_CONTEXT.md — Mémoire Persistante Claude
> Dernière mise à jour: 2026-04-09 — SESSION ACTIVE
> Projet: S25 Lumière — Autonomous Multi-Agent Crypto Trading
> Major: Stef Boss (stephaneboss) | excavaneige@gmail.com

---

## 📌 PROTOCOLE DÉMARRAGE SESSION — LIRE EN PREMIER

1. Lire ce fichier (CLAUDE_CONTEXT.md)
2. Lire la mémoire MASTER sur Google Drive:
   👉 https://docs.google.com/document/d/1ztAi7FxXG6ZTLhqaSQX46CQJz5vMvWaNtLEM5sIVkZE/edit
   (MEMOIRE IA PERSISTANTE - Stephane Major - NE PAS SUPPRIMER)
3. Vérifier TRINITY ChatGPT pour directives récentes
4. Checker s25.smajor.org + api.smajor.org/api/status

---

## 🎯 ROLE DE CLAUDE (WS5)

Claude = **Builder / Deploy** — Workstream 5
- Construit et déploie le code sur Akash
- Maintient cockpit_lumiere.py + nexus routes
- Gère les subagents: oracle-agent, onchain-guardian
- Aucune dépendance locale — tout via endpoints stables smajor.org

---

## ✅ COMMITS RÉCENTS (SESSION 2026-04-09)

| Commit | Fichier | Description |
|--------|---------|-------------|
| `e7e2329` | cockpit_lumiere.py | Priority 3B + Priority 1 — HA non-bloquant + KIMI direct |
| `e1c5be7` | s25_nexus_routes_v2.py | Priority 3B — HA secondaire non-bloquant /api/v2/* |

### Détail Priority 3B (cockpit_lumiere.py)
- `/api/status` : 1 test HA (2s timeout) au lieu de 6x5s = ZERO blocage
- Source primaire: `agents_state.json` (runtime memory)
- HA devient secondaire: `ha_status`, `ha_warning` dans la réponse
- **LIVE CONFIRMÉ**: api.smajor.org/api/status retourne `ha_status:"unreachable"` + pipeline MULTI_SOURCE

### Détail Priority 1 (cockpit_lumiere.py)
- Nouveau endpoint `POST /api/kimi/intel` — KIMI signal direct sans Cloudflare tunnel
- Nouveau endpoint `GET /api/kimi/intel` — lecture cache signaux KIMI
- Auth: `_trinity_auth()` (X-S25-Secret ou HA_TOKEN)
- `mode: "direct_no_tunnel"` dans la réponse

### Détail Priority 3B (s25_nexus_routes_v2.py)
- `/api/v2/status` : HA 2s timeout, `ha_warning` + `ha_status.source` dans data dict
- `/api/v2/infra` : HA 2s timeout, `ha.source` + `ha.warning` dans return jsonify

---

## 🏗️ INFRASTRUCTURE

| Composant | Endpoint | État |
|-----------|----------|------|
| Cockpit | s25.smajor.org | ✅ ONLINE |
| API | api.smajor.org | ✅ ONLINE |
| MERLIN MCP | merlin.smajor.org/mcp | ⚠️ A redéployer |
| Home Assistant | http://10.0.0.136:8123 | ⚠️ LAN only (normal) |
| Akash DSEQ actif | 26182802 | RTX 4090 $0.42/h |
| SDL V2 ready | — | RTX 3090Ti $0.30/h (attente sig Keplr) |

---

## 🤖 AGENTS MESH S25

| Agent | Rôle | Plateforme |
|-------|------|-----------|
| TRINITY | Commander / Guide | ChatGPT GPT |
| MERLIN | Orchestrateur HA | Gemini Gems |
| COMET | Watchman Radar | Perplexity/Harpa |
| ARKON-5 | Signal Engine | s25.smajor.org |
| KIMI K2 | Web3 Signal | Akash Network |
| CLAUDE | Builder / Deploy | Anthropic Cowork |
| GOUV4 | Planificateur | GPT-4 |

---

## 📋 WORKSTREAMS

| WS | Nom | Status | Notes |
|----|-----|--------|-------|
| WS1 | Akash Runtime | ACTIF | DSEQ 26182802, V3 migration pending (Keplr) |
| WS2 | TRINITY/GPT | ONLINE | Guide projet, check ChatGPT |
| WS3 | Gemini/MERLIN | PENDING | Redéploiement Akash requis |
| WS4 | KIMI Direct | DONE | /api/kimi/intel endpoint live (Priority 1) |
| WS5 | Claude Subagents | ACTIF | oracle-agent + onchain-guardian a tuner |
| WS6 | Provider Intel | BACKLOG | — |

---

## 🚀 PROCHAINES PRIORITÉS

1. **V3 Migration Akash**: Stef signe le SDL V2 via Keplr (RTX 3090Ti $0.30/h)
2. **MERLIN redéploiement**: merlin.smajor.org/mcp doit être stable sur Akash
3. **WS5 Bonus**: COMET weight 0.5->0.65, consensus >=2 agents actif
4. **oracle-agent**: Enrichir sources + tuner risk model
5. **onchain-guardian**: Tuner sources onchain

---

## 🔑 DOCTRINE S25

> "L'agent est un maillon interchangeable, pas la source de vérité."
> ZERO dépendance locale. Tout via endpoints stables (smajor.org).
> HA = secondaire. agents_state.json = runtime memory.

---

## 🔗 LIENS CLÉS

- GitHub: https://github.com/stephaneboss/S25-COMMAND-CENTER
- Cockpit: https://s25.smajor.org
- API Status: https://api.smajor.org/api/status
- KIMI Intel: https://api.smajor.org/api/kimi/intel
- Nexus V2: https://api.smajor.org/api/v2/status
- Google Drive MASTER: https://docs.google.com/document/d/1ztAi7FxXG6ZTLhqaSQX46CQJz5vMvWaNtLEM5sIVkZE/edit
