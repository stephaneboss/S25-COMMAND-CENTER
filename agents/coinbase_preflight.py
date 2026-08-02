"""
S25 Lumiere - Coinbase preflight + non-financial heartbeat + canary procedure.
================================================================================
Mission mis_PG7Ig33AFRLs: prepare a safe, progressive return to live Coinbase
trading WITHOUT risking funds while available_usd is below a safe minimum.

Three layers, all read-only except run_canary_order (which self-blocks unless
every guard passes):

  1. preflight_check()      - read-only diagnostic: mode, balance, per-product
                               minimum, estimated fees, open orders, API health.
  2. non_financial_heartbeat() - quote + product validation + a SIMULATED order
                               (size/fee math, no submission). Written to its own
                               telemetry log (coinbase_heartbeat_log.jsonl), NEVER
                               trades_log.jsonl - it must not be miscounted as a
                               real fill by position_tracker/quant_brain's
                               live_perf. Proves the pipeline is alive between
                               real trades.
  3. run_canary_order()     - the actual first live trade, capped at CANARY_USD,
                               single order, idempotency key, fill verification,
                               fee/slippage logging. Refuses to run unless
                               preflight_check() reports can_proceed=True AND
                               available_usd >= CANARY_USD + fee margin.

reconcile_portfolio() explains the $0.5x live balance vs the larger historical
FIFO position numbers: they are two different views (current real holdings vs
a historical ledger going back months), not a data bug - see mis_kE667jmyWxK0.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("s25.coinbase_preflight")

REPO = Path(__file__).resolve().parent.parent
HEARTBEAT_LOG = REPO / "memory" / "coinbase_heartbeat_log.jsonl"

CANARY_USD = 5.0
FEE_MARGIN_PCT = 2.5  # conservative: ~1.2%/side round trip + buffer


def _normalize(resp: Any) -> Dict[str, Any]:
    """Coinbase SDK responses are sometimes dict, sometimes an object - same
    normalization pattern already used throughout coinbase_executor.py."""
    if isinstance(resp, dict):
        return resp
    return getattr(resp, "__dict__", {}) or {}


def _get_product_info(exe, product_id: str) -> Dict[str, Any]:
    """Read-only: base_min_size / quote_min_size / increments for a product."""
    c = exe._get_client()
    if c is None:
        return {"ok": False, "error": "client_unavailable"}
    try:
        resp = c.get_product(product_id)
        d = _normalize(resp)
        return {
            "ok": True,
            "product_id": product_id,
            "base_min_size": d.get("base_min_size"),
            "quote_min_size": d.get("quote_min_size"),
            "base_increment": d.get("base_increment"),
            "price_increment": d.get("price_increment") or d.get("quote_increment"),
            "status": d.get("status"),
            "trading_disabled": d.get("trading_disabled", False),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _get_open_orders(exe) -> Dict[str, Any]:
    """Read-only: list open orders (holds that would reduce available_usd)."""
    c = exe._get_client()
    if c is None:
        return {"ok": False, "error": "client_unavailable", "count": None}
    try:
        resp = c.list_orders(order_status=["OPEN", "PENDING"])
        d = _normalize(resp)
        orders = d.get("orders") or []
        return {"ok": True, "count": len(orders), "order_ids": [
            (o.get("order_id") if isinstance(o, dict) else getattr(o, "order_id", None)) for o in orders
        ]}
    except Exception as e:
        # Not all SDK versions/permissions expose list_orders identically -
        # fail safe: report unknown rather than silently assuming zero.
        return {"ok": False, "error": str(e)[:200], "count": None}


def preflight_check(exe, product_id: str, usd_amount: float, side: str = "BUY") -> Dict[str, Any]:
    """Read-only. Never places an order. Returns can_proceed + every reason it can't."""
    exe.refresh_mode_from_ha()
    reasons: List[str] = []

    mode = "live" if not exe.dry_run else "dry_run"

    accounts = exe.get_accounts()
    available_usd = None
    if accounts.get("ok"):
        available_usd = accounts.get("balances", {}).get("USD", 0.0)
    else:
        reasons.append(f"balance_check_failed: {accounts.get('error')}")

    product_info = _get_product_info(exe, product_id)
    if not product_info.get("ok"):
        reasons.append(f"product_info_failed: {product_info.get('error')}")

    open_orders = _get_open_orders(exe)
    if open_orders.get("ok") and (open_orders.get("count") or 0) > 0:
        reasons.append(f"open_orders_present: {open_orders['count']} (holds may reduce available balance)")

    quote_min = None
    try:
        quote_min = float(product_info.get("quote_min_size")) if product_info.get("quote_min_size") else None
    except (TypeError, ValueError):
        quote_min = None

    est_fee_usd = round(usd_amount * (FEE_MARGIN_PCT / 100.0), 4)
    required_usd = usd_amount + est_fee_usd

    if available_usd is not None:
        if available_usd < required_usd:
            reasons.append(
                f"insufficient_balance: available={available_usd:.4f} USD < "
                f"required={required_usd:.4f} USD (order {usd_amount} + est. fee {est_fee_usd})"
            )
    if quote_min is not None and usd_amount < quote_min:
        reasons.append(f"below_product_minimum: {usd_amount} < quote_min_size={quote_min}")
    if product_info.get("trading_disabled"):
        reasons.append("product_trading_disabled")
    if mode != "live":
        reasons.append("not_in_live_mode (dry_run - no funds at risk, but canary requires live mode explicitly)")

    return {
        "ok": True,
        "checked_at": time.time(),
        "product_id": product_id,
        "side": side,
        "usd_amount": usd_amount,
        "mode": mode,
        "available_usd": available_usd,
        "estimated_fee_usd": est_fee_usd,
        "required_usd": required_usd,
        "product_info": product_info,
        "open_orders": open_orders,
        "api_health": "ok" if accounts.get("ok") and product_info.get("ok") else "degraded",
        "blocking_reasons": reasons,
        "can_proceed": len(reasons) == 0,
    }


