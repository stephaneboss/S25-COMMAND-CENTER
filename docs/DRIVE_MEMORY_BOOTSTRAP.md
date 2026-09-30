# Mémoire privée Drive : amorçage des agents

Ce dépôt public contient le **protocole**, jamais les notes privées, les identifiants de dossiers, les jetons OAuth ou les factures. Le dossier Drive et les autorisations sont configurés sur chaque hôte par l'opérateur. Une connexion à Drive est un droit de lecture; elle n'accorde aucune autorisation de modifier un contrat, d'envoyer un courriel ou de passer un ordre.

## Contrat de synchronisation

La source privée contient `INDEX.json` (`schema: s25.memory.index.v1`) et une liste de fichiers Markdown avec leur SHA-256. Un processus séparé, authentifié sur l'hôte, synchronise ces fichiers vers un répertoire privé hors dépôt. Par exemple, si rclone est déjà configuré :

```bash
rclone copy "${S25_DRIVE_REMOTE}:${S25_DRIVE_MEMORY_PATH}" "${S25_MEMORY_DIR}" \
  --include 'INDEX.json' --include '*.md' --exclude '*'
```

Ne mettre ni les valeurs de ces variables ni la configuration rclone dans Git. Monter le répertoire en lecture seule pour les agents. Vérifier la fraîcheur de la synchronisation et le statut de rclone avant de considérer la mémoire actuelle.

Le worker CLAUDE charge les fichiers au début d'une mission seulement si `S25_MEMORY_DIR` est défini. Il vérifie noms, tailles et empreintes; un échec indique que la mémoire est indisponible. `S25_MEMORY_AUDIT_LOG` peut désigner un journal privé des fichiers et empreintes lus. Les notes sont données au modèle comme **références non fiables**; elles ne remplacent jamais l'autorisation de Stef ni les règles T0–T3.

## Test de réception sur l'hôte

1. Synchroniser un dossier de test sans données clients, avec un `INDEX.json` valide.
2. Lancer une mission de lecture CLAUDE et vérifier l'empreinte dans le journal privé.
3. Modifier un fichier sans mettre à jour l'index : le chargement doit échouer avec `memory_checksum_mismatch`.
4. Refaire le test sur Comet et les autres agents **uniquement après** l'installation du même lecteur sur leur runtime. Un heartbeat « online » ne valide pas leur lecture de Drive.
