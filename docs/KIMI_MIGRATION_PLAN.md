# KIMI Migration Plan

## But

Transformer KIMI d'un scanner dependant d'un tunnel manuel en agent Web3 stable du mesh S25.

## Etat actuel

- KIMI est connu dans la memoire comme scanner 1M tokens
- son statut est `standby`
- il depend encore d'un tunnel Cloudflare / Home Assistant manuel
- il n'ecrit pas encore comme un agent autonome de premier rang dans le cockpit

## Etat cible

KIMI doit:
- exposer un endpoint stable
- pousser ses scans dans le cockpit ou via mission update
- mettre a jour `memory/state`
- alimenter COMET et ARKON
- ne pas tomber si le laptop est ferme

## Strategie de migration

### Phase 1 - bridge stable

Objectif:
- remplacer le tunnel manuel par un endpoint stable

Options:
- service Akash dedie KIMI
- bridge public stable derriere Worker/Tunnel nomme

Attendu:
- TRINITY peut interroger ou missionner KIMI sans dependance locale

### Phase 2 - protocoliser les echanges

KIMI doit remonter au moins:
- `last_scan`
- `status`
- `scan_window`
- `top_hits`
- `threats`

Canaux cibles:
- `POST /api/memory/ping`
- `POST /api/memory/state`
- `POST /api/missions/update`

### Phase 3 - integration mesh

Quand KIMI detecte quelque chose:
1. journaliser son heartbeat
2. ecrire un resume dans `memory/state`
3. creer ou mettre a jour une mission
4. pousser un resume intel vers COMET feed
5. laisser ARKON ou MERLIN valider si besoin

## Definition de done

- KIMI online dans `mesh/status`
- plus aucun prerequis de tunnel manuel
- scans visibles dans `memory/state`
- retours relies a missions ou COMET feed
- fermeture du laptop sans impact sur KIMI

## Priorite

KIMI est un chantier de niveau C a migrer en niveau A/B.
Il vient juste apres `oracle-agent` et `onchain-guardian` si l'objectif est l'autonomie Akash complete.
