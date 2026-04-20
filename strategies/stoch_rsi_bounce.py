"""Stoch RSI oversold bounce: BUY when %K crosses above %D in oversold (< 20)."""
from __future__ import annotations

from typing import Optional

from .base import BaseStrategy, MarketData, Signal
from .indicators import stoch_rsi


class StochRsiBounceStrategy(BaseStrategy):
    name = "stoch_rsi_bounce"
    description = "BUY on Stoch-RSI %K crossing above %D while both < 25"
    default_enabled = False
    default_usd_size = 3.0

    OVERSOLD = 25.0

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        if len(market.candles_1h) < 40:
            return None
        closes = [c.close for c in market.candles_1h]
        k_now, d_now = stoch_rsi(closes)
        k_prev, d_prev = stoch_rsi(closes[:-1])
        if None in (k_now, d_now, k_prev, d_prev):
            return None

        if (k_prev <= d_prev and k_now > d_now
                and k_now < self.OVERSOLD + 5 and d_now < self.OVERSOLD + 5):
            confidence = min(0.85, 0.62 + (self.OVERSOLD - min(k_now, d_now)) / 50)
            return Signal(
                action="BUY",
                confidence=round(confidence, 3),
                strategy=self.name,
                reason=f"StochRSI bounce: %K {k_prev:.1f}->{k_now:.1f} %D {d_prev:.1f}->{d_now:.1f}",
            )
        return None
