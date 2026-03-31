# V3 COMMAND CENTER — DISPATCH AGENTS
# S25-COMMAND-CENTER | 2026-03-31 | COMET
# Source de verite: GitHub + Drive + Wallet = Human in the loop

---

## ETAT DU SYSTEME — SNAPSHOT 2026-03-31 17h00 EDT

### Infrastructure active
- **DSEQ actif**: 26182802 — RTX 4090 @ $0.42/h — provider.ahn2-na.akash.pub
- **SDL V2 pret**: RTX 3090Ti @ $0.30/h — linuxserver/webtop:ubuntu-kde — AWAITING WALLET SIGNATURE
- **Alien local**: 3060 12GB — fallback + dev local
- **S25 machine**: 3090 24GB — pipeline principal multi-agent

### Wallet
- **Human in the loop**: STEPHANEBOSS via Keplr
- **Toute approbation critique** = signature wallet obligatoire
- **Aucun agent ne signe de facon autonome**

---

## ENDPOINTS STABLES — NE PAS CHANGER SANS VALIDATION

| Service | Endpoint stable cible | Status |
|---|---|---|
| Cockpit public | https://s25.smajor.org | CIBLE |
| API business | https://api.smajor.org | CIBLE |
| MERLIN MCP | https://merlin.smajor.org/mcp | CIBLE |
| TRINITY proxy | https://trinity-s25-proxy.trinitys25steph.workers.dev | LIVE |
| MERLIN MCP live | https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp | LIVE |
| Ninja conteneur | http://ev5hvoffv1djbdh02ddqoog9os.ingress.ahn2-na.akash.pub/ | LIVE DSEQ 26182802 |

> REGLE: Les agents pointent vers les endpoints STABLES (smajor.org).
> Le CNAME pointe vers l'ingress Akash actif. Swap de conteneur = update DNS seulement.

---

## DISPATCH AGENTS — ROLES ET REALIGNEMENT V3

### COMET (Perplexity) — Frontend + Watchman Radar
- **Role**: Execution rapide, tests endpoints, validation routage, patchs frontend
- **Endpoint owner**: https://s25.smajor.org + https://api.smajor.org
- **Actions autorisees**: deploy SDL, test liens, audit repo, doc operateur
- **Limite**: NE PAS signer transactions wallet — attendre confirmation humaine
- **Status**: ACTIF — SDL V2 prepare, Deal 3090Ti trouve ($0.30/h)

### CLAUDE — Builder + Deploy
- **Role**: Architecture, code backend, Docker, manifests Akash
- **Endpoint owner**: cockpit_lumiere.py + agents/
- **Actions autorisees**: PR, refactoring, Dockerfile, tests CI
- **Commit recent**: feat(kimi) 3h ago — actif
- **Status**: ACTIF

### GPT (TRINITY) — Orchestrateur vocal + GOUV4 Planner
- **Role**: Voice control, planning session, GOUV4 layer, interface humaine
- **Endpoint owner**: trinity_config/ + GOUV4 pipeline
- **Actions autorisees**: planification, brief quotidien, commandes vocales
- **Note**: Construit avec Steph depuis des annees — connait l'historique du projet
- **Status**: ACTIF

### GEMINI (MERLIN / ARKON-5) — Orchestrateur + Analyseur Trading
- **Role**: Orchestration HA, analyse signaux BUY/SELL/HOLD, MERLIN MCP
- **Endpoint owner**: https://merlin.smajor.org/mcp + HA automations
- **PROBLEME IDENTIFIE**: Gemini Orchestrator semble desynchronise / surcharge
- **ACTIONS REQUISES**:
  1. Reajuster le contexte Gemini avec ce fichier comme source de verite
  2. Pointer MERLIN MCP vers endpoint stable (pas URL Akash temporaire)
  3. Valider que les automations HA (s25_arkon5_buy_alert etc.) sont actives
  4. Reduire le bruit: Gemini doit orchestrer, pas tout faire seul
- **Status**: NEEDS REALIGNMENT

