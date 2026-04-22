#!/usr/bin/env python3
"""
S25 Mesh Watchdog Cron — surveille le control plane (Trinity spec §3)
======================================================================
Runs every 30s (via cron */1min with sleep offset OR systemd timer).

Logic (per Trinity spec):
  loop every 30s:
    read system_state
    if global_status == critical or severe:
      enforce_policy_mode("safe")
      throttle missions non critiques
      ensure fallback agents ready

Reads /api/mesh/state, writes degraded_mode flag, and optionally opens
a missing incident if the condition is present but not tracked yet.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import requests

logger = logging.getLogger("s25.mesh_watchdog")

REPO = Path(__file__).resolve().parent.parent
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")
DEGRADED_FLAG = REPO / "memory" / "command_mesh" / "degraded_mode.json"


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def _secret() -> str:
    try:
        from security.vault import vault_get
        s = vault_get("S25_SHARED_SECRET", "")
        if s:
            return s
    except Exception:
        pass
    return _env_get("S25_SHARED_SECRET")


def set_degraded_mode(active: bool, reason: str = ""):
    DEGRADED_FLAG.parent.mkdir(parents=True, exist_ok=True)
    if active:
        DEGRADED_FLAG.write_text(json.dumps({
            "active": True,
            "activated_at": time.time(),
            "reason": reason,
        }, indent=2))
    else:
        if DEGRADED_FLAG.exists():
            DEGRADED_FLAG.unlink()


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    try:
        r = requests.get(f"{COCKPIT}/api/mesh/state", timeout=5)
        state = r.json().get("state", {})
    except Exception as e:
        logger.error("failed to fetch state: %s", e)
        return 1

    global_status = state.get("global_status", "unknown")
    mesh_status = state.get("mesh_status", "unknown")
    online = state.get("agents_online", 0)
    expected = state.get("agents_expected", 0)
    active_inc = state.get("active_incidents", 0)

    logger.info("state: global=%s mesh=%s agents=%d/%d incidents=%d",
                global_status, mesh_status, online, expected, active_inc)

    # Decide degraded_mode
    if global_status in ("critical", "severe"):
        set_degraded_mode(True, f"global_status={global_status}")
        logger.warning("🚨 degraded_mode ENABLED — non-critical missions throttled")
    elif global_status == "degraded":
        # Warn but don't throttle yet
        logger.info("ℹ️  mesh degraded but not critical — watching")
        if DEGRADED_FLAG.exists():
            set_degraded_mode(False)
    else:
        if DEGRADED_FLAG.exists():
            set_degraded_mode(False)
            logger.info("✅ degraded_mode DISABLED — healthy again")

    # Auto-open incident if critical AND no matching active incident
    if global_status in ("critical", "severe") and active_inc == 0:
        secret = _secret()
        headers = {"X-S25-Secret": secret} if secret else {}
        try:
            requests.post(
                f"{COCKPIT}/api/mesh/open_incident",
                headers=headers,
                json={
                    "severity": global_status,
                    "title": f"Watchdog detected {global_status} state",
                    "summary": f"agents {online}/{expected} online, active_incidents=0",
                    "category": "watchdog_auto",
                    "source": "mesh_watchdog",
                    "evidence": state,
                    "recommended_actions": [
                        "review_agents_offline",
                        "check_akash_bridges",
                        "enable_degraded_mode",
                    ],
                    "owner": "TRINITY",
                },
                timeout=5,
            )
            logger.warning("auto-incident opened (no prior tracking)")
        except Exception as e:
            logger.warning("failed to open incident: %s", e)

    print(json.dumps({
        "global_status": global_status,
        "degraded_mode": DEGRADED_FLAG.exists(),
        "online": online, "expected": expected,
        "active_incidents": active_inc,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
