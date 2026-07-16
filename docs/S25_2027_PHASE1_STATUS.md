# S25 2027 — Phase 1 : état réel et fondations (2026-07-16)

Exécuté par CLAUDE (mission `mis_jEfBdUWYbNMn`, dispatchée par TRINITY le 2026-07-12).
Complète `S25_2027_ARCHITECTURE.md` (cible) et `S25_2027_RUNBOOK.md` (opérations).

## 1. Inventaire réel (vérifié le 2026-07-16, pas déclaratif)

### Services
| Composant | État | Preuve |
|-----------|------|--------|
| s25-cockpit (systemd user) | actif depuis 2026-07-11, PID 13060, ~396 MB | `service_status` |
| Tunnel Cloudflare s25-alien | OK, cockpit-alien.smajor.org répond direct | `/health` 200 v2.0.0 |
| Worker CF api.smajor.org | **DÉGRADÉ** : bug `Body has already been used` sur retry → 502 sur POST en fallback | test 2026-07-16 |
| GPU / Ollama | RTX 3060, ollama serve PID 2144, ~54 °C | `gpu_status` |
| Machine | RAM 22.5/32 GB libre, disque 73 % utilisé | `/api/health/full` |

### Crons (14 actifs, tous confirmés dans crontab)
mission_worker (1 min) · coinbase_ha_publisher (1 min) · mesh_signal_bridge (2 min) ·
trailing_stop_manager (3 min) · alerts/evaluate + auto_signal_scanner (5 min) ·
drawdown_guardian + comet_sentiment (10 min) · dca_scheduler (15 min) ·
push_system_to_ha + git_auto_sync (30 min) · quant_brain + heartbeat-HA (1 h) ·
purge logs (hebdo).

### Mesh — agents réellement vivants vs déclarés
- Vivants : CLAUDE (enregistré 2026-07-16 via `report_health`), MERLIN, workers infra
  (system_health, git_auto_sync).
- **Statuts périmés** : ORACLE « online » avec last_seen 2026-05-05 ; HOME_ASSISTANT,
  COCKPIT_LUMIERE et d'autres affichent « online » avec des heartbeats d'avril-juillet.
  → violation du principe « les statuts périmés doivent être marqués stale ». Voir backlog P1.

### Pipeline trading
kill_switch=false (intact), mode=authorized, threat T0, signaux frais, breaker
COINBASE:trade_execute 10/10 succès. Aucun impact des travaux Phase 1 (lecture seule +
commits docs).

## 2. Nettoyage logique effectué (non destructif)

- `inc_KpxNzVnu5OQC` (critical, 2026-04-22, mesh_degradation) → **resolved**, contexte
  dépassé, mesh reconfiguré depuis, E2E PASS 2026-07-16.
- `inc_dtuQ9NEqItvm` (low, 2026-04-27, titre/summary vides) → **resolved**, aucune donnée.
- 6 missions CLAUDE en attente depuis le 2026-07-12 : 1 exécutée (vérif E2E),
  3 fermées comme doublons superseded, audit Obscura livré, docs Vietnam commit `22e23b4`.
- **Pas supprimé** (volontairement) : 4 entrées DLQ de test d'avril (traçabilité, purge = P2),
  fichiers `cockpit_lumiere.py.*_bak` (P2), `.env.bak.*` non traqué (P1 sécurité).

## 3. Bug résolu : « heartbeat qui hang »

Collision de nommage, deux routes différentes :
- `POST/GET /api/mesh/heartbeat` (cockpit_lumiere.py:4787) = push mesh+market vers HA
  (`push_mesh_to_ha`) — **bloque** quand HA est lent (pas de timeout). Ce n'est PAS le
  heartbeat agent.
- `POST /api/mesh/report_health` (command_mesh.py, blueprint `/api/mesh`) = le VRAI
  heartbeat agent. Fonctionne (CLAUDE enregistré, `next_probe_sec: 30`).

Consigne : les agents utilisent exclusivement `report_health`. Renommage de la route HA
= P1 (touche cockpit_lumiere.py → patch isolé + rollback obligatoires).

