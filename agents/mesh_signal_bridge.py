#!/usr/bin/env python3
"""
S25 Mesh Signal Bridge
======================
Cron */2. Reads agents_state.json (the S25 mesh dispatch target) and
forwards any fresh non-already-dispatched signal from Trinity / Merlin /
Oracle / ARKON5 / Comet to /webhook/tradingview with source = original
agent name. The webhook applies the agent's weight (TV_WEIGHTS) and
routes through the same risk + execution stack as TV alerts.

Idempotency: a dispatch-key hash is stored in memory/mesh_dispatched.json.
Freshness: only signals <= 4 min old are dispatched.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("s25.mesh_bridge")

REPO = Path(__file__).resolve().parent.parent
STATE_IN = REPO / "memory" / "agents_state.json"
STATE_OUT = REPO / "memory" / "mesh_dispatched.json"
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")

# Skip: already executed via their own path (don't dispatch our own)
SKIP_SOURCES = {"TRADINGVIEW", "AUTO_SCANNER", "MESH_BRIDGE", "DCA", ""}
# Max age of a signal to be dispatchable
FRESH_SEC = 240
# Min effective confidence to dispatch
MIN_CONF = 0.55


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def load_dispatched() -> Dict:
    if not STATE_OUT.exists():
        return {}
    try:
        return json.loads(STATE_OUT.read_text())
    except Exception:
        return {}


def save_dispatched(d: Dict):
    STATE_OUT.parent.mkdir(parents=True, exist_ok=True)
    STATE_OUT.write_text(json.dumps(d, indent=2))


def signal_key(sig: Dict) -> str:
    s = f"{sig.get('ts','')}|{sig.get('source','')}|{sig.get('symbol','')}|{sig.get('action','')}|{sig.get('confidence',0)}"
    return sha1(s.encode()).hexdigest()[:16]


def parse_ts(ts: str) -> Optional[float]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).timestamp()
    except Exception:
        return None


def load_buffer() -> List[Dict]:
    if not STATE_IN.exists():
        return []
    try:
        data = json.loads(STATE_IN.read_text())
        buf = list((data.get("pipeline", {}) or {}).get("signals_buffer", []) or [])
        # Inject the live ARKON5 state as a signal if not already in buffer.
        # ARKON5 publishes action/conf into /api/status but not into signals_buffer,
        # so we synthesize a signal entry for the bridge.
        arkon_sig = _load_arkon_status(data)
        if arkon_sig:
            buf.append(arkon_sig)
        return buf
    except Exception as e:
        logger.warning("state read failed: %s", e)
        return []


def _load_arkon_status(agents_state: Dict) -> Optional[Dict]:
    """Read ARKON5 from /api/status (cockpit). Returns a synthetic signal or None."""
    try:
        r = requests.get(f"{COCKPIT}/api/status", timeout=5)
        if r.status_code != 200:
            return None
        d = r.json()
        action = str(d.get("arkon5_action", "")).upper()
        conf_s = str(d.get("arkon5_conf", "") or "0")
        try:
            conf = float(conf_s) / 100.0 if float(conf_s) > 1 else float(conf_s)
        except Exception:
            return None
        if action not in ("BUY", "SELL") or conf < 0.60:
            return None
        ts = d.get("timestamp") or datetime.now(timezone.utc).isoformat()
        return {
            "ts": ts,
            "source": "ARKON5",
            "symbol": "BTC/USD",  # ARKON5 targets BTC by convention
            "action": action,
            "confidence": round(conf, 3),
            "price": 0,
            "synthetic": True,
        }
    except Exception as e:
        logger.warning("ARKON5 status read failed: %s", e)
        return None


def normalize_symbol(sym: str) -> Optional[str]:
    """Convert BTC/USD or BTCUSD or BTC-USD to ticker format the webhook expects."""
    if not sym:
        return None
    sym = sym.upper().replace("/", "").replace("-", "")
    if not sym.endswith(("USD", "USDT", "USDC")):
        return None
    return sym


def dispatch_signal(sig: Dict) -> Dict:
    tv_pp = _env_get("TV_PASSPHRASE")
    ticker = normalize_symbol(sig.get("symbol", ""))
    if not ticker:
        return {"ok": False, "reason": "bad_symbol"}
    body = {
        "ticker": ticker,
        "action": str(sig.get("action", "")).upper(),
        "price": float(sig.get("price") or 0),
        "confidence": float(sig.get("confidence") or 0),
        "strategy": f"[mesh:{sig.get('source','?')}] auto-relay",
        "source": sig.get("source", "MESH_BRIDGE"),
        "interval": "mesh",
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
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    now = time.time()
    dispatched = load_dispatched()
    buffer = load_buffer()
    fired = 0
    skipped_stale = 0
    skipped_dup = 0
    skipped_conf = 0
    skipped_source = 0

    for sig in buffer:
        src = str(sig.get("source", "")).upper()
        if src in SKIP_SOURCES:
            skipped_source += 1
            continue
        action = str(sig.get("action", "")).upper()
        if action not in ("BUY", "SELL"):
            continue
        conf = float(sig.get("confidence") or 0)
        if conf < MIN_CONF:
            skipped_conf += 1
            continue

        ts = parse_ts(sig.get("ts", ""))
        if ts is None or (now - ts) > FRESH_SEC:
            skipped_stale += 1
            continue

        key = signal_key(sig)
        if key in dispatched:
            skipped_dup += 1
            continue

        result = dispatch_signal(sig)
        dispatched[key] = {
            "ts": ts, "source": src, "symbol": sig.get("symbol"),
            "action": action, "conf": conf, "result": result,
        }
        fired += 1
        logger.info("DISPATCH %s %s %s conf=%.2f => %s",
                    src, action, sig.get("symbol"), conf, result)

    # Prune old entries from dispatched state (keep last 500)
    if len(dispatched) > 500:
        sorted_keys = sorted(dispatched.items(), key=lambda kv: kv[1].get("ts", 0))
        dispatched = dict(sorted_keys[-500:])

    save_dispatched(dispatched)
    logger.info("tick: %d buffer | fired=%d | skip(stale=%d dup=%d conf=%d src=%d)",
                len(buffer), fired, skipped_stale, skipped_dup, skipped_conf, skipped_source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
