"""
Unit tests for oracle.py
========================
All external HTTP calls are mocked — no real network traffic.
"""

from __future__ import annotations

import time
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

import sys
import os

# Add parent directory to path so imports work when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from oracle import PriceOracle, _PriceCache


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_config(**overrides) -> Config:
    """Return a minimal Config for testing."""
    defaults = dict(
        MODE="dry",
        SPREAD_THRESHOLD=0.005,
        MIN_SIGNAL_SCORE=60,
        PRICE_CACHE_SECONDS=5,
        MIN_POOL_LIQUIDITY_USD=10_000.0,
    )
    defaults.update(overrides)
    return Config(**defaults)


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = status_code == 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from requests.exceptions import HTTPError
        resp.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
    return resp


# ─── Cache tests ──────────────────────────────────────────────────────────────

class TestPriceCache(unittest.TestCase):

    def test_miss_on_empty(self):
        cache = _PriceCache(ttl_seconds=5)
        self.assertIsNone(cache.get("osm", "ATOM"))

    def test_hit_within_ttl(self):
        cache = _PriceCache(ttl_seconds=5)
        cache.set("osm", "ATOM", 8.5)
        self.assertEqual(cache.get("osm", "ATOM"), 8.5)

    def test_miss_after_ttl(self):
        cache = _PriceCache(ttl_seconds=0)  # expires immediately
        cache.set("osm", "ATOM", 8.5)
        time.sleep(0.01)
        # Any access after TTL should return None
        self.assertIsNone(cache.get("osm", "ATOM"))

    def test_different_sources_independent(self):
        cache = _PriceCache(ttl_seconds=5)
        cache.set("osm", "ATOM", 8.0)
        cache.set("mexc", "ATOM", 8.5)
        self.assertEqual(cache.get("osm", "ATOM"), 8.0)
        self.assertEqual(cache.get("mexc", "ATOM"), 8.5)

    def test_clear(self):
        cache = _PriceCache(ttl_seconds=60)
        cache.set("osm", "ATOM", 8.0)
        cache.clear()
        self.assertIsNone(cache.get("osm", "ATOM"))


# ─── Osmosis price parsing tests ──────────────────────────────────────────────

class TestOsmosisPriceParsing(unittest.TestCase):

    def setUp(self):
        self.config = _make_config()
        self.session = MagicMock()
        self.oracle = PriceOracle(self.config, session=self.session)

    def _set_session_responses(self, *responses):
        """Each call to session.get returns the next response in sequence."""
        self.session.get.side_effect = list(responses)

    def test_atom_price_two_hop(self):
        """
        ATOM price = ATOM/OSMO price * OSMO/USD price.
        Pool 1: ATOM/OSMO = 8.0 OSMO per ATOM
        Pool 678: OSMO/USDC = 1.25 USD per OSMO
        Expected: 8.0 * 1.25 = 10.0
        """
        pool1_resp = _mock_response({"spot_price": "8.0"})
        pool678_resp = _mock_response({"spot_price": "1.25"})
        self._set_session_responses(pool1_resp, pool678_resp)

        price = self.oracle.get_osmosis_price("ATOM")

        self.assertIsNotNone(price)
        self.assertAlmostEqual(price, 10.0, places=4)

    def test_osmosis_price_returned_as_float(self):
        """Ensure string prices from LCD are converted to float."""
        pool1_resp = _mock_response({"spot_price": "7.500000000000000000"})
        pool678_resp = _mock_response({"spot_price": "1.000000000000000000"})
        self.session.get.side_effect = [pool1_resp, pool678_resp]

        price = self.oracle.get_osmosis_price("ATOM")
        self.assertIsInstance(price, float)
        self.assertAlmostEqual(price, 7.5, places=4)

    def test_returns_none_on_http_error(self):
        """Should return None when the LCD returns an error."""
        from requests.exceptions import HTTPError
        self.session.get.side_effect = HTTPError("503 Service Unavailable")

        price = self.oracle.get_osmosis_price("ATOM")
        self.assertIsNone(price)

    def test_returns_none_on_missing_spot_price_key(self):
        """Should return None if 'spot_price' key is absent from response."""
        resp = _mock_response({"error": "pool not found"})
        self.session.get.side_effect = [resp]

        price = self.oracle.get_osmosis_price("ATOM")
        self.assertIsNone(price)

    def test_invalid_symbol_returns_none(self):
        """
        Unknown symbol: the ValueError raised internally is caught by
        get_osmosis_price and returns None (safe degradation).
        The raw _fetch helper does raise, so we test both behaviours.
        """
        # Public API: degrades gracefully → None
        price = self.oracle.get_osmosis_price("UNKNOWN_TOKEN")
        self.assertIsNone(price)

        # Internal helper: raises ValueError directly
        with self.assertRaises(ValueError):
            self.oracle._fetch_osmosis_price_usd("UNKNOWN_TOKEN")


