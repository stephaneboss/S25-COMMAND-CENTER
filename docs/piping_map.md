# S25 Lumiere -- Piping Map

> **"L'usine a ponts de rat"** -- ~$83/mois en subscriptions = 10-20k$/mois en compute brut

## Architecture Generale

```
+-----------------------------------------------------------------------+
|                    S25 LUMIERE -- PIPELINE                            |
+-----------------------------------------------------------------------+
|                                                                       |
|  DATA SOURCES (Gratuit 100%)                                          |
|  +----------+ +-----------+ +----------+ +------------+              |
|  |CoinGecko | |Fear&Greed | |Reddit RSS| |Ollama Local|              |
|  |  5 min   | |  15 min   | |  30 min  | |   60 min   |              |
|  +----+-----+ +-----+-----+ +----+-----+ +------+-----+              |
|       +-------------+-----------+--------------+                      |
|                     |                                                 |
|           agent_loop.py (autonome)                                   |
|                     |                                                 |
|           +---------v----------+                                      |
|           |   S25 COCKPIT      |  <- Akash DSEQ 25822281             |
|           | cockpit_lumiere.py |                                      |
|           | /api/intel         |                                      |
|           | /api/signal        |                                      |
|           | /api/threat        |                                      |
|           | /api/status        |                                      |
|           +---------+----------+                                      |
|                     |                                                 |
+---------------------+-----------------------------------------------+
|  AGENTS (Chat Subscriptions ~$30/mois chacun)                        |
|                     |                                                 |
|  +-------+   +------v------------------------------+                 |
|  | KIMI  +-->+ TRINITY (GPT orchestrateur)          |                 |
|  |Web3   |   | Commands vocales Stef                |                 |
|  |Scanner|   | OpenAPI Actions -> Cockpit           |                 |
|  +-------+   +------+------------------------------+                 |
|                     |                                                 |
|         +-----------+-----------+                                     |
|         |           |           |                                     |
|  +------v------+ +--v---------+ +----v------+                        |
|  |   ARKON     | |   MERLIN   | |   COMET   |                        |
|  | (Claude)    | |  (Gemini)  | |(Perplexity|                        |
|  | Analyste    | | Validateur | | Watchman) |                        |
|  | claude CLI  | | web search | | comet_    |                        |
|  +------+------+ +------+-----+ | bridge    |                        |
|         |               |       +----+------+                        |
|         +---------------+            |                               |
|                 |                    | threat_level T0-T3            |
|         +-------v--------+           |                               |
|         | RiskGuardian   |<----------+                               |
|         |risk_guardian.py|                                           |
|         +-------+--------+                                           |
|                 |                                                    |
|         +-------v--------+                                           |
|         | MEXC Executor  |                                           |
|         |mexc_executor.py|  <- dry_run=True par defaut               |
|         +----------------+                                           |
|                                                                      |
+----------------------------------------------------------------------+
```

## Budget Stack ($83/mois = 120-240x ROI vs API directes)

| Agent | Outil | Cout | Capacite |
|-------|-------|------|----------|
| TRINITY | ChatGPT Plus | ~$20/mois | GPT-4o unlimited, voice, actions |
| ARKON | Claude Pro + Code | ~$20/mois | Claude 3.5 unlimited + CLI agent |
| MERLIN | Gemini Advanced | ~$22/mois | Gemini 1.5 Pro + web search |
| COMET | Perplexity Pro | ~$20/mois | Real-time web, unlimited |
| KIMI | Kimi Pro | ~$1/mois | 1M context, web3 scan |
| **DATA** | CoinGecko/Reddit/Ollama | **$0** | Infinite loops |
| **INFRA** | Akash Network | ~$5/mois | Container 24/7 |
| **TUNNEL** | Cloudflare (gratuit) | **$0** | HTTPS tunnel |

## Flux Happy Path (signal KIMI -> trade MEXC)

```
1. KIMI detecte setup -> genere signal JSON
2. POST -> Cloudflare tunnel -> kimi_proxy.py -> HA webhook
3. HA -> input_text.ai_prompt = signal
4. TRINITY lit le signal -> appelle /api/signal cockpit
5. Cockpit recoit -> notifie ARKON via claude CLI
6. ARKON analyse -> APPROVE/HOLD
7. Si APPROVE -> MERLIN confirme via web search
8. MERLIN CONFIRM -> RiskGuardian calcule position size
9. RiskGuardian OK -> MEXC Executor (dry_run=True)
10. Log du trade simule -> Dashboard cockpit
11. COMET monitore -> threat level T0 maintenu
12. TRINITY informe Stef -> vocal ou dashboard
```

## Nouveaux outils (2026-03)

### Claude Code (ARKON sur Akash)
```bash
# Sur le serveur Akash, ARKON peut maintenant:
claude "Analyse le dernier signal KIMI dans /tmp/agent_loop.log et donne une recommandation"
claude --print "Review agents/risk_guardian.py pour bugs potentiels"
```

### Codex CLI (TRINITY sur laptop)
```bash
# Sur le laptop Stef, TRINITY via Codex:
codex "Genere une requete API pour le cockpit S25 et affiche le status"
codex "Aide-moi a debugger comet_bridge.py -- affiche les dernieres erreurs"
```

## Prochaines etapes

- [x] TRINITY GPT config (OpenAPI spec + system prompt)
- [x] COMET Bridge v2.1 (crash fixes)
- [x] COMET system prompt (reactif, as de l'air)
- [x] agent_loop.py (boucle autonome gratuite)
- [x] ARKON config (analyste profond)
- [x] MERLIN config (validateur web)
- [x] KIMI config (scanner Web3 1M tokens)
- [ ] HA_TOKEN -> Akash env vars (pour push entites HA)
- [ ] Tester pipeline end-to-end en dry_run
- [ ] MEXC live mode (dry_run -> False, quand pret)
- [ ] Claude Code agent script pour ARKON autonome
- [ ] Codex integration script pour TRINITY laptop
