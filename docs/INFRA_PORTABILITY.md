# Infra Portability

## But

Garder Akash comme cible principale sans enfermer S25 dans Akash.

Le systeme doit pouvoir migrer en gardant:
- le meme conteneur
- les memes variables d'environnement
- les memes endpoints publics
- la meme memoire persistante

## Strategie

### Cible primaire

- Akash
- cockpit public
- Worker ou front public stable

### Plan B

- VM Linux classique
- bare metal
- autre cloud
- Kubernetes plus tard si utile

## Contrat runtime minimum

Pour qu'un provider soit compatible, il doit permettre:
- un conteneur Docker standard
- un volume persistant pour `MEMORY_DIR`
- des variables env
- une URL publique HTTPS
- un healthcheck sur `/api/version`

## Elements deja portables

- [Dockerfile](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/Dockerfile)
- [docker-compose.fallback.yml](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/docker-compose.fallback.yml)
- [start_cockpit_stack.sh](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/scripts/start_cockpit_stack.sh)
- Worker Cloudflare comme front stable

## Variables critiques

- `PORT`
- `MEMORY_DIR`
- `S25_SHARED_SECRET`
- `HA_URL`
- `HA_TOKEN`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `PERPLEXITY_API_KEY`
- `KIMI_API_KEY`
- `RUN_ORACLE_AGENT`
- `RUN_ONCHAIN_GUARDIAN`
- `ORACLE_POLL_SECONDS`
- `ORACLE_SYMBOLS`
- `ONCHAIN_POLL_SECONDS`
- `ONCHAIN_TOKEN_LIST`
- `GEMINI_EMBED_MODEL`

## Decision importante

Le front public stable doit rester separe du provider compute.

Donc:
- compute peut etre Akash aujourd'hui
- demain il peut etre ailleurs
- la GPT pointe toujours vers un domaine ou proxy stable

## Migration type

1. lancer le meme conteneur sur le nouveau provider
2. rebrancher le volume memory
3. verifier `/api/version`, `/api/status`, `/api/memory`, `/api/mesh/status`
4. basculer le proxy public vers le nouveau backend
5. verifier TRINITY

## Rule

Ne jamais lier la GPT directement a un host compute ephemere si un front stable existe.