# ─── MEXC price parsing tests ─────────────────────────────────────────────────

class TestMexcPriceParsing(unittest.TestCase):

    def setUp(self):
        self.config = _make_config()
        self.session = MagicMock()
        self.oracle = PriceOracle(self.config, session=self.session)

    def test_normal_mexc_response(self):
        """Standard MEXC ticker response."""
        self.session.get.return_value = _mock_response(
            {"symbol": "ATOMUSDT", "price": "9.4200"}
        )
        price = self.oracle.get_cex_price("ATOM")
        self.assertAlmostEqual(price, 9.42, places=4)

    def test_mexc_returns_none_on_network_error(self):
        import requests
        self.session.get.side_effect = requests.exceptions.ConnectionError("offline")
        price = self.oracle.get_cex_price("ATOM")
        self.assertIsNone(price)

    def test_mexc_returns_none_on_missing_price_key(self):
        self.session.get.return_value = _mock_response({"symbol": "ATOMUSDT"})
        price = self.oracle.get_cex_price("ATOM")
        self.assertIsNone(price)


# ─── Spread calculation tests ─────────────────────────────────────────────────

class TestSpreadCalculation(unittest.TestCase):

    def setUp(self):
        self.config = _make_config(SPREAD_THRESHOLD=0.005)
        self.session = MagicMock()
        self.oracle = PriceOracle(self.config, session=self.session)

    def _patch_prices(self, osm: float, cex: float):
        """Inject known prices directly into the cache."""
        self.oracle._cache.set("osm", "ATOM", osm)
        self.oracle._cache.set("mexc", "ATOM", cex)

    def _patch_liquidity(self, value: float):
        """Patch pool liquidity check to return a fixed value."""
        self.oracle._get_pool_liquidity_usd = MagicMock(return_value=value)

    def test_buy_signal_when_osm_cheaper(self):
        """
        When OSM price < CEX price, we should BUY on OSM.
        """
        self._patch_prices(osm=9.0, cex=10.0)  # 10% spread
        self._patch_liquidity(50_000.0)

        result = self.oracle.get_spread("ATOM")

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "BUY")
        self.assertLess(result["spread_pct"], 0)

    def test_sell_signal_when_osm_more_expensive(self):
        """
        When OSM price > CEX price, we should SELL on OSM.
        """
        self._patch_prices(osm=11.0, cex=10.0)  # +10% spread
        self._patch_liquidity(50_000.0)

        result = self.oracle.get_spread("ATOM")

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "SELL")
        self.assertGreater(result["spread_pct"], 0)

    def test_spread_pct_formula(self):
        """Verify (osm - cex) / cex calculation."""
        self._patch_prices(osm=10.5, cex=10.0)
        self._patch_liquidity(50_000.0)

        result = self.oracle.get_spread("ATOM")

        expected_spread = (10.5 - 10.0) / 10.0  # 0.05
        self.assertAlmostEqual(result["spread_pct"], expected_spread, places=4)

    def test_returns_none_when_cex_price_is_zero(self):
        self._patch_prices(osm=10.0, cex=0.0)
        result = self.oracle.get_spread("ATOM")
        self.assertIsNone(result)

    def test_returns_none_when_osm_price_unavailable(self):
        # Only cache CEX price; leave OSM uncached
        self.oracle._cache.set("mexc", "ATOM", 10.0)
        # OSM call will hit the session which raises
        self.session.get.side_effect = Exception("network error")

        result = self.oracle.get_spread("ATOM")
        self.assertIsNone(result)


