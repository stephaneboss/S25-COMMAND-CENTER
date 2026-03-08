#!/bin/bash
# arkon_claude_code_runner.sh
# Lance ARKON comme agent Claude Code sur le serveur Akash
# Usage: ./claude_code_runner.sh "analyse le dernier signal KIMI"

set -e

COCKPIT_URL="${COCKPIT_URL:-http://localhost:5000}"
LOG_FILE="/tmp/arkon_claude.log"

echo "[ARKON] $(date) -- Invocation Claude Code" >> "$LOG_FILE"

if [ -z "$1" ]; then
    TASK="Consulte /tmp/agent_loop.log et /tmp/comet_bridge.log, analyse les 10 dernieres lignes, et pousse un resume au cockpit via POST $COCKPIT_URL/api/intel avec {message, level, source: 'ARKON'}"
else
    TASK="$1"
fi

echo "[ARKON] Task: $TASK" >> "$LOG_FILE"

# Lance Claude Code en mode non-interactif
claude --print "$TASK" 2>&1 | tee -a "$LOG_FILE"

echo "[ARKON] Done -- $(date)" >> "$LOG_FILE"
