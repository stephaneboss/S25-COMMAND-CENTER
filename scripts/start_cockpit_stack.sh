#!/usr/bin/env sh
set -eu

echo "[S25] starting cockpit stack"

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

if [ "${RUN_TREASURY_AUTOPILOT:-false}" = "true" ]; then
  echo "[S25] starting treasury autopilot"
  python -m agents.treasury_autopilot &
fi

echo "[S25] starting cockpit web"
exec python -m agents.cockpit_lumiere
