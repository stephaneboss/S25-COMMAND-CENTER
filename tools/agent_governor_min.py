#!/usr/bin/env python3
"""S25 Agent Governor minimal read-only inventory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("memory/command_mesh/agents.json")
DEFAULT_OUTPUT = Path("memory/agent_governor_state.json")
SIGNAL = {"signal_relay", "mesh_routing", "strategy_scan", "multi_coin", "mesh_auto_relay"}
EXEC = {"trade_execute", "bracket_orders", "bracket_update", "trailing_stops", "dca_schedules"}


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def agents_from(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict) and isinstance(raw.get("agents"), list):
        return [x for x in raw["agents"] if isinstance(x, dict)]
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


def caps(agent: dict[str, Any]) -> set[str]:
    value = agent.get("capabilities") or []
    if isinstance(value, str):
        value = [value]
    return {str(x) for x in value}


def name(agent: dict[str, Any]) -> str:
    return str(agent.get("agent_id") or agent.get("name") or "unknown")


def role(agent: dict[str, Any], capset: set[str]) -> str:
    n = name(agent).lower()
    kind = str(agent.get("kind") or agent.get("type") or "").lower()
    if "coinbase" in n or "trade_execute" in capset:
        return "executor"
    if "trailing" in n or {"bracket_update", "trailing_stops"} & capset:
        return "order_manager"
    if "dca" in n or "dca_schedules" in capset:
        return "scheduler"
    if SIGNAL & capset or kind == "signal":
        return "signal"
    if kind in {"brain", "llm"}:
        return "brain"
    if kind in {"infra", "gateway"}:
        return "infra"
    return "observer"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()
    governed = []
    for agent in agents_from(load_json(args.input, [])):
        c = caps(agent)
        r = role(agent, c)
        governed.append({"agent_id": name(agent), "status": str(agent.get("status") or "unknown"), "role": r, "can_signal": bool(SIGNAL & c), "can_execute": "trade_execute" in c or name(agent).upper() == "COINBASE", "can_modify_orders": bool(EXEC & c and "trade_execute" not in c), "capabilities": sorted(c)})
