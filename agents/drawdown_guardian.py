#!/usr/bin/env python3
"""
S25 Drawdown Guardian
=====================
Runs every 10 min via cron. If total P&L (realized + unrealized) drops
below -X% of portfolio, automatically flips LIVE trading OFF and toggles
HA kill-switch ON.

Thresholds:
  - `soft`: below this, log a warning but keep trading
  - `hard`: below this, kill-switch ON + LIVE flag OFF + HA notification

State kept in memory/drawdown_state.json so a single breach fires once
(no flap during the same breach window). A reset is possible via manual
toggle of the kill-switch back to OFF.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import requests

logger = logging.getLogger("s25.drawdown_guardian")

REPO = Path(__file__).resolve().parent.parent
STATE_FILE = REPO / "memory" / "drawdown_state.json"

SOFT_THRESHOLD_PCT = -3.0   # warn
HARD_THRESHOLD_PCT = -5.0   # kill

COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def _ha_service(domain: str, service: str, entity_id: str):
    url = _env_get("HA_URL") or "http://10.0.0.136:8123"
    token = _env_get("HA_TOKEN")
    if not token:
        return {"ok": False, "error": "no HA_TOKEN"}
    try:
        r = requests.post(
            f"{url.rstrip('/')}/api/services/{domain}/{service}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"entity_id": entity_id},
            timeout=6,
        )
        return {"ok": r.status_code == 200, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _ha_notify(title: str, message: str):
    url = _env_get("HA_URL") or "http://10.0.0.136:8123"
    token = _env_get("HA_TOKEN")
    if not token:
        return
    try:
        requests.post(
            f"{url.rstrip('/')}/api/services/persistent_notification/create",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"title": title, "message": message},
            timeout=6,
        )
    except Exception:
        pass


def load_state() -> Dict:
    if not STATE_FILE.exists():
        return {"last_breach_level": "none", "last_check_ts": 0}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"last_breach_level": "none", "last_check_ts": 0}


def save_state(s: Dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, indent=2))


def compute_drawdown_pct() -> Optional[float]:
    """Return total_pnl as % of portfolio."""
    try:
        r = requests.get(f"{COCKPIT}/api/trading/pnl", timeout=6)
        pnl = r.json() if r.status_code == 200 else None
        r2 = requests.get(f"{COCKPIT}/api/coinbase/portfolio", timeout=6)
        port = r2.json() if r2.status_code == 200 else None
        if not pnl or not port:
            return None
        total_pnl = float(pnl.get("total_pnl") or 0)
        portfolio = float(port.get("total_usd") or 0)
        if portfolio <= 0:
            return None
        return (total_pnl / portfolio) * 100
    except Exception as e:
        logger.warning("compute_drawdown_pct failed: %s", e)
        return None


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    dd_pct = compute_drawdown_pct()
    if dd_pct is None:
        logger.warning("could not compute drawdown; skipping")
        return 1

    state = load_state()
    state["last_check_ts"] = time.time()
    state["last_drawdown_pct"] = round(dd_pct, 3)

    now_level = "none"
    if dd_pct <= HARD_THRESHOLD_PCT:
        now_level = "hard"
    elif dd_pct <= SOFT_THRESHOLD_PCT:
        now_level = "soft"

    prev_level = state.get("last_breach_level", "none")

    if now_level == "hard" and prev_level != "hard":
        logger.error("DRAWDOWN HARD breach: %.2f%% <= %.1f%%. Killing LIVE trading.",
                     dd_pct, HARD_THRESHOLD_PCT)
        # 1) flip LIVE off
        try:
            requests.post(f"{COCKPIT}/api/coinbase/live-mode",
                          json={"enabled": False}, timeout=6)
        except Exception as e:
            logger.warning("flip LIVE off failed: %s", e)
        # 2) turn HA kill-switch ON
        _ha_service("input_boolean", "turn_on", "input_boolean.s25_kill_switch")
        # 3) notify
        _ha_notify(
            "🛑 S25 DRAWDOWN HARD BREACH",
            f"Total P&L {dd_pct:.2f}% breached {HARD_THRESHOLD_PCT}%. "
            "LIVE trading disabled + kill-switch ON. Manual reset required.",
        )
    elif now_level == "soft" and prev_level not in ("soft", "hard"):
        logger.warning("DRAWDOWN SOFT warn: %.2f%%", dd_pct)
        _ha_notify(
            "⚠️ S25 Drawdown warning",
            f"Total P&L at {dd_pct:.2f}%. Still trading, monitor closely.",
        )
    elif now_level == "none" and prev_level != "none":
        logger.info("drawdown recovered: %.2f%%", dd_pct)
        _ha_notify(
            "✅ S25 Drawdown recovered",
            f"Total P&L back to {dd_pct:.2f}%. You may re-enable LIVE manually.",
        )

    state["last_breach_level"] = now_level
    save_state(state)
    logger.info("drawdown=%.2f%% level=%s (prev=%s)", dd_pct, now_level, prev_level)
    return 0


if __name__ == "__main__":
    sys.exit(main())
