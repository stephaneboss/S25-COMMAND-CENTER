#!/usr/bin/env sh
set -eu

echo "[S25] starting cockpit stack"

start_optional() {
  flag="$1"
  label="$2"
  cmd="$3"
  eval "enabled=\${$flag:-false}"
  if [ "${enabled}" = "true" ]; then
    echo "[S25] starting ${label}"
    sh -c "${cmd}" &
  fi
}

bootstrap_google_secrets() {
  env_file="${S25_BOOTSTRAP_ENV_PATH:-/tmp/s25-bootstrap.env}"
  echo "[S25] bootstrapping google secret manager bundle -> ${env_file}"
  python -m agents.google_secret_manager_bootstrap \
    --project-id "${GOOGLE_CLOUD_PROJECT}" \
    --output "${env_file}"
  set -a
  # shellcheck disable=SC1090
  . "${env_file}"
  set +a
  echo "[S25] google secret manager bundle loaded"
}

if [ "${S25_BOOTSTRAP_GOOGLE_SECRETS:-false}" = "true" ]; then
  bootstrap_google_secrets
fi

start_optional "RUN_ORACLE_AGENT" "oracle-agent" "python -m agents.oracle_agent"

start_optional "RUN_ONCHAIN_GUARDIAN" "onchain-guardian" "python -m agents.onchain_guardian"

start_optional "RUN_MERLIN_MCP_BRIDGE" "merlin mcp bridge" "python -m agents.merlin_mcp_bridge"

start_optional "RUN_MERLIN_FEEDBACK_LOOP" "merlin feedback loop" "python -m agents.merlin_feedback_loop"

start_optional "RUN_GEMINI_OPS_DAEMON" "gemini ops daemon" "python -m agents.gemini_ops_daemon"

start_optional "RUN_TREASURY_AUTOPILOT" "treasury autopilot" "python -m agents.treasury_autopilot"

start_optional "RUN_BALANCE_SENTINEL" "balance sentinel" "python -m agents.balance_sentinel"
start_optional "RUN_TREASURY_ENGINE" "treasury engine" "python -m agents.treasury_engine"
start_optional "RUN_COMET_BRIDGE" "comet bridge" "python -m agents.comet_bridge"
start_optional "RUN_PROVIDER_WATCH" "provider watch" "python -m agents.provider_watch"
start_optional "RUN_AGENT_LOOP" "agent-loop (prix 5min / F&G 15min / Reddit 30min / rapport 60min)" "python -m agents.agent_loop"

echo "[S25] starting cockpit web"
exec python -m agents.cockpit_lumiere
