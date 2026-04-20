"""S25 Technical Indicators — pure Python, no extra deps.

Covers: EMA, SMA, MACD, Bollinger Bands, Stochastic RSI, ATR (already in
risk_engine), volume z-score, consecutive-candles color.
"""
from __future__ import annotations

from typing import List, Optional, Tuple


def sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    alpha = 2 / (period + 1)
    # Seed EMA with SMA over the first `period` values
    seed = sum(values[:period]) / period
    e = seed
    for v in values[period:]:
        e = v * alpha + e * (1 - alpha)
    return e


def ema_series(values: List[float], period: int) -> List[float]:
    """Return full EMA series (same length as input; uses SMA seed)."""
    if len(values) < period:
        return []
    alpha = 2 / (period + 1)
    seed = sum(values[:period]) / period
    out = [seed]
    for v in values[period:]:
        out.append(v * alpha + out[-1] * (1 - alpha))
    # Pad left so index aligns with input (None for pre-seed positions)
    return [None] * (period - 1) + out  # type: ignore


def macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (macd_line, signal_line, histogram). None if insufficient data."""
    if len(closes) < slow + signal:
        return None, None, None
    ef = ema_series(closes, fast)
    es = ema_series(closes, slow)
    macd_line = [f - s if (f is not None and s is not None) else None for f, s in zip(ef, es)]
    valid = [m for m in macd_line if m is not None]
    if len(valid) < signal:
        return None, None, None
    sig = ema(valid, signal)
    m_now = valid[-1]
    hist = m_now - sig if sig is not None else None
    return m_now, sig, hist


def bollinger(closes: List[float], period: int = 20, num_std: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (middle, upper, lower)."""
    if len(closes) < period:
        return None, None, None
    window = closes[-period:]
    m = sum(window) / period
    var = sum((v - m) ** 2 for v in window) / period
    std = var ** 0.5
    return m, m + num_std * std, m - num_std * std


def stoch_rsi(closes: List[float], rsi_period: int = 14, stoch_period: int = 14,
              smooth_k: int = 3, smooth_d: int = 3) -> Tuple[Optional[float], Optional[float]]:
    """Return (%K, %D). Both in [0, 100]."""
    if len(closes) < rsi_period + stoch_period + smooth_k:
        return None, None

    # Compute RSI series
    rsi_vals: List[float] = []
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(0.0, diff))
        losses.append(max(0.0, -diff))
    for i in range(rsi_period - 1, len(gains)):
        avg_g = sum(gains[i - rsi_period + 1:i + 1]) / rsi_period
        avg_l = sum(losses[i - rsi_period + 1:i + 1]) / rsi_period
        if avg_l == 0:
            rsi_vals.append(100.0)
        else:
            rs = avg_g / avg_l
            rsi_vals.append(100.0 - (100.0 / (1.0 + rs)))

    if len(rsi_vals) < stoch_period + smooth_k:
        return None, None

    # Stoch RSI = (RSI - min(RSI,N)) / (max(RSI,N) - min(RSI,N))
    stoch_vals: List[float] = []
    for i in range(stoch_period - 1, len(rsi_vals)):
        window = rsi_vals[i - stoch_period + 1:i + 1]
        lo = min(window); hi = max(window)
        if hi == lo:
            stoch_vals.append(50.0)
        else:
            stoch_vals.append((rsi_vals[i] - lo) / (hi - lo) * 100.0)

    if len(stoch_vals) < smooth_k:
        return None, None
    k_series = []
    for i in range(smooth_k - 1, len(stoch_vals)):
        k_series.append(sum(stoch_vals[i - smooth_k + 1:i + 1]) / smooth_k)

    if len(k_series) < smooth_d:
        return None, None
    d = sum(k_series[-smooth_d:]) / smooth_d
    k = k_series[-1]
    return k, d


def volume_zscore(volumes: List[float], period: int = 20) -> Optional[float]:
    """z-score of last volume vs `period` average."""
    if len(volumes) < period + 1:
        return None
    window = volumes[-period - 1:-1]  # exclude current
    mean = sum(window) / period
    var = sum((v - mean) ** 2 for v in window) / period
    std = var ** 0.5
    if std == 0:
        return 0.0
    return (volumes[-1] - mean) / std
