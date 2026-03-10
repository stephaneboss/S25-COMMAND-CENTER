# Model Spend Governance

## But

Utiliser les abonnements et quotas deja payes avant d'ajouter des couts infra inutiles.

## Enveloppe connue

Abonnements declares par Stef:
- OpenAI / GPT: 30 USD
- Gemini: 30 USD
- Kimi: 30 USD
- Claude: 30 USD
- Perplexity: max 375 USD
- Akash: variable selon depot AKT

## Principe

- Ce qui est deja paye doit etre exploite au maximum avant d'acheter plus d'infra.
- Ce qui est critique pour le boot doit rester sur Akash.
- Ce qui est cher doit etre reserve aux taches a plus forte valeur.

## Ordre d'utilisation recommande

### 1. Gratuit ou deja amorti

- GOUV4 pour router intelligemment
- endpoints cockpit et missions sur Akash
- Worker public stable
- Ollama local en fallback uniquement

### 2. Abonnements a fort rendement

- Gemini pour `trading_analysis`
- Perplexity pour `market_news` et veille COMET
- Claude pour `code_generation` et `automation_yaml`
- GPT pour `planning`, `governance`, orchestration vocale
- Kimi pour scanning Web3 et memecoin surveillance

### 3. Infra Akash payante additionnelle

A n'utiliser que si:
- elle remplace une dependance laptop
- elle reduit un point unique de panne
- elle augmente l'autonomie du pipeline

## Mapping taches -> moteur

| Tache | Moteur prefere | Pourquoi |
|------|-----------------|----------|
| trading_analysis | Gemini | bon ratio cout / structure |
| market_news | Perplexity | web et veille temps reel |
| code_generation | Claude | qualite code / yaml |
| strategy_planning | GPT | gouvernance / orchestration |
| web3_scan | Kimi | specialisation memecoins / Web3 |
| fallback | Ollama | zero cout marginal local |

## Regles de gouvernance

1. Toujours router via GOUV4 plutot que choisir un modele au hasard.
2. Toute tache repetitive doit etre missionnee et tracee dans le cockpit.
3. Si une depense Akash remplace une dependance laptop critique, elle est justifiee.
4. Si une depense n'augmente ni autonomie ni qualite, on la differe.

## Priorites budgetaires infra

1. garder le cockpit Akash stable
2. deployer `oracle-agent`
3. deployer `onchain-guardian`
4. rendre KIMI stable sans tunnel manuel
5. ensuite seulement monter les capacites non critiques
