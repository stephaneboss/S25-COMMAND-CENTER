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

echo "[S25] starting cockpit web"
exec python -m agents.cockpit_lumiere
