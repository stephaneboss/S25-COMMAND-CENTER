"""
S25-KIMI-v2 Risk Manager
========================
All guardrails that stand between the oracle signal and actual execution.

Components
----------
CircuitBreaker   – shuts trading down after repeated failures
BalanceGuard     – enforces reserve and per-trade size limits
PositionSizer    – scales notional exposure to signal confidence
DailyLossTracker – hard stop once MAX_DAILY_LOSS_USD is reached
RiskManager      – facade that runs the full pre-trade gauntlet
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)


# ─── Circuit Breaker ──────────────────────────────────────────────────────────

@dataclass
class CircuitBreaker:
    """
    Trips after *max_fails* consecutive execution failures and blocks all
    trading until the cooldown period expires.

    Usage::

        cb = CircuitBreaker(config)
        cb.record_failure()
        if cb.is_tripped:
            ...wait...
        cb.record_success()  # resets consecutive count
    """

    _max_fails: int
    _cooldown_seconds: float
    _consecutive_fails: int = field(default=0, init=False)
    _tripped_at: Optional[float] = field(default=None, init=False)

    @classmethod
    def from_config(cls, config: Config) -> "CircuitBreaker":
        return cls(
            _max_fails=config.MAX_CONSECUTIVE_FAILS,
            _cooldown_seconds=config.CIRCUIT_BREAKER_COOLDOWN_MIN * 60,
        )

    @property
    def is_tripped(self) -> bool:
        """True if the breaker is open (trading blocked)."""
        if self._tripped_at is None:
            return False
        elapsed = time.monotonic() - self._tripped_at
        if elapsed >= self._cooldown_seconds:
            # Auto-reset
            logger.info(
                "CircuitBreaker: cooldown expired after %.0f s — resetting",
                elapsed,
            )
            self._reset()
            return False
        return True

    @property
    def seconds_until_reset(self) -> float:
        """Remaining seconds before auto-reset (0 if not tripped)."""
        if self._tripped_at is None:
            return 0.0
        remaining = self._cooldown_seconds - (time.monotonic() - self._tripped_at)
        return max(0.0, remaining)

    @property
    def consecutive_fails(self) -> int:
        return self._consecutive_fails

    def record_success(self) -> None:
        """Call after a successful trade execution."""
        if self._consecutive_fails > 0:
            logger.debug("CircuitBreaker: resetting fail counter after success")
        self._consecutive_fails = 0

    def record_failure(self) -> None:
        """Call after a failed trade execution."""
        self._consecutive_fails += 1
        logger.warning(
            "CircuitBreaker: failure recorded (%d/%d)",
            self._consecutive_fails,
            self._max_fails,
        )
        if self._consecutive_fails >= self._max_fails:
            self._trip()

    def _trip(self) -> None:
        if self._tripped_at is None:
            logger.error(
                "CircuitBreaker TRIPPED after %d consecutive failures. "
                "Cooling down for %.0f minutes.",
                self._consecutive_fails,
                self._cooldown_seconds / 60,
            )
            self._tripped_at = time.monotonic()

    def _reset(self) -> None:
        self._consecutive_fails = 0
        self._tripped_at = None


# ─── Balance Guard ────────────────────────────────────────────────────────────

class BalanceGuard:
    """
    Enforces wallet reserve and per-trade size caps.

    Rules
    -----
    - Never trade if balance_usd <= MIN_RESERVE_USD
    - Per-trade size ≤ min(TRADE_SIZE_USD, MAX_TRADE_USD, 10 % of balance)
    """

    def __init__(self, config: Config) -> None:
        self._cfg = config

    def check_reserve(self, balance_usd: float) -> bool:
        """Return True if balance is above the minimum reserve."""
        ok = balance_usd > self._cfg.MIN_RESERVE_USD
        if not ok:
            logger.warning(
                "BalanceGuard: balance $%.2f is below reserve $%.2f",
                balance_usd, self._cfg.MIN_RESERVE_USD,
            )
        return ok

    def get_safe_trade_size(self, balance_usd: float, trade_size_usd: float) -> float:
        """
        Return the adjusted trade size that respects all safety rules.

        Caps
        ----
        1. Configured TRADE_SIZE_USD
        2. MAX_TRADE_USD hard cap
        3. 10 % of current wallet balance
        4. Never leave balance below MIN_RESERVE_USD
        """
        ten_pct = balance_usd * 0.10
        available = balance_usd - self._cfg.MIN_RESERVE_USD

        size = min(
            trade_size_usd,
            self._cfg.MAX_TRADE_USD,
            ten_pct,
            available,
        )
        size = max(0.0, size)

        if size < trade_size_usd:
            logger.info(
                "BalanceGuard: trade size reduced from $%.2f to $%.2f "
                "(balance=$%.2f)",
                trade_size_usd, size, balance_usd,
            )
        return size


# ─── Position Sizer ───────────────────────────────────────────────────────────

class PositionSizer:
    """
    Converts a signal score and balance into a concrete position size
    expressed in micro-units (1 ATOM = 1_000_000 uatom).

    Scaling table
    -------------
    score  60-69  → 50 % of safe trade size
    score  70-84  → 75 % of safe trade size
    score  85-100 → 100 % of safe trade size
    """

    def __init__(self, config: Config) -> None:
        self._cfg = config
        self._guard = BalanceGuard(config)

    def calculate(
        self,
        signal_score: int,
        balance_usd: float,
        price: float,
    ) -> int:
        """
        Return position size in micro-units (integer).

        Parameters
        ----------
        signal_score:
            Composite score 0-100.
        balance_usd:
            Current wallet value in USD.
        price:
            Current asset price in USD (used to convert $ → units).

        Returns
        -------
        int
            Position in micro-units.  Returns 0 if score is below threshold
            or balance is insufficient.
        """
        if signal_score < self._cfg.MIN_SIGNAL_SCORE:
            logger.debug("PositionSizer: score %d below threshold, size=0", signal_score)
            return 0

        if price <= 0:
            logger.warning("PositionSizer: price is zero or negative, size=0")
            return 0

        # Determine scaling factor
        if signal_score >= 85:
            scale = 1.00
        elif signal_score >= 70:
            scale = 0.75
        else:
            scale = 0.50

        safe_usd = self._guard.get_safe_trade_size(
            balance_usd, self._cfg.TRADE_SIZE_USD
        )
        notional_usd = safe_usd * scale
        amount_base = notional_usd / price           # in whole tokens
        amount_micro = int(amount_base * 1_000_000)  # convert to micro-units

        logger.debug(
            "PositionSizer: score=%d scale=%.2f notional=$%.2f "
            "price=$%.4f micro=%d",
            signal_score, scale, notional_usd, price, amount_micro,
        )
        return amount_micro


# ─── Daily Loss Tracker ───────────────────────────────────────────────────────

class DailyLossTracker:
    """
    Tracks realised losses within the current UTC day and halts trading
    once MAX_DAILY_LOSS_USD is exceeded.

    Note: For persistence across restarts, initialise with the value
    returned by ``ledger.get_daily_pnl()``.
    """

    def __init__(self, config: Config, initial_pnl: float = 0.0) -> None:
        self._max_loss = config.MAX_DAILY_LOSS_USD
        self._realised_pnl = initial_pnl
        logger.info(
            "DailyLossTracker initialised: current_pnl=$%.2f limit=$%.2f",
            initial_pnl, self._max_loss,
        )

    @property
    def realised_pnl(self) -> float:
        return self._realised_pnl

    @property
    def loss_limit_reached(self) -> bool:
        """True when today's losses exceed the daily cap."""
        return self._realised_pnl <= -self._max_loss

    def record_trade_pnl(self, pnl_usd: float) -> None:
        """Add a trade P&L (positive = profit, negative = loss)."""
        self._realised_pnl += pnl_usd
        logger.info(
            "DailyLossTracker: trade P&L $%.4f → daily total $%.4f",
            pnl_usd, self._realised_pnl,
        )
        if self.loss_limit_reached:
            logger.error(
                "DailyLossTracker: daily loss limit $%.2f REACHED "
                "(total $%.2f). Trading halted.",
                self._max_loss, self._realised_pnl,
            )

    def reset(self) -> None:
        """Call at start of a new UTC day."""
        logger.info("DailyLossTracker: day reset (previous P&L $%.2f)", self._realised_pnl)
        self._realised_pnl = 0.0


