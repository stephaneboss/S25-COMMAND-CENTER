#!/bin/bash
# S25 auto-pull: pull external git smajor pushes + reload systemd if code changed
# Runs every 5 min via crontab
cd /home/alienstef/S25-COMMAND-CENTER || exit 1
# Get current HEAD sha
BEFORE=$(git rev-parse HEAD)
# Fetch + pull (ff-only to avoid merge conflicts in autonomous mode)
git pull --ff-only origin main 2>&1 | tee -a /tmp/auto_pull.log
AFTER=$(git rev-parse HEAD)
if [ "$BEFORE" != "$AFTER" ]; then
  echo "$(date -Iseconds) AUTO-PULL: $BEFORE -> $AFTER, reloading cockpit" >> /tmp/auto_pull.log
  # Reload only if cockpit_lumiere.py or agents/ changed
  CHANGED=$(git diff --name-only $BEFORE $AFTER)
  if echo "$CHANGED" | grep -qE '^(cockpit_lumiere\.py|agents/.+\.py)$'; then
    systemctl --user reload-or-restart s25-cockpit && echo "$(date -Iseconds) RELOADED s25-cockpit" >> /tmp/auto_pull.log
  fi
fi
