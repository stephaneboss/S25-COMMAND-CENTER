#!/usr/bin/env python3
"""
S25 DCA Scheduler
=================
Dollar-cost-average buyer. Runs every N minutes via cron; for each
configured schedule, checks if the interval has elapsed and pushes a
BUY signal through /webhook/tradingview.

Config at memory/dca_schedules.json:
[
  {
    "name": "btc_weekly",
    "symbol": "BTC-USD",
    "usd": 10.0,
    "interval_hours": 168,
    "enabled": true
  }
]

Commands:
  python -m agents.dca_scheduler              # run one tick
  python -m agents.dca_scheduler --list       # show schedules + next fire
  python -m agents.dca_scheduler --add '{"name":"btc_w","symbol":"BTC-USD","usd":10,"interval_hours":168}'
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("s25.dca")

CONFIG_FILE = Path(__file__).resolve().parent.parent / "memory" / "dca_schedules.json"
STATE_FILE = Path(__file__).resolve().parent.parent / "memory" / "dca_state.json"
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")


def _env_get(key: str) -> str:
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def load_schedules() -> List[Dict]:
    if not CONFIG_FILE.exists():
        return []
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return []


def save_schedules(schedules: List[Dict]):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(schedules, indent=2))


def load_state() -> Dict[str, float]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state: Dict[str, float]):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def push_buy(symbol: str, usd: float, name: str) -> Dict:
    tv_pp = _env_get("TV_PASSPHRASE")
    ticker = symbol.replace("-", "")
    body = {
        "ticker": ticker, "action": "BUY", "price": 0,
        "confidence": 0.99,  # DCA is pre-decided, not a read of market
        "usd_amount": float(usd),
        "strategy": f"[DCA:{name}]",
        "interval": "dca",
        "passphrase": tv_pp,
    }
    try:
        r = requests.post(f"{COCKPIT}/webhook/tradingview", json=body, timeout=10)
        d = r.json() if r.status_code == 200 else {}
        return {"http": r.status_code, "verdict": d.get("verdict"),
                "cex_ok": d.get("cex_result", {}).get("ok")}
    except Exception as e:
        return {"error": str(e)}


def tick():
    schedules = load_schedules()
    state = load_state()
    now = time.time()
    fired = 0
    for s in schedules:
        if not s.get("enabled", True):
            continue
        name = s["name"]
        interval = float(s.get("interval_hours", 24)) * 3600
        last = float(state.get(name, 0))
        if now - last < interval:
            continue
        result = push_buy(s["symbol"], s["usd"], name)
        state[name] = now
        fired += 1
        logger.info("DCA FIRED %s %s $%.2f => %s", name, s["symbol"], s["usd"], result)
    save_state(state)
    return fired


def list_schedules():
    schedules = load_schedules()
    state = load_state()
    now = time.time()
    out = []
    for s in schedules:
        name = s["name"]
        interval = float(s.get("interval_hours", 24)) * 3600
        last = float(state.get(name, 0))
        next_fire = last + interval
        out.append({
            **s,
            "last_fire_ts": last or None,
            "next_fire_ts": next_fire if last else now,
            "next_fire_in_hours": round((next_fire - now) / 3600, 2) if last else 0,
        })
    return out


def add_schedule(payload: Dict):
    schedules = load_schedules()
    required = ("name", "symbol", "usd", "interval_hours")
    for k in required:
        if k not in payload:
            raise ValueError(f"missing {k}")
    payload.setdefault("enabled", True)
    # Replace if same name
    schedules = [s for s in schedules if s["name"] != payload["name"]]
    schedules.append(payload)
    save_schedules(schedules)
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--add", help="JSON payload {name,symbol,usd,interval_hours}")
    parser.add_argument("--remove", help="schedule name to remove")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if args.list:
        print(json.dumps(list_schedules(), indent=2, default=str)); return 0
    if args.add:
        r = add_schedule(json.loads(args.add))
        print(json.dumps(r, indent=2)); return 0
    if args.remove:
        schedules = load_schedules()
        schedules = [s for s in schedules if s["name"] != args.remove]
        save_schedules(schedules); print(f"removed: {args.remove}"); return 0

    fired = tick()
    logger.info("DCA tick done, %d fired", fired)
    return 0


if __name__ == "__main__":
    sys.exit(main())
