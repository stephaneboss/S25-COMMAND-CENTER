# Agent Registry

## But

Registre unique des agents S25 avec:
- role
- runtime cible
- dependances critiques
- niveau d'autonomie
- prochaine migration

## Regles

- Un agent critique doit avoir un runtime principal public ou Akash.
- Un agent local ne peut pas etre prerequis du boot global.
- Toute migration hors laptop doit etre tracee ici.

## Agents coeur

| Agent | Role | Modele / moteur | Runtime principal | Fallback | Niveau |
|-------|------|------------------|-------------------|----------|--------|
| TRINITY | Orchestrateur vocal et texte | GPT | GPT Actions + cockpit Akash | aucun local requis | A |
| ARKON | Builder / analyste infra | Claude Code | Akash cible | laptop outillage | B |
| MERLIN | Validateur / analyse web | Gemini | Akash cible | API distante | B |
| COMET | Watchman intel temps reel | Perplexity | Cockpit Akash + missions | aucun local requis | A |
| KIMI | Pompe a data Web3 / memecoins | Kimi | a migrer vers endpoint stable | tunnel manuel HA | C |
| GOUV4 | Routeur et gouvernance quota/cout | logique Python | Cockpit Akash | aucun | A |

## Agents et sous-agents a deployer sur Akash

| Agent | Role | Etat | Priorite |
|-------|------|------|----------|
| oracle-agent | prix multi-source | non deploye | critique |
| onchain-guardian | whales, rugs, alertes | non deploye | critique |
| defi-liquidity-manager | DeFi / APY / IL | backlog | normal |
| code-validator | validation avant deploy | backlog | normal |
| auto-documenter | docs et etat runtime | backlog | normal |

## Definition des niveaux

- Niveau A = autonome sans laptop
- Niveau B = peut tolerer du support laptop, mais doit migrer
- Niveau C = depend encore d'un flux local ou manuel

## Prochaines migrations

### 1. KIMI

- sortir du tunnel manuel
- donner un endpoint stable ou un bridge Akash
- le garder comme capteur et pompe a data, pas comme cerveau du systeme
- journaliser ses scans dans `memory/state` et `comet_feed`

### 2. MERLIN

- documenter le worker d'analyse ou le bridge Gemini stable
- l'executer derriere Akash ou une API distante stable

### 3. ARKON subagents

- deployer `oracle-agent`
- deployer `onchain-guardian`
- brancher leurs retours dans missions et feed intel

### 4. Dell-Linux

- le garder pour Ollama et calcul local additionnel
- le sortir des prerequis du pipeline principal
