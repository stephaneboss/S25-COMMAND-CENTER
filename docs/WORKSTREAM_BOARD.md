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
- cockpit Akash present
- stack `cockpit + oracle + guardian` codee
- sandbox update encore a finaliser

Next:
- update sandbox
- verifier `mesh/status`
- verifier `status`

### WS2 - GPT / TRINITY

Owner:
- Codex

But:
- zero popup de confirmation
- statut vocal coherent

Etat:
- spec `x-openai-isConsequential: false`
- backend status corrige en code
- republish UI a refaire si l'editeur repond

Next:
- republier GPT
- verifier nouveau thread vocal

### WS3 - Gemini / MERLIN

Owner:
- Codex + Claude

But:
- faire de Gemini le pilier stable long terme

Etat:
- fondation embeddings ajoutee
- GOUV4 connait retrieval / semantic memory

Next:
- brancher retrieval a TRINITY / MERLIN
- indexer docs, logs, missions

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

## Blockers

- editeur GPT ChatGPT instable dans le navigateur pilote
- Akash Console lourde a piloter via le Chrome debug
- workflow lint CI du repo encore rouge pour des dettes legacy non liees aux derniers commits
