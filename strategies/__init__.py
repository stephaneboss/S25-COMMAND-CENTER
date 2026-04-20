"""S25 Trading Strategies package (v2, +4 advanced strategies)."""
from .base import BaseStrategy, Signal, MarketData
from .registry import get_registry, StrategyRegistry
from .rsi_dip import RsiDipStrategy
from .rsi_top import RsiTopStrategy
from .ma_crossover import MaCrossoverStrategy
from .breakout import BreakoutStrategy
from .macd_cross import MacdCrossStrategy
from .bollinger_bounce import BollingerBounceStrategy
from .stoch_rsi_bounce import StochRsiBounceStrategy
from .volume_surge import VolumeSurgeStrategy

__all__ = [
    "BaseStrategy", "Signal", "MarketData",
    "StrategyRegistry", "get_registry",
    "RsiDipStrategy", "RsiTopStrategy",
    "MaCrossoverStrategy", "BreakoutStrategy",
    "MacdCrossStrategy", "BollingerBounceStrategy",
    "StochRsiBounceStrategy", "VolumeSurgeStrategy",
]


def bootstrap() -> StrategyRegistry:
    r = get_registry()
    r.register(RsiDipStrategy())
    r.register(RsiTopStrategy())
    r.register(MaCrossoverStrategy())
    r.register(BreakoutStrategy())
    r.register(MacdCrossStrategy())
    r.register(BollingerBounceStrategy())
    r.register(StochRsiBounceStrategy())
    r.register(VolumeSurgeStrategy())
    return r