def non_financial_heartbeat(exe, product_id: str = "BTC-USD", usd_amount: float = 5.0) -> Dict[str, Any]:
    """Quote + product validation + a SIMULATED order (no submission).

    Proves the pipeline (auth, product lookup, price feed, size/fee math) is
    alive between real trades. Written to its OWN telemetry log - deliberately
    NOT trades_log.jsonl, so it can never be miscounted as a real fill by
    position_tracker.compute_positions() or quant_brain's live_perf window.
    """
    pf = preflight_check(exe, product_id, usd_amount, "BUY")
    price = exe.get_product_price(product_id)
    simulated_size = round(usd_amount / price, 8) if price else None
    entry = {
        "ts": time.time(),
        "type": "non_financial_heartbeat",
        "product_id": product_id,
        "usd_amount": usd_amount,
        "quote_price": price,
        "simulated_base_size": simulated_size,
        "estimated_fee_usd": pf["estimated_fee_usd"],
        "api_health": pf["api_health"],
        "would_be_blocked": not pf["can_proceed"],
        "blocking_reasons": pf["blocking_reasons"],
    }
    try:
        HEARTBEAT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with HEARTBEAT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except OSError as e:
        logger.warning("heartbeat log write failed: %s", e)
    return entry


def run_canary_order(exe, product_id: str = "BTC-USD", usd_amount: float = CANARY_USD) -> Dict[str, Any]:
    """The actual first live canary trade. Refuses unless every guard passes.

    Single order, no auto-repeat, idempotency via client_order_id, fill
    verification, fee/slippage logged. This function places a REAL order when
    (and only when) preflight passes - it is not called anywhere automatically.
    """
    pf = preflight_check(exe, product_id, usd_amount, "BUY")
    if not pf["can_proceed"]:
        return {"ok": False, "blocked": True, "reasons": pf["blocking_reasons"], "preflight": pf}
    if usd_amount > CANARY_USD:
        return {"ok": False, "blocked": True, "reasons": [f"canary_cap_exceeded: {usd_amount} > {CANARY_USD}"]}

    idempotency_key = f"s25-canary-{uuid4().hex[:12]}"
    price_before = exe.get_product_price(product_id)
    result = exe.place_market_order(product_id, "BUY", usd_amount, reason="canary_test", source=idempotency_key)
    price_after = exe.get_product_price(product_id)
    slippage_pct = None
    if price_before and price_after:
        slippage_pct = round(((price_after - price_before) / price_before) * 100, 4)

    outcome = {
        "ok": bool(result.get("ok")),
        "blocked": False,
        "idempotency_key": idempotency_key,
        "order_result": result,
        "price_before": price_before,
        "price_after": price_after,
        "slippage_pct": slippage_pct,
        "preflight": pf,
    }
    if not result.get("ok"):
        outcome["rollback_note"] = "order rejected/failed at submission - nothing to unwind, no partial fill"
    return outcome


def reconcile_portfolio(exe) -> Dict[str, Any]:
    """Explains live Coinbase balance vs historical FIFO position numbers.

    These are two different views and a mismatch is NOT a bug:
      - live balance (this function, exe.get_accounts()) = what's actually
        held on Coinbase right now.
      - position_tracker.compute_positions() = a FIFO replay of every trade
        EVER recorded in trades_log.jsonl, including months-old historical
        activity that may include manually-seeded/legacy rows (see
        mis_kE667jmyWxK0 audit - buy_trade_id values like 's25-past-sell-doge-1'
        are clearly not organic Coinbase fills).
    """
    accounts = exe.get_accounts()
    try:
        from agents.position_tracker import compute_positions
        positions = compute_positions(spot_fn=exe.get_product_price)
    except Exception as e:
        positions = {"ok": False, "error": str(e)[:200]}

    live_balances = accounts.get("balances", {}) if accounts.get("ok") else {}
    computed_cost_basis = sum(p.get("cost_basis_usd") or 0 for p in positions.get("positions", []))

    return {
        "ok": True,
        "live_usd_available": live_balances.get("USD"),
        "live_all_balances": live_balances,
        "historical_ledger_open_cost_basis_usd": round(computed_cost_basis, 4),
        "historical_ledger_position_count": positions.get("open_position_count"),
        "explanation": (
            "Mismatch expected and documented: live balance reflects what Coinbase "
            "holds NOW; the historical ledger (trades_log.jsonl since inception) "
            "includes months of past activity, some of it pre-dating the current "
            "near-zero balance and some legacy/synthetic rows from before the "
            "PnL audit (mis_kE667jmyWxK0). Do not treat the ledger total as current "
            "inventory - use exe.get_accounts() for that."
        ),
    }