# ─── Score formula tests ──────────────────────────────────────────────────────

class TestScoreFormula(unittest.TestCase):

    def setUp(self):
        self.config = _make_config(
            SPREAD_THRESHOLD=0.005,
            MIN_POOL_LIQUIDITY_USD=10_000.0,
        )
        self.session = MagicMock()
        self.oracle = PriceOracle(self.config, session=self.session)

    def _score(self, spread_pct: float, liquidity: float) -> int:
        self.oracle._get_pool_liquidity_usd = MagicMock(return_value=liquidity)
        return self.oracle._compute_score("ATOM", spread_pct)

    def test_score_at_exact_threshold(self):
        """Spread = threshold → base_score = 50 (threshold × 50 / threshold)."""
        score = self._score(0.005, 50_000.0)
        # base = int(0.005/0.005*50) = 50, liquidity bonus +10 = 60
        self.assertEqual(score, 60)

    def test_score_doubles_with_double_spread(self):
        """
        Spread = 2× threshold → base = 100, cap at 100, + bonus = 100.
        """
        score = self._score(0.010, 50_000.0)
        self.assertEqual(score, 100)

    def test_score_capped_at_100(self):
        """Score must never exceed 100."""
        score = self._score(1.0, 50_000.0)  # huge spread
        self.assertLessEqual(score, 100)

    def test_score_floored_at_0(self):
        """Score must never go below 0."""
        score = self._score(0.000001, 0.0)  # tiny spread + penalty
        self.assertGreaterEqual(score, 0)

    def test_low_liquidity_penalty(self):
        """
        Pool below $10k should subtract 30 from the score.
        Use a smaller spread so the base score doesn't hit the 100 cap,
        making the +10 / -30 bonuses clearly visible.

        spread=0.005 (= 1× threshold) → base = int(0.005/0.005*50) = 50
        high_liq: 50 + 10 = 60
        low_liq:  50 - 30 = 20
        diff = 40
        """
        score_high_liq = self._score(0.005, 50_000.0)
        score_low_liq = self._score(0.005, 1_000.0)
        self.assertEqual(score_high_liq - score_low_liq, 40)  # +10 vs -30

    def test_none_liquidity_no_adjustment(self):
        """When liquidity is None, score should not change."""
        self.oracle._get_pool_liquidity_usd = MagicMock(return_value=None)
        score = self.oracle._compute_score("ATOM", 0.010)
        # base = 100, no adjustment
        self.assertEqual(score, 100)


# ─── Cache behaviour tests ────────────────────────────────────────────────────

class TestCacheBehaviour(unittest.TestCase):

    def setUp(self):
        self.config = _make_config(PRICE_CACHE_SECONDS=60)
        self.session = MagicMock()
        self.oracle = PriceOracle(self.config, session=self.session)

    def test_second_call_uses_cache(self):
        """
        The session should only be called once for two consecutive
        get_cex_price calls within the TTL window.
        """
        self.session.get.return_value = _mock_response({"price": "9.0"})

        first = self.oracle.get_cex_price("ATOM")
        second = self.oracle.get_cex_price("ATOM")

        self.assertEqual(first, second)
        # Session called exactly once (second call served from cache)
        self.assertEqual(self.session.get.call_count, 1)

    def test_invalidate_cache_forces_refetch(self):
        """After invalidate_cache(), the next call must hit the network."""
        self.session.get.return_value = _mock_response({"price": "9.0"})
        self.oracle.get_cex_price("ATOM")
        self.oracle.invalidate_cache()

        self.session.get.return_value = _mock_response({"price": "9.5"})
        price = self.oracle.get_cex_price("ATOM")

        self.assertAlmostEqual(price, 9.5, places=4)
        self.assertEqual(self.session.get.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
