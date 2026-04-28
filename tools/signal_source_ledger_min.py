#!/usr/bin/env python3
"""S25 Signal Source Ledger minimal.

Records signal provenance only. No trading, no routing, no execution.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_LEDGER = Path("memory/signal_source_ledger.jsonl")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_symbol(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    return str(value).upper().replace("/", "-")


def normalize(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "ts": event.get("ts") or now_iso(),
        "symbol": norm_symbol(event.get("symbol")),
        "action": str(event.get("action") or "UNKNOWN").upper(),
        "source_label": event.get("source_label") or "unknown",
        "actual_ingress": event.get("actual_ingress") or "unknown",
        "source_agent": event.get("source_agent") or "unknown",
        "strategy": event.get("strategy") or "unknown",
        "confidence": event.get("confidence"),
        "effective_confidence": event.get("effective_confidence"),
        "verdict": event.get("verdict") or "unknown",
        "payload_price": event.get("payload_price"),
        "price_source": event.get("price_source") or "unknown",
        "signal_age_sec": event.get("signal_age_sec"),
        "routed_to": event.get("routed_to"),
        "mission_id": event.get("mission_id"),
        "reason": event.get("reason") or "",
        "mode": event.get("mode") or "unknown",
    }


def append_event(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    item = normalize(event)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    return item


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def latest(path: Path, symbol: str | None = None) -> dict[str, Any] | None:
    wanted = norm_symbol(symbol) if symbol else None
    for row in reversed(load_events(path)):
        if wanted is None or norm_symbol(row.get("symbol")) == wanted:
            return row
    return None


def explain(row: dict[str, Any] | None) -> str:
    if not row:
        return "No signal found. Ledger is empty or not wired yet."
    return (
        f"{row.get('symbol')} {row.get('action')} signal: "
        f"label={row.get('source_label')}, ingress={row.get('actual_ingress')}, "
        f"source_agent={row.get('source_agent')}, strategy={row.get('strategy')}, "
        f"verdict={row.get('verdict')}, routed_to={row.get('routed_to')}, "
        f"price_source={row.get('price_source')}. Reason: {row.get('reason')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="S25 Signal Source Ledger minimal")
    parser.add_argument("--path", type=Path, default=DEFAULT_LEDGER)
    sub = parser.add_subparsers(dest="cmd", required=True)
    app = sub.add_parser("append")
    app.add_argument("--symbol", required=True)
    app.add_argument("--action", required=True)
    app.add_argument("--source-label", default="unknown")
    app.add_argument("--actual-ingress", default="unknown")
    app.add_argument("--source-agent", default="unknown")
    app.add_argument("--strategy", default="unknown")
    app.add_argument("--confidence", type=float, default=None)
    app.add_argument("--effective-confidence", type=float, default=None)
    app.add_argument("--verdict", default="unknown")
    app.add_argument("--payload-price", type=float, default=None)
    app.add_argument("--price-source", default="unknown")
    app.add_argument("--routed-to", default=None)
    app.add_argument("--mission-id", default=None)
    app.add_argument("--reason", default="")
