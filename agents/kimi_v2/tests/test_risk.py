"""
Unit tests for risk.py
======================
Pure logic tests — no network calls, no file I/O.
"""

from __future__ import annotations

import time
import unittest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from risk import (
    BalanceGuard,
    CircuitBreaker,
    DailyLossTracker,
    PositionSizer,
    RiskManager,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _config(**overrides) -> Config:
    defaults = dict(
        MODE="dry",
        TRADE_SIZE_USD=5.0,
        MAX_TRADE_USD=10.0,
        MIN_RESERVE_USD=2.0,
        MAX_DAILY_LOSS_USD=15.0,
        MAX_CONSECUTIVE_FAILS=3,
        CIRCUIT_BREAKER_COOLDOWN_MIN=1,  # 1 min in tests (we mock time anyway)
        SPREAD_THRESHOLD=0.005,
        MIN_SIGNAL_SCORE=60,
    )
    defaults.update(overrides)
    return Config(**defaults)


def _signal(score: int = 70, spread_pct: float = 0.01, direction: str = "BUY") -> dict:
    return {
        "symbol": "ATOM",
        "direction": direction,
        "score": score,
        "spread_pct": spread_pct,
        "osm_price": 9.0,
        "cex_price": 10.0,
    }


# ─── CircuitBreaker ───────────────────────────────────────────────────────────

class TestCircuitBreaker(unittest.TestCase):

    def test_not_tripped_initially(self):
        cb = CircuitBreaker.from_config(_config())
        self.assertFalse(cb.is_tripped)

    def test_trips_after_max_fails(self):
        """Should trip exactly at MAX_CONSECUTIVE_FAILS."""
        cb = CircuitBreaker.from_config(_config(MAX_CONSECUTIVE_FAILS=3))
        cb.record_failure()
        cb.record_failure()
        self.assertFalse(cb.is_tripped)  # 2 fails, not yet
        cb.record_failure()
        self.assertTrue(cb.is_tripped)   # 3rd fail → tripped

    def test_success_resets_counter(self):
        """Recording a success should reset the consecutive fail counter."""
        cb = CircuitBreaker.from_config(_config(MAX_CONSECUTIVE_FAILS=3))
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        self.assertEqual(cb.consecutive_fails, 0)
        self.assertFalse(cb.is_tripped)

    def test_success_after_trip_does_not_reset(self):
        """Once tripped, calling record_success() does NOT reset the breaker
        (only the cooldown timer does)."""
        cb = CircuitBreaker.from_config(_config(MAX_CONSECUTIVE_FAILS=1))
        cb.record_failure()
        self.assertTrue(cb.is_tripped)
        cb.record_success()
        # Still tripped — cooldown hasn't passed
        self.assertTrue(cb.is_tripped)

    def test_auto_reset_after_cooldown(self):
        """
        After the cooldown expires, is_tripped should return False.
        We use a tiny cooldown (0 seconds via monkey-patching) to avoid
        sleeping in tests.
        """
        cb = CircuitBreaker.from_config(_config(MAX_CONSECUTIVE_FAILS=1))
        cb.record_failure()
        self.assertTrue(cb.is_tripped)

        # Simulate cooldown elapsed by rewinding the trip timestamp
        cb._tripped_at = time.monotonic() - (cb._cooldown_seconds + 1)

        self.assertFalse(cb.is_tripped)

    def test_trip_does_not_re_trip(self):
        """
        After circuit is already tripped, additional failures should not
        reset or advance the trip timestamp.
        """
        cb = CircuitBreaker.from_config(_config(MAX_CONSECUTIVE_FAILS=1))
        cb.record_failure()
        first_trip_time = cb._tripped_at

        cb.record_failure()
        cb.record_failure()

        # Trip time should not change
        self.assertEqual(cb._tripped_at, first_trip_time)

    def test_seconds_until_reset(self):
        cb = CircuitBreaker.from_config(
            _config(MAX_CONSECUTIVE_FAILS=1, CIRCUIT_BREAKER_COOLDOWN_MIN=1)
        )
        self.assertEqual(cb.seconds_until_reset, 0.0)
        cb.record_failure()
        secs = cb.seconds_until_reset
        self.assertGreater(secs, 0)
        self.assertLessEqual(secs, 60)


# ─── BalanceGuard ─────────────────────────────────────────────────────────────

class TestBalanceGuard(unittest.TestCase):

    def setUp(self):
        self.guard = BalanceGuard(_config(
            TRADE_SIZE_USD=5.0,
            MAX_TRADE_USD=10.0,
            MIN_RESERVE_USD=2.0,
        ))

    def test_check_reserve_above(self):
        self.assertTrue(self.guard.check_reserve(10.0))

    def test_check_reserve_below(self):
        self.assertFalse(self.guard.check_reserve(1.5))

    def test_check_reserve_exactly_at_limit(self):
        """Balance equal to reserve is NOT enough — must be strictly above."""
        self.assertFalse(self.guard.check_reserve(2.0))

    def test_safe_trade_size_normal(self):
        """With $100 balance, normal TRADE_SIZE_USD=5 should pass through."""
        size = self.guard.get_safe_trade_size(100.0, 5.0)
        self.assertAlmostEqual(size, 5.0, places=4)

    def test_safe_trade_size_ten_pct_cap(self):
        """Trade size must not exceed 10% of balance."""
        # balance=20, 10%=2, trade_size=5 → capped at 2
        size = self.guard.get_safe_trade_size(20.0, 5.0)
        self.assertAlmostEqual(size, 2.0, places=4)

    def test_safe_trade_size_reserve_cap(self):
        """Available = balance - reserve; cannot spend the reserve."""
        # balance=4, reserve=2, available=2, trade_size=5 → capped at 2
        size = self.guard.get_safe_trade_size(4.0, 5.0)
        self.assertAlmostEqual(size, 0.4, places=4)  # 10% of 4 = 0.4 < 2

    def test_safe_trade_size_max_trade_cap(self):
        """Trade size capped at MAX_TRADE_USD=10 even if balance is huge."""
        size = self.guard.get_safe_trade_size(1000.0, 50.0)
        self.assertAlmostEqual(size, 10.0, places=4)

    def test_safe_trade_size_zero_when_no_margin(self):
        """If balance == reserve there is nothing to trade."""
        size = self.guard.get_safe_trade_size(2.0, 5.0)
        self.assertAlmostEqual(size, 0.0, places=4)


# ─── PositionSizer ────────────────────────────────────────────────────────────

class TestPositionSizer(unittest.TestCase):

    def setUp(self):
        self.sizer = PositionSizer(_config(
            TRADE_SIZE_USD=10.0,
            MAX_TRADE_USD=20.0,
            MIN_RESERVE_USD=2.0,
            MIN_SIGNAL_SCORE=60,
        ))

    def _calc(self, score: int, balance: float = 1000.0, price: float = 10.0) -> int:
        return self.sizer.calculate(score, balance, price)

    def test_below_threshold_returns_zero(self):
        self.assertEqual(self._calc(score=59), 0)

    def test_at_threshold_uses_50pct(self):
        """score 60-69 → 50% of $10 = $5 / $10 = 0.5 ATOM = 500_000 micro"""
        units = self._calc(score=60)
        self.assertEqual(units, 500_000)

    def test_score_70_uses_75pct(self):
        """score 70-84 → 75% of $10 = $7.5 / $10 = 0.75 ATOM = 750_000 micro"""
        units = self._calc(score=70)
        self.assertEqual(units, 750_000)

    def test_score_85_uses_100pct(self):
        """score 85+ → 100% of $10 = 1 ATOM = 1_000_000 micro"""
        units = self._calc(score=85)
        self.assertEqual(units, 1_000_000)

    def test_score_100_uses_100pct(self):
        units = self._calc(score=100)
        self.assertEqual(units, 1_000_000)

    def test_zero_price_returns_zero(self):
        self.assertEqual(self._calc(score=80, price=0.0), 0)

    def test_returns_integer(self):
        units = self._calc(score=70)
        self.assertIsInstance(units, int)

    def test_position_respects_balance_guard(self):
        """
        With a tiny balance, the safe trade size should reduce the position.
        balance=$10, reserve=$2, 10%=$1 → safe_size=min(10,20,1,8)=1
        score=85 → 100% * $1 / $10 = 0.1 ATOM = 100_000 micro
        """
        units = self._calc(score=85, balance=10.0, price=10.0)
        # safe_size = min(10, 20, 1.0, 8.0) = 1.0
        # position = 1.0 / 10.0 * 1_000_000 = 100_000
        self.assertEqual(units, 100_000)


# ─── DailyLossTracker ─────────────────────────────────────────────────────────

class TestDailyLossTracker(unittest.TestCase):

    def test_not_triggered_initially(self):
        tracker = DailyLossTracker(_config(MAX_DAILY_LOSS_USD=15.0))
        self.assertFalse(tracker.loss_limit_reached)

    def test_not_triggered_below_limit(self):
        tracker = DailyLossTracker(_config(MAX_DAILY_LOSS_USD=15.0))
        tracker.record_trade_pnl(-10.0)
        self.assertFalse(tracker.loss_limit_reached)

    def test_triggered_at_exact_limit(self):
        tracker = DailyLossTracker(_config(MAX_DAILY_LOSS_USD=15.0))
        tracker.record_trade_pnl(-15.0)
        self.assertTrue(tracker.loss_limit_reached)

    def test_triggered_beyond_limit(self):
        tracker = DailyLossTracker(_config(MAX_DAILY_LOSS_USD=15.0))
        tracker.record_trade_pnl(-5.0)
        tracker.record_trade_pnl(-5.0)
        tracker.record_trade_pnl(-6.0)
        self.assertTrue(tracker.loss_limit_reached)

    def test_profits_offset_losses(self):
        tracker = DailyLossTracker(_config(MAX_DAILY_LOSS_USD=15.0))
        tracker.record_trade_pnl(-14.0)
        tracker.record_trade_pnl(5.0)   # profit brings total to -9
        self.assertFalse(tracker.loss_limit_reached)

    def test_initialised_with_existing_pnl(self):
        tracker = DailyLossTracker(
            _config(MAX_DAILY_LOSS_USD=15.0), initial_pnl=-14.5
        )
        # One more small loss should tip it over
        tracker.record_trade_pnl(-1.0)
        self.assertTrue(tracker.loss_limit_reached)

    def test_reset(self):
        tracker = DailyLossTracker(_config(MAX_DAILY_LOSS_USD=15.0))
        tracker.record_trade_pnl(-20.0)
        tracker.reset()
        self.assertFalse(tracker.loss_limit_reached)
        self.assertEqual(tracker.realised_pnl, 0.0)


# ─── RiskManager (integration) ────────────────────────────────────────────────

class TestRiskManager(unittest.TestCase):

    def setUp(self):
        self.cfg = _config(
            TRADE_SIZE_USD=5.0,
            MAX_TRADE_USD=10.0,
            MIN_RESERVE_USD=2.0,
            MAX_DAILY_LOSS_USD=15.0,
            MAX_CONSECUTIVE_FAILS=3,
            CIRCUIT_BREAKER_COOLDOWN_MIN=60,
            SPREAD_THRESHOLD=0.005,
            MIN_SIGNAL_SCORE=60,
        )
        self.rm = RiskManager(self.cfg)

    # ── pre_trade_check ────────────────────────────────────────────────────────

    def test_passes_all_checks(self):
        ok, reason = self.rm.pre_trade_check(_signal(score=70), balance_usd=100.0)
        self.assertTrue(ok)
        self.assertEqual(reason, "OK")

    def test_fails_when_circuit_breaker_tripped(self):
        for _ in range(3):
            self.rm.circuit_breaker.record_failure()
        ok, reason = self.rm.pre_trade_check(_signal(score=70), balance_usd=100.0)
        self.assertFalse(ok)
        self.assertIn("circuit breaker", reason.lower())

    def test_fails_when_daily_loss_limit_reached(self):
        self.rm.daily_loss.record_trade_pnl(-20.0)
        ok, reason = self.rm.pre_trade_check(_signal(score=70), balance_usd=100.0)
        self.assertFalse(ok)
        self.assertIn("daily loss", reason.lower())

    def test_fails_when_balance_below_reserve(self):
        ok, reason = self.rm.pre_trade_check(_signal(score=70), balance_usd=1.0)
        self.assertFalse(ok)
        self.assertIn("reserve", reason.lower())

    def test_fails_when_score_below_threshold(self):
        ok, reason = self.rm.pre_trade_check(_signal(score=50), balance_usd=100.0)
        self.assertFalse(ok)
        self.assertIn("score", reason.lower())

    def test_fails_when_spread_below_threshold(self):
        ok, reason = self.rm.pre_trade_check(
            _signal(score=70, spread_pct=0.001), balance_usd=100.0
        )
        self.assertFalse(ok)
        self.assertIn("spread", reason.lower())

    # ── record_outcome ────────────────────────────────────────────────────────

    def test_record_success_resets_fail_counter(self):
        self.rm.circuit_breaker.record_failure()
        self.rm.circuit_breaker.record_failure()
        self.rm.record_outcome(success=True, pnl_usd=0.5)
        self.assertEqual(self.rm.circuit_breaker.consecutive_fails, 0)

    def test_record_failure_increments_counter(self):
        self.rm.record_outcome(success=False, pnl_usd=0.0)
        self.rm.record_outcome(success=False, pnl_usd=0.0)
        self.assertEqual(self.rm.circuit_breaker.consecutive_fails, 2)

    def test_record_outcome_updates_pnl(self):
        self.rm.record_outcome(success=True, pnl_usd=-3.0)
        self.assertAlmostEqual(self.rm.daily_loss.realised_pnl, -3.0, places=4)

    # ── calculate_position ────────────────────────────────────────────────────

    def test_calculate_position_returns_int(self):
        result = self.rm.calculate_position(_signal(score=70), balance_usd=100.0)
        self.assertIsInstance(result, int)

    def test_calculate_position_zero_when_score_low(self):
        result = self.rm.calculate_position(_signal(score=40), balance_usd=100.0)
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
