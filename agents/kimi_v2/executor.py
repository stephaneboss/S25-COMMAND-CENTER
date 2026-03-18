"""
S25-KIMI-v2 Swap Executor
=========================
Handles three execution modes:

DRY   – Logs what would happen. No state changes. Returns synthetic success.
PAPER – Simulates a swap, estimates theoretical P&L, records to ledger.
LIVE  – Builds and broadcasts a real Osmosis MsgSwapExactAmountIn transaction
        using cosmpy. Requires WALLET_MNEMONIC and WALLET_ADDRESS.

All public methods return a uniform result dict::

    {
        "success":    bool,
        "tx_hash":    str | None,
        "actual_out": float | None,   # micro-units received
        "gas_used":   int | None,
        "pnl_usd":    float | None,
        "error":      str | None,
    }
"""

from __future__ import annotations

import logging
from typing import Optional

from config import Config
from ledger import TradeLedger

logger = logging.getLogger(__name__)

# ─── Pool routing ─────────────────────────────────────────────────────────────
#
# For a BUY signal (DEX cheaper): buy on Osmosis, sell on CEX.
#   → Osmosis: swap USDC → ATOM  (route: USDC pool678→OSMO pool1→ATOM)
#
# For a SELL signal (DEX more expensive): sell on Osmosis, buy on CEX.
#   → Osmosis: swap ATOM → USDC  (route: ATOM pool1→OSMO pool678→USDC)
#
# Simple 2-hop routes through OSMO as the hub token.

_POOL_ROUTES: dict[tuple[str, str], list[dict]] = {
    # (symbol, direction) → list of {pool_id, token_out_denom}
    ("ATOM", "BUY"): [
        {"pool_id": 678, "token_out_denom": "uosmo"},       # USDC→OSMO
        {"pool_id": 1,   "token_out_denom": "__ATOM__"},    # OSMO→ATOM (filled at runtime)
    ],
    ("ATOM", "SELL"): [
        {"pool_id": 1,   "token_out_denom": "uosmo"},       # ATOM→OSMO
        {"pool_id": 678, "token_out_denom": "__USDC__"},    # OSMO→USDC (filled at runtime)
    ],
}


def _build_route(symbol: str, direction: str, config: Config) -> list[dict]:
    """Return the pool route with concrete denom values filled in."""
    key = (symbol, direction)
    if key not in _POOL_ROUTES:
        raise ValueError(f"No route defined for ({symbol}, {direction})")

    route = []
    for hop in _POOL_ROUTES[key]:
        out_denom = hop["token_out_denom"]
        if out_denom == "__ATOM__":
            out_denom = config.DENOM_ATOM
        elif out_denom == "__USDC__":
            out_denom = config.DENOM_USDC
        route.append({"pool_id": hop["pool_id"], "token_out_denom": out_denom})
    return route


def _in_denom(symbol: str, direction: str, config: Config) -> str:
    """Return the denom we send into the swap."""
    if direction == "BUY":
        return config.DENOM_USDC    # We spend USDC to buy the asset
    else:
        denom_map = {
            "ATOM": config.DENOM_ATOM,
            "OSMO": config.DENOM_OSMO,
        }
        return denom_map.get(symbol, config.DENOM_ATOM)


def _out_denom(symbol: str, direction: str, config: Config) -> str:
    """Return the denom we expect to receive from the swap."""
    if direction == "BUY":
        denom_map = {
            "ATOM": config.DENOM_ATOM,
            "OSMO": config.DENOM_OSMO,
        }
        return denom_map.get(symbol, config.DENOM_ATOM)
    else:
        return config.DENOM_USDC


# ─── Executor ─────────────────────────────────────────────────────────────────

