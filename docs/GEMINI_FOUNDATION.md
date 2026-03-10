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

## Priorites Gemini

1. validation via MERLIN
2. retrieval / semantic memory
3. embeddings sur docs, memory, logs, missions
4. support aux analyses trading

## Base implementee

Fichier:
- [gemini_memory.py](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/agents/gemini_memory.py)

Role:
- indexer `memory/SHARED_MEMORY.md`
- indexer `memory/agents_state.json`
- produire un index local `memory/gemini_memory_index.json`
- permettre une recherche semantique basique

Variables:
- `GEMINI_API_KEY`
- `GEMINI_EMBED_MODEL=gemini-embedding-001`
- `MEMORY_DIR`

## Commandes

Rebuild index:

```bash
python -m agents.gemini_memory
```

## Prochaines etapes

1. brancher ce retrieval dans TRINITY / MERLIN
2. indexer aussi:
   - runbooks
   - logs agents
   - missions history
   - docs architecture
3. faire tourner cette indexation sur Akash plutot que sur laptop
