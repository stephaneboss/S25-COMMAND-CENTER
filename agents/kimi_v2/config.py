"""
S25-KIMI-v2 Configuration
=========================
All runtime settings for the CEX-DEX arbitrage bot.
Values are loaded from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal


def _require_env(var: str, description: str) -> str:
    """Fetch a required environment variable or raise a clear error."""
    value = os.environ.get(var)
    if not value:
        raise EnvironmentError(
            f"Required env var '{var}' is not set. {description}"
        )
    return value


def _optional_env(var: str, default: str = "") -> str:
    return os.environ.get(var, default)


@dataclass(frozen=True)
class Config:
    """
    Immutable runtime configuration for S25-KIMI-v2.

    Load via `Config.from_env()` — never instantiate directly in production.
    """

    # ─── Execution Mode ────────────────────────────────────────────────────────
    MODE: Literal["dry", "paper", "live"] = "dry"

    # ─── Wallet ────────────────────────────────────────────────────────────────
    WALLET_MNEMONIC: str = ""
    WALLET_ADDRESS: str = ""

    # ─── Trade Sizing (USD) ────────────────────────────────────────────────────
    TRADE_SIZE_USD: float = 5.0
    MAX_TRADE_USD: float = 10.0
    MIN_RESERVE_USD: float = 2.0

    # ─── Risk Limits ───────────────────────────────────────────────────────────
    MAX_DAILY_LOSS_USD: float = 15.0
    MAX_CONSECUTIVE_FAILS: int = 3
    CIRCUIT_BREAKER_COOLDOWN_MIN: int = 60

    # ─── Signal Thresholds ─────────────────────────────────────────────────────
    SPREAD_THRESHOLD: float = 0.005   # 0.5 % minimum spread to act
    MIN_SIGNAL_SCORE: int = 60        # 0-100 composite score

    # ─── Timing ────────────────────────────────────────────────────────────────
    SCAN_INTERVAL: int = 30           # seconds between main-loop iterations

    # ─── Telegram ──────────────────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # ─── Osmosis LCD ───────────────────────────────────────────────────────────
    OSMOSIS_LCD: str = "https://lcd.osmosis.zone"

    # ─── MEXC REST API ─────────────────────────────────────────────────────────
    MEXC_API: str = "https://api.mexc.com/api/v3"

    # ─── Osmosis Pool IDs ──────────────────────────────────────────────────────
    # Pool 1  : ATOM / OSMO
    # Pool 3  : AKT  / OSMO
    # Pool 678: OSMO / USDC
    POOL_ATOM_OSMO: int = 1
    POOL_AKT_OSMO: int = 3
    POOL_OSMO_USDC: int = 678

    # ─── IBC / Native Denoms ───────────────────────────────────────────────────
    DENOM_ATOM: str = (
        "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
    )
    DENOM_OSMO: str = "uosmo"
    DENOM_USDC: str = (
        "ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858"
    )

    # ─── Slippage ──────────────────────────────────────────────────────────────
    MAX_SLIPPAGE: float = 0.01        # 1 % max accepted slippage

    # ─── Liquidity Floor ───────────────────────────────────────────────────────
    MIN_POOL_LIQUIDITY_USD: float = 10_000.0

    # ─── Database ──────────────────────────────────────────────────────────────
    DB_PATH: str = "trades.db"

    # ─── Price Cache ───────────────────────────────────────────────────────────
    PRICE_CACHE_SECONDS: int = 5

    # ─── Heartbeat ─────────────────────────────────────────────────────────────
    HEARTBEAT_INTERVAL: int = 100     # log heartbeat every N scans

    @classmethod
    def from_env(cls) -> "Config":
        """
        Build a Config from environment variables.

        Rules
        -----
        - MODE defaults to "dry"; changing to "live" requires
          the env var ``LIVE_MODE_CONFIRMED=yes`` to be set.
        - Wallet credentials are only required in live/paper mode.
        - Telegram credentials are optional (alerts degrade gracefully).
        """
        raw_mode = _optional_env("S25_MODE", "dry").lower()
        if raw_mode not in ("dry", "paper", "live"):
            raise ValueError(
                f"S25_MODE must be one of dry/paper/live, got '{raw_mode}'"
            )
        mode: Literal["dry", "paper", "live"] = raw_mode  # type: ignore[assignment]

        if mode == "live":
            confirmed = _optional_env("LIVE_MODE_CONFIRMED", "").lower()
            if confirmed != "yes":
                raise EnvironmentError(
                    "To run in LIVE mode you must set LIVE_MODE_CONFIRMED=yes. "
                    "This is a deliberate safety gate."
                )
            wallet_mnemonic = _require_env(
                "WALLET_MNEMONIC", "Required for live trading."
            )
            wallet_address = _require_env(
                "WALLET_ADDRESS", "Required for live trading."
            )
        elif mode == "paper":
            wallet_mnemonic = _optional_env("WALLET_MNEMONIC")
            wallet_address = _optional_env("WALLET_ADDRESS")
        else:
            wallet_mnemonic = ""
            wallet_address = ""

        return cls(
            MODE=mode,
            WALLET_MNEMONIC=wallet_mnemonic,
            WALLET_ADDRESS=wallet_address,
            # Trade sizing
            TRADE_SIZE_USD=float(_optional_env("TRADE_SIZE_USD", "5.0")),
            MAX_TRADE_USD=float(_optional_env("MAX_TRADE_USD", "10.0")),
            MIN_RESERVE_USD=float(_optional_env("MIN_RESERVE_USD", "2.0")),
            # Risk
            MAX_DAILY_LOSS_USD=float(_optional_env("MAX_DAILY_LOSS_USD", "15.0")),
            MAX_CONSECUTIVE_FAILS=int(_optional_env("MAX_CONSECUTIVE_FAILS", "3")),
            CIRCUIT_BREAKER_COOLDOWN_MIN=int(
                _optional_env("CIRCUIT_BREAKER_COOLDOWN_MIN", "60")
            ),
            # Signal
            SPREAD_THRESHOLD=float(_optional_env("SPREAD_THRESHOLD", "0.005")),
            MIN_SIGNAL_SCORE=int(_optional_env("MIN_SIGNAL_SCORE", "60")),
            # Timing
            SCAN_INTERVAL=int(_optional_env("SCAN_INTERVAL", "30")),
            # Telegram
            TELEGRAM_TOKEN=_optional_env("TELEGRAM_TOKEN"),
            TELEGRAM_CHAT_ID=_optional_env("TELEGRAM_CHAT_ID"),
            # Endpoints
            OSMOSIS_LCD=_optional_env(
                "OSMOSIS_LCD", "https://lcd.osmosis.zone"
            ),
            MEXC_API=_optional_env(
                "MEXC_API", "https://api.mexc.com/api/v3"
            ),
            # DB
            DB_PATH=_optional_env("DB_PATH", "trades.db"),
        )

    # ── Convenience helpers ────────────────────────────────────────────────────

    @property
    def is_live(self) -> bool:
        return self.MODE == "live"

    @property
    def is_paper(self) -> bool:
        return self.MODE == "paper"

    @property
    def is_dry(self) -> bool:
        return self.MODE == "dry"

    @property
    def pool_id_for(self) -> dict[str, int]:
        """Map symbol → primary pool ID used for price queries."""
        return {
            "ATOM": self.POOL_ATOM_OSMO,
            "AKT": self.POOL_AKT_OSMO,
            "OSMO": self.POOL_OSMO_USDC,
        }

    def __repr__(self) -> str:
        return (
            f"Config(MODE={self.MODE!r}, "
            f"TRADE_SIZE_USD={self.TRADE_SIZE_USD}, "
            f"SPREAD_THRESHOLD={self.SPREAD_THRESHOLD}, "
            f"MIN_SIGNAL_SCORE={self.MIN_SIGNAL_SCORE})"
        )