## 4. Séparation code / config / runtime / secrets — plan

État actuel : tout vit dans le repo `S25-COMMAND-CENTER`, y compris l'état runtime
(`memory/*.json` modifiés en continu → git dirty permanent, commits auto-sync pollués).

Cible (migration progressive, feature flags, sans casser le service) :
1. **Code** : repo git — seuls `agents/`, `docs/`, `config/` (templates), `tests/`,
   `static/`, scripts. Aucun état mutable.
2. **Config** : `config/` versionné avec valeurs par défaut + overrides locaux non
   versionnés (`config/local/` dans .gitignore).
3. **Runtime** : déplacer `memory/` (états mutables : missions, breakers, cooldowns,
   ledgers) vers `~/s25-runtime/` hors repo. Étapes : (a) symlink transitoire
   `memory -> ~/s25-runtime` pour zéro changement de code, (b) .gitignore, (c) variable
   `S25_RUNTIME_DIR` dans le code, (d) git_auto_sync ne committe plus que du code/docs.
   Les journaux d'audit (`code_journal`, `ops_journal`) restent sauvegardés (rsync cron).
4. **Secrets** : `.env` unique hors git (déjà le cas) ; supprimer `.env.bak.*` du
   worktree ; interdire tout secret en dur dans le code (le fallback secret en dur dans
   `ops_route`/cockpit doit disparaître → P1).

## 5. Healthcheck unifié — état

`GET /api/health/full` existe et fonctionne (service, pipeline, GPU, RAM, disque,
commits, cron worker). **Écarts** vs « source de vérité » de l'architecture cible :
- n'agrège pas : mesh (fraîcheur heartbeats), breakers, DLQ, incidents ouverts, missions actives ;
- champs coinbase à null (IP allowlist à re-vérifier depuis le nouveau réseau) ;
- pas de champ `stale` calculé sur l'âge des heartbeats.

## 6. Backlog priorisé

**P0 (sécurité/fiabilité immédiate)**
1. Patcher le worker CF api.smajor.org : `request.clone()` avant le premier fetch
   (bug body-reuse → 502 sur tous les POST en fallback d'origine).
2. Watchdog mesh : statut dérivé de l'âge du heartbeat (`stale` si > seuil), ne plus
   jamais afficher « online » avec un last_seen vieux de 2 mois.

**P1**
3. Renommer `/api/mesh/heartbeat` (route HA push) en `/api/ha/push_mesh` + timeout sur
   l'appel HA — patch isolé cockpit_lumiere.py avec rollback.
4. Étendre `/api/health/full` : mesh freshness, breakers, DLQ, incidents, missions.
5. Supprimer le secret par défaut en dur (`S25_SHARED_SECRET` fallback) dans ops_route.
6. Nettoyer `.env.bak.*` du worktree ; vérifier qu'aucun backup de secrets n'est traqué.
7. Coinbase : re-valider l'IP sortante post-déménagement réseau contre l'allowlist.

**P2**
8. Migration runtime hors repo (plan §4, étapes a→d).
9. Purge des 4 entrées DLQ de test d'avril + entries replay ledger orphelines.
10. Supprimer les backups `cockpit_lumiere.py.*_bak` (4 fichiers à la racine).
11. Découper cockpit_lumiere.py (monolithe ~5000+ lignes) en blueprints — derrière
    feature flag, un blueprint à la fois, tests avant/après.

## 7. Risques et blocages

- SSH direct vers AlienStef indisponible depuis le poste (ancienne IP 10.0.0.97 morte
  après déménagement réseau) — tout passe par l'API cockpit ; documenter la nouvelle IP
  LAN dans le runbook dès qu'elle est connue.
- `cockpit_lumiere.py` reste le point unique fragile (monolithe + 4 backups à la racine) ;
  toute modif = patch isolé + `git apply --check` + rollback (règle mission respectée :
  non modifié en Phase 1).
- Le worker CF en 502 sur POST masque des pannes potentielles pour les clients qui
  passent par api.smajor.org au lieu de cockpit-alien direct (Trinity GPT notamment).
