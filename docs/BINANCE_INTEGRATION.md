# Binance Integration — Structure & Procédures (préparation seulement)

**Statut au 2026-08-02** : compte Binance vérifié côté Steph, **actuellement sans fonds** (contexte fourni par Steph/TRINITY, pas vérifié par cet agent — aucun accès direct au compte Binance). Aucune clé API créée, aucun fonds déplacé, aucune modification du compte. Ce document prépare uniquement la structure pour une intégration future, sur le même modèle de sécurité que Coinbase (`agents/coinbase_executor.py`, `agents/coinbase_preflight.py`).

## Structure de dossiers proposée

```
agents/binance/
  README.md          # ce fichier explique le statut placeholder
  __init__.py         # vide, réservé pour agents.binance.executor plus tard
docs/
  BINANCE_INTEGRATION.md   # ce document
```

Aucun fichier exécutable de trading n'est créé à ce stade — uniquement la structure et la doc, conformément à la mission.

## Configuration (future, jamais en clair)

- Clés API Binance : **jamais dans `.env` en clair** — suivre le même chemin que Coinbase (`security/vault.py`, priorité OS keyring > bundle chiffré > `.env` en dernier recours avec warning de dépréciation).
- Permissions API recommandées à la création (quand Steph créera la clé) : **lecture + trade spot uniquement**, **jamais retrait/withdraw**, IP whitelist obligatoire (même pattern que Coinbase : IP publique d'AlienStef).
- Nom de variables proposé : `BINANCE_API_KEY`, `BINANCE_API_SECRET` (ou `BINANCE_API_SECRET_PATH` pour un fichier PEM/HMAC séparé, comme `CBA_API_SECRET_PATH`).

## Sécurité

- `dry_run=True` par défaut obligatoire, comme `CoinbaseExecutor`.
- Réutiliser le pattern `_pre_flight()` + le nouveau `coinbase_preflight.py` (préflight lecture seule, canary plafonné, idempotency key) plutôt que d'inventer un nouveau modèle de garde-fous.
- Whitelist de produits explicite (pas de trading sur une paire non listée).
- Aucune clé, aucun secret, aucun montant réel dans les logs.

## API (Binance Spot)

- Utiliser l'API Spot Binance (`api.binance.com`), pas Futures/Margin — cohérent avec le profil de risque actuel (micro-comptes, pas d'effet de levier).
- Tester d'abord sur le **testnet Binance** (`testnet.binance.vision`) avant tout accès au compte réel — un canal de test gratuit qui n'existe pas côté Coinbase et qu'il faut exploiter ici.
- Bibliothèque candidate : `python-binance` (mature, largement utilisée) — à valider par Steph avant ajout aux dépendances.

## Logs

- Fichier dédié `memory/binance_trades_log.jsonl`, format aligné sur `trades_log.jsonl` (mêmes champs : `ts`, `trade_id`, `symbol`, `side`, `usd_amount`, `base_size`, `avg_price`, `fee`, `mode`, `success`) pour réutiliser `position_tracker.py` sans dupliquer la logique PnL.
- Heartbeat non-financier séparé (`memory/binance_heartbeat_log.jsonl`), même principe que `coinbase_heartbeat_log.jsonl` — jamais mélangé aux vrais trades.

## Procédures (quand le compte sera financé)

1. Steph crée la clé API Binance lui-même (lecture+trade seulement, IP whitelist) — jamais cet agent.
2. La clé est chargée via le vault, jamais vue en clair par un agent.
3. `agents/binance/executor.py` (à écrire) réutilise le même squelette que `CoinbaseExecutor` : `dry_run` par défaut, `_pre_flight()`, produits whitelistés.
4. Un `preflight_check()` équivalent à celui de Coinbase avant tout ordre réel.
5. Premier ordre = canary plafonné (même principe que le canary Coinbase à 5 USD), jamais un montant arbitraire.
6. Aucune activation live tant que ces étapes ne sont pas validées explicitement par Steph.

## Ce qui n'est PAS fait par ce document

- Aucune clé créée.
- Aucun fonds déplacé ou vérifié en direct (le "sans fonds" vient du contexte fourni, pas d'un appel API réel).
- Aucun code d'exécution de trade écrit — seulement la structure et la documentation.
