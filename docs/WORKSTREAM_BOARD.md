# Workstream Board

## But

Vue courte des chantiers actifs pour piloter S25 comme une entreprise IA.

## Active

### WS1 - Runtime Akash

Owner:
- Codex

But:
- sortir le coeur S25 du laptop

Etat (audit 2026-04-14, Claude Opus 4.6):
- DSEQ historiques **TOUS FERMES** (expiration escrow):
  - `25883220` public -> closed
  - `25838342` prod -> closed
  - `25882621` v2 -> closed
  - `25878071` merlin-mesh -> closed (container `da0m4r4tu5...ingress.akashprovid.com` retourne 404)
  - `25708774` GPU -> closed
- DSEQ reels actifs (6 deployments, 5 leases ouverts):
  - `25822281` (provider akash1v4m...yykk) -> lease-status 404, provider mort, a fermer
  - `26028154` (jjozzietech) -> `s25-cockpit` LIVE mais pointe sur HA URL `nabu.casa` expiree (ghost)
  - `26034859` (jjozzietech) -> doublon ghost de 26028154
  - `26128127` (antonaccimattia) -> `service-1` 502 Bad Gateway, a fermer
  - `26129577` (akash15fq) -> deployment active mais lease CLOSED, a cleaner
  - `26270769` (team-michel:31554 TCP) -> **S25 Lumiere Cockpit v2.0 LIVE**, build_sha 290ab31, HA connected, MERLIN online, GOUV4 alive. C'est le NOUVEAU public Akash de facto.
- MERLIN MCP restaure via cockpit reverse-proxy `cockpit-alien.smajor.org/mcp` (commit `a3b1465`) en attendant redeploy Akash proprement.

Next:
- fermer proprement les 5 DSEQ morts/ghosts pour recuperer l escrow (~1.2 AKT total)
- wirer `s25.smajor.org` worker sur `http://provider.team-michel.com:31554` OR redeployer un cockpit HTTPS-ingress propre
- rebuilder image docker `ghcr.io/stephaneboss/s25-command-center:main` (HEAD a3b1465) et redeployer merlin-mesh + cockpit via un SDL propre
- wrangler secret put ORIGIN_BASE sur workers `merlin-s25-proxy` + `trinity-s25-proxy` (requiert CLOUDFLARE_API_TOKEN)

### WS2 - GPT / TRINITY

Owner:
- Codex

But:
- zero popup de confirmation
- statut vocal coherent

Etat:
- spec `x-openai-isConsequential: false`
- backend status corrige en code et live sur le Worker public
- republish UI a refaire si l'editeur repond
- endpoint cockpit stable toujours derriere `workers.dev`

Next:
- republier GPT
- verifier nouveau thread vocal
- verifier que TRINITY lit bien `MESH_READY` et `READY` depuis le nouveau public

### WS3 - Gemini / MERLIN

Owner:
- Codex + Claude

But:
- faire de Gemini le pilier stable long terme

Etat:
- fondation embeddings ajoutee
- GOUV4 connait retrieval / semantic memory
- provider watch indexable dans la memoire Gemini
- bridge MCP live sur Akash:
  - `https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp`
- writeback MCP direct fonctionne
- Gemini `Interactions + mcp_server` encore bloque cote Google

Next:
- brancher retrieval a TRINITY / MERLIN
- indexer docs, logs, missions
- exploiter `PROVIDER_WATCH` et `PROVIDER_INTELLIGENCE` dans MERLIN
- debloquer quota/projet Google pour `Interactions`

### WS4 - KIMI

Owner:
- Codex

But:
- KIMI = pompe a data Web3

Etat:
- recadre dans prompts/docs
- mission KIMI active
- encore dependant d'un tunnel manuel

Next:
- endpoint stable KIMI
- writeback memory/state

### WS5 - Claude Subagents

Owner:
- Claude

But:
- rendre `oracle-agent` et `onchain-guardian` productifs

Etat:
- runtimes Python poses
- contrats cockpit poses

Next:
- tuning sources
- enrichissement risk model

### WS6 - Provider Intel

Owner:
- Codex + COMET + MERLIN

But:
- suivre les nouveautes critiques providers sans attendre les surprises

Etat:
- doctrine provider intelligence posee
- snapshot local provider a present generable
- mission COMET provider-watch a present armable
- base Akash nettoyee, sans les DSEQ `Unknown` recents
- mission handshake multi-agent queuee:
  - `mission-09e3b85db8`
  - `TRINITY -> MERLIN -> COMET`
  - sans modification des chaines HA existantes

Next:
- armer la mission COMET provider-watch
- relire les impacts Gemini / OpenAI / Comet dans TRINITY
- brancher le snapshot provider dans la memoire semantique Gemini

## Blockers

- editeur GPT ChatGPT instable dans le navigateur pilote
- Akash Console lourde a piloter via le Chrome debug
- workflow lint CI du repo encore rouge pour des dettes legacy non liees aux derniers commits
