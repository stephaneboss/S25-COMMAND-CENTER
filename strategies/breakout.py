"""Breakout strategy: close > max of last N candles (1h)."""
from __future__ import annotations

from typing import Optional

from .base import BaseStrategy, MarketData, Signal


class BreakoutStrategy(BaseStrategy):
    name = "breakout_1h"
    description = "BUY when 1h close breaks above the last 20-bar high"
    default_enabled = False
    default_usd_size = 5.0

    LOOKBACK = 20

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        c = market.candles_1h
        if len(c) < self.LOOKBACK + 1:
            return None
        last = c[-1]
        prior = c[-(self.LOOKBACK + 1):-1]
        prior_high = max(k.high for k in prior)
        if last.close > prior_high:
            lift = (last.close - prior_high) / prior_high * 100
            if lift < 0.1:
                return None  # noise
            return Signal(
                action="BUY",
                confidence=min(0.85, 0.60 + lift / 5),
                strategy=self.name,
                reason=f"breakout above {self.LOOKBACK}h high (+{lift:.2f}%)",
            )
        return None
