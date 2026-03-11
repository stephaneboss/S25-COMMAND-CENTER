# Claude / Codex Handoff

## But

Eviter que Claude et Codex refassent les memes analyses ou repartent d'un etat flou.

Ce document est la passerelle de travail entre:
- Claude = backend, architecture, review, sous-agents, codebase
- Codex = integration, outillage, runtime, publication, orchestration repo

## Regles de fonctionnement

1. Toute avancee structurante doit laisser une trace ici ou dans les docs cibles.
2. Avant de lancer un gros chantier, lire:
   - [AGENT_REGISTRY.md](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/docs/AGENT_REGISTRY.md)
   - [AKASH_AUTONOMY_TARGET.md](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/docs/AKASH_AUTONOMY_TARGET.md)
   - [TRINITY_ACTIVATION_RUNBOOK.md](C:/Users/Steph/Documents/Playground/S25-COMMAND-CENTER-git/docs/TRINITY_ACTIVATION_RUNBOOK.md)
3. Toute migration hors laptop doit etre documentee comme telle.
4. Toute action live doit indiquer:
   - commit
   - image
   - endpoint
   - etat attendu

## Repartition recommande

### Claude

- backend Python
- design des sous-agents
- quality gates
- refactors structurels
- hardening du cockpit
- agents `oracle`, `guardian`, `risk`, `treasury`

### Codex

- integration GPT / Actions
- workers / proxy / Cloudflare
- SDL Akash
- outillage operable
- docs de runbook
- synchronisation du vrai etat runtime

## Etat courant de reference

- endpoint public stable:
  - `https://trinity-s25-proxy.trinitys25steph.workers.dev`
- origin public courant:
  - `http://fpog7pbvepbkrfae1529ics23k.ingress.cap-test-compute.com`
- DSEQ cockpit public courant:
  - `25883220`
- bridge MCP MERLIN live:
  - `https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp`
- DSEQ merlin-mesh:
  - `25878071`
- runtime cible:
  - Akash first
- GPT:
  - TRINITY live
- agents deja traces:
  - TRINITY
  - COMET
  - KIMI
  - ORACLE
  - ONCHAIN_GUARDIAN

## Chantiers ouverts

1. republish GPT live si l'editeur ChatGPT repond
2. verifier la lecture TRINITY du backend public `25883220`
3. ORACLE et ONCHAIN_GUARDIAN en live sur Akash
4. KIMI hors tunnel manuel
5. Gemini semantic memory reliee a TRINITY / MERLIN
6. debloquer Gemini `Interactions + mcp_server` sur le projet Google courant
7. garder HA en lateral, pas comme point de verite principal du mesh

## Doctrine live

- Le point de verite S25 est le mesh Akash, pas Home Assistant.
- Home Assistant reste une chaine d'execution laterale a preserver sans casser l'existant.
- Toute remise en place doit viser:
  - `TRINITY -> cockpit public -> MERLIN MCP -> missions -> retour mesh`
- La mission de validation courante est:
  - `mission-09e3b85db8`
  - intent: `Validate S25 multi-agent handshake: TRINITY issues mission, MERLIN confirms mesh readiness, COMET keeps provider watch intact.`

## Commandes operateur

- handshake MCP:
  - `python scripts/test_merlin_mcp_handshake.py https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp`
- Gemini live:
  - `python scripts/run_gemini_merlin_interaction.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp`
- writeback MCP:
  - `python scripts/write_merlin_mcp_feedback.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp --summary "MERLIN MCP bridge live on Akash. Public handshake validated on dseq 25878071."`

## Anti-duplication

Avant de coder:
- verifier si un helper existe deja dans `agents/`, `scripts/`, `docs/`
- si un chantier est en cours, documenter la nouvelle decision plutot que repartir de zero
- si Claude ou Codex changent la doctrine, mettre a jour ce fichier
