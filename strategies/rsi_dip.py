"""Dip-buy strategy: RSI < 35 AND 24h change < -3%."""
from __future__ import annotations

from typing import Optional

from .base import BaseStrategy, MarketData, Signal


class RsiDipStrategy(BaseStrategy):
    name = "rsi_dip"
    description = "Buy when RSI < 35 and 24h change is < -3%"
    default_enabled = True
    default_usd_size = 2.0

    RSI_MAX = 35.0
    CHANGE_MAX = -3.0

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        if market.rsi is None or market.change_24h_pct is None:
            return None
        if market.rsi >= self.RSI_MAX:
            return None
        if market.change_24h_pct >= self.CHANGE_MAX:
            return None
        confidence = min(0.92, 0.60 + (self.RSI_MAX - market.rsi) / 100 + abs(market.change_24h_pct) / 100)
        return Signal(
            action="BUY",
            confidence=round(confidence, 3),
            strategy=self.name,
            reason=f"RSI={market.rsi:.1f}<{self.RSI_MAX} change={market.change_24h_pct:.2f}%",
        )
