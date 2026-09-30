#!/usr/bin/env bash
# S25 deterministic deploy on Alien (chantier 1).
# Pull main without touching local changes, restart the cockpit when code changed, then
# PROVE it: /api/version build_sha must equal the code SHA (last commit outside memory/).
# Every run ends with a runtime check, so deploy.json never keeps a stale receipt.
# Self-heals a runtime that is not on the code SHA (e.g. build_sha=dev), once per SHA.
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

write_state() {  # status expected runtime [heal_sha]
  mkdir -p "$(dirname "$state")"
  printf '{"ts":"%s","status":"%s","expected_sha":"%s","runtime_sha":"%s","heal_sha":"%s"}\n' \
    "$(date -Iseconds)" "$1" "$2" "$3" "${4-$(last_state_field heal_sha)}" >"$state.tmp" && mv "$state.tmp" "$state"
}

last_state_field() {  # field
  [[ -f "$state" ]] || return 0
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2],""))' "$state" "$1" 2>/dev/null || true
}

restart_and_verify() {  # expected_sha reason heal_sha
  local expected=$1 reason=$2 heal=$3 got=""
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  # A reload can leave Flask running its previously imported Python modules.
  if ! systemctl --user restart "$service" || ! systemctl --user is-active --quiet "$service"; then
    echo "$(date -Iseconds) AUTO-PULL RESTART FAILED: $service; repository at $expected ($reason)"
    write_state restart_failed "$expected" "" "$heal"
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
    write_state verified "$expected" "$got" "$heal"
    return 0
  fi
  echo "$(date -Iseconds) DEPLOY MISMATCH: expected $expected, runtime reports '${got:-unreachable}'"
  write_state mismatch "$expected" "$got" "$heal"
  return 1
}

# Code identity = last commit touching code (memory/ excluded): git_auto_sync commits
# runtime state every 30 min, which must neither restart nor "drift" the cockpit.
code_sha() { git log -1 --format=%H -- . ':(exclude)memory'; }

cd "$repo"
before=$(git rev-parse HEAD)
code_before=$(code_sha)
if ! git pull --ff-only origin main; then
  echo "$(date -Iseconds) AUTO-PULL FAILED: repository remains at $before"
  exit 1
fi
head_after=$(git rev-parse HEAD)
after=$(code_sha)

if [[ "$before" != "$head_after" ]]; then
  echo "$(date -Iseconds) AUTO-PULL UPDATED: $before -> $head_after (code $code_before -> $after)"
  if [[ "$code_before" != "$after" ]]; then
    restart_and_verify "$after" "code update" ""
    exit $?
  fi
  echo "$(date -Iseconds) AUTO-PULL NO RESTART: memory-only update, code still $after"
else
  echo "$(date -Iseconds) AUTO-PULL UNCHANGED: $head_after"
fi

# Runtime check, every run that did not just restart: the process must be on the code
# SHA (catches stale runtime, build_sha=dev, dirty tree, memory-only pulls). At most ONE heal restart per SHA (heal_sha), whether that
# heal succeeded or not; later drift on the same SHA stays visible, no restart loop.
got=$(runtime_sha)
if [[ -z "$got" ]]; then
  echo "$(date -Iseconds) DEPLOY UNREACHABLE: $version_url did not answer (code $after)"
  write_state unreachable "$after" ""
  exit 1
fi
if [[ "$got" == "$after" ]]; then
  [[ "$(last_state_field status)" == verified && "$(last_state_field expected_sha)" == "$after" ]] \
    || write_state verified "$after" "$got"
  exit 0
fi
if [[ "$(last_state_field heal_sha)" == "$after" ]]; then
  echo "$(date -Iseconds) DEPLOY DRIFT PERSISTS: runtime '$got' != code $after (heal already used for this SHA, manual check needed)"
  write_state drift "$after" "$got"
  exit 1
fi
echo "$(date -Iseconds) DEPLOY DRIFT: runtime '$got' != code $after, healing"
restart_and_verify "$after" "drift heal" "$after"
