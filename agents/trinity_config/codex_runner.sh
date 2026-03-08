#!/bin/bash
# trinity_codex_runner.sh
# Lance TRINITY via Codex CLI sur le laptop Windows (Git Bash)
# Usage: ./codex_runner.sh "status du cockpit S25"

COCKPIT_URL="${COCKPIT_URL:-http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com}"
LOG_FILE="/tmp/trinity_codex.log"

echo "[TRINITY] $(date) -- Invocation Codex" >> "$LOG_FILE"

if [ -z "$1" ]; then
    TASK="Fais un GET sur $COCKPIT_URL/api/status et affiche le resultat formate. Ensuite consulte $COCKPIT_URL/api/intel pour les dernieres alertes."
else
    TASK="$1"
fi

echo "[TRINITY] Task: $TASK" >> "$LOG_FILE"

# Lance Codex en mode non-interactif
codex --quiet "$TASK" 2>&1 | tee -a "$LOG_FILE"

echo "[TRINITY] Done -- $(date)" >> "$LOG_FILE"
