#!/bin/bash
# trinity_codex_runner.sh
# Lance TRINITY via Codex CLI sur le laptop Windows (Git Bash)
# Usage: ./codex_runner.sh "status du cockpit S25"

COCKPIT_URL="${COCKPIT_URL:-https://uoqlngdqqlc29fhg8l78qt80d8.ingress.akashprovid.com}"
LOG_FILE="${TRINITY_LOG_FILE:-/tmp/trinity_codex.log}"

echo "[TRINITY] $(date) -- Invocation Codex" >> "$LOG_FILE"

if [ -z "$1" ]; then
    TASK="TRINITY: appelle $COCKPIT_URL/api/trinity/ping, puis $COCKPIT_URL/api/memory, puis $COCKPIT_URL/api/status. Fais un resume court en francais de l'etat S25 et des points critiques."
else
    TASK="$1"
fi

echo "[TRINITY] Task: $TASK" >> "$LOG_FILE"

# Lance Codex en mode non-interactif
codex --quiet "$TASK" 2>&1 | tee -a "$LOG_FILE"

echo "[TRINITY] Done -- $(date)" >> "$LOG_FILE"
