#!/usr/bin/env python3
"""
S25 Backtester v1
=================
Replays any registered strategy against historical 1h candles from Coinbase
and reports simulated P&L, win rate, max drawdown.

Simulation rules:
  - At each candle i (>= warmup), build MarketData with:
      spot = candles[i].close
      rsi  = RSI(14) computed on candles[0..i]
      change_24h_pct = (close[i] / close[i-24] - 1) * 100
      candles_1h = candles[0..i]
  - Strategy decides BUY or SELL
  - For each BUY at price p: open a position with SL=-3%, TP=+6%
  - On each subsequent candle, check if low <= SL or high >= TP -> close
  - If neither, and strategy says SELL -> close at current close
  - Fee 1.2% taker on each leg
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("s25.backtest")


def _rsi(closes: List[float], period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    gains, losses = 0.0, 0.0
    for i in range(-period, 0):
        diff = closes[i] - closes[i - 1]
        if diff >= 0: gains += diff
        else: losses -= diff
    avg_g = gains / period
    avg_l = losses / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100.0 - (100.0 / (1.0 + rs))


@dataclass
class BTPosition:
    entry_price: float
    entry_ts: int
    qty_usd: float  # notional at entry
    sl_price: float
    tp_price: float


@dataclass
class BTStats:
    trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl_pct: float = 0.0
    pnl_series: List[float] = field(default_factory=list)
    max_drawdown_pct: float = 0.0
    closes_log: List[Dict] = field(default_factory=list)

    def finalize(self) -> Dict:
        win_rate = (self.wins / self.trades * 100) if self.trades else 0
        avg_win = (sum(p for p in self.pnl_series if p > 0) / self.wins) if self.wins else 0
        avg_loss = (sum(p for p in self.pnl_series if p < 0) / self.losses) if self.losses else 0
        # Max drawdown calc
        peak = 0
        equity = 0
        max_dd = 0
        for p in self.pnl_series:
            equity += p
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
        return {
            "trades": self.trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate_pct": round(win_rate, 2),
            "total_pnl_pct": round(self.total_pnl_pct, 3),
            "avg_win_pct": round(avg_win, 3),
            "avg_loss_pct": round(avg_loss, 3),
            "max_drawdown_pct": round(max_dd, 3),
            "closes": self.closes_log[-20:],  # last 20 trades
        }


def backtest_strategy(strategy, candles, symbol: str,
                      sl_pct: float = 3.0, tp_pct: float = 6.0,
                      fee_pct: float = 1.2, warmup: int = 26) -> Dict:
    """Replay strategy on candles. Returns stats dict."""
    from strategies.base import MarketData
    stats = BTStats()
    positions: List[BTPosition] = []

    for i in range(warmup, len(candles)):
        prior = candles[:i + 1]
        current = candles[i]
        closes = [c.close for c in prior]
        rsi = _rsi(closes, 14)
        change_24h_pct = None
        if i >= 24:
            change_24h_pct = (current.close / candles[i - 24].close - 1) * 100

        # Check open positions for SL/TP hit first
        still_open = []
        for pos in positions:
            hit = None
            if current.low <= pos.sl_price:
                hit = ("SL", pos.sl_price)
            elif current.high >= pos.tp_price:
                hit = ("TP", pos.tp_price)
            if hit:
                exit_price = hit[1]
                gross_pct = (exit_price / pos.entry_price - 1) * 100
                net_pct = gross_pct - 2 * fee_pct
                stats.trades += 1
                stats.pnl_series.append(net_pct)
                stats.total_pnl_pct += net_pct
                if net_pct > 0: stats.wins += 1
                else: stats.losses += 1
                stats.closes_log.append({
                    "entry": pos.entry_price, "exit": exit_price,
                    "reason": hit[0], "pnl_pct": round(net_pct, 3),
                })
            else:
                still_open.append(pos)
        positions = still_open

        # Build market
        market = MarketData(
            symbol=symbol, spot=current.close,
            change_24h_pct=change_24h_pct, rsi=rsi,
            candles_1h=prior,
        )
        try:
            sig = strategy.should_fire(market)
        except Exception:
            sig = None
        if not sig:
            continue

        if sig.action == "BUY":
            entry = current.close
            positions.append(BTPosition(
                entry_price=entry, entry_ts=current.start, qty_usd=100,  # %-based, notional arbitrary
                sl_price=entry * (1 - sl_pct / 100),
                tp_price=entry * (1 + tp_pct / 100),
            ))
        elif sig.action == "SELL" and positions:
            # Close oldest position at market
            pos = positions.pop(0)
            exit_price = current.close
            gross_pct = (exit_price / pos.entry_price - 1) * 100
            net_pct = gross_pct - 2 * fee_pct
            stats.trades += 1
            stats.pnl_series.append(net_pct)
            stats.total_pnl_pct += net_pct
            if net_pct > 0: stats.wins += 1
            else: stats.losses += 1
            stats.closes_log.append({
                "entry": pos.entry_price, "exit": exit_price,
                "reason": "SIGNAL_SELL", "pnl_pct": round(net_pct, 3),
            })

    return stats.finalize()


def run_all(strategy_name: str, symbol: str, days: int = 30) -> Dict:
    """Entry point for /api/trading/backtest."""
    from agents.coinbase_executor import get_executor
    import strategies

    registry = strategies.bootstrap()
    strategy = registry.strategies.get(strategy_name)
    if strategy is None:
        return {"ok": False, "error": f"unknown strategy: {strategy_name}"}

    exe = get_executor()
    limit = min(300, days * 24)
    candles = exe.get_candles(symbol, "ONE_HOUR", limit=limit)
    if len(candles) < 30:
        return {"ok": False, "error": f"not enough candles: {len(candles)}"}

    result = backtest_strategy(strategy, candles, symbol)
    return {"ok": True, "strategy": strategy_name, "symbol": symbol,
            "candles_used": len(candles), **result}
