"""
S25 Position Tracker
====================
Append-only JSONL trade log + FIFO matching for realized P&L.

Design:
  - Every S25 order placed writes one line to trades_log.jsonl
  - "Positions" are computed by matching BUY/SELL per symbol in FIFO order
  - Unrealized P&L uses current spot price (Coinbase executor)
  - Realized P&L from closed buy/sell pairs
  - Fees are subtracted when known; otherwise assumed 1.2% taker on notional
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("s25.positions")

LOG_PATH = Path(__file__).resolve().parent.parent / "memory" / "trades_log.jsonl"


@dataclass
class TradeEntry:
    ts: float                    # unix time
    trade_id: str                # client_order_id
    order_id: Optional[str]      # Coinbase order id
    symbol: str                  # BTC-USD
    side: str                    # BUY|SELL
    usd_amount: float            # requested notional
    base_size: Optional[float]   # executed qty (if known)
    avg_price: Optional[float]   # filled avg price (if known)
    fee: Optional[float]         # USD
    mode: str                    # live|dry_run
    strategy: str                # free-form (TV alert, auto_scanner, etc.)
    source: str                  # webhook source tag
    success: bool                # order submit success
    notes: str = ""


def record_trade(entry: TradeEntry) -> bool:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(json.dumps(asdict(entry), default=str) + "\n")
        return True
    except Exception as e:
        logger.warning("record_trade failed: %s", e)
        return False


def _load_all() -> List[Dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    out = []
    try:
        for line in LOG_PATH.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception as e:
        logger.warning("load_all failed: %s", e)
    return out


def _live_trades(filter_mode: Optional[str] = "live") -> List[Dict[str, Any]]:
    trades = _load_all()
    trades = [t for t in trades if t.get("success")]
    if filter_mode:
        trades = [t for t in trades if t.get("mode") == filter_mode]
    return trades


def compute_positions(spot_fn=None) -> Dict[str, Any]:
    """Match BUY/SELL per symbol in FIFO order. Return open lots and realized P&L.

    spot_fn(symbol) -> current price (float) or None, used to compute unrealized P&L.
    """
    trades = _live_trades("live")
    trades.sort(key=lambda t: t.get("ts", 0))

    open_lots: Dict[str, List[Dict]] = {}  # symbol -> FIFO queue of {qty_left, cost_basis, ts}
    realized: List[Dict] = []

    for t in trades:
        sym = t.get("symbol", "")
        side = t.get("side", "")
        size = t.get("base_size")
        price = t.get("avg_price")
        fee = float(t.get("fee") or 0)
        if size is None or price is None or size == 0:
            # Fallback: if base_size missing, derive from usd_amount/price (rough)
            try:
                if price and t.get("usd_amount"):
                    size = float(t["usd_amount"]) / float(price)
            except Exception:
                continue
        if not size or not price:
            continue

        qty = float(size)
        px = float(price)

        if side == "BUY":
            open_lots.setdefault(sym, []).append({
                "ts": t.get("ts"),
                "qty_left": qty,
                "entry_price": px,
                "entry_fee_frac": fee / (qty * px) if qty * px > 0 else 0.012,
                "trade_id": t.get("trade_id"),
            })
        elif side == "SELL":
            remaining = qty
            lots = open_lots.setdefault(sym, [])
            while remaining > 0 and lots:
                lot = lots[0]
                matched = min(lot["qty_left"], remaining)
                buy_cost = matched * lot["entry_price"]
                sell_proceeds = matched * px
                entry_fee = buy_cost * lot["entry_fee_frac"]
                exit_fee = (fee * matched / qty) if qty > 0 else 0
                pnl = sell_proceeds - buy_cost - entry_fee - exit_fee
                realized.append({
                    "symbol": sym,
                    "qty": matched,
                    "entry_price": lot["entry_price"],
                    "exit_price": px,
                    "entry_ts": lot.get("ts"),
                    "exit_ts": t.get("ts"),
                    "pnl_usd": round(pnl, 4),
                    "pnl_pct": round((pnl / buy_cost) * 100, 3) if buy_cost else 0,
                    "buy_trade_id": lot.get("trade_id"),
                    "sell_trade_id": t.get("trade_id"),
                })
                lot["qty_left"] -= matched
                remaining -= matched
                if lot["qty_left"] <= 1e-9:
                    lots.pop(0)
            # If SELL exceeds open position (e.g. user pre-held) we silently
            # drop remainder — it's selling non-S25 inventory, not our tracked P&L.

    positions = []
    unrealized_total = 0.0
    for sym, lots in open_lots.items():
        lots = [l for l in lots if l.get("qty_left", 0) > 0]
        if not lots:
            continue
        qty_total = sum(l["qty_left"] for l in lots)
        cost = sum(l["qty_left"] * l["entry_price"] for l in lots)
        avg_entry = cost / qty_total if qty_total else 0
        spot = spot_fn(sym) if spot_fn else None
        mkt_value = (spot * qty_total) if spot else None
        unrealized = (mkt_value - cost) if mkt_value is not None else None
        if unrealized is not None:
            unrealized_total += unrealized
        positions.append({
            "symbol": sym,
            "qty": round(qty_total, 6),
            "avg_entry": round(avg_entry, 6),
            "cost_basis_usd": round(cost, 4),
            "spot_price": spot,
            "market_value_usd": round(mkt_value, 4) if mkt_value is not None else None,
            "unrealized_pnl_usd": round(unrealized, 4) if unrealized is not None else None,
            "unrealized_pnl_pct": (
                round((unrealized / cost) * 100, 3) if unrealized is not None and cost else None
            ),
            "lot_count": len(lots),
        })

    realized_total = sum(r["pnl_usd"] for r in realized)
    wins = [r for r in realized if r["pnl_usd"] > 0]
    losses = [r for r in realized if r["pnl_usd"] < 0]
    win_rate = round((len(wins) / len(realized)) * 100, 2) if realized else None

    return {
        "ok": True,
        "positions": positions,
        "open_position_count": len(positions),
        "realized_trades": realized[-50:],  # last 50 closed pairs
        "realized_pnl_total": round(realized_total, 4),
        "realized_pnl_count": len(realized),
        "win_rate_pct": win_rate,
        "avg_win_usd": round(sum(r["pnl_usd"] for r in wins) / len(wins), 4) if wins else None,
        "avg_loss_usd": round(sum(r["pnl_usd"] for r in losses) / len(losses), 4) if losses else None,
        "unrealized_pnl_total": round(unrealized_total, 4),
        "total_pnl": round(realized_total + unrealized_total, 4),
    }


def last_trades(n: int = 20) -> List[Dict]:
    trades = _load_all()
    return trades[-n:]


def record_from_order_result(result: Dict[str, Any], signal: Dict[str, Any]) -> bool:
    """Build a TradeEntry from a place_market_order() result and persist it."""
    order = result.get("order") or {}
    raw = order.get("raw") or {}
    sr = raw.get("success_response") if isinstance(raw, dict) else {}
    base_size = order.get("base_size_submitted")
    try:
        base_size = float(base_size) if base_size is not None else None
    except Exception:
        base_size = None

    entry = TradeEntry(
        ts=time.time(),
        trade_id=order.get("client_order_id", f"s25-{int(time.time())}"),
        order_id=order.get("order_id") or (sr.get("order_id") if isinstance(sr, dict) else None),
        symbol=order.get("product_id", ""),
        side=order.get("side", ""),
        usd_amount=float(order.get("usd_amount", 0) or 0),
        base_size=base_size,
        avg_price=None,  # filled later via order lookup
        fee=None,
        mode=order.get("mode", "dry_run"),
        strategy=signal.get("strategy", signal.get("source", "")),
        source=signal.get("source", ""),
        success=bool(order.get("success", False)),
        notes=signal.get("reason", ""),
    )
    return record_trade(entry)


def backfill_fills(lookup_fn) -> int:
    """For trades missing avg_price/fee, look them up on Coinbase and update log.

    lookup_fn(order_id) -> {filled_size, filled_value, total_fees}
    """
    trades = _load_all()
    updated = 0
    for t in trades:
        if t.get("avg_price") is not None:
            continue
        oid = t.get("order_id")
        if not oid:
            continue
        try:
            info = lookup_fn(oid)
            if not info:
                continue
            filled_size = float(info.get("filled_size") or 0)
            filled_value = float(info.get("filled_value") or 0)
            fees = float(info.get("total_fees") or 0)
            if filled_size > 0:
                t["base_size"] = filled_size
                t["avg_price"] = filled_value / filled_size
                t["fee"] = fees
                updated += 1
        except Exception:
            continue
    if updated:
        tmp = LOG_PATH.with_suffix(".tmp")
        with tmp.open("w") as f:
            for t in trades:
                f.write(json.dumps(t, default=str) + "\n")
        tmp.replace(LOG_PATH)
    return updated
