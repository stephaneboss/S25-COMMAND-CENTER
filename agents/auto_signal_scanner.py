#!/usr/bin/env python3
"""
S25 Auto Signal Scanner
=======================
Runs every 5 min via cron. Pulls TradingView public scanner for the
Coinbase-listed whitelist, applies a simple momentum/dip strategy, and
pushes signals to /webhook/tradingview — which is still gated by the
file-flag for dry/live, so this stays safe-by-default.

Strategy v1 (simple, meant to be iterated on):
  dip_buy  : RSI < 35  AND 24h change < -3%   -> BUY (small)
  top_sell : RSI > 70  AND 24h change > +5%   -> SELL (only if held)
  else     : HOLD, no signal pushed

Rate limit: max 1 signal per symbol per 15 min (cooldown file).

Deploy:
  cron: every 5 min
  */5 * * * * /home/alienstef/S25-COMMAND-CENTER/.venv/bin/python3 -m agents.auto_signal_scanner >> /tmp/auto_signal_scanner.log 2>&1
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("s25.auto_scanner")

WHITELIST = [
    ("BTC-USD", "BTCUSD"),
    ("ETH-USD", "ETHUSD"),
    ("AKT-USD", "AKTUSD"),
    ("SOL-USD", "SOLUSD"),
    ("ATOM-USD", "ATOMUSD"),
    ("DOGE-USD", "DOGEUSD"),
]

TV_SCAN_URL = "https://scanner.tradingview.com/crypto/scan"
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")
COOLDOWN_FILE = Path.home() / "S25-COMMAND-CENTER" / ".auto_scanner_cooldown.json"
COOLDOWN_SEC = 15 * 60  # 15 min per symbol


def load_cooldown() -> Dict[str, float]:
    if not COOLDOWN_FILE.exists():
        return {}
    try:
        return json.loads(COOLDOWN_FILE.read_text())
    except Exception:
        return {}


def save_cooldown(d: Dict[str, float]):
    COOLDOWN_FILE.write_text(json.dumps(d))


def _env_get(key: str) -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def tv_scan() -> List[Dict]:
    tickers = [f"COINBASE:{tv}" for _, tv in WHITELIST]
    body = {
        "symbols": {"tickers": tickers, "query": {"types": []}},
        "columns": ["close", "change", "RSI", "volume"],
    }
    try:
        r = requests.post(TV_SCAN_URL, json=body, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", [])
        out = []
        for row in data:
            s_full = row.get("s", "")  # e.g. "COINBASE:AKTUSD"
            vals = row.get("d", [])
            if len(vals) < 4:
                continue
            out.append({
                "tv_symbol": s_full.split(":", 1)[-1],
                "close": float(vals[0]) if vals[0] is not None else None,
                "change": float(vals[1]) if vals[1] is not None else None,
                "rsi": float(vals[2]) if vals[2] is not None else None,
                "volume": float(vals[3]) if vals[3] is not None else None,
            })
        return out
    except Exception as e:
        logger.error("TV scan failed: %s", e)
        return []


def decide(row: Dict) -> Optional[Dict]:
    """Return a signal dict or None."""
    rsi = row.get("rsi")
    change = row.get("change")
    close = row.get("close")
    if rsi is None or change is None or close is None:
        return None

    # dip buy
    if rsi < 35 and change < -3.0:
        confidence = min(0.90, 0.65 + (35 - rsi) / 100 + abs(change) / 100)
        return {
            "action": "BUY",
            "confidence": round(confidence, 3),
            "strategy": f"dip_buy rsi={rsi:.1f} change={change:.2f}%",
            "usd_amount": 2.0,  # small fixed notional per auto signal
        }
    # top sell
    if rsi > 70 and change > 5.0:
        confidence = min(0.85, 0.60 + (rsi - 70) / 100 + change / 100)
        return {
            "action": "SELL",
            "confidence": round(confidence, 3),
            "strategy": f"top_sell rsi={rsi:.1f} change={change:.2f}%",
            "usd_amount": 2.0,
        }
    return None


def push_signal(tv_symbol: str, decision: Dict, close: float) -> Dict:
    tv_pp = _env_get("TV_PASSPHRASE")
    body = {
        "ticker": tv_symbol,
        "action": decision["action"],
        "price": close,
        "confidence": decision["confidence"],
        "usd_amount": decision["usd_amount"],
        "strategy": f"[auto] {decision['strategy']}",
        "interval": "5m_auto",
        "passphrase": tv_pp,
    }
    try:
        r = requests.post(f"{COCKPIT}/webhook/tradingview", json=body, timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {"ok": True, "verdict": d.get("verdict"), "cex_ok": d.get("cex_result", {}).get("ok")}
        return {"ok": False, "http": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info("auto scanner cycle starting")

    scan = tv_scan()
    if not scan:
        logger.warning("empty scan, exiting")
        return 1

    cooldown = load_cooldown()
    now = time.time()
    fired = 0
    for row in scan:
        tv = row["tv_symbol"]
        # cooldown check
        if cooldown.get(tv, 0) + COOLDOWN_SEC > now:
            continue
        decision = decide(row)
        if not decision:
            continue
        result = push_signal(tv, decision, row["close"])
        fired += 1
        cooldown[tv] = now
        logger.info(
            "FIRED %s %s $%.2f conf=%.2f verdict=%s cex_ok=%s",
            decision["action"], tv, decision["usd_amount"], decision["confidence"],
            result.get("verdict"), result.get("cex_ok"),
        )

    save_cooldown(cooldown)
    logger.info("cycle done, %d signal(s) fired, %d coins scanned", fired, len(scan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
