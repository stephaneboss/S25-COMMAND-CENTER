"""S25 Trading Strategies package."""
from .base import BaseStrategy, Signal, MarketData
from .registry import get_registry, StrategyRegistry
from .rsi_dip import RsiDipStrategy
from .rsi_top import RsiTopStrategy
from .ma_crossover import MaCrossoverStrategy
from .breakout import BreakoutStrategy

__all__ = [
    "BaseStrategy",
    "Signal",
    "MarketData",
    "StrategyRegistry",
    "get_registry",
    "RsiDipStrategy",
    "RsiTopStrategy",
    "MaCrossoverStrategy",
    "BreakoutStrategy",
]


def bootstrap() -> StrategyRegistry:
    """Register all built-in strategies in the singleton registry."""
    r = get_registry()
    r.register(RsiDipStrategy())
    r.register(RsiTopStrategy())
    r.register(MaCrossoverStrategy())
    r.register(BreakoutStrategy())
    return r
