"""Base interfaces for S25 trading strategies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Candle:
    start: int        # unix ts
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class MarketData:
    """Snapshot passed to every strategy per symbol per tick."""
    symbol: str                       # e.g. BTC-USD
    spot: Optional[float] = None      # live price
    change_24h_pct: Optional[float] = None
    rsi: Optional[float] = None       # from TV scanner
    volume: Optional[float] = None
    candles_1h: List[Candle] = field(default_factory=list)
    candles_15m: List[Candle] = field(default_factory=list)


@dataclass
class Signal:
    action: str              # BUY | SELL
    confidence: float        # 0..1
    strategy: str            # strategy.name
    reason: str              # human readable
    usd_amount: float = 2.0


class BaseStrategy:
    """Subclass and override should_fire."""

    name: str = "base"
    description: str = ""
    default_enabled: bool = False
    default_usd_size: float = 2.0
    # If True, strategy only sees symbols that are in Coinbase whitelist.
    whitelist_only: bool = True

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        return None

    def info(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "default_enabled": self.default_enabled,
            "default_usd_size": self.default_usd_size,
        }