class SwapExecutor:
    """
    Executes or simulates Osmosis swaps according to the configured mode.

    Parameters
    ----------
    config:
        Runtime config.
    ledger:
        TradeLedger instance for recording outcomes.
    """

    def __init__(self, config: Config, ledger: TradeLedger) -> None:
        self._cfg = config
        self._ledger = ledger

    # ── Main entrypoint ────────────────────────────────────────────────────────

    def execute(self, signal: dict, amount_units: int) -> dict:
        """
        Attempt a swap based on the provided signal.

        Parameters
        ----------
        signal:
            Dict from ``oracle.get_spread()`` with keys:
            symbol, direction, spread_pct, score, osm_price, cex_price.
        amount_units:
            Position size in micro-units (from PositionSizer).

        Returns
        -------
        dict
            Uniform result: success, tx_hash, actual_out, gas_used, pnl_usd, error.
        """
        symbol = signal["symbol"]
        direction = signal["direction"]

        logger.info(
            "Executor [%s]: %s %s amount=%d score=%d",
            self._cfg.MODE.upper(), direction, symbol, amount_units, signal["score"],
        )

        if self._cfg.is_dry:
            return self._execute_dry(signal, amount_units)
        elif self._cfg.is_paper:
            return self._execute_paper(signal, amount_units)
        else:
            return self._execute_live(signal, amount_units)

    # ── DRY mode ───────────────────────────────────────────────────────────────

    def _execute_dry(self, signal: dict, amount_units: int) -> dict:
        """Log the intended trade and return a synthetic success."""
        symbol = signal["symbol"]
        direction = signal["direction"]
        osm_price = signal.get("osm_price", 0.0)
        cex_price = signal.get("cex_price", 0.0)

        in_d = _in_denom(symbol, direction, self._cfg)
        out_d = _out_denom(symbol, direction, self._cfg)

        note = (
            f"[DRY] Would swap {amount_units} {in_d} → {out_d} "
            f"via Osmosis. osm_price={osm_price:.4f} cex_price={cex_price:.4f} "
            f"spread={signal['spread_pct']:.4%} score={signal['score']}"
        )
        logger.info(note)

        self._ledger.record_trade(
            mode="dry",
            symbol=symbol,
            direction=direction,
            signal_score=signal["score"],
            spread_pct=signal["spread_pct"],
            in_denom=in_d,
            out_denom=out_d,
            in_amount=float(amount_units),
            out_amount=None,
            tx_hash=None,
            status="dry",
            gas_fee=None,
            pnl_usd=None,
            notes=note,
        )

        return {
            "success": True,
            "tx_hash": None,
            "actual_out": None,
            "gas_used": None,
            "pnl_usd": None,
            "error": None,
        }

    # ── PAPER mode ─────────────────────────────────────────────────────────────

    def _execute_paper(self, signal: dict, amount_units: int) -> dict:
        """
        Simulate the swap and compute theoretical P&L.

        P&L model
        ---------
        BUY on DEX, SELL on CEX (spread_pct < 0 → osm cheaper):
            We spend cex_price * amount_base USD on Osmosis.
            We receive osm_price * amount_base USD equivalent.
            Effective gain = (cex_price - osm_price) * amount_base
            Minus estimated fees (0.2 % of notional + $0.05 flat gas).

        SELL on DEX, BUY on CEX (spread_pct > 0 → osm more expensive):
            Equivalent mirror calculation.
        """
        symbol = signal["symbol"]
        direction = signal["direction"]
        osm_price = signal.get("osm_price", 0.0)
        cex_price = signal.get("cex_price", 0.0)

        in_d = _in_denom(symbol, direction, self._cfg)
        out_d = _out_denom(symbol, direction, self._cfg)

        amount_base = amount_units / 1_000_000  # micro → whole tokens

        # Theoretical P&L (ignoring order-book impact)
        spread_abs = abs(signal["spread_pct"])
        notional_usd = amount_base * ((osm_price + cex_price) / 2)
        gross_pnl = notional_usd * spread_abs
        fees = notional_usd * 0.002 + 0.05   # 0.2 % pool fee + flat gas
        net_pnl = round(gross_pnl - fees, 6)

        # Simulate output amount (what we'd receive)
        if direction == "BUY":
            # We sent USDC, receive ATOM at osm_price
            theoretical_out = (amount_units / osm_price) if osm_price > 0 else 0.0
        else:
            # We sent ATOM, receive USDC
            theoretical_out = float(amount_units) * osm_price / 1_000_000

        note = (
            f"[PAPER] Simulated {direction} {amount_base:.6f} {symbol}. "
            f"gross_pnl=${gross_pnl:.4f} fees=${fees:.4f} net_pnl=${net_pnl:.4f}"
        )
        logger.info(note)

        self._ledger.record_trade(
            mode="paper",
            symbol=symbol,
            direction=direction,
            signal_score=signal["score"],
            spread_pct=signal["spread_pct"],
            in_denom=in_d,
            out_denom=out_d,
            in_amount=float(amount_units),
            out_amount=theoretical_out,
            tx_hash=None,
            status="paper",
            gas_fee=50_000.0,  # simulated 0.05 OSMO gas
            pnl_usd=net_pnl,
            notes=note,
        )

        return {
            "success": True,
            "tx_hash": None,
            "actual_out": theoretical_out,
            "gas_used": 50_000,
            "pnl_usd": net_pnl,
            "error": None,
        }

    # ── LIVE mode ──────────────────────────────────────────────────────────────

    def _execute_live(self, signal: dict, amount_units: int) -> dict:
        """
        Build and broadcast a real MsgSwapExactAmountIn on Osmosis.

        Uses cosmpy for wallet management and transaction signing.
        """
        symbol = signal["symbol"]
        direction = signal["direction"]
        osm_price = signal.get("osm_price", 0.0)

        in_d = _in_denom(symbol, direction, self._cfg)
        out_d = _out_denom(symbol, direction, self._cfg)

        try:
            # Deferred import: cosmpy is only required in live mode
            from cosmpy.aerial.client import LedgerClient, NetworkConfig  # type: ignore
            from cosmpy.aerial.wallet import LocalWallet               # type: ignore
            from cosmpy.crypto.keypairs import Secp256k1               # type: ignore
        except ImportError as exc:
            error_msg = f"cosmpy not installed — cannot run LIVE mode: {exc}"
            logger.error(error_msg)
            self._record_failure(signal, amount_units, in_d, out_d, error_msg)
            return _failure_result(error_msg)

        try:
            # ── Wallet ──────────────────────────────────────────────────────
            wallet = LocalWallet.from_mnemonic(self._cfg.WALLET_MNEMONIC)

            # ── Network client ──────────────────────────────────────────────
            net_cfg = NetworkConfig(
                chain_id="osmosis-1",
                url=f"rest+{self._cfg.OSMOSIS_LCD}",
                fee_minimum_gas_price=0.0025,
                fee_denomination="uosmo",
                staking_denomination="uosmo",
            )
            client = LedgerClient(net_cfg)

            # ── Slippage check ──────────────────────────────────────────────
            # Estimate minimum acceptable output before broadcasting.
            # If actual swap output would be worse than (1 - MAX_SLIPPAGE),
            # we abort before spending any gas.
            amount_base = amount_units / 1_000_000
            if direction == "BUY" and osm_price > 0:
                expected_out = amount_base / osm_price * 1_000_000
            else:
                expected_out = amount_base * osm_price * 1_000_000

            min_out = int(expected_out * (1 - self._cfg.MAX_SLIPPAGE))

            if min_out <= 0:
                error_msg = (
                    f"Slippage check: computed min_out={min_out} ≤ 0 — aborting"
                )
                logger.error(error_msg)
                self._record_failure(signal, amount_units, in_d, out_d, error_msg)
                return _failure_result(error_msg)

            logger.info(
                "Live swap: %s %d %s → min_out=%d %s (slippage≤%.1f%%)",
                direction, amount_units, in_d, min_out, out_d,
                self._cfg.MAX_SLIPPAGE * 100,
            )

            # ── Build swap message ──────────────────────────────────────────
            route = _build_route(symbol, direction, self._cfg)

            # cosmpy MsgSwapExactAmountIn
            from cosmpy.protos.osmosis.gamm.v1beta1.tx_pb2 import (  # type: ignore
                MsgSwapExactAmountIn, SwapAmountInRoute,
            )
            from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin  # type: ignore

            routes_proto = [
                SwapAmountInRoute(
                    pool_id=hop["pool_id"],
                    token_out_denom=hop["token_out_denom"],
                )
                for hop in route
            ]

            msg = MsgSwapExactAmountIn(
                sender=self._cfg.WALLET_ADDRESS,
                routes=routes_proto,
                token_in=Coin(denom=in_d, amount=str(amount_units)),
                token_out_min_amount=str(min_out),
            )

            # ── Broadcast ───────────────────────────────────────────────────
            tx = client.send_tokens(  # type: ignore[call-arg]
                destination=self._cfg.WALLET_ADDRESS,
                amount=0,
                denom="uosmo",
                sender=wallet,
                memo="S25-KIMI-v2",
            )

            # For the actual swap we use the lower-level broadcast:
            tx_response = client.broadcast_tx(  # type: ignore[call-arg]
                wallet=wallet,
                msgs=[msg],
                gas_limit=250_000,
                fee="6250uosmo",
                memo="S25-KIMI-v2",
            )

            tx_hash = getattr(tx_response, "txhash", None) or str(tx_response)
            gas_used = getattr(tx_response, "gas_used", None)

            # ── Estimate P&L from on-chain result ───────────────────────────
            actual_out = _parse_actual_out(tx_response, out_d)
            pnl_usd = _estimate_pnl(
                direction, amount_units, actual_out, osm_price,
                signal.get("cex_price", 0.0),
            )

            self._ledger.record_trade(
                mode="live",
                symbol=symbol,
                direction=direction,
                signal_score=signal["score"],
                spread_pct=signal["spread_pct"],
                in_denom=in_d,
                out_denom=out_d,
                in_amount=float(amount_units),
                out_amount=float(actual_out) if actual_out else None,
                tx_hash=tx_hash,
                status="success",
                gas_fee=float(gas_used) if gas_used else None,
                pnl_usd=pnl_usd,
                notes=f"Live swap broadcast. tx={tx_hash}",
            )

            return {
                "success": True,
                "tx_hash": tx_hash,
                "actual_out": actual_out,
                "gas_used": gas_used,
                "pnl_usd": pnl_usd,
                "error": None,
            }

        except Exception as exc:
            error_msg = f"Live swap failed: {exc}"
            logger.exception("Executor: live swap error")
            self._record_failure(signal, amount_units, in_d, out_d, error_msg)
            return _failure_result(error_msg)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _record_failure(
        self,
        signal: dict,
        amount_units: int,
        in_denom: str,
        out_denom: str,
        error_msg: str,
    ) -> None:
        """Record a failed execution to the ledger."""
        self._ledger.record_trade(
            mode=self._cfg.MODE,
            symbol=signal["symbol"],
            direction=signal["direction"],
            signal_score=signal.get("score", 0),
            spread_pct=signal.get("spread_pct", 0.0),
            in_denom=in_denom,
            out_denom=out_denom,
            in_amount=float(amount_units),
            out_amount=None,
            tx_hash=None,
            status="failed",
            gas_fee=None,
            pnl_usd=None,
            notes=error_msg,
        )


