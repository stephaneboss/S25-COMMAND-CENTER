# Gemini Foundation

## Positionnement

Gemini est un pilier long terme de S25.

Pourquoi:
- Google est une base stable de long terme
- Gemini tient bien la charge sur validation, structuration, retrieval et embeddings
- AI Studio + Gemini API restent une base fiable pour construire la memoire et la gouvernance

## Doctrine S25

- TRINITY orchestre
- GOUV4 route
- MERLIN valide
- Gemini fournit aussi la couche semantique de memoire/recherche

## Doctrine web-native

Pour S25, Gemini doit etre traite comme une pile web-native:

1. `Interactions API` pour les sessions outillees
2. `mcp_server` pour brancher MERLIN sur le mesh S25
3. `google_search` pour grounding web temps reel
4. `url_context` pour docs, repos, pages produit, changelogs
5. `Live API` pour les futures surfaces vocales temps reel

Ce que cela veut dire:
- MERLIN lit le mesh via MCP
- Gemini va sur le web via `google_search`
- Gemini lit des pages cibles via `url_context`
- TRINITY garde l'orchestration
- COMET garde le travail navigateur et la veille web

## Regles de combinaison

- `Remote MCP`:
  - fonctionne avec `Interactions API`
  - demande un serveur `streamable-http`
  - ne marche pas encore avec les modeles `Gemini 3`
- `URL context`:
  - utile pour docs, GitHub, changelogs, pages produit
  - ne se combine pas encore avec le function calling classique
- `Grounding with Google Search`:
  - utile pour l'info recente et les citations
  - peut se combiner avec `url_context`
- `Live API`:
  - bonne base pour le vocal temps reel
  - le function calling y est manuel cote client

## Base live S25

- MCP public live:
  - `https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp`
- DSEQ:
  - `25878071`
- Etat:
  - handshake public OK
  - writeback MCP direct OK
  - `Interactions + mcp_server` encore bloque cote Google sur le projet courant

## Priorites Gemini

1. validation via MERLIN
2. retrieval / semantic memory
3. embeddings sur docs, memory, logs, missions
4. support aux analyses trading
5. grounding web et lecture de docs officielles
6. futur vocal temps reel via Live API

## Base implementee

Fichier:
- [gemini_memory.py](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/agents/gemini_memory.py)

Role:
- indexer `memory/SHARED_MEMORY.md`
- indexer `memory/agents_state.json`
- indexer `memory/PROVIDER_WATCH.md`
- indexer `memory/provider_watch_snapshot.json`
- indexer les docs structurantes `PROVIDER_INTELLIGENCE`, `COMET_WORK_SYSTEM`, `AGENT_REGISTRY`, `WORKSTREAM_BOARD`
- produire un index local `memory/gemini_memory_index.json`
- permettre une recherche semantique basique

Variables:
- `GEMINI_API_KEY`
- `GEMINI_EMBED_MODEL=gemini-embedding-001`
- `MEMORY_DIR`
- `GEMINI_INTERACTION_MODEL=gemini-2.5-flash`

## Commandes

Rebuild index:

```bash
python -m agents.gemini_memory
```

Search memory:

```bash
python -m agents.gemini_memory --query "provider watch gemini embeddings" --top-k 5
```

Test handshake MCP public:

```bash
python scripts/test_merlin_mcp_handshake.py https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
```

Test Gemini live via Interactions:

```bash
python scripts/run_gemini_merlin_interaction.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
```

Writeback MCP direct:

```bash
python scripts/write_merlin_mcp_feedback.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp --summary "MERLIN MCP bridge live on Akash. Public handshake validated on dseq 25878071."
```

## Sources officielles

- Interactions API:
  - https://ai.google.dev/gemini-api/docs/interactions
- URL context:
  - https://ai.google.dev/gemini-api/docs/url-context
- Grounding with Google Search:
  - https://ai.google.dev/gemini-api/docs/google-search
- Tool use with Live API:
  - https://ai.google.dev/gemini-api/docs/live-api/tools
- Gemini API libraries:
  - https://ai.google.dev/gemini-api/docs/libraries
- Release notes:
  - https://ai.google.dev/gemini-api/docs/changelog

## Prochaines etapes

1. brancher ce retrieval dans TRINITY / MERLIN
2. indexer aussi:
   - runbooks
   - logs agents
   - missions history
   - docs architecture
3. faire tourner cette indexation sur Akash plutot que sur laptop
4. utiliser cette memoire pour la veille provider et les validations MERLIN
5. debloquer `Interactions + mcp_server` sur le projet Google courant
6. ajouter `google_search` et `url_context` dans les flows MERLIN une fois le point `Interactions` stable
