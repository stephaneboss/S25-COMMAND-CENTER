#!/usr/bin/env python3
"""
S25 Stability Alerter — triggers HA notifications on mesh anomalies.

Runs every 2 min via cron. Checks:
  - backpressure level (warn/congested)
  - breakers_open count > 0
  - DLQ growth (> ALERT_DLQ_JUMP new entries since last tick)

Fires HA notify.mobile_app_s_25 + persistent_notification.create.
De-duplicates via memory/stability/alerter_state.json so the same alert
doesn't fire repeatedly (cooldown 15min per alert kind).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("s25.stability_alerter")

REPO = Path(__file__).resolve().parent.parent
STATE_PATH = REPO / "memory" / "stability" / "alerter_state.json"
COOLDOWN_SEC = 15 * 60
ALERT_DLQ_JUMP = 5


def _env_file_get(key: str) -> Optional[str]:
    env = REPO / ".env"
    if not env.exists():
        return None
    for line in env.read_text().splitlines():
        if line.strip().startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _ha_config():
    url = os.getenv("HA_URL") or _env_file_get("HA_URL") or "http://10.0.0.136:8123"
    token = os.getenv("HA_TOKEN") or _env_file_get("HA_TOKEN") or ""
    return url.rstrip("/"), token


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def _notify(kind: str, title: str, message: str) -> bool:
    url, token = _ha_config()
    if not token:
        logger.warning("no HA token")
        return False
    h = {"Authorization": f"Bearer {token}",
         "Content-Type": "application/json"}
    ok_all = True

    # Mobile push
    try:
        r = requests.post(
            f"{url}/api/services/notify/mobile_app_s_25",
            headers=h,
            json={"title": title, "message": message,
                  "data": {"tag": f"s25_stab_{kind}",
                           "channel": "S25 Stability",
                           "importance": "high"}},
            timeout=6,
        )
        ok_all = ok_all and (r.status_code < 400)
    except Exception as e:
        logger.warning("mobile_app notify err: %s", e)
        ok_all = False

    # Persistent notification (always fires)
    try:
        r = requests.post(
            f"{url}/api/services/persistent_notification/create",
            headers=h,
            json={"title": title, "message": message,
                  "notification_id": f"s25_stab_{kind}"},
            timeout=6,
        )
        ok_all = ok_all and (r.status_code < 400)
    except Exception as e:
        logger.warning("persistent_notification err: %s", e)
        ok_all = False

    return ok_all


def should_alert(kind: str, state: dict, now: float) -> bool:
    last = state.get("last_fired", {}).get(kind, 0)
    return (now - last) >= COOLDOWN_SEC


def record_fired(kind: str, state: dict, now: float):
    state.setdefault("last_fired", {})[kind] = now


def tick():
    sys.path.insert(0, str(REPO))
    from agents.stability_layer import (
        backpressure_level, list_breakers, stats,
    )

    bp = backpressure_level()
    breakers = list_breakers().get("breakers", {})
    open_breakers = [k for k, v in breakers.items()
                     if v.get("state") == "open"]
    st = stats()

    state = _load(STATE_PATH, {"last_fired": {}, "last_dlq_total": 0})
    now = time.time()
    fired = []

    # Backpressure congested
    if bp["level"] == "congested":
        if should_alert("bp_congested", state, now):
            ok = _notify(
                "bp_congested",
                "S25 Mesh CONGESTED",
                f"Signal rate {bp['signal_rate_60s']}/min, "
                f"queue {bp['missions_queued']}. Normal-priority "
                f"signals throttled with 429.",
            )
            if ok:
                record_fired("bp_congested", state, now)
                fired.append("bp_congested")

    # Backpressure warn
    elif bp["level"] == "warn":
        if should_alert("bp_warn", state, now):
            ok = _notify(
                "bp_warn",
                "S25 Mesh warn",
                f"Load climbing: sig60s={bp['signal_rate_60s']} "
                f"missions={bp['missions_queued']}",
            )
            if ok:
                record_fired("bp_warn", state, now)
                fired.append("bp_warn")

    # Breaker open
    if open_breakers:
        kind = f"breaker_{'_'.join(sorted(open_breakers))[:40]}"
        if should_alert(kind, state, now):
            ok = _notify(
                kind,
                f"S25 Circuit breaker OPEN — {len(open_breakers)}",
                "Open breakers: " + ", ".join(open_breakers),
            )
            if ok:
                record_fired(kind, state, now)
                fired.append(kind)

    # DLQ growth
    last_dlq = state.get("last_dlq_total", 0)
    dlq_now = st.get("dlq_total", 0)
    if dlq_now - last_dlq >= ALERT_DLQ_JUMP:
        if should_alert("dlq_growth", state, now):
            ok = _notify(
                "dlq_growth",
                "S25 DLQ growing",
                f"+{dlq_now - last_dlq} new DLQ entries "
                f"(total={dlq_now}). Check stability/dlq.",
            )
            if ok:
                record_fired("dlq_growth", state, now)
                fired.append("dlq_growth")
    state["last_dlq_total"] = dlq_now

    _save(STATE_PATH, state)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backpressure": bp["level"],
        "breakers_open": len(open_breakers),
        "dlq_total": dlq_now,
        "fired": fired,
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    tick()
