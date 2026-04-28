#!/usr/bin/env python3
"""S25 Micro Scanner Observe-Only.

This tool is intentionally safe: it never sends orders and never imports the
Coinbase executor. It reads prices from a JSON snapshot or stdin, computes a
small local score, and appends observations to a JSONL journal.

The live cockpit can later feed this tool with Coinbase spot prices. Until the
opsRun argument bridge is fixed, this module remains a ready-to-wire building
block.
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_JOURNAL = Path("memory/micro_scanner_observe.jsonl")
DEFAULT_STATE = Path("memory/micro_scanner_state.json")


@dataclass
class ScannerConfig:
    min_points: int = 8
    max_history: int = 120
    rsi_period: int = 14
    bollinger_period: int = 20
    bollinger_stdev: float = 2.0
    stale_seconds: int = 120


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def append_jsonl(path: Path, item: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def normalize_prices(raw: Dict[str, Any]) -> Dict[str, float]:
    """Normalize price maps from either {prices:{}} or flat JSON."""
    prices = raw.get("prices", raw) if isinstance(raw, dict) else {}
    out: Dict[str, float] = {}
    for key, value in prices.items():
        try:
            out[str(key).upper().replace("/", "-")] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def load_prices(path: Optional[Path]) -> Dict[str, float]:
    if path:
        return normalize_prices(load_json(path, {}))
    try:
        import sys

        payload = sys.stdin.read().strip()
        if payload:
            return normalize_prices(json.loads(payload))
    except json.JSONDecodeError:
        return {}
    return {}


def update_history(state: Dict[str, Any], prices: Dict[str, float], cfg: ScannerConfig) -> Dict[str, Any]:
    history = state.setdefault("history", {})
    ts = utc_now()
    for symbol, price in prices.items():
        rows = history.setdefault(symbol, [])
        rows.append({"ts": ts, "price": price})
        if len(rows) > cfg.max_history:
            del rows[: len(rows) - cfg.max_history]
    state["updated_at"] = ts
    return state


def rsi(values: List[float], period: int = 14) -> Optional[float]:
    if len(values) < period + 1:
        return None
    gains: List[float] = []
    losses: List[float] = []
    window = values[-(period + 1) :]
    for prev, cur in zip(window, window[1:]):
        delta = cur - prev
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def bollinger(values: List[float], period: int = 20, stdev_factor: float = 2.0) -> Optional[Dict[str, float]]:
    if len(values) < period:
        return None
    window = values[-period:]
    mid = statistics.fmean(window)
    stdev = statistics.pstdev(window)
    return {
        "lower": round(mid - stdev_factor * stdev, 8),
        "mid": round(mid, 8),
        "upper": round(mid + stdev_factor * stdev, 8),
    }


def momentum(values: List[float], lookback: int = 5) -> Optional[float]:
    if len(values) < lookback + 1:
        return None
    old = values[-(lookback + 1)]
    cur = values[-1]
    if old == 0:
        return None
    return round(((cur - old) / old) * 100, 4)


def score_symbol(symbol: str, rows: List[Dict[str, Any]], cfg: ScannerConfig) -> Dict[str, Any]:
    values = [float(row["price"]) for row in rows if "price" in row]
    latest = values[-1] if values else None
    item: Dict[str, Any] = {
        "symbol": symbol,
        "price": latest,
        "points": len(values),
        "rsi": None,
        "bollinger": None,
        "momentum_5": None,
        "score": 0,
        "signal": "INSUFFICIENT_DATA",
        "reasons": [],
    }
    if len(values) < cfg.min_points:
        item["reasons"].append(f"need at least {cfg.min_points} points")
        return item

    rsi_value = rsi(values, period=cfg.rsi_period)
    bb = bollinger(values, period=min(cfg.bollinger_period, len(values)), stdev_factor=cfg.bollinger_stdev)
    mom = momentum(values, lookback=min(5, len(values) - 1))
    item["rsi"] = rsi_value
    item["bollinger"] = bb
    item["momentum_5"] = mom

    score = 0
    reasons: List[str] = []

    if rsi_value is not None:
        if rsi_value <= 30:
            score += 2
            reasons.append("RSI oversold")
        elif rsi_value >= 70:
            score -= 2
            reasons.append("RSI overbought")

    if bb and latest is not None:
        if latest <= bb["lower"]:
            score += 2
            reasons.append("price near/lower Bollinger band")
        elif latest >= bb["upper"]:
            score -= 1
            reasons.append("price near/upper Bollinger band")

    if mom is not None:
        if mom > 0.15:
            score += 1
            reasons.append("short momentum positive")
        elif mom < -0.15:
            score -= 1
            reasons.append("short momentum negative")

    item["score"] = score
    item["reasons"] = reasons
    if score >= 3:
        item["signal"] = "WATCH_BUY"
    elif score <= -3:
        item["signal"] = "WATCH_SELL"
    else:
        item["signal"] = "HOLD_OBSERVE"
    return item


def scan_once(prices: Dict[str, float], state_path: Path, journal_path: Path, cfg: ScannerConfig) -> Dict[str, Any]:
    state = load_json(state_path, {"history": {}})
    state = update_history(state, prices, cfg)
    observations = [
        score_symbol(symbol, rows, cfg)
        for symbol, rows in sorted(state.get("history", {}).items())
        if symbol in prices
    ]
    result = {
        "ts": utc_now(),
        "mode": "observe_only",
        "price_source": "external_snapshot_or_stdin",
        "observations": observations,
    }
    save_json(state_path, state)
    append_jsonl(journal_path, result)
    return result


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="S25 micro scanner observe-only")
    parser.add_argument("--prices", type=Path, default=None, help="JSON file with prices, or stdin if omitted")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    parser.add_argument("--min-points", type=int, default=8)
    args = parser.parse_args(list(argv) if argv is not None else None)

    prices = load_prices(args.prices)
