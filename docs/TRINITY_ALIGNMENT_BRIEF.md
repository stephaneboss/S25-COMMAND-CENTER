# TRINITY Alignment Brief

## Vision officielle

- `smajor.org` devient la facade business et operations
- `S25 Lumiere` reste le backend central
- `s25-merlin-mesh` reste la gateway MCP / agents principale pour MERLIN
- le WebUI MERLIN n'est pas la source de verite

## Regle de raisonnement

Quand TRINITY parle de l'etat MERLIN:

1. verifier le mesh S25
2. verifier les backends
3. verifier le MCP
4. traiter le WebUI comme optionnel

## Mapping metier

- site / vitrine -> `www.smajor.org`
- cockpit / backend visible -> `s25.smajor.org`
- API -> `api.smajor.org`
- MERLIN MCP -> `merlin.smajor.org`
- branch IA / produits -> `majorai.smajor.org` ou `ai.smajor.org`

## Comportement attendu

- ne pas presenter Home Assistant comme coeur du systeme
- ne pas presenter le WebUI MERLIN comme gateway
- presenter `S25` comme couche de coordination industrielle
- presenter les agents comme responsables de fonctions de l'entreprise
