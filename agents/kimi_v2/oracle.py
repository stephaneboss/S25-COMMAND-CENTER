"""
S25-KIMI-v2 Price Oracle
========================
Fetches spot prices from Osmosis DEX (via LCD REST) and MEXC CEX,
computes the spread, and returns a composite signal score.

All prices are denominated in USD (or USDC as proxy).
Cache TTL prevents hammering the endpoints on every scan.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)


# ─── Internal cache ───────────────────────────────────────────────────────────

class _PriceCache:
    """Simple in-memory TTL cache keyed by (source, symbol)."""

    def __init__(self, ttl_seconds: int = 5) -> None:
        self._ttl = ttl_seconds
        self._store: dict[tuple[str, str], tuple[float, float]] = {}
        # value tuple: (price, timestamp)

    def get(self, source: str, symbol: str) -> Optional[float]:
        key = (source, symbol)
        if key not in self._store:
            return None
        price, ts = self._store[key]
        if time.monotonic() - ts > self._ttl:
            del self._store[key]
            return None
        return price

    def set(self, source: str, symbol: str, price: float) -> None:
        self._store[(source, symbol)] = (price, time.monotonic())

    def clear(self) -> None:
        self._store.clear()


# ─── Oracle ───────────────────────────────────────────────────────────────────

class PriceOracle:
    """
    Dual-source price oracle: Osmosis DEX + MEXC CEX.

    Parameters
    ----------
    config:
        Runtime config object (provides URLs, pool IDs, thresholds).
    session:
        Optional requests.Session to inject (useful for testing / mocking).
    """

    # Osmosis GAMM pool-price endpoint template
    _OSMOSIS_POOL_PRICE = (
        "{lcd}/osmosis/gamm/v1beta1/pools/{pool_id}/prices"
        "?base_asset_denom={base}&quote_asset_denom={quote}"
    )
    # Osmosis pool-total-liquidity endpoint (for liquidity check)
    _OSMOSIS_POOL_ASSETS = (
        "{lcd}/osmosis/gamm/v1beta1/pools/{pool_id}"
    )
    # MEXC ticker
    _MEXC_TICKER = "{api}/ticker/price?symbol={symbol}USDT"

    def __init__(
        self,
        config: Config,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._cfg = config
        self._session = session or requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        self._cache = _PriceCache(ttl_seconds=config.PRICE_CACHE_SECONDS)

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_osmosis_price(self, symbol: str) -> Optional[float]:
        """
        Return the Osmosis spot price of *symbol* in USD (USDC proxy).

        For ATOM we query pool 1 (ATOM/OSMO) → price in OSMO, then
        convert OSMO → USD via pool 678 (OSMO/USDC).

        Returns None on any error.
        """
        cached = self._cache.get("osm", symbol)
        if cached is not None:
            return cached

        try:
            price = self._fetch_osmosis_price_usd(symbol)
        except Exception as exc:
            logger.warning("Osmosis price fetch failed for %s: %s", symbol, exc)
            return None

        if price is not None:
            self._cache.set("osm", symbol, price)
        return price

    def get_cex_price(self, symbol: str) -> Optional[float]:
        """
        Return the MEXC spot price of *symbol* in USDT.

        Returns None on any error.
        """
        cached = self._cache.get("mexc", symbol)
        if cached is not None:
            return cached

        try:
            price = self._fetch_mexc_price(symbol)
        except Exception as exc:
            logger.warning("MEXC price fetch failed for %s: %s", symbol, exc)
            return None

        if price is not None:
            self._cache.set("mexc", symbol, price)
        return price

    def get_spread(self, symbol: str) -> Optional[dict]:
        """
        Compute the price spread between Osmosis and MEXC.

        Returns a dict::

            {
                "symbol":      str,
                "osm_price":   float,   # USD
                "cex_price":   float,   # USD
                "spread_pct":  float,   # (osm - cex) / cex
                "direction":   "BUY" | "SELL",
                "score":       int,     # 0-100
            }

        - direction = "BUY"  → OSM cheaper, buy on OSM, sell on CEX
        - direction = "SELL" → OSM more expensive, buy on CEX, sell on OSM

        Returns None if either price source fails.
        """
        osm_price = self.get_osmosis_price(symbol)
        cex_price = self.get_cex_price(symbol)

        if osm_price is None or cex_price is None:
            logger.warning(
                "Cannot compute spread for %s: osm=%s cex=%s",
                symbol, osm_price, cex_price,
            )
            return None

        if cex_price == 0:
            logger.warning("CEX price is zero for %s, skipping", symbol)
            return None

        spread_pct = (osm_price - cex_price) / cex_price
        direction = "BUY" if spread_pct < 0 else "SELL"

        score = self._compute_score(symbol, spread_pct)

        result = {
            "symbol": symbol,
            "osm_price": round(osm_price, 6),
            "cex_price": round(cex_price, 6),
            "spread_pct": round(spread_pct, 6),
            "direction": direction,
            "score": score,
        }
        logger.debug("Spread result: %s", result)
        return result

    # ── Private helpers ────────────────────────────────────────────────────────

    def _fetch_osmosis_price_usd(self, symbol: str) -> Optional[float]:
        """
        Resolve symbol → USD price via Osmosis GAMM pools.

        Strategy
        --------
        1. Get symbol/OSMO price from the primary pool.
        2. Get OSMO/USDC price from pool 678.
        3. Multiply to get symbol/USD.
        """
        pool_ids = self._cfg.pool_id_for
        if symbol not in pool_ids:
            raise ValueError(f"No pool configured for symbol '{symbol}'")

        pool_id = pool_ids[symbol]

        # Denom map
        denom_map: dict[str, str] = {
            "ATOM": self._cfg.DENOM_ATOM,
            "AKT": "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E3674D0489393",
            "OSMO": self._cfg.DENOM_OSMO,
        }
        base_denom = denom_map.get(symbol)
        if base_denom is None:
            raise ValueError(f"No IBC denom configured for symbol '{symbol}'")

        # Step 1: symbol → OSMO
        if symbol == "OSMO":
            # OSMO is the base; use pool 678 directly vs USDC
            osmo_price_in_usd = self._query_pool_price(
                pool_id=self._cfg.POOL_OSMO_USDC,
                base_denom=self._cfg.DENOM_OSMO,
                quote_denom=self._cfg.DENOM_USDC,
            )
            return osmo_price_in_usd

        symbol_in_osmo = self._query_pool_price(
            pool_id=pool_id,
            base_denom=base_denom,
            quote_denom=self._cfg.DENOM_OSMO,
        )
        if symbol_in_osmo is None:
            return None

        # Step 2: OSMO → USD
        osmo_in_usd = self._query_pool_price(
            pool_id=self._cfg.POOL_OSMO_USDC,
            base_denom=self._cfg.DENOM_OSMO,
            quote_denom=self._cfg.DENOM_USDC,
        )
        if osmo_in_usd is None:
            return None

        return symbol_in_osmo * osmo_in_usd

    def _query_pool_price(
        self,
        pool_id: int,
        base_denom: str,
        quote_denom: str,
    ) -> Optional[float]:
        """
        Hit the Osmosis GAMM price endpoint for a given pool.

        The API returns something like::

            { "spot_price": "8.473200000000000000" }
        """
        url = self._OSMOSIS_POOL_PRICE.format(
            lcd=self._cfg.OSMOSIS_LCD,
            pool_id=pool_id,
            base=base_denom,
            quote=quote_denom,
        )
        resp = self._session.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        raw = data.get("spot_price")
        if raw is None:
            logger.warning("No spot_price in response: %s", data)
            return None

        return float(raw)

    def _fetch_mexc_price(self, symbol: str) -> Optional[float]:
        """
        Fetch the latest MEXC ticker price for {symbol}USDT.
        """
        url = self._MEXC_TICKER.format(api=self._cfg.MEXC_API, symbol=symbol)
        resp = self._session.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        raw = data.get("price")
        if raw is None:
            logger.warning("No 'price' in MEXC response: %s", data)
            return None

        return float(raw)

    def _get_pool_liquidity_usd(self, symbol: str) -> Optional[float]:
        """
        Estimate pool total value in USD by summing pool assets.

        Returns None if the request fails. Returns 0 if assets cannot be
        parsed (triggers the score penalty).
        """
        pool_id = self._cfg.pool_id_for.get(symbol)
        if pool_id is None:
            return None

        url = self._OSMOSIS_POOL_ASSETS.format(
            lcd=self._cfg.OSMOSIS_LCD,
            pool_id=pool_id,
        )
        try:
            resp = self._session.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("Pool liquidity check failed: %s", exc)
            return None

        # Pool object can be wrapped in {"pool": {...}}
        pool = data.get("pool", data)
        pool_assets = pool.get("pool_assets", [])

        osmo_price = self._cache.get("osm", "OSMO")
        if osmo_price is None:
            # Approximate OSMO at $1 if we don't have a fresh price
            osmo_price = 1.0

        total_usd = 0.0
        for asset in pool_assets:
            token = asset.get("token", {})
            amount_raw = token.get("amount", "0")
            denom = token.get("denom", "")
            amount = float(amount_raw) / 1_000_000  # micro-units → base

            if denom == self._cfg.DENOM_OSMO:
                total_usd += amount * osmo_price
            elif denom == self._cfg.DENOM_USDC:
                total_usd += amount  # USDC ≈ USD
            else:
                # Rough estimate: use CEX price if available
                sym_price = self._cache.get("mexc", symbol)
                if sym_price:
                    total_usd += amount * sym_price

        return total_usd

    def _compute_score(self, symbol: str, spread_pct: float) -> int:
        """
        Compute a 0-100 composite signal score.

        Formula
        -------
        base_score = min(100, int(abs(spread_pct) / SPREAD_THRESHOLD * 50))
        liquidity_bonus = +10 if pool TVL >= MIN_POOL_LIQUIDITY_USD
        liquidity_penalty = -30 if pool TVL < MIN_POOL_LIQUIDITY_USD

        Final score is clamped to [0, 100].
        """
        threshold = self._cfg.SPREAD_THRESHOLD
        base_score = min(100, int(abs(spread_pct) / threshold * 50))

        # Liquidity adjustment
        liquidity_usd = self._get_pool_liquidity_usd(symbol)
        if liquidity_usd is None:
            # Cannot verify → neutral (no bonus, no penalty)
            liquidity_adj = 0
        elif liquidity_usd >= self._cfg.MIN_POOL_LIQUIDITY_USD:
            liquidity_adj = 10
        else:
            liquidity_adj = -30

        raw_score = base_score + liquidity_adj
        return max(0, min(100, raw_score))

    # ── Utility ────────────────────────────────────────────────────────────────

    def invalidate_cache(self) -> None:
        """Force-clear the price cache (useful in tests and after errors)."""
        self._cache.clear()
