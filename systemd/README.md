# Unités systemd S25 (Alien)

**Mécanisme actif sur Alien : crontab** (vérifié le 30 sept. 2026 via `/api/ops/crontab`).
`auto_pull_cron.sh` (*/5), `mesh_watchdog_cron` (chaque minute + à :30), `mission_worker`,
`claude_mesh_relay/worker`, `git_auto_sync` (*/30)… tournent tous par cron.

Les unités de ce dossier sont des **alternatives inactives**. Ne pas activer une unité si le
même script tourne déjà en cron, sinon il s'exécute en double :

| Unité | Équivalent cron actif | Statut |
|---|---|---|
| `s25-mesh-watchdog.timer` | `agents.mesh_watchdog_cron` | **ne pas activer** |
| `s25-auto-pull.timer` | `scripts/auto_pull_cron.sh` */5 | **ne pas activer** |

Seule `s25-cockpit` (service utilisateur) est un service systemd réellement utilisé : c'est lui
que l'auto-pull redémarre et que `opsRun service_status` / `log_tail file=cockpit` interrogent.