# ─── Module-level helpers ─────────────────────────────────────────────────────

def _failure_result(error_msg: str) -> dict:
    return {
        "success": False,
        "tx_hash": None,
        "actual_out": None,
        "gas_used": None,
        "pnl_usd": None,
        "error": error_msg,
    }


def _parse_actual_out(tx_response: object, out_denom: str) -> Optional[float]:
    """
    Try to parse the actual received amount from a cosmpy tx response.

    The structure varies between cosmpy versions; we do a best-effort parse.
    Returns None if parsing fails.
    """
    try:
        # cosmpy sometimes has logs with events
        logs = getattr(tx_response, "logs", None)
        if not logs:
            return None
        for log in logs:
            events = getattr(log, "events", [])
            for event in events:
                if getattr(event, "type", "") == "token_swapped":
                    for attr in getattr(event, "attributes", []):
                        if getattr(attr, "key", "") == "tokens_out":
                            value = getattr(attr, "value", "")
                            # Value looks like "1234uosmo"
                            amount_str = "".join(c for c in value if c.isdigit())
                            if amount_str and out_denom in value:
                                return float(amount_str)
    except Exception:
        pass
    return None


def _estimate_pnl(
    direction: str,
    in_amount: int,
    out_amount: Optional[float],
    osm_price: float,
    cex_price: float,
) -> Optional[float]:
    """
    Estimate realised P&L in USD from a completed live swap.

    BUY case: we spent USDC (in_amount micro-USDC), received ATOM.
              P&L = out_amount/1e6 * cex_price - in_amount/1e6
    SELL case: we spent ATOM (in_amount micro-ATOM), received USDC.
              P&L = out_amount/1e6 - in_amount/1e6 * cex_price
    """
    if out_amount is None:
        return None

    in_base = in_amount / 1_000_000
    out_base = out_amount / 1_000_000

    if direction == "BUY":
        # spent USDC, received ATOM
        value_received = out_base * cex_price  # what we can sell it for
        value_spent = in_base                  # USDC is 1:1 USD
        return round(value_received - value_spent, 6)
    else:
        # spent ATOM, received USDC
        value_received = out_base              # USDC ≈ USD
        value_spent = in_base * cex_price      # what we paid in USD terms
        return round(value_received - value_spent, 6)
