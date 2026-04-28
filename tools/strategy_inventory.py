#!/usr/bin/env python3
"""S25 local strategy inventory.

Read-only helper used to locate strategy names and trading logic in the Alien
repo. It does not import the live trading pipeline and it does not execute
orders.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_ROOT = Path(".")
DEFAULT_PATTERNS = (
    "strategy",
    "strategies",
    "stoch_rsi",
    "stoch",
    "bollinger",
    "dca",
    "arkon",
    "tradingview",
    "coinbase",
    "mexc",
    "merlin",
    "oracle",
)
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
}
TEXT_SUFFIXES = {
    ".py",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".toml",
    ".env",
}


def _iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def _safe_read(path: Path, max_bytes: int) -> str:
    try:
        raw = path.read_bytes()[:max_bytes]
        return raw.decode("utf-8", errors="ignore")
    except OSError:
        return ""


def _line_hits(text: str, patterns: List[str], max_hits: int) -> List[Dict[str, object]]:
    hits: List[Dict[str, object]] = []
    lower_patterns = [p.lower() for p in patterns]
    for idx, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        matched = [p for p in lower_patterns if p in lower]
        if matched:
            hits.append({"line": idx, "patterns": matched, "text": line.strip()[:240]})
        if len(hits) >= max_hits:
            break
    return hits


def _extract_strategy_names(text: str) -> List[str]:
    names = set()
    regexes = [
        r"\[([^\]]*(?:stoch|bollinger|dca|rsi|macd|breakout|bounce|scalp)[^\]]*)\]",
        r"strategy[\"']?\s*[:=]\s*[\"']([^\"']+)[\"']",
        r"name[\"']?\s*[:=]\s*[\"']([^\"']*(?:stoch|bollinger|dca|rsi|macd|breakout|bounce|scalp)[^\"']*)[\"']",
    ]
    for regex in regexes:
        for match in re.finditer(regex, text, flags=re.IGNORECASE):
            value = match.group(1).strip()
            if 2 <= len(value) <= 120:
                names.add(value)
    return sorted(names)


def inventory(
    root: Path = DEFAULT_ROOT,
    patterns: Iterable[str] = DEFAULT_PATTERNS,
    max_bytes_per_file: int = 256_000,
    max_hits_per_file: int = 20,
) -> Dict[str, object]:
    pattern_list = list(patterns)
    files = []
    strategy_names = set()

    for path in _iter_files(root):
        text = _safe_read(path, max_bytes=max_bytes_per_file)
        if not text:
            continue
        hits = _line_hits(text, pattern_list, max_hits=max_hits_per_file)
        extracted = _extract_strategy_names(text)
        if hits or extracted:
            rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
            files.append({"file": rel, "hits": hits, "strategy_names": extracted})
            strategy_names.update(extracted)

    return {
        "root": str(root),
        "files_seen": len(files),
        "patterns": pattern_list,
        "strategy_names": sorted(strategy_names),
        "matches": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory local S25 strategy references")
    parser.add_argument("--root", default=".")
    parser.add_argument("--pattern", action="append", default=None)
    parser.add_argument("--max-hits-per-file", type=int, default=20)
    parser.add_argument("--max-bytes-per-file", type=int, default=256_000)
    args = parser.parse_args()

    data = inventory(
        root=Path(args.root),
        patterns=args.pattern or DEFAULT_PATTERNS,
        max_bytes_per_file=args.max_bytes_per_file,
        max_hits_per_file=args.max_hits_per_file,
    )
