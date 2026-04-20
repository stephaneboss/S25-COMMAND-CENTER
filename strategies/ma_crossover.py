"""MA7 × MA25 crossover strategy on 1h candles."""
from __future__ import annotations

from typing import List, Optional

from .base import BaseStrategy, Candle, MarketData, Signal


def _sma(candles: List[Candle], period: int) -> Optional[float]:
    if len(candles) < period:
        return None
    closes = [c.close for c in candles[-period:]]
    return sum(closes) / period


class MaCrossoverStrategy(BaseStrategy):
    name = "ma_crossover"
    description = "MA7 crossing MA25 on 1h candles. Bullish cross=BUY, bearish=SELL"
    default_enabled = False  # disabled until we validate candle pipeline
    default_usd_size = 5.0

    FAST = 7
    SLOW = 25

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        c = market.candles_1h
        if len(c) < self.SLOW + 1:
            return None
        ma_fast_now = _sma(c, self.FAST)
        ma_slow_now = _sma(c, self.SLOW)
        ma_fast_prev = _sma(c[:-1], self.FAST)
        ma_slow_prev = _sma(c[:-1], self.SLOW)
        if None in (ma_fast_now, ma_slow_now, ma_fast_prev, ma_slow_prev):
            return None
        # Bullish cross: fast was below, now above
        if ma_fast_prev <= ma_slow_prev and ma_fast_now > ma_slow_now:
            spread = (ma_fast_now - ma_slow_now) / ma_slow_now * 100
            return Signal(
                action="BUY",
                confidence=min(0.85, 0.65 + spread / 10),
                strategy=self.name,
                reason=f"bullish MA7×MA25 cross spread={spread:.2f}%",
            )
        # Bearish cross: fast was above, now below
        if ma_fast_prev >= ma_slow_prev and ma_fast_now < ma_slow_now:
            spread = (ma_slow_now - ma_fast_now) / ma_slow_now * 100
            return Signal(
                action="SELL",
                confidence=min(0.82, 0.65 + spread / 10),
                strategy=self.name,
                reason=f"bearish MA7×MA25 cross spread={spread:.2f}%",
            )
        return None
