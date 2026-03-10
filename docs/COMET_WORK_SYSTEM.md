# COMET Work System

## But

Exploiter Comet comme poste de veille et d'action web pour S25 sans en faire le cerveau principal.

## Principe

- TRINITY orchestre
- MERLIN valide
- COMET surveille et collecte
- GOUV4 decide si une nouveaute merite integration

## Pourquoi maintenant

Comet a des briques utiles pour nous:
- `Shortcuts` pour des workflows repetables
- `Tasks` pour des recherches et checks recurrentes
- `Voice Mode` pour piloter des actions navigateur plus naturellement
- des controles d'autorisations Assistant pour eviter les abus
- une logique `Perplexity at Work` qui colle bien a la veille provider

## Stack COMET recommandee

### 1. Un espace "Provider Watch"

But:
- centraliser OpenAI, Gemini, Claude, Comet, Kimi et Akash

Inputs:
- changelogs officiels
- blogs produits officiels
- pages permissions / shortcuts / enterprise

Output attendu:
- un resume court
- l'impact S25
- l'action recommande

## Shortcuts recommandes

Source officielle:
- [Comet Shortcuts](https://www.perplexity.ai/help-center/en/articles/11897890-comet-shortcuts)

Creer au minimum:
- `;prov`
  expansion: "Check official updates from OpenAI, Google Gemini, Anthropic, Perplexity Comet, and Akash. Return only major changes from primary sources, then give S25 impact and a recommended action."
- `;prov-gemini`
  expansion: "Check official Google Gemini and AI Studio release notes, embeddings, multimodal, and memory-related changes. Return only what matters for MERLIN and semantic memory."
- `;prov-openai`
  expansion: "Check official OpenAI changelog and Responses API updates. Return only what matters for TRINITY, actions, tools, and voice flows."
- `;prov-claude`
  expansion: "Check official Anthropic release notes and model lifecycle updates. Return only what matters for backend, coding, compatibility, and long-context workflows."
- `;prov-comet`
  expansion: "Check official Perplexity Comet product, shortcuts, permissions, and work surfaces. Return only what improves S25 browser automation and provider watch."

## Tasks recommandes

Source officielle:
- [Perplexity at Work PDF](https://r2cdn.perplexity.ai/pdf/pplx-at-work.pdf)

Usage S25:
- creer une tache quotidienne de veille provider
- creer une tache hebdomadaire sur Akash et infra Web3
- pousser les sorties utiles dans le cockpit comme mission ou note de suivi

## Voice Mode

Source officielle:
- [Comet Voice Mode](https://comet-help.perplexity.ai/en/articles/13860420-voice-mode)

Usage S25:
- utile pour la navigation et les checks web mains libres
- pas une surface de decision finale
- a garder comme acceleration pour l'operateur, pas comme autorite autonome

## Permissions COMET

Source officielle:
- [Control what Comet Assistant can use](https://comet-help.perplexity.ai/en/articles/12658082-control-what-comet-assistant-can-use)

Regle S25:
- laisser Comet lire le web, docs et tabs utiles
- limiter l'acces aux comptes sensibles
- garder les actions critiques en confirmation humaine

## Boucle operationnelle

1. COMET lit les sources officielles avec `;prov` ou un shortcut cible.
2. COMET produit un resume court avec impacts.
3. La mission est ecrite dans le cockpit via `/api/missions`.
4. Le feed COMET est relu par TRINITY.
5. MERLIN/Gemini valide si la nouveaute touche memoire, embeddings ou retrieval.
6. GOUV4 priorise en:
   - `now`
   - `next`
   - `watch`

## Contrat de sortie

Chaque mise a jour provider doit produire:
- `provider`
- `source_url`
- `date_checked`
- `what_changed`
- `s25_impact`
- `recommended_action`
- `owner`

## Ce que COMET ne doit pas faire

- decider seul d'un changement d'architecture
- publier seul une nouvelle integration
- remplacer MERLIN pour la validation ou TRINITY pour l'orchestration

## Connexion avec le cockpit

Utiliser:
- `POST /api/missions`
- `POST /api/missions/update`
- `GET /api/comet/feed`

Helper local:

```powershell
pwsh -File scripts/arm_provider_watch_mission.ps1
```

Rail deployment Gemini/MERLIN:

```powershell
pwsh -File scripts/prepare_merlin_mesh_deploy.ps1
pwsh -File scripts/test_merlin_mcp_handshake.ps1 -Endpoint "http://<ingress>/mcp"
```

## Done

Le systeme est bien configure quand:
- les shortcuts COMET existent
- une mission `COMET` de veille provider est active
- un snapshot provider existe dans `memory/PROVIDER_WATCH.md`
- TRINITY peut reciter les impacts `now / next / watch`