### KIMI Web3 — Source Signaux
- **Role**: Signaux crypto Web3, analyses marche
- **Endpoint owner**: agents/kimi_bridge — /api/kimi/ping + /api/kimi/ask
- **Commit recent**: feat(kimi) 3h ago — bridge actif
- **Status**: SIGNAL — surveiller stabilite

---

## PLAN MIGRATION V3 — ORDRE D'EXECUTION

```
ETAPE 1 — WALLET (TOI)
  > Ouvrir SDL Builder: https://console.akash.network/sdl-builder
  > Remplacer PASSWORD=REPLACE_AT_DEPLOY par ton vrai mot de passe
  > Cliquer Deploy → Keplr → Signer
  > Attendre bids providers avec RTX 3090Ti disponible
  > Accepter meilleur bid → nouveau DSEQ cree

ETAPE 2 — COMET (apres signature)
  > Recuperer nouvel ingress URL du nouveau DSEQ
  > Tester endpoint: curl http://[nouveau-ingress]/
  > Mettre a jour DNS CNAME smajor.org → nouvel ingress
  > Documenter nouveau DSEQ dans akash/deploy_ninja_supercomputer.yaml

ETAPE 3 — COMET
  > Valider que tous les agents pointent vers smajor.org (pas vers URL Akash directe)
  > Cleanup repo: retirer secrets exposes du dernier commit
  > Lancer scrub historique Git si necessaire

ETAPE 4 — WALLET (TOI)
  > Confirmer stabilite du nouveau conteneur (24h minimum)
  > Signer deletion du DSEQ 26182802 (4090 $0.42/h)

ETAPE 5 — TOUS LES AGENTS
  > Realigner Gemini Orchestrator sur nouveau contexte V3
  > Valider pipeline: Kimi signal → HA → ARKON-5 → MEXC
  > Rapport de sante complet
```

---

## SECURITE — REGLES NON NEGOCIABLES

- **Wallet = seule autorite** pour transactions, deployments, deletions
- **Secrets = jamais dans repo public** — uniquement vault local ou env injection au deploy
- **Historique Git** = doit etre scrubbed si secrets ont ete commites
- **Gemini Drive** = lecture seule pour les agents — ecriture par Steph seulement
- **Mémoire persistante Drive** = NE PAS SUPPRIMER — source de contexte long terme
- **Repo public** = SDL, docs, configs exemple, endpoints stables NON SENSIBLES
- **Repo prive / local** = mots de passe, API keys, seeds, tokens

---

## NOTE POUR GEMINI ORCHESTRATOR

Gemini — si tu lis ce fichier:

Tu n'es pas seul et tu n'as pas besoin de tout faire. Le mesh est:
- **COMET** gere le frontend, les tests, les endpoints
- **CLAUDE** gere le code et les deployments
- **GPT/TRINITY** gere la voix, le planning et la relation humaine
- **TOI** tu orchestres HA, tu analyses les signaux trading, tu geres MERLIN MCP

Ton job = **orchestrer proprement**, pas micromanager tout le systeme.
Pointe vers `https://merlin.smajor.org/mcp` — pas vers l'URL Akash temporaire.
Les automations HA sont ta surface principale. Reste dedans.

---

## PROCHAINE V3 — CIBLES

- [ ] Full Linux KDE sur RTX 3090Ti (SDL V2 pret — awaiting wallet)
- [ ] Endpoints stables smajor.org actifs et DNS pointe
- [ ] Secrets rotate et hors du repo public
- [ ] Gemini Orchestrator realigne sur ce contexte
- [ ] Pipeline Kimi → HA → ARKON → MEXC valide end-to-end
- [ ] Contrat Akash long terme signe quand stable 24h+

---
*Dispatch prepare par COMET (Perplexity) — 2026-03-31 17h00 EDT*
*Source: GEMINI_ORCHESTRATOR_BRIEF.md + Drive memoires + GitHub S25-COMMAND-CENTER*
*Human in the loop: stephaneboss via Keplr wallet*
