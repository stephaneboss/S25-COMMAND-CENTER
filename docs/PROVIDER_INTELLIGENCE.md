# Provider Intelligence

## But

Suivre les nouveautes des fournisseurs importants pour que S25 s'optimise avec le marche au lieu de rester fige.

## Regle

On suit uniquement les sources officielles ou primaires:
- OpenAI
- Google AI / Gemini
- Anthropic
- Perplexity / Comet

## OpenAI

### Ce qui compte

- migration continue vers `Responses API`
- outils natifs pour agents
- pression a rester compatible MCP / agent workflows

### Sources

- Changelog: [OpenAI API changelog](https://platform.openai.com/docs/changelog)
- Migration: [Assistants migration guide](https://platform.openai.com/docs/guides/assistants)
- Tools / Responses: [New tools and features in the Responses API](https://openai.com/index/new-tools-and-features-in-the-responses-api/)

### Lecture S25

- TRINITY doit rester sur un modele compatible Actions / Responses
- nos integrations GPT doivent privilegier les patterns agents modernes
- il faut rester souple, car OpenAI change vite

## Google / Gemini

### Ce qui compte

- Gemini est une base long terme stable
- `gemini-embedding-001` est la brique memoire la plus interessante pour S25
- Google pousse aussi fort l'audio, les tools multiples et les context tools
- Google pousse une vraie pile web-native:
  - `Interactions API`
  - `mcp_server`
  - `google_search`
  - `url_context`
  - `Live API`

### Sources

- Release notes: [Gemini API changelog](https://ai.google.dev/gemini-api/docs/changelog)
- Embeddings GA: [Gemini Embedding now generally available](https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/)
- Interactions API: [Interactions API](https://ai.google.dev/gemini-api/docs/interactions)
- URL context: [URL context](https://ai.google.dev/gemini-api/docs/url-context)
- Google Search grounding: [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- Live API tools: [Tool use with Live API](https://ai.google.dev/gemini-api/docs/live-api/tools)
- Official SDK: [Gemini API libraries](https://ai.google.dev/gemini-api/docs/libraries)

### Lecture S25

- MERLIN doit etre plus qu'un validateur secondaire
- Gemini doit tenir la memoire semantique, la validation et le retrieval
- c'est un investissement durable
- le bon modele pour `remote MCP` aujourd'hui est `gemini-2.5-flash`
- `Gemini 3` ne doit pas etre la base MCP tant que Google ne l'a pas ouvert
- `google_search + url_context` est une combinaison forte pour la veille provider
- `Live API` est la bonne cible pour les futures surfaces vocales temps reel

## Anthropic / Claude

### Ce qui compte

- gros contexte
- compatibilite OpenAI-like sur l'API
- valeur forte pour backend, code, YAML, review

### Sources

- API release notes: [Anthropic API release notes](https://docs.anthropic.com/en/release-notes/api)
- Model lifecycle: [Anthropic model deprecations](https://docs.anthropic.com/en/docs/about-claude/model-deprecations)

### Lecture S25

- Claude reste la meilleure force de travail backend / infra / review
- il faut garder Claude et Codex organises pour ne pas doubler les efforts

## Perplexity / Comet

### Ce qui compte

- Comet est plus qu'un simple navigateur: automatisation, contexte cross-tabs, workflows
- Comet Enterprise ajoute des controles d'autorisations, politiques, deployment MDM, et gouvernance d'actions
- `Shortcuts` et `Tasks` sont les briques les plus interessantes pour industrialiser la veille provider
- `Voice Mode` peut accelerer les checks manuels quand on opere S25 en vocal

### Sources

- Comet product page: [Perplexity Comet](https://comet.perplexity.ai/)
- Comet Enterprise: [Perplexity Comet Enterprise](https://www.perplexity.ai/enterprise/comet-new)
- Assistant permissions: [Control what Comet Assistant can use](https://comet-help.perplexity.ai/en/articles/12658082-control-what-comet-assistant-can-use)
- Voice mode: [Comet Voice Mode](https://comet-help.perplexity.ai/en/articles/13860420-voice-mode)
- Work guide: [Perplexity at Work PDF](https://r2cdn.perplexity.ai/pdf/pplx-at-work.pdf)

### Lecture S25

- COMET doit etre exploite pour la veille et l'automatisation du travail web
- pas comme cerveau principal, mais comme moteur de recherche, contexte et action web
- si la section Work est mature, elle peut nourrir le flux de nouveautes providers
- `Shortcuts` est aujourd'hui la meilleure base pour des routines provider-watch reutilisables
- les controles d'autorisations Assistant doivent rester stricts pour les surfaces sensibles

## Decision strategique

### Pilier long terme

- Google / Gemini

### Orchestrateur produit

- OpenAI / TRINITY

### Force backend

- Claude + Codex

### Veille et automation web

- Perplexity / Comet

## Application a S25

1. Gemini tient la memoire semantique et la validation
2. TRINITY orchestre les actions et le front vocal
3. Claude et Codex tiennent l'usine backend
4. Comet surveille le web, les nouveautes et les workflows repetitifs

## Routine recommande

- relire les changelogs officiels chaque semaine
- documenter les impacts S25 quand une nouveaute change:
  - agents
  - models
  - embeddings
  - tools
  - permissions
- construire un snapshot local avec:
  - `pwsh -File scripts/build_provider_watch_snapshot.ps1`
- armer une mission COMET de veille provider avec:
  - `pwsh -File scripts/arm_provider_watch_mission.ps1`
- garder COMET comme watchtower web et MERLIN comme validateur structurel
