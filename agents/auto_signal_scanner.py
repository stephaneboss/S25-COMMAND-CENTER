#!/usr/bin/env python3
"""
S25 Auto Signal Scanner v2 — strategy-registry dispatcher
==========================================================
For each coin in the whitelist, build a MarketData snapshot (TV scanner
for RSI/change, Coinbase candles for MA/breakout) and run every enabled
strategy. Each signal gets pushed to /webhook/tradingview.

Cooldown per (strategy, symbol) pair: 15 min.
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
COOLDOWN_FILE = Path(__file__).resolve().parent.parent / ".auto_scanner_cooldown.json"
COOLDOWN_SEC = 15 * 60


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


def tv_scan() -> Dict[str, Dict]:
    """Return {tv_symbol: {rsi, change, close, volume}}."""
    tickers = [f"COINBASE:{tv}" for _, tv in WHITELIST]
    body = {
        "symbols": {"tickers": tickers, "query": {"types": []}},
        "columns": ["close", "change", "RSI", "volume"],
    }
    out: Dict[str, Dict] = {}
    try:
        r = requests.post(TV_SCAN_URL, json=body, timeout=8)
        r.raise_for_status()
        for row in r.json().get("data", []):
            s_full = row.get("s", "")
            vals = row.get("d", [])
            if len(vals) < 4:
                continue
            tv_sym = s_full.split(":", 1)[-1]
            out[tv_sym] = {
                "close": float(vals[0]) if vals[0] is not None else None,
                "change": float(vals[1]) if vals[1] is not None else None,
                "rsi": float(vals[2]) if vals[2] is not None else None,
                "volume": float(vals[3]) if vals[3] is not None else None,
            }
    except Exception as e:
        logger.error("TV scan failed: %s", e)
    return out


def build_markets() -> List:
    from strategies.base import MarketData
    # Import executor only here so cron (no DBus) doesn't try to init it
    # when it can't read the keyring — in that case we skip candle-based
    # strategies but still run RSI ones.
    try:
        from agents.coinbase_executor import get_executor
        exe = get_executor()
        can_candles = bool(exe._api_key and exe._api_secret)
    except Exception as e:
        logger.warning("executor unavailable (expected in cron): %s", e)
        exe = None
        can_candles = False

    tv = tv_scan()
    markets: List[MarketData] = []
    for cb_sym, tv_sym in WHITELIST:
        row = tv.get(tv_sym, {})
        # Candles optional — only populated if executor available (via cockpit)
        candles_1h = []
        if can_candles and exe:
            try:
                candles_1h = exe.get_candles(cb_sym, "ONE_HOUR", limit=40)
            except Exception:
                candles_1h = []
        markets.append(MarketData(
            symbol=cb_sym,
            spot=row.get("close"),
            change_24h_pct=row.get("change"),
            rsi=row.get("rsi"),
            volume=row.get("volume"),
            candles_1h=candles_1h,
            candles_15m=[],
        ))
    return markets


def push_signal_to_webhook(symbol: str, signal) -> Dict:
    tv_pp = _env_get("TV_PASSPHRASE")
    # Convert BTC-USD -> BTCUSD for the webhook
    ticker = symbol.replace("-", "")
    body = {
        "ticker": ticker,
        "action": signal.action,
        "price": 0,  # spot is on the other side
        "confidence": signal.confidence,
        "usd_amount": signal.usd_amount,
        "strategy": f"[{signal.strategy}] {signal.reason}",
        "interval": "auto",
        "passphrase": tv_pp,
    }
    try:
        r = requests.post(f"{COCKPIT}/webhook/tradingview", json=body, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {"ok": True, "verdict": d.get("verdict"),
                    "cex_ok": d.get("cex_result", {}).get("ok")}
        return {"ok": False, "http": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info("=== auto_signal_scanner v2 cycle ===")

    # Bootstrap registry (idempotent)
    try:
        import strategies
        registry = strategies.bootstrap()
    except Exception as e:
        logger.error("strategy bootstrap failed: %s", e)
        return 1

    markets = build_markets()
    logger.info("markets built: %d (%s)", len(markets),
                ", ".join(f"{m.symbol}=rsi:{m.rsi}" for m in markets if m.rsi is not None))

    hits = registry.dispatch(markets)
    cooldown = load_cooldown()
    now = time.time()
    fired = 0
    for strat_name, symbol, sig in hits:
        cd_key = f"{strat_name}::{symbol}"
        if cooldown.get(cd_key, 0) + COOLDOWN_SEC > now:
            logger.info("cooldown skip: %s", cd_key)
            continue
        res = push_signal_to_webhook(symbol, sig)
        cooldown[cd_key] = now
        fired += 1
        logger.info("FIRED [%s] %s %s conf=%.2f usd=%.2f verdict=%s cex_ok=%s",
                    strat_name, sig.action, symbol, sig.confidence,
                    sig.usd_amount, res.get("verdict"), res.get("cex_ok"))

    save_cooldown(cooldown)
    logger.info("cycle done | enabled=%d | hits=%d | fired=%d",
                len(registry.enabled_strategies()), len(hits), fired)
    return 0


if __name__ == "__main__":
    sys.exit(main())
