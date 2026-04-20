"""
S25 Risk Engine — pro-grade position sizing and dynamic SL.

- compute_notional: risk-based sizing from portfolio value and SL distance
- compute_atr_pct: 1.5x ATR on 1h candles → adaptive SL per coin
- get_config / set_config: persistent risk parameters
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("s25.risk_engine")

CONFIG_FILE = Path(__file__).resolve().parent.parent / "memory" / "risk_config.json"

DEFAULT_CONFIG = {
    "risk_per_trade_pct": 1.0,        # % of portfolio risked per trade
    "default_sl_pct": 3.0,            # baseline SL when ATR unavailable
    "default_tp_pct": 6.0,            # baseline TP (2x SL for 1:2 R/R)
    "use_volatility_sl": True,        # if True, SL = max(1.0, min(8.0, 1.5*ATR%))
    "atr_multiplier": 1.5,
    "atr_period": 14,
    "sl_min_pct": 1.0,
    "sl_max_pct": 8.0,
    "max_concurrent_positions": 3,
    "max_single_trade_usd": 50.0,
    "min_single_trade_usd": 1.0,      # Coinbase market min
    # Trailing stop thresholds
    "trail_activation_pct": 3.0,      # move SL to breakeven once +3%
    "trail_step_pct": 2.0,            # once above activation, SL trails by 2%
    "trail_enabled": True,
}


def get_config() -> Dict:
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        cfg = json.loads(CONFIG_FILE.read_text())
        # Fill missing keys from defaults
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception as e:
        logger.warning("risk config load failed: %s", e)
        return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def set_config(updates: Dict) -> Dict:
    cfg = get_config()
    for k, v in updates.items():
        if k in DEFAULT_CONFIG:
            cfg[k] = v
    save_config(cfg)
    return cfg


def compute_atr_pct(candles: List, period: int = 14) -> Optional[float]:
    """Return ATR as % of last close."""
    if not candles or len(candles) < period + 1:
        return None
    trs: List[float] = []
    for i in range(1, len(candles)):
        c = candles[i]
        prev_close = candles[i - 1].close
        tr = max(
            c.high - c.low,
            abs(c.high - prev_close),
            abs(c.low - prev_close),
        )
        trs.append(tr)
    recent = trs[-period:]
    if not recent:
        return None
    atr = sum(recent) / len(recent)
    last_close = candles[-1].close
    if last_close <= 0:
        return None
    return (atr / last_close) * 100.0


def compute_adaptive_sl_pct(candles, cfg: Optional[Dict] = None) -> float:
    """Return adaptive SL %. Falls back to default_sl_pct if ATR unavailable."""
    cfg = cfg or get_config()
    if not cfg.get("use_volatility_sl", True):
        return cfg["default_sl_pct"]
    atr = compute_atr_pct(candles, cfg.get("atr_period", 14))
    if atr is None:
        return cfg["default_sl_pct"]
    sl = atr * cfg.get("atr_multiplier", 1.5)
    sl_min = cfg.get("sl_min_pct", 1.0)
    sl_max = cfg.get("sl_max_pct", 8.0)
    return max(sl_min, min(sl_max, sl))


def compute_notional(
    portfolio_usd: float,
    sl_pct: float,
    cfg: Optional[Dict] = None,
) -> float:
    """Return the USD notional for a new trade, given portfolio and SL distance."""
    cfg = cfg or get_config()
    if portfolio_usd <= 0 or sl_pct <= 0:
        return cfg["min_single_trade_usd"]
    risk_amount = portfolio_usd * cfg["risk_per_trade_pct"] / 100.0
    notional = risk_amount / (sl_pct / 100.0)
    # Never exceed half the portfolio in a single trade for small accounts
    soft_cap = portfolio_usd * 0.5
    notional = min(notional, soft_cap)
    notional = min(notional, cfg["max_single_trade_usd"])
    notional = max(cfg["min_single_trade_usd"], notional)
    return round(notional, 2)


def summary(portfolio_usd: float, candles_by_symbol: Dict[str, list]) -> Dict:
    """For /api/trading/risk-config — full risk picture."""
    cfg = get_config()
    per_symbol = {}
    for sym, candles in (candles_by_symbol or {}).items():
        atr = compute_atr_pct(candles, cfg["atr_period"])
        sl_pct = compute_adaptive_sl_pct(candles, cfg)
        notional = compute_notional(portfolio_usd, sl_pct, cfg)
        per_symbol[sym] = {
            "atr_pct": round(atr, 3) if atr is not None else None,
            "sl_pct": round(sl_pct, 3),
            "tp_pct": round(sl_pct * (cfg["default_tp_pct"] / cfg["default_sl_pct"]), 3),
            "notional_usd": notional,
        }
    return {
        "portfolio_usd": round(portfolio_usd, 2),
        "config": cfg,
        "per_symbol": per_symbol,
    }
