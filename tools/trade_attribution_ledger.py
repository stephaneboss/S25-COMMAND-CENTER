#!/usr/bin/env python3
"""S25 Trade Attribution Ledger.

Small standalone JSONL ledger used to answer one critical question:
"why does this trade exist?"

This module is intentionally not wired into live execution yet.  It provides
safe primitives that the Coinbase executor, ARKON5, MERLIN, ORACLE, or TRINITY
can call later when a real order is created.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_LEDGER_PATH = Path("memory/trade_attribution_ledger.jsonl")

DEFAULT_FIELDS: Dict[str, Any] = {
    "ts": None,
    "symbol": "UNKNOWN",
    "side": "UNKNOWN",
    "usd_amount": None,
    "source_signal": "unknown",
    "source_agent": "unknown",
    "strategy": "unknown",
    "confidence": None,
    "mission_id": None,
    "coinbase_order_id": None,
    "reason": "",
    "price_source": "unknown",
    "execution_agent": "unknown",
    "mode": "unknown",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_path(path: str | Path = DEFAULT_LEDGER_PATH) -> Path:
    return Path(path)


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Return a normalized trade attribution event.

    Unknown fields are preserved under ``extra`` to avoid losing forensic data.
    """
    normalized = dict(DEFAULT_FIELDS)
    extra: Dict[str, Any] = {}

    for key, value in event.items():
        if key in normalized:
            normalized[key] = value
        else:
            extra[key] = value

    if not normalized["ts"]:
        normalized["ts"] = _now_iso()

    if normalized["symbol"]:
        normalized["symbol"] = str(normalized["symbol"]).upper().replace("/", "-")
    if normalized["side"]:
        normalized["side"] = str(normalized["side"]).upper()

    if extra:
        normalized["extra"] = extra

    return normalized


def load_ledger(path: str | Path = DEFAULT_LEDGER_PATH) -> List[Dict[str, Any]]:
    """Load JSONL ledger entries. Missing files return an empty list."""
    ledger_path = _coerce_path(path)
    if not ledger_path.exists():
        return []

    entries: List[Dict[str, Any]] = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                entries.append(
                    {
                        "ts": _now_iso(),
                        "symbol": "UNKNOWN",
                        "side": "UNKNOWN",
                        "reason": f"corrupt ledger line {line_no}",
                        "raw": line,
                    }
                )
                continue
            if isinstance(item, dict):
                entries.append(item)
    return entries


def append_trade_event(
    event: Dict[str, Any], path: str | Path = DEFAULT_LEDGER_PATH
) -> Dict[str, Any]:
    """Append a normalized event to the ledger and return it."""
    ledger_path = _coerce_path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_event(event)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
    return normalized


def _symbol_matches(entry: Dict[str, Any], symbol: Optional[str]) -> bool:
    if not symbol:
        return True
    wanted = symbol.upper().replace("/", "-")
    actual = str(entry.get("symbol", "")).upper().replace("/", "-")
    return actual == wanted or actual.startswith(wanted)


def latest_trade(
    symbol: Optional[str] = None, path: str | Path = DEFAULT_LEDGER_PATH
) -> Optional[Dict[str, Any]]:
    """Return the most recent trade event, optionally filtered by symbol."""
    entries = load_ledger(path)
    for entry in reversed(entries):
        if _symbol_matches(entry, symbol):
            return entry
    return None


def explain_latest(
    symbol: Optional[str] = None, path: str | Path = DEFAULT_LEDGER_PATH
) -> str:
    """Human-readable explanation for the latest attributed trade."""
    trade = latest_trade(symbol=symbol, path=path)
    if not trade:
        target = f" for {symbol}" if symbol else ""
        return f"No attributed trade found{target}. Ledger is empty or not wired yet."

    symbol_txt = trade.get("symbol", "UNKNOWN")
    side_txt = trade.get("side", "UNKNOWN")
    amount = trade.get("usd_amount")
    amount_txt = f"{amount} USD" if amount is not None else "unknown USD amount"

    return (
        f"{symbol_txt} {side_txt} exists because {trade.get('execution_agent', 'unknown')} "
        f"executed {amount_txt} from source_signal={trade.get('source_signal', 'unknown')} "
        f"source_agent={trade.get('source_agent', 'unknown')} "
        f"strategy={trade.get('strategy', 'unknown')} "
        f"confidence={trade.get('confidence')} "
        f"mission_id={trade.get('mission_id')} "
        f"coinbase_order_id={trade.get('coinbase_order_id')} "
        f"price_source={trade.get('price_source', 'unknown')} "
        f"mode={trade.get('mode', 'unknown')}. "
        f"Reason: {trade.get('reason', '')}"
    )


def _append_demo(path: str | Path) -> Dict[str, Any]:
    return append_trade_event(
        {
            "symbol": "DOGE-USD",
            "side": "BUY",
            "usd_amount": 2.0,
            "source_signal": "demo",
            "source_agent": "TRINITY",
            "strategy": "manual_demo",
            "confidence": 0.0,
            "mission_id": "demo",
            "coinbase_order_id": "demo",
            "reason": "demo ledger entry; not a live trade",
            "price_source": "coinbase_spot",
            "execution_agent": "COINBASE",
            "mode": "dry_demo",
        },
        path=path,
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="S25 Trade Attribution Ledger")
    parser.add_argument("--path", default=str(DEFAULT_LEDGER_PATH), help="ledger JSONL path")

    sub = parser.add_subparsers(dest="command", required=True)
    latest_cmd = sub.add_parser("latest", help="explain latest attributed trade")