# ─── RiskManager (facade) ─────────────────────────────────────────────────────

class RiskManager:
    """
    Single entry-point for all risk checks.

    Instantiate once and call ``pre_trade_check`` before every execution.
    Feed results back via ``record_outcome`` so the circuit breaker and
    loss tracker stay up-to-date.
    """

    def __init__(self, config: Config, initial_daily_pnl: float = 0.0) -> None:
        self._cfg = config
        self.circuit_breaker = CircuitBreaker.from_config(config)
        self.balance_guard = BalanceGuard(config)
        self.position_sizer = PositionSizer(config)
        self.daily_loss = DailyLossTracker(config, initial_daily_pnl)

    def pre_trade_check(
        self,
        signal: dict,
        balance_usd: float,
    ) -> tuple[bool, str]:
        """
        Run all safety checks before attempting a trade.

        Returns
        -------
        (True, "OK")
            All checks passed.
        (False, reason: str)
            At least one check failed; *reason* is human-readable.
        """
        # 1. Circuit breaker
        if self.circuit_breaker.is_tripped:
            mins = self.circuit_breaker.seconds_until_reset / 60
            return False, (
                f"Circuit breaker is tripped — resets in {mins:.1f} min"
            )

        # 2. Daily loss limit
        if self.daily_loss.loss_limit_reached:
            return False, (
                f"Daily loss limit reached "
                f"(P&L ${self.daily_loss.realised_pnl:.2f})"
            )

        # 3. Balance reserve
        if not self.balance_guard.check_reserve(balance_usd):
            return False, (
                f"Balance ${balance_usd:.2f} is below reserve "
                f"${self._cfg.MIN_RESERVE_USD:.2f}"
            )

        # 4. Signal score
        score = signal.get("score", 0)
        if score < self._cfg.MIN_SIGNAL_SCORE:
            return False, (
                f"Signal score {score} < threshold {self._cfg.MIN_SIGNAL_SCORE}"
            )

        # 5. Spread sanity
        spread_pct = abs(signal.get("spread_pct", 0.0))
        if spread_pct < self._cfg.SPREAD_THRESHOLD:
            return False, (
                f"Spread {spread_pct:.4%} < threshold "
                f"{self._cfg.SPREAD_THRESHOLD:.4%}"
            )

        # 6. Effective trade size > 0
        safe_size = self.balance_guard.get_safe_trade_size(
            balance_usd, self._cfg.TRADE_SIZE_USD
        )
        if safe_size <= 0:
            return False, "Effective trade size would be zero or negative"

        return True, "OK"

    def record_outcome(self, success: bool, pnl_usd: float = 0.0) -> None:
        """
        Feed back the result of an execution attempt.

        - On failure: increments circuit-breaker counter.
        - On success: resets circuit-breaker counter.
        - Always: updates daily P&L tracker.
        """
        if success:
            self.circuit_breaker.record_success()
        else:
            self.circuit_breaker.record_failure()

        if pnl_usd != 0.0:
            self.daily_loss.record_trade_pnl(pnl_usd)

    def calculate_position(
        self,
        signal: dict,
        balance_usd: float,
    ) -> int:
        """Convenience wrapper around PositionSizer.calculate."""
        score = signal.get("score", 0)
        price = signal.get("osm_price") or signal.get("cex_price") or 0.0
        return self.position_sizer.calculate(score, balance_usd, price)
