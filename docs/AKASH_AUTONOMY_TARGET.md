# Akash Autonomy Target

## Objectif

Construire un S25 qui reste operationnel si:
- le laptop Dell est ferme
- Chrome local est coupe
- aucun script local n'est relance manuellement

Le laptop reste une station d'admin et de dev, pas une piece obligatoire du runtime principal.

## Cible 120 secondes

En moins de 120 secondes apres un redemarrage Akash, le systeme doit pouvoir:
- repondre sur `api/version`
- repondre sur `api/memory`
- repondre sur `api/mesh/status`
- repondre sur `api/router/report`
- accepter une mission `COMET`
- conserver la memoire et l'etat runtime

## Hierarchie de runtime

### Tier 1 - obligatoire, autonome

Doit vivre sur Akash ou derriere un endpoint public stable:
- cockpit S25
- TRINITY bridge public
- MERLIN MCP bridge public
- memory API
- mission queue
- feed COMET
- routage GOUV4

### Tier 2 - fortement recommande

Doit etre migrable hors laptop rapidement:
- oracle-agent
- onchain-guardian
- scanner KIMI ou son endpoint de collecte
- bridge Home Assistant resilient

### Tier 3 - fallback local acceptable

Peut rester local tant que le coeur tient sans lui:
- Dell-Linux Ollama
- outils Codex/CLI
- scripts de debug et de maintenance

## Regles de conception

1. Une fonction critique ne doit jamais exister sur une seule machine locale.
2. Toute URL consommee par la GPT doit etre stable, publique et TLS propre.
3. Toute mission creee par TRINITY doit survivre a la fermeture du laptop.
4. Les etats `agents_state` et `comet_feed` doivent rester lisibles sans runtime local.
5. Un composant local utile doit etre classe comme `fallback`, pas comme prerequis du boot.

## Etat actuel

Base officielle conservee sur Akash:
- `25878071` = `s25-merlin-mesh` officiel
- `25883220` = cockpit public courant derriere le Worker public
- `25838342` = cockpit principal historique conserve
- `25822281` = cockpit secondaire / sandbox de pouvoir
- `25882621` = cockpit secondaire v2 sur `provider.dal.leet.haus`
- `25708774` = module GPU laisse intact

Deja autonomes:
- cockpit Akash
- endpoint stable `workers.dev`
- bridge MCP MERLIN live sur Akash
- GPT TRINITY live
- memory, mesh, router, missions, COMET feed
- `api/status` public corrige via le cockpit `25883220`

Encore dependants a reduire:
- KIMI tunnel / scanner
- Dell-Linux `agent_loop.py`
- injection et verification continue de `HA_TOKEN`
- migration hors de l'ancien cockpit historique `25838342`

## Prochaines migrations recommandees

1. Deployer `oracle-agent` sur Akash
2. Deployer `onchain-guardian` sur Akash
3. Garder `merlin-mesh` (`25878071`) comme module Akash separe officiel
4. Donner a COMET une boucle plus autonome que la simple mission queue
5. Mettre KIMI derriere un endpoint stable au lieu d'un tunnel manuel
6. Garder Dell-Linux uniquement pour l'inference locale additionnelle
7. Faire tourner `Gemini Ops Daemon` sur Akash pour surveiller `Interactions + MCP` sans laptop
