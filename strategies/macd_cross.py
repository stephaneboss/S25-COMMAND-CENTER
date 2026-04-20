"""MACD histogram crosses zero on 1h candles."""
from __future__ import annotations

from typing import Optional

from .base import BaseStrategy, MarketData, Signal
from .indicators import macd


class MacdCrossStrategy(BaseStrategy):
    name = "macd_cross"
    description = "MACD(12,26,9) histogram crossing zero on 1h candles"
    default_enabled = False  # needs backtest validation
    default_usd_size = 3.0

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        if len(market.candles_1h) < 40:
            return None
        closes = [c.close for c in market.candles_1h]
        m_now, sig, hist_now = macd(closes)
        if hist_now is None:
            return None
        # Compute previous hist to detect cross
        m_prev, sig_prev, hist_prev = macd(closes[:-1])
        if hist_prev is None:
            return None

        if hist_prev <= 0 and hist_now > 0:
            return Signal(
                action="BUY",
                confidence=min(0.85, 0.60 + abs(hist_now) / max(closes[-1] * 0.001, 1e-9) * 0.05),
                strategy=self.name,
                reason=f"MACD hist cross up: {hist_prev:.5f}->{hist_now:.5f}",
            )
        if hist_prev >= 0 and hist_now < 0:
            return Signal(
                action="SELL",
                confidence=min(0.80, 0.60 + abs(hist_now) / max(closes[-1] * 0.001, 1e-9) * 0.05),
                strategy=self.name,
                reason=f"MACD hist cross down: {hist_prev:.5f}->{hist_now:.5f}",
            )
        return None
