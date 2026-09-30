#!/usr/bin/env bash
# S25 deterministic deploy on Alien (chantier 1).
# Pull main without touching local changes, restart the cockpit when runtime code
# changed, then PROVE it: /api/version build_sha must equal git HEAD.
# Also self-heals a runtime that never picked up HEAD (e.g. build_sha=dev), once per SHA.
set -euo pipefail

repo=${S25_AUTO_PULL_REPO:-/home/alienstef/S25-COMMAND-CENTER}
log=${S25_AUTO_PULL_LOG:-/tmp/auto_pull.log}
state=${S25_DEPLOY_STATE:-$HOME/.local/state/s25/deploy.json}
version_url=${S25_VERSION_URL:-http://localhost:7777/api/version}
verify_tries=${S25_VERIFY_TRIES:-12}
verify_sleep=${S25_VERIFY_SLEEP:-5}
service=s25-cockpit

exec >>"$log" 2>&1
exec 9>"${S25_AUTO_PULL_LOCK:-/tmp/s25-auto-pull.lock}"
if ! flock -n 9; then
  echo "$(date -Iseconds) AUTO-PULL SKIPPED: another pull is running"
  exit 0
fi

runtime_sha() {
  curl -fsS -m 5 "$version_url" 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("build_sha",""))' 2>/dev/null || true
}

write_state() {  # status expected runtime
  mkdir -p "$(dirname "$state")"
  printf '{"ts":"%s","status":"%s","expected_sha":"%s","runtime_sha":"%s"}\n' \
    "$(date -Iseconds)" "$1" "$2" "$3" >"$state.tmp" && mv "$state.tmp" "$state"
}

last_state_field() {  # field
  [[ -f "$state" ]] || return 0
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2],""))' "$state" "$1" 2>/dev/null || true
}

restart_and_verify() {  # expected_sha reason
  local expected=$1 reason=$2 got=""
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  # A reload can leave Flask running its previously imported Python modules.
  if ! systemctl --user restart "$service" || ! systemctl --user is-active --quiet "$service"; then
    echo "$(date -Iseconds) AUTO-PULL RESTART FAILED: $service; repository at $expected ($reason)"
    write_state restart_failed "$expected" ""
    return 1
  fi
  echo "$(date -Iseconds) AUTO-PULL RESTARTED: $service at $expected ($reason)"
  for ((i = 0; i < verify_tries; i++)); do
    got=$(runtime_sha)
    [[ "$got" == "$expected" ]] && break
    sleep "$verify_sleep"
  done
  if [[ "$got" == "$expected" ]]; then
    echo "$(date -Iseconds) DEPLOY VERIFIED: runtime_sha == $expected"
    write_state verified "$expected" "$got"
    return 0
  fi
  echo "$(date -Iseconds) DEPLOY MISMATCH: expected $expected, runtime reports '${got:-unreachable}'"
  write_state mismatch "$expected" "$got"
  return 1
}

cd "$repo"
before=$(git rev-parse HEAD)
if ! git pull --ff-only origin main; then
  echo "$(date -Iseconds) AUTO-PULL FAILED: repository remains at $before"
  exit 1
fi
after=$(git rev-parse HEAD)

if [[ "$before" != "$after" ]]; then
  echo "$(date -Iseconds) AUTO-PULL UPDATED: $before -> $after"
  changed=$(git diff --name-only "$before" "$after")
  if grep -qE '^(cockpit_lumiere\.py|(agents|tools|strategies|security|config|configs)/.+\.(py|json|ya?ml))$' <<<"$changed"; then
    restart_and_verify "$after" "code update"
    exit $?
  fi
  echo "$(date -Iseconds) AUTO-PULL NO RESTART: no runtime file changed"
  exit 0
fi

echo "$(date -Iseconds) AUTO-PULL UNCHANGED: $after"

# Drift check: HEAD unchanged but the running process is not on it (stale runtime,
# build_sha=dev). Heal once per SHA; a repeated mismatch stays visible, no restart loop.
got=$(runtime_sha)
if [[ -z "$got" ]]; then
  echo "$(date -Iseconds) DEPLOY DRIFT UNKNOWN: $version_url unreachable"
  exit 0
fi
if [[ "$got" == "$after" ]]; then
  [[ "$(last_state_field status)" == verified && "$(last_state_field expected_sha)" == "$after" ]] \
    || write_state verified "$after" "$got"
  exit 0
fi
if [[ "$(last_state_field expected_sha)" == "$after" && "$(last_state_field status)" != verified ]]; then
  echo "$(date -Iseconds) DEPLOY DRIFT PERSISTS: runtime '$got' != HEAD $after (already retried, manual check needed)"
  exit 1
fi
echo "$(date -Iseconds) DEPLOY DRIFT: runtime '$got' != HEAD $after, healing"
restart_and_verify "$after" "drift heal"
