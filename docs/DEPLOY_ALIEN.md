# Déploiement déterministe sur Alien (chantier 1)

**Objectif :** le code qui tourne sur Alien est prouvé identique au commit attendu :
`GET /api/version → build_sha == git rev-parse HEAD`.

## Chaîne
branche → PR (CLAUDE) → tests → merge (Stef) → `s25-auto-pull.timer` (5 min) →
`git pull --ff-only` → `systemctl --user restart s25-cockpit` → vérification `build_sha`.

## Preuves
- `/api/version` : `build_sha` (APP_BUILD_SHA > `git rev-parse HEAD` au démarrage > `dev`) et `started_at`.
- `~/.local/state/s25/deploy.json` : `{status: verified|mismatch|restart_failed, expected_sha, runtime_sha, ts}`.
- `/tmp/auto_pull.log` : `DEPLOY VERIFIED`, `DEPLOY MISMATCH`, `DEPLOY DRIFT`, `DEPLOY DRIFT PERSISTS`.

## Dérive (runtime ≠ HEAD sans nouveau pull)
Un redémarrage de guérison **une seule fois par SHA**. Si ça ne suffit pas : `DEPLOY DRIFT PERSISTS`,
code de sortie ≠ 0, aucun redémarrage en boucle → intervention humaine.

## Rollback
1. Sur GitHub : `git revert <sha>` via PR → merge → l'auto-pull redéploie et vérifie (voie normale).
2. Urgence sur Alien (Stef ou CLAUDE autorisé) :
   ```bash
   systemctl --user stop s25-auto-pull.timer
   cd ~/S25-COMMAND-CENTER && git checkout <sha_connu_bon>
   systemctl --user restart s25-cockpit
   curl -s localhost:7777/api/version   # build_sha == <sha_connu_bon>
   ```
   Puis revert sur `main` et `systemctl --user start s25-auto-pull.timer` (sinon le pull ramène main).

## Hors périmètre
Akash (image Docker, `APP_BUILD_SHA` fourni au build) ; agents hors cockpit (timers séparés, P2 inventaire mesh).
