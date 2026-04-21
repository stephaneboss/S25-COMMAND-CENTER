#!/usr/bin/env python3
"""
S25 Quant Brain — self-tuning strategy orchestrator
====================================================
Cron every 6h. Learns from actual live trade performance and from
re-running backtests, then automatically tunes the strategy registry:

  - Disables strategies whose actual live P&L is losing (>5 trades, <-3%)
  - Raises usd_size for strategies profitable in live (>3 trades, >2%)
  - Removes losing symbols from per-strategy whitelists
  - Re-enables a disabled strategy if its backtest turned positive again

All decisions are logged to memory/quant_brain_log.jsonl with a rationale
and pushed as HA persistent_notification so the user sees what it did.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import requests

logger = logging.getLogger("s25.quant_brain")

REPO = Path(__file__).resolve().parent.parent
LOG_PATH = REPO / "memory" / "quant_brain_log.jsonl"
TRADES_LOG = REPO / "memory" / "trades_log.jsonl"
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")

# Decision thresholds — conservative on purpose
DISABLE_IF_PNL_PCT_BELOW = -3.0
DISABLE_MIN_TRADES = 5
RAISE_IF_PNL_PCT_ABOVE = 2.0
RAISE_MIN_TRADES = 3
WINDOW_HOURS_LIVE = 24 * 7   # analyze last 7 days of live trades
WINDOW_DAYS_BACKTEST = 30


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def log_decision(entry: Dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def ha_notify(title: str, message: str):
    url = _env_get("HA_URL") or "http://10.0.0.136:8123"
    token = _env_get("HA_TOKEN")
    if not token:
        return
    try:
        requests.post(
            f"{url.rstrip('/')}/api/services/persistent_notification/create",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json={"title": title, "message": message},
            timeout=6,
        )
    except Exception:
        pass


def live_performance_by_strategy_symbol() -> Dict:
    """Aggregate last WINDOW_HOURS_LIVE trades by (strategy, symbol).

    Uses the `strategy` field in each trade (TRADINGVIEW/rsi_dip/bollinger_bounce/etc)
    if it starts with '[strat_name]' or matches a known strategy prefix.
    Otherwise falls back to `source`.
    """
    if not TRADES_LOG.exists():
        return {}
    cutoff = time.time() - WINDOW_HOURS_LIVE * 3600
    agg: Dict[tuple, Dict] = defaultdict(
        lambda: {"trades": 0, "wins": 0, "losses": 0,
                 "total_usd": 0.0, "realized_pnl": 0.0}
    )
    # We need avg_price AND fills AND sides to compute realized P&L properly.
    # Simpler: count trades per (source, symbol), then pair-up consecutive
    # BUY/SELL in time-order to estimate P&L.
    trades = []
    for line in TRADES_LOG.read_text().splitlines():
        if not line.strip():
            continue
        try:
            t = json.loads(line)
        except Exception:
            continue
        ts = t.get("ts", 0)
        if not isinstance(ts, (int, float)) or ts < cutoff:
            continue
        if not t.get("success") or t.get("mode") != "live":
            continue
        strat = t.get("strategy", "") or ""
        src = t.get("source", "") or ""
        # Try to extract strategy name from '[name] ...'
        import re
        m = re.match(r"^\[([a-z_0-9]+)\]", strat)
        if m:
            strat_name = m.group(1)
        elif src in ("rsi_dip", "rsi_top", "bollinger_bounce", "stoch_rsi_bounce",
                     "ma_crossover", "breakout_1h", "macd_cross", "volume_surge"):
            strat_name = src
        else:
            strat_name = src.lower() or "unknown"
        trades.append({
            "ts": ts, "strategy": strat_name, "symbol": t.get("symbol", ""),
            "side": t.get("side", ""),
            "base_size": t.get("base_size"), "avg_price": t.get("avg_price"),
            "fee": t.get("fee") or 0,
            "usd_amount": t.get("usd_amount"),
        })
    trades.sort(key=lambda x: x["ts"])

    # FIFO pair-up per symbol to compute rough P&L per (strategy, symbol)
    open_lots: Dict[str, List[Dict]] = defaultdict(list)
    for t in trades:
        sym = t["symbol"]
        key = (t["strategy"], sym)
        agg[key]["trades"] += 1
        agg[key]["total_usd"] += float(t.get("usd_amount") or 0)
        size = t.get("base_size")
        price = t.get("avg_price")
        if not size or not price:
            continue
        if t["side"] == "BUY":
            open_lots[sym].append({"qty": float(size), "price": float(price),
                                    "fee": float(t.get("fee") or 0),
                                    "strat": t["strategy"]})
        elif t["side"] == "SELL":
            qty_to_close = float(size)
            while qty_to_close > 0 and open_lots[sym]:
                lot = open_lots[sym][0]
                matched = min(lot["qty"], qty_to_close)
                pnl = (float(price) - lot["price"]) * matched - lot["fee"] - float(t.get("fee") or 0)
                pnl_pct = ((float(price) / lot["price"]) - 1) * 100
                close_key = (lot["strat"], sym)  # attribute to strategy that opened
                agg[close_key]["realized_pnl"] += pnl
                if pnl > 0:
                    agg[close_key]["wins"] += 1
                else:
                    agg[close_key]["losses"] += 1
                lot["qty"] -= matched
                qty_to_close -= matched
                if lot["qty"] <= 1e-9:
                    open_lots[sym].pop(0)
    # Convert tuple keys to flat dicts
    return {
        f"{strat}|{sym}": {
            "strategy": strat, "symbol": sym, **v,
            "pnl_pct": round((v["realized_pnl"] / v["total_usd"]) * 100, 3)
                      if v["total_usd"] > 0 else 0,
        }
        for (strat, sym), v in agg.items()
    }


def run_backtest_matrix() -> List[Dict]:
    """Pull backtest matrix from the cockpit endpoint."""
    try:
        r = requests.get(f"{COCKPIT}/api/trading/backtest/all?days={WINDOW_DAYS_BACKTEST}",
                         timeout=120)
        if r.status_code == 200:
            return r.json().get("matrix", [])
    except Exception as e:
        logger.warning("backtest matrix fetch failed: %s", e)
    return []


def get_strategies_state() -> List[Dict]:
    try:
        r = requests.get(f"{COCKPIT}/api/trading/strategies", timeout=10)
        if r.status_code == 200:
            return r.json().get("strategies", [])
    except Exception:
        pass
    return []


def apply_toggle(name: str, enabled: bool):
    try:
        r = requests.post(f"{COCKPIT}/api/trading/strategies/{name}/toggle",
                          json={"enabled": enabled}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def apply_symbols(name: str, symbols: List[str]):
    try:
        r = requests.post(f"{COCKPIT}/api/trading/strategies/{name}/symbols",
                          json={"symbols": symbols}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def apply_usd_size(name: str, usd: float):
    try:
        r = requests.post(f"{COCKPIT}/api/trading/strategies/{name}/usd-size",
                          json={"usd": usd}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def decide_and_apply():
    live_perf = live_performance_by_strategy_symbol()
    backtest = run_backtest_matrix()
    strategies = get_strategies_state()

    # Index backtest by strategy
    bt_by_strat_sym = {f"{r['strategy']}|{r['symbol']}": r for r in backtest}

    decisions = []
    for s in strategies:
        name = s["name"]
        current_syms = s.get("symbols") or []
        usd = float(s.get("usd_size", 2.0))
        currently_enabled = bool(s.get("enabled"))

        # Aggregate actual live across symbols
        live_for_strat = [v for k, v in live_perf.items() if k.startswith(f"{name}|")]
        total_trades = sum(v["trades"] for v in live_for_strat)
        total_pnl_pct = sum(v["pnl_pct"] for v in live_for_strat) / len(live_for_strat) if live_for_strat else 0
        total_pnl_usd = sum(v["realized_pnl"] for v in live_for_strat)

        # Rule A: disable if losing and enough trades
        if currently_enabled and total_trades >= DISABLE_MIN_TRADES and total_pnl_pct < DISABLE_IF_PNL_PCT_BELOW:
            if apply_toggle(name, False):
                decisions.append({
                    "action": "disable",
                    "strategy": name,
                    "reason": f"actual live {total_pnl_pct:.2f}% over {total_trades} trades (threshold {DISABLE_IF_PNL_PCT_BELOW}%)",
                    "total_pnl_usd": round(total_pnl_usd, 3),
                })
            continue

        # Rule B: raise usd_size if winning
        if currently_enabled and total_trades >= RAISE_MIN_TRADES and total_pnl_pct > RAISE_IF_PNL_PCT_ABOVE:
            new_usd = min(usd * 1.25, 25.0)  # cap at $25
            if abs(new_usd - usd) > 0.5 and apply_usd_size(name, new_usd):
                decisions.append({
                    "action": "raise_usd_size",
                    "strategy": name,
                    "from": usd, "to": new_usd,
                    "reason": f"live {total_pnl_pct:.2f}% over {total_trades} trades",
                })

        # Rule C: trim whitelist by losing symbols
        if currently_enabled and len(current_syms) > 1:
            losing = []
            for sym in current_syms:
                k = f"{name}|{sym}"
                stats = live_perf.get(k)
                if stats and stats["trades"] >= 3 and stats["pnl_pct"] < -5:
                    losing.append(sym)
            if losing:
                new_syms = [s for s in current_syms if s not in losing]
                if new_syms and apply_symbols(name, new_syms):
                    decisions.append({
                        "action": "trim_symbols",
                        "strategy": name,
                        "dropped": losing,
                        "kept": new_syms,
                        "reason": "per-symbol actual loss > 5%",
                    })

        # Rule D: re-enable if backtest matrix shows a positive combo for a disabled strategy
        if not currently_enabled:
            profitable_syms = [
                r["symbol"] for k, r in bt_by_strat_sym.items()
                if r["strategy"] == name and r["trades"] >= 3
                and r["win_rate_pct"] >= 55 and r["total_pnl_pct"] >= 5
            ]
            if profitable_syms:
                if apply_toggle(name, True) and apply_symbols(name, profitable_syms):
                    decisions.append({
                        "action": "reenable",
                        "strategy": name,
                        "symbols": profitable_syms,
                        "reason": f"backtest 30d matrix shows {len(profitable_syms)} profitable combos",
                    })

    return {
        "decisions": decisions,
        "live_perf_rows": len(live_perf),
        "backtest_rows": len(backtest),
        "strategies_seen": len(strategies),
    }


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    logger.info("=== quant_brain tick ===")
    result = decide_and_apply()
    log_decision({"summary": result})

    if result["decisions"]:
        lines = []
        for d in result["decisions"]:
            lines.append(f"• {d['action']} {d['strategy']}: {d['reason']}")
        ha_notify(
            f"🧠 Quant Brain — {len(result['decisions'])} decision(s)",
            "\n".join(lines[:10]),
        )
        logger.info("decisions applied: %s", result["decisions"])
    else:
        logger.info("no changes — config stable")

    import json as _j
    print(_j.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
