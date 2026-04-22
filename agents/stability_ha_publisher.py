#!/usr/bin/env python3
"""
S25 Stability HA Publisher — pushes Phase 2 stability metrics to Home Assistant.

Creates sensors:
  - sensor.s25_backpressure_level (ok | warn | congested)
  - sensor.s25_backpressure_signals_60s
  - sensor.s25_backpressure_missions_queued
  - sensor.s25_breakers_open
  - sensor.s25_dlq_total
  - binary_sensor.s25_mesh_safe_mode (on if degraded_mode active or congested)

Cron every 1 min. Token + URL read from .env.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("s25.stability_ha")

REPO = Path(__file__).resolve().parent.parent


def _env_file_get(key: str) -> Optional[str]:
    env = REPO / ".env"
    if not env.exists():
        return None
    try:
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def _ha_config():
    url = os.getenv("HA_URL") or _env_file_get("HA_URL") or "http://10.0.0.136:8123"
    token = os.getenv("HA_TOKEN") or _env_file_get("HA_TOKEN") or ""
    if not (url and token):
        raise RuntimeError("HA_URL / HA_TOKEN missing")
    return url.rstrip("/"), token


def _post_state(url, token, entity, state, attrs=None) -> bool:
    try:
        r = requests.post(
            f"{url}/api/states/{entity}",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json={"state": str(state), "attributes": attrs or {}},
            timeout=6,
        )
        return r.status_code in (200, 201)
    except Exception as e:
        logger.warning("HA POST %s err: %s", entity, e)
        return False


def collect_and_publish():
    sys.path.insert(0, str(REPO))
    from agents.stability_layer import (
        backpressure_level,
        list_breakers,
        stats,
    )

    url, token = _ha_config()
    bp = backpressure_level()
    breakers = list_breakers().get("breakers", {})
    open_breakers = [k for k, v in breakers.items() if v.get("state") == "open"]
    st = stats()

    degraded = False
    dfile = REPO / "memory" / "command_mesh" / "degraded_mode.json"
    try:
        if dfile.exists():
            degraded = bool(json.loads(dfile.read_text()).get("active"))
    except Exception:
        pass

    pushed = {}
    pushed["sensor.s25_backpressure_level"] = _post_state(
        url, token, "sensor.s25_backpressure_level", bp["level"],
        {
            "friendly_name": "S25 Mesh Backpressure",
            "icon": "mdi:speedometer",
            "signals_60s": bp["signal_rate_60s"],
            "missions_queued": bp["missions_queued"],
            "retries_due": bp["retries_due"],
            "thresholds": bp["thresholds"],
        },
    )
    pushed["sensor.s25_backpressure_signals_60s"] = _post_state(
        url, token, "sensor.s25_backpressure_signals_60s",
        bp["signal_rate_60s"],
        {"unit_of_measurement": "sig/min",
         "friendly_name": "S25 Signals last 60s"},
    )
    pushed["sensor.s25_backpressure_missions_queued"] = _post_state(
        url, token, "sensor.s25_backpressure_missions_queued",
        bp["missions_queued"],
        {"friendly_name": "S25 Missions Queued",
         "icon": "mdi:format-list-checks"},
    )
    pushed["sensor.s25_breakers_open"] = _post_state(
        url, token, "sensor.s25_breakers_open",
        len(open_breakers),
        {
            "friendly_name": "S25 Circuit Breakers Open",
            "icon": "mdi:electric-switch-closed",
            "total": st.get("breakers_total", 0),
            "open_keys": open_breakers,
        },
    )
    pushed["sensor.s25_dlq_total"] = _post_state(
        url, token, "sensor.s25_dlq_total",
        st.get("dlq_total", 0),
        {"friendly_name": "S25 DLQ Total",
         "icon": "mdi:email-alert"},
    )
    safe_state = "on" if (bp["level"] == "congested" or degraded) else "off"
    pushed["binary_sensor.s25_mesh_safe_mode"] = _post_state(
        url, token, "binary_sensor.s25_mesh_safe_mode", safe_state,
        {
            "friendly_name": "S25 Mesh Safe Mode",
            "device_class": "problem",
            "icon": "mdi:alert-octagon",
            "backpressure": bp["level"],
            "degraded_flag": degraded,
        },
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pushed": pushed,
        "backpressure": bp,
        "breakers_open": len(open_breakers),
        "dlq_total": st.get("dlq_total", 0),
        "safe_mode": safe_state,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    res = collect_and_publish()
    print(json.dumps(res, indent=2))
