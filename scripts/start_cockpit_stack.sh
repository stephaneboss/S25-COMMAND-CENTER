#!/usr/bin/env sh
set -eu

echo "[S25] starting cockpit stack"

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

if [ "${RUN_AGENT_LOOP:-false}" = "true" ]; then
  echo "[S25] starting agent-loop (prix 5min / F&G 15min / Reddit 30min / rapport 60min)"
  python -m agents.agent_loop &
fi

if [ "${RUN_ORACLE_AGENT:-false}" = "true" ]; then
  echo "[S25] starting oracle-agent"
  python -m agents.oracle_agent &
fi

if [ "${RUN_ONCHAIN_GUARDIAN:-false}" = "true" ]; then
  echo "[S25] starting onchain-guardian"
  python -m agents.onchain_guardian &
fi

if [ "${RUN_MERLIN_MCP_BRIDGE:-false}" = "true" ]; then
  echo "[S25] starting merlin mcp bridge"
  python -m agents.merlin_mcp_bridge &
fi

if [ "${RUN_MERLIN_FEEDBACK_LOOP:-false}" = "true" ]; then
  echo "[S25] starting merlin feedback loop"
  python -m agents.merlin_feedback_loop &
fi

if [ "${RUN_GEMINI_OPS_DAEMON:-false}" = "true" ]; then
  echo "[S25] starting gemini ops daemon"
  python -m agents.gemini_ops_daemon &
fi

if [ "${RUN_TREASURY_AUTOPILOT:-false}" = "true" ]; then
  echo "[S25] starting treasury autopilot"
  python -m agents.treasury_autopilot &
fi

echo "[S25] starting cockpit web"
exec python -m agents.cockpit_lumiere
