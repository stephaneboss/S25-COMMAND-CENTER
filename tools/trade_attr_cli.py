#!/usr/bin/env python3
"""Manual CLI for S25 trade attribution.

This is a safe operator tool. It does not execute trades. It only writes or
reads the attribution ledger created by tools/trade_attribution_ledger.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from trade_attribution_ledger import (
    DEFAULT_LEDGER_PATH,
    append_trade_event,
    explain_latest,
    load_ledger,
)


def _matches(entry: Dict[str, Any], symbol: Optional[str]) -> bool:
    if not symbol:
        return True
    wanted = symbol.upper().replace("/", "-")
    actual = str(entry.get("symbol", "")).upper().replace("/", "-")
    return actual == wanted or actual.startswith(wanted)


def list_trades(symbol: Optional[str], limit: int, path: str | Path) -> List[Dict[str, Any]]:
    entries = [entry for entry in load_ledger(path) if _matches(entry, symbol)]
    entries.reverse()
    if limit <= 0:
        return entries
    return entries[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="S25 manual trade attribution CLI")
    parser.add_argument("--path", default=str(DEFAULT_LEDGER_PATH))
    sub = parser.add_subparsers(dest="command", required=True)

    latest_cmd = sub.add_parser("latest")
    latest_cmd.add_argument("symbol", nargs="?", default=None)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("symbol", nargs="?", default=None)
    list_cmd.add_argument("--limit", type=int, default=10)

    append_cmd = sub.add_parser("append")
    append_cmd.add_argument("--symbol", required=True)
    append_cmd.add_argument("--side", required=True)
    append_cmd.add_argument("--usd-amount", type=float, default=None)
    append_cmd.add_argument("--source-signal", default="manual")
    append_cmd.add_argument("--source-agent", default="TRINITY")
    append_cmd.add_argument("--strategy", default="manual_attribution")
    append_cmd.add_argument("--confidence", type=float, default=None)
    append_cmd.add_argument("--mission-id", default=None)
    append_cmd.add_argument("--coinbase-order-id", default=None)
    append_cmd.add_argument("--reason", default="manual attribution")
    append_cmd.add_argument("--price-source", default="coinbase_spot")
    append_cmd.add_argument("--execution-agent", default="COINBASE")
    append_cmd.add_argument("--mode", default="authorized")

    args = parser.parse_args()

    if args.command == "latest":
        print(explain_latest(symbol=args.symbol, path=args.path))
        return 0

    if args.command == "list":
        print(
            json.dumps(
                list_trades(symbol=args.symbol, limit=args.limit, path=args.path),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "append":
        event = append_trade_event(vars(args), path=args.path)
        print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
