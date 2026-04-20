#!/usr/bin/env python3
"""
S25 COMET Sentiment Signal
==========================
Free rule-based sentiment trader. Uses ninja_routes (Fear&Greed + CoinGecko/Binance BTC)
and publishes a BUY/SELL signal into pipeline.signals_buffer when extreme.

Rules (contrarian mean-reversion):
  Fear&Greed <= 25 AND BTC 24h change <= -2%%   -> BUY  (buy-the-fear)
  Fear&Greed >= 75 AND BTC 24h change >= +4%%   -> SELL (sell-the-greed)
  else: nothing

Dedup: 1 signal per (action, fear bucket) per 30 min.
Cron */10. The mesh_signal_bridge will then forward to Coinbase webhook
with source=COMET (weight 0.50).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("s25.comet_sentiment")

REPO = Path(__file__).resolve().parent.parent
STATE_IN = REPO / "memory" / "agents_state.json"
COOLDOWN = REPO / "memory" / "comet_sentiment_cooldown.json"
COOLDOWN_SEC = 30 * 60

FG_BUY_MAX = 25
FG_SELL_MIN = 75
CHANGE_BUY_MAX = -2.0
CHANGE_SELL_MIN = 4.0


def load_cooldown() -> Dict:
    if not COOLDOWN.exists():
        return {}
    try:
        return json.loads(COOLDOWN.read_text())
    except Exception:
        return {}


def save_cooldown(d: Dict):
    COOLDOWN.parent.mkdir(parents=True, exist_ok=True)
    COOLDOWN.write_text(json.dumps(d))


def publish_signal(sig: Dict):
    """Append to pipeline.signals_buffer in agents_state.json."""
    try:
        data = json.loads(STATE_IN.read_text()) if STATE_IN.exists() else {}
        pipe = data.setdefault("pipeline", {})
        buf = pipe.setdefault("signals_buffer", [])
        buf.append(sig)
        pipe["signals_buffer"] = buf[-50:]
        STATE_IN.write_text(json.dumps(data))
        return True
    except Exception as e:
        logger.error("publish failed: %s", e)
        return False


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    try:
        sys.path.insert(0, str(REPO))
        from agents.ninja_routes import get_full_intel_snapshot
    except Exception as e:
        logger.error("ninja_routes import failed: %s", e)
        return 1

    snap = get_full_intel_snapshot()
    fg = (snap.get("fear_greed") or {}).get("value")
    btc = (snap.get("prices") or {}).get("bitcoin") or {}
    change = btc.get("usd_24h_change")
    price = btc.get("usd")
    if fg is None or change is None:
        logger.warning("missing fg=%s change=%s", fg, change); return 1
    fg = int(fg)
    change = float(change)

    action = None
    reason = None
    confidence = None
    if fg <= FG_BUY_MAX and change <= CHANGE_BUY_MAX:
        action = "BUY"
        # Deeper fear + deeper drop = higher conviction
        confidence = min(0.85, 0.55 + (FG_BUY_MAX - fg) / 100 + abs(change) / 30)
        reason = f"fear={fg}<={FG_BUY_MAX} change24h={change:.2f}%<={CHANGE_BUY_MAX}"
    elif fg >= FG_SELL_MIN and change >= CHANGE_SELL_MIN:
        action = "SELL"
        confidence = min(0.80, 0.55 + (fg - FG_SELL_MIN) / 100 + change / 30)
        reason = f"greed={fg}>={FG_SELL_MIN} change24h={change:.2f}%>={CHANGE_SELL_MIN}"
    else:
        logger.info("no extreme: fg=%d change24h=%.2f%% (neutral)", fg, change)
        return 0

    cooldown = load_cooldown()
    fg_bucket = "buy" if action == "BUY" else "sell"
    now = time.time()
    if cooldown.get(fg_bucket, 0) + COOLDOWN_SEC > now:
        logger.info("cooldown skip: %s (last fired %d min ago)",
                    fg_bucket, int((now - cooldown.get(fg_bucket, 0)) / 60))
        return 0

    signal = {
        "symbol": "BTC/USD",
        "action": action,
        "source": "COMET",
        "confidence": round(confidence, 3),
        "price": price,
        "ts": datetime.now(timezone.utc).isoformat(),
        "strategy": f"sentiment: {reason}",
    }
    if publish_signal(signal):
        cooldown[fg_bucket] = now
        save_cooldown(cooldown)
        logger.info("PUBLISHED COMET %s BTC conf=%.2f reason=%s",
                    action, confidence, reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
