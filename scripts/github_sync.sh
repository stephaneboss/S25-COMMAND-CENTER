#!/bin/bash
# ============================================================
# S25 LUMIÈRE — GitHub Auto-Sync (cron: 03:00 UTC daily)
# Auto-commit des modifications vers stephaneboss/S25-COMMAND-CENTER
# ============================================================

REPO_DIR="/opt/s25-command-center"
LOG="/var/log/s25_github_sync.log"
TS=$(date +"%Y-%m-%d %H:%M:%S UTC")

log() { echo "[$TS] $1" | tee -a "$LOG"; }

log "=== S25 GitHub Sync démarré ==="

cd "$REPO_DIR" || { log "ERROR: Repo non trouvé dans $REPO_DIR"; exit 1; }

# Vérifier s'il y a des changements
if [ -z "$(git status --porcelain)" ]; then
    log "Aucun changement détecté — sync ignoré"
    exit 0
fi

# Copier les fichiers S25 dynamiques depuis HA
cp /tmp/s25_watchdog_status.json "$REPO_DIR/logs/watchdog_status.json" 2>/dev/null
cp /config/www/ai_analysis.json "$REPO_DIR/logs/ai_analysis_latest.json" 2>/dev/null

# Git add + commit
git add -A
git commit -m "🤖 S25 Auto-sync $(date +%Y-%m-%d) | ARKON-5 ACTIVE | Claude Build"
git push origin main

if [ $? -eq 0 ]; then
    log "✅ Push GitHub réussi"
else
    log "❌ Push GitHub échoué"
fi

log "=== Sync terminé ==="
