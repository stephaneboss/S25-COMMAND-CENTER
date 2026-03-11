# Workstream Board

## But

Vue courte des chantiers actifs pour piloter S25 comme une entreprise IA.

## Active

### WS1 - Runtime Akash

Owner:
- Codex

But:
- sortir le coeur S25 du laptop

Etat:
- endpoint Worker stable en place
- cockpit Akash public courant present: `25883220`
- cockpit Akash principal historique conserve: `25838342`
- cockpit Akash secondaire conserve: `25822281`
- cockpit Akash secondaire v2 cree: `25882621`
- module `merlin-mesh` officiel live: `25878071`
- module GPU conserve: `25708774`

Next:
- garder la separation prod / sandbox sans multiplier les faux builds
- garder `25883220` comme public tant qu'il reste sain
- verifier `mesh/status`
- nettoyer les dependances HA qui ne doivent pas redevenir le point de verite

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
