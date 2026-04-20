#!/usr/bin/env python3
"""
S25 Trailing Stop Manager
==========================
Runs every few minutes. For each open bracket SELL (S25-placed), checks
the current spot price vs the entry, and tightens the stop_trigger_price
when profit thresholds are hit.

Rules:
  - trail_activation_pct     move SL to breakeven (entry price) once profit >= threshold
  - trail_step_pct           once above activation, trail SL at `trail_step_pct` below current peak

Implementation:
  - List open bracket orders via Coinbase list_orders filtered by client_order_id prefix "s25-br-"
  - For each order, fetch its entry price from the trades_log.jsonl (matching buy event)
  - Compute current spot; decide whether to update stop_trigger_price
  - Use edit_order to change the stop price (Coinbase API allows it)

Cron: */5 (same cadence as auto_signal_scanner is fine)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("s25.trailing")


STATE_FILE = Path(__file__).resolve().parent.parent / "memory" / "trailing_state.json"
TRADES_LOG = Path(__file__).resolve().parent.parent / "memory" / "trades_log.jsonl"


def _load_state() -> Dict[str, Dict]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _save_state(s: Dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, indent=2))


def _most_recent_buy_entry(product_id: str) -> Optional[Dict]:
    """Find the most recent live BUY in the trade log for this product."""
    if not TRADES_LOG.exists():
        return None
    buys: List[Dict] = []
    for line in TRADES_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            t = json.loads(line)
        except Exception:
            continue
        if (t.get("symbol") == product_id and t.get("side") == "BUY"
                and t.get("success") and t.get("mode") == "live"):
            buys.append(t)
    return buys[-1] if buys else None


def run_tick():
    from agents.coinbase_executor import get_executor
    from agents import risk_engine

    cfg = risk_engine.get_config()
    if not cfg.get("trail_enabled", True):
        logger.info("trailing disabled")
        return {"ok": True, "updates": 0, "skipped": "trail_disabled"}

    exe = get_executor()
    c = exe._get_client()
    if c is None:
        return {"ok": False, "error": "client_unavailable"}

    try:
        resp = c.list_orders(order_status="OPEN", limit=50)
    except Exception as e:
        return {"ok": False, "error": f"list_orders failed: {e}"}

    d = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
    orders = d.get("orders") or []

    activation = cfg.get("trail_activation_pct", 3.0) / 100.0
    step = cfg.get("trail_step_pct", 2.0) / 100.0

    state = _load_state()
    updates = 0
    touched: List[Dict] = []

    for o in orders:
        od = o if isinstance(o, dict) else getattr(o, "__dict__", {})
        coid = od.get("client_order_id") or ""
        if not coid.startswith("s25-br-"):
            continue  # only our bracket sells
        product = od.get("product_id")
        side = od.get("side")
        if side != "SELL" or not product:
            continue
        order_id = od.get("order_id")
        if not order_id:
            continue

        # Pull trigger price
        cfg_field = od.get("order_configuration") or {}
        cfg_field = cfg_field if isinstance(cfg_field, dict) else {}
        trigger_key = next((k for k in cfg_field if "bracket" in k.lower()), None)
        inner = cfg_field.get(trigger_key) if trigger_key else None
        inner = inner if isinstance(inner, dict) else {}
        current_stop = inner.get("stop_trigger_price")
        current_limit = inner.get("limit_price")
        try:
            current_stop = float(current_stop) if current_stop is not None else None
            current_limit = float(current_limit) if current_limit is not None else None
        except Exception:
            current_stop = None; current_limit = None

        # Find the entry price for this position
        buy_record = _most_recent_buy_entry(product)
        entry_price = None
        if buy_record:
            try:
                entry_price = float(buy_record.get("avg_price") or 0)
            except Exception:
                entry_price = None
        if not entry_price or entry_price <= 0:
            continue

        spot = exe.get_product_price(product)
        if not spot:
            continue

        profit_pct = (spot - entry_price) / entry_price
        st_entry = state.setdefault(order_id, {"peak_price": spot, "activated": False})
        if spot > st_entry["peak_price"]:
            st_entry["peak_price"] = spot
        peak = st_entry["peak_price"]

        new_stop = current_stop
        action = None

        if profit_pct >= activation and not st_entry["activated"]:
            # Move stop to breakeven (entry) at least
            if current_stop is None or current_stop < entry_price:
                new_stop = entry_price
                st_entry["activated"] = True
                action = "breakeven"
        elif st_entry["activated"]:
            # Trail below peak
            desired_stop = peak * (1 - step)
            if current_stop is None or desired_stop > current_stop:
                new_stop = desired_stop
                action = f"trail (peak={peak:.6f})"

        if action and new_stop is not None and (current_stop is None or new_stop > current_stop):
            try:
                # edit_order expects string prices
                edit_resp = c.edit_order(
                    order_id=order_id,
                    stop_trigger_price=f"{new_stop:.8f}",
                    limit_price=f"{current_limit:.8f}" if current_limit else None,
                )
                ed = edit_resp if isinstance(edit_resp, dict) else getattr(edit_resp, "__dict__", {})
                success = ed.get("success")
                updates += 1
                touched.append({
                    "order_id": order_id, "product": product,
                    "entry": entry_price, "spot": spot, "profit_pct": round(profit_pct * 100, 3),
                    "old_stop": current_stop, "new_stop": new_stop,
                    "action": action, "edit_ok": bool(success),
                })
                logger.info("trail %s [%s] entry=%.6f spot=%.6f profit=%.2f%% stop %.6f->%.6f ok=%s",
                            product, action, entry_price, spot, profit_pct*100,
                            current_stop or 0, new_stop, success)
            except Exception as e:
                logger.warning("edit_order failed for %s: %s", order_id, e)

    _save_state(state)
    return {"ok": True, "updates": updates, "touched": touched}


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    r = run_tick()
    print(json.dumps(r, indent=2, default=str))


if __name__ == "__main__":
    main()
