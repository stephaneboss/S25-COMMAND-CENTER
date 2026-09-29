#!/usr/bin/env bash
# Pull main without touching local changes; restart the Python service on code updates.
set -euo pipefail

repo=${S25_AUTO_PULL_REPO:-/home/alienstef/S25-COMMAND-CENTER}
log=${S25_AUTO_PULL_LOG:-/tmp/auto_pull.log}
exec >>"$log" 2>&1
exec 9>"${S25_AUTO_PULL_LOCK:-/tmp/s25-auto-pull.lock}"
if ! flock -n 9; then
  echo "$(date -Iseconds) AUTO-PULL SKIPPED: another pull is running"
  exit 0
fi

cd "$repo"
before=$(git rev-parse HEAD)
if ! git pull --ff-only origin main; then
  echo "$(date -Iseconds) AUTO-PULL FAILED: repository remains at $before"
  exit 1
fi
after=$(git rev-parse HEAD)
if [[ "$before" == "$after" ]]; then
  echo "$(date -Iseconds) AUTO-PULL UNCHANGED: $after"
  exit 0
fi

echo "$(date -Iseconds) AUTO-PULL UPDATED: $before -> $after"
changed=$(git diff --name-only "$before" "$after")
if grep -qE '^(cockpit_lumiere\.py|agents/.+\.py)$' <<<"$changed"; then
  # A reload can leave Flask running its previously imported Python modules.
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  if ! systemctl --user restart s25-cockpit || ! systemctl --user is-active --quiet s25-cockpit; then
    echo "$(date -Iseconds) AUTO-PULL RESTART FAILED: s25-cockpit; repository at $after"
    exit 1
  fi
  echo "$(date -Iseconds) AUTO-PULL RESTARTED: s25-cockpit at $after"
fi
