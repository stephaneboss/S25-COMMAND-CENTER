# Web3 Autopilot

## But

Automatiser la surveillance de tresorerie Web3 sans signer de transaction aveugle.

## Principe

- `treasury_engine.py` calcule l'etat et les quotes
- `treasury_autopilot.py` pousse l'etat dans le cockpit
- quand une recharge AKT devient necessaire, il cree une mission
- la signature reelle reste separee tant que le mode "full auto" n'est pas explicitement arme

## Fichiers

- `agents/treasury_engine.py`
- `agents/treasury_autopilot.py`
- `agents/balance_sentinel.py`

## Variables

- `TREASURY_POLL_SECONDS`
- `TREASURY_DEPLOYMENTS`
- `TREASURY_AUTOMISSION`
- `AKASH_WALLET_ADDRESS`
- `HA_TOKEN`

## Runtime

- Akash principal ou fallback compose
- pas de dependance laptop pour la surveillance

## Sorties

- `intel.treasury_status` dans la memoire partagee
- mission `infra_monitoring` si alerte critique
- heartbeat `TREASURY`

## Cible long terme

1. surveiller
2. quotter
3. missionner
4. signer seulement via chemin securise dedie

## Regle

Pas de transaction on-chain automatique sans:
- coffre de cles propre
- policy explicite
- dry-run valide
- journal d'audit
