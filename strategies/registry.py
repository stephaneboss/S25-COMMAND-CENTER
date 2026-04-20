"""S25 strategy registry with persistent enable/disable state."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from .base import BaseStrategy, MarketData, Signal

logger = logging.getLogger("s25.strategies")

STATE_FILE = Path(__file__).resolve().parent.parent / "memory" / "strategies_state.json"


class StrategyRegistry:
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self._state: Dict[str, dict] = self._load_state()

    def _load_state(self) -> Dict[str, dict]:
        if not STATE_FILE.exists():
            return {}
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception as e:
            logger.warning("state load failed: %s", e)
            return {}

    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self._state, indent=2))

    def register(self, strategy: BaseStrategy):
        self.strategies[strategy.name] = strategy
        if strategy.name not in self._state:
            self._state[strategy.name] = {
                "enabled": strategy.default_enabled,
                "usd_size": strategy.default_usd_size,
                "symbols": [],  # empty = all whitelist; list = only these coins
                "last_signal_ts": None,
                "last_signal_symbol": None,
                "total_signals": 0,
            }
            self._save_state()
        # Ensure existing entries have symbols field (back-compat)
        if "symbols" not in self._state[strategy.name]:
            self._state[strategy.name]["symbols"] = []
            self._save_state()

    def is_enabled(self, name: str) -> bool:
        return bool(self._state.get(name, {}).get("enabled", False))

    def enabled_strategies(self) -> List[BaseStrategy]:
        return [s for n, s in self.strategies.items() if self.is_enabled(n)]

    def toggle(self, name: str, enabled: bool) -> bool:
        if name not in self.strategies:
            return False
        entry = self._state.setdefault(name, {})
        entry["enabled"] = bool(enabled)
        self._save_state()
        return True

    def set_usd_size(self, name: str, usd: float) -> bool:
        if name not in self.strategies:
            return False
        entry = self._state.setdefault(name, {})
        entry["usd_size"] = max(0.01, min(500.0, float(usd)))  # clamp sane
        self._save_state()
        return True

    def set_symbols(self, name: str, symbols: list) -> bool:
        """Restrict a strategy to a specific list of coins. [] = all allowed."""
        if name not in self.strategies:
            return False
        entry = self._state.setdefault(name, {})
        entry["symbols"] = [s.upper() for s in symbols if s]
        self._save_state()
        return True

    def get_symbols(self, name: str) -> list:
        return list(self._state.get(name, {}).get("symbols", []))

    def record_signal(self, name: str, signal: Signal, market: MarketData):
        entry = self._state.setdefault(name, {})
        entry["last_signal_ts"] = time.time()
        entry["last_signal_symbol"] = market.symbol
        entry["last_signal_action"] = signal.action
        entry["total_signals"] = int(entry.get("total_signals", 0)) + 1
        self._save_state()

    def dispatch(self, markets: List[MarketData]) -> List[tuple]:
        """Run every enabled strategy against each market. Returns list of
        (strategy_name, symbol, signal) tuples.

        If a strategy has a non-empty `symbols` list in its state, only those
        coins are evaluated for it (per-symbol whitelist).
        """
        out: List[tuple] = []
        for strategy in self.enabled_strategies():
            st = self._state.get(strategy.name, {})
            usd_size = float(st.get("usd_size", strategy.default_usd_size))
            allowed = [s.upper() for s in st.get("symbols", [])]
            for market in markets:
                if allowed and market.symbol.upper() not in allowed:
                    continue
                try:
                    sig = strategy.should_fire(market)
                except Exception as e:
                    logger.warning("strategy %s crashed on %s: %s", strategy.name, market.symbol, e)
                    continue
                if sig is None:
                    continue
                sig.usd_amount = usd_size
                self.record_signal(strategy.name, sig, market)
                out.append((strategy.name, market.symbol, sig))
        return out

    def snapshot(self) -> List[dict]:
        """For /api/trading/strategies."""
        out = []
        for name, strat in self.strategies.items():
            st = self._state.get(name, {})
            info = strat.info()
            info.update({
                "enabled": st.get("enabled", False),
                "usd_size": st.get("usd_size", strat.default_usd_size),
                "symbols": st.get("symbols", []),  # empty = all whitelist
                "total_signals": st.get("total_signals", 0),
                "last_signal_ts": st.get("last_signal_ts"),
                "last_signal_symbol": st.get("last_signal_symbol"),
                "last_signal_action": st.get("last_signal_action"),
            })
            out.append(info)
        return out


_registry: Optional[StrategyRegistry] = None


def get_registry() -> StrategyRegistry:
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
    return _registry
