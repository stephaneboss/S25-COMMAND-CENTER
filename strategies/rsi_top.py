"""Top-sell strategy: RSI > 70 AND 24h change > +5%."""
from __future__ import annotations

from typing import Optional

from .base import BaseStrategy, MarketData, Signal


class RsiTopStrategy(BaseStrategy):
    name = "rsi_top"
    description = "Sell when RSI > 70 and 24h change is > +5%"
    default_enabled = True
    default_usd_size = 2.0

    RSI_MIN = 70.0
    CHANGE_MIN = 5.0

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        if market.rsi is None or market.change_24h_pct is None:
            return None
        if market.rsi <= self.RSI_MIN:
            return None
        if market.change_24h_pct <= self.CHANGE_MIN:
            return None
        confidence = min(0.88, 0.60 + (market.rsi - self.RSI_MIN) / 100 + market.change_24h_pct / 100)
        return Signal(
            action="SELL",
            confidence=round(confidence, 3),
            strategy=self.name,
            reason=f"RSI={market.rsi:.1f}>{self.RSI_MIN} change={market.change_24h_pct:.2f}%",
        )
