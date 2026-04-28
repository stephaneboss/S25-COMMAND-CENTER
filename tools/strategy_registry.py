#!/usr/bin/env python3
"""S25 Strategy Registry helper. Read-only control-plane tool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = Path("config/strategy_registry.json")


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    if not path.exists():
        return {"strategies": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"strategies": {}}
    if not isinstance(data, dict):
        return {"strategies": {}}
    data.setdefault("strategies", {})
    return data


def list_strategies(registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for name, cfg in registry.get("strategies", {}).items():
        if not isinstance(cfg, dict):
            continue
        rows.append({
            "name": name,
            "mode": cfg.get("mode", "unknown"),
            "family": cfg.get("family", "unknown"),
            "symbols": cfg.get("symbols", []),
            "suspected_actual_source": cfg.get("suspected_actual_source", "unknown"),
            "allowed_to_emit_signal": bool(cfg.get("allowed_to_emit_signal", False)),
            "allowed_to_execute_live": bool(cfg.get("allowed_to_execute_live", False)),
        })
    return sorted(rows, key=lambda item: item["name"])


def live_report(registry: dict[str, Any]) -> dict[str, Any]:
    live = []
    emitters = []
    for name, cfg in registry.get("strategies", {}).items():
        if not isinstance(cfg, dict):
            continue
        if cfg.get("allowed_to_execute_live"):
            live.append(name)
        if cfg.get("allowed_to_emit_signal"):
            emitters.append(name)
    return {
        "signal_emitters": sorted(emitters),
        "live_execution_enabled": sorted(live),
        "safe_for_compact_ops": len(live) == 0,
    }


def render_summary(registry: dict[str, Any]) -> str:
    rows = list_strategies(registry)
    report = live_report(registry)
    lines = ["S25 Strategy Registry", "", f"Strategies: {len(rows)}", ""]
    for row in rows:
        symbols = ",".join(row["symbols"])
        lines.append(
            f"- {row['name']} [{row['mode']}] family={row['family']} "
            f"symbols={symbols} source={row['suspected_actual_source']} "
            f"live={row['allowed_to_execute_live']}"
        )
    lines.append("")
    lines.append(f"Safe for compact ops: {report['safe_for_compact_ops']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="S25 Strategy Registry")
    parser.add_argument("--path", type=Path, default=DEFAULT_REGISTRY)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    sub.add_parser("list")
    sub.add_parser("live-report")
    show = sub.add_parser("show")
    show.add_argument("name")
    args = parser.parse_args()
    registry = load_registry(args.path)
    if args.command == "summary":
        print(render_summary(registry))
        return 0
    if args.command == "list":
        print(json.dumps(list_strategies(registry), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "live-report":
        print(json.dumps(live_report(registry), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "show":
        item = registry.get("strategies", {}).get(args.name)
        if not isinstance(item, dict):
            print(json.dumps({"ok": False, "error": "strategy not found", "name": args.name}, indent=2))
            return 1
