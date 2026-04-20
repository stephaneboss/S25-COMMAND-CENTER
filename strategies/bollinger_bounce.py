"""Bollinger band mean-reversion: BUY when price touches lower band and RSI<45."""
from __future__ import annotations

from typing import Optional

from .base import BaseStrategy, MarketData, Signal
from .indicators import bollinger


class BollingerBounceStrategy(BaseStrategy):
    name = "bollinger_bounce"
    description = "BUY when close <= lower Bollinger band (20,2) AND RSI < 45"
    default_enabled = False
    default_usd_size = 3.0

    PERIOD = 20
    NUM_STD = 2.0
    RSI_MAX = 45.0

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        if len(market.candles_1h) < self.PERIOD + 1 or market.rsi is None:
            return None
        closes = [c.close for c in market.candles_1h]
        mid, upper, lower = bollinger(closes, self.PERIOD, self.NUM_STD)
        if lower is None:
            return None
        last_close = closes[-1]
        if market.rsi > self.RSI_MAX:
            return None
        if last_close > lower:
            return None

        # Distance below lower band (how deep)
        penetration = (lower - last_close) / lower * 100
        confidence = min(0.88, 0.60 + penetration / 5 + (self.RSI_MAX - market.rsi) / 100)
        return Signal(
            action="BUY",
            confidence=round(confidence, 3),
            strategy=self.name,
            reason=f"BB lower touch: close={last_close:.5f} lower={lower:.5f} RSI={market.rsi:.1f}",
        )
