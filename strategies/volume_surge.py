"""Volume surge + green candle: BUY when current vol z-score > 2 and last candle green."""
from __future__ import annotations

from typing import Optional

from .base import BaseStrategy, MarketData, Signal
from .indicators import volume_zscore


class VolumeSurgeStrategy(BaseStrategy):
    name = "volume_surge"
    description = "BUY when volume z-score > 2 and last candle closes green (+)"
    default_enabled = False
    default_usd_size = 3.0

    Z_THRESHOLD = 2.0

    def should_fire(self, market: MarketData) -> Optional[Signal]:
        if len(market.candles_1h) < 25:
            return None
        volumes = [c.volume for c in market.candles_1h]
        z = volume_zscore(volumes, period=20)
        if z is None or z < self.Z_THRESHOLD:
            return None
        last = market.candles_1h[-1]
        if last.close <= last.open:
            return None  # only if green
        green_pct = (last.close - last.open) / last.open * 100
        if green_pct < 0.5:
            return None  # need meaningful push
        confidence = min(0.82, 0.60 + (z - self.Z_THRESHOLD) / 10 + green_pct / 20)
        return Signal(
            action="BUY",
            confidence=round(confidence, 3),
            strategy=self.name,
            reason=f"vol z={z:.2f} green +{green_pct:.2f}%",
        )
