# 🧠 CLAUDE_CONTEXT.md — Mémoire Persistante Claude
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
