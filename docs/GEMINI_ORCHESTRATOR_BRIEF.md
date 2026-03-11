# Gemini Orchestrator Brief

## Verite officielle

- `smajor.org` est le domaine parapluie officiel
- `S25 Lumiere` est le backend central
- `MERLIN MCP` est la surface tools et validation
- `Home Assistant` reste une chaine laterale
- le point de verite operationnel est le mesh S25, pas un WebUI vide

## Endpoints utiles

- cockpit public: `https://trinity-s25-proxy.trinitys25steph.workers.dev`
- cockpit public cible domaine: `https://s25.smajor.org`
- api business cible: `https://api.smajor.org`
- MERLIN MCP live: `https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp`
- MERLIN MCP cible domaine: `https://merlin.smajor.org/mcp`

## Architecture a respecter

Flux principal:

`User -> app/public portal -> api.smajor.org or s25.smajor.org -> S25 mesh -> backends / agents -> response`

## Contraintes

- Akash-first
- GitHub = source de verite
- Cloudflare = facade stable
- ne pas reintroduire une dependance forte au laptop
- ne pas traiter le WebUI MERLIN comme gateway principale

## Taches attendues

1. Clarifier l'arborescence fonctionnelle du mega site
2. Aider a definir les modules business prioritaires
3. Garder la distinction:
   - facade web
   - backend S25
   - mesh agents
4. Recommander les prochains MVP sans casser la base existante
