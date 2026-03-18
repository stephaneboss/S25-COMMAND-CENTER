"""
S25-KIMI-v2 Main Orchestrator
==============================
Entry point for the CEX-DEX arbitrage bot.

Startup sequence
----------------
1. Load Config from environment variables
2. Validate env vars (hard fail if LIVE and missing credentials)
3. Detect wallet balance (live/paper) or set dummy balance (dry)
4. Send startup Telegram report
5. Enter main scan loop

Main loop (every SCAN_INTERVAL seconds)
----------------------------------------
1. Check circuit breaker — skip if tripped
2. Get price spread from oracle
3. If score >= MIN_SIGNAL_SCORE, run pre_trade_check
4. If check passes, size position and execute
5. Record outcome, update circuit breaker and loss tracker
6. Send Telegram alert
7. Every HEARTBEAT_INTERVAL scans, log + send heartbeat

Shutdown
--------
CTRL+C triggers graceful shutdown: final report is sent to Telegram.
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Optional

# ── Local modules ──────────────────────────────────────────────────────────────
from config import Config
from executor import SwapExecutor
from ledger import TradeLedger
from oracle import PriceOracle
from reporter import TelegramReporter
from risk import RiskManager

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("s25_kimi_v2.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("s25.kimi_v2.main")


# ─── Balance fetch ─────────────────────────────────────────────────────────────

def _fetch_balance(config: Config) -> float:
    """
    Fetch wallet balance in USD.

    - DRY mode:   returns a synthetic $100 for simulation purposes.
    - PAPER mode: returns synthetic $100 unless wallet balance is fetchable.
    - LIVE mode:  queries Osmosis LCD for actual USDC + ATOM balance.

    Falls back to $0 on any error (which will block trading via BalanceGuard).
    """
    if config.is_dry:
        logger.info("Balance (DRY): synthetic $100.00")
        return 100.0

    if not config.WALLET_ADDRESS:
        logger.warning("No WALLET_ADDRESS configured — using synthetic $100")
        return 100.0

    try:
        import requests

        url = (
            f"{config.OSMOSIS_LCD}/cosmos/bank/v1beta1/balances/"
            f"{config.WALLET_ADDRESS}"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        balances = resp.json().get("balances", [])

        total_usd = 0.0
        for coin in balances:
            denom = coin.get("denom", "")
            amount = float(coin.get("amount", 0)) / 1_000_000

            if denom == config.DENOM_USDC:
                total_usd += amount  # USDC ≈ $1
            elif denom == config.DENOM_OSMO:
                # Approximate OSMO at a fixed price; a real implementation
                # would query the oracle here
                total_usd += amount * 1.0  # placeholder $1/OSMO
            elif denom == config.DENOM_ATOM:
                total_usd += amount * 8.0  # placeholder $8/ATOM

        logger.info("Balance (on-chain): $%.2f USD", total_usd)
        return total_usd

    except Exception as exc:
        logger.error("Balance fetch failed: %s — using $0", exc)
        return 0.0


# ─── Graceful shutdown ─────────────────────────────────────────────────────────

class _ShutdownFlag:
    """Tiny flag that flips to True on SIGINT / SIGTERM."""

    def __init__(self) -> None:
        self.requested = False

    def trigger(self, *_: object) -> None:
        logger.info("Shutdown requested")
        self.requested = True


# ─── Main loop ─────────────────────────────────────────────────────────────────

def run_bot(config: Optional[Config] = None) -> None:
    """
    Full bot lifecycle: startup → loop → shutdown.

    Parameters
    ----------
    config:
        If None, loads from environment via Config.from_env().
    """
    # ── Load config ────────────────────────────────────────────────────────────
    if config is None:
        try:
            config = Config.from_env()
        except (EnvironmentError, ValueError) as exc:
            logger.critical("Config error: %s", exc)
            sys.exit(1)

    logger.info("Starting S25-KIMI-v2 in MODE=%s", config.MODE.upper())

    # ── LIVE gate ──────────────────────────────────────────────────────────────
    # Extra safety: refuse to start LIVE if the code somehow got here
    # without the config safety check passing.
    if config.is_live:
        import os
        if os.environ.get("LIVE_MODE_CONFIRMED", "").lower() != "yes":
            logger.critical(
                "LIVE mode requires LIVE_MODE_CONFIRMED=yes. Refusing to start."
            )
            sys.exit(1)
        logger.warning(
            "!!! RUNNING IN LIVE MODE — REAL FUNDS AT RISK !!!"
        )

    # ── Instantiate components ─────────────────────────────────────────────────
    ledger = TradeLedger(config)
    reporter = TelegramReporter(config)
    oracle = PriceOracle(config)

    # Seed the daily loss tracker with what's already in the ledger
    todays_pnl = ledger.get_daily_pnl()
    risk = RiskManager(config, initial_daily_pnl=todays_pnl)
    executor = SwapExecutor(config, ledger)

    # ── Initial balance ────────────────────────────────────────────────────────
    balance_usd = _fetch_balance(config)

    # ── Startup report ─────────────────────────────────────────────────────────
    reporter.send_startup_report(config.MODE, balance_usd)

    # ── Signal handlers ────────────────────────────────────────────────────────
    shutdown = _ShutdownFlag()
    signal.signal(signal.SIGINT, shutdown.trigger)
    signal.signal(signal.SIGTERM, shutdown.trigger)

    # ── Main scan loop ─────────────────────────────────────────────────────────
    scan_count = 0
    symbol = "ATOM"  # Primary trading pair (extend to list for multi-pair)

    logger.info(
        "Entering main loop: symbol=%s interval=%ds", symbol, config.SCAN_INTERVAL
    )

    while not shutdown.requested:
        scan_count += 1
        loop_start = time.monotonic()

        try:
            _run_single_scan(
                scan_count=scan_count,
                symbol=symbol,
                config=config,
                oracle=oracle,
                risk=risk,
                executor=executor,
                reporter=reporter,
                ledger=ledger,
                balance_usd=balance_usd,
            )

            # Refresh balance every 10 scans in live/paper mode
            if not config.is_dry and scan_count % 10 == 0:
                balance_usd = _fetch_balance(config)

            # Heartbeat
            if scan_count % config.HEARTBEAT_INTERVAL == 0:
                daily_pnl = ledger.get_daily_pnl()
                logger.info(
                    "Heartbeat #%d | balance=$%.2f | daily_pnl=$%.4f",
                    scan_count, balance_usd, daily_pnl,
                )
                reporter.send_heartbeat(scan_count, balance_usd, daily_pnl)

        except Exception as exc:
            # Catch-all so a single scan error never kills the loop
            logger.exception("Unhandled error in scan #%d: %s", scan_count, exc)
            reporter.send_warning(f"Unhandled scan error: {exc}")

        # ── Sleep for remainder of interval ───────────────────────────────────
        elapsed = time.monotonic() - loop_start
        sleep_time = max(0.0, config.SCAN_INTERVAL - elapsed)
        if not shutdown.requested:
            time.sleep(sleep_time)

    # ── Graceful shutdown ──────────────────────────────────────────────────────
    logger.info("Bot stopped after %d scans.", scan_count)
    daily_pnl = ledger.get_daily_pnl()
    stats = ledger.get_stats(days=7)
    reporter.send_shutdown_report(scan_count, daily_pnl, stats)


def _run_single_scan(
    *,
    scan_count: int,
    symbol: str,
    config: Config,
    oracle: PriceOracle,
    risk: RiskManager,
    executor: SwapExecutor,
    reporter: TelegramReporter,
    ledger: TradeLedger,
    balance_usd: float,
) -> None:
    """
    Execute one full scan iteration.

    Steps
    -----
    1. Check circuit breaker
    2. Fetch spread / signal
    3. Pre-trade risk check
    4. Size position
    5. Execute trade
    6. Record outcome and notify
    """
    # ── 1. Circuit breaker ────────────────────────────────────────────────────
    if risk.circuit_breaker.is_tripped:
        mins = risk.circuit_breaker.seconds_until_reset / 60
        logger.info(
            "Scan #%d: circuit breaker active — %.1f min remaining",
            scan_count, mins,
        )
        return

    # ── 2. Fetch signal ───────────────────────────────────────────────────────
    signal = oracle.get_spread(symbol)

    if signal is None:
        logger.warning("Scan #%d: oracle returned no signal for %s", scan_count, symbol)
        return

    score = signal["score"]
    spread_pct = signal["spread_pct"]

    logger.info(
        "Scan #%d | %s | osm=%.4f cex=%.4f spread=%.4f%% score=%d dir=%s",
        scan_count, symbol,
        signal["osm_price"], signal["cex_price"],
        spread_pct * 100, score, signal["direction"],
    )

    if score < config.MIN_SIGNAL_SCORE:
        logger.debug(
            "Scan #%d: score %d below threshold %d — skip",
            scan_count, score, config.MIN_SIGNAL_SCORE,
        )
        return

    # ── 3. Pre-trade risk check ───────────────────────────────────────────────
    ok, reason = risk.pre_trade_check(signal, balance_usd)
    if not ok:
        logger.info("Scan #%d: risk check FAILED — %s", scan_count, reason)

        # Alert if circuit breaker just tripped
        if "circuit breaker" in reason.lower():
            reporter.send_circuit_breaker_alert(reason)
        return

    # ── 4. Size position ──────────────────────────────────────────────────────
    amount_units = risk.calculate_position(signal, balance_usd)
    if amount_units <= 0:
        logger.info("Scan #%d: position size is zero — skip", scan_count)
        return

    logger.info(
        "Scan #%d: EXECUTING %s %s — %d micro-units",
        scan_count, signal["direction"], symbol, amount_units,
    )

    # ── 5. Execute ────────────────────────────────────────────────────────────
    result = executor.execute(signal, amount_units)
    success = result.get("success", False)
    pnl = result.get("pnl_usd")

    # ── 6. Record and notify ──────────────────────────────────────────────────
    risk.record_outcome(success, pnl or 0.0)

    # Send Telegram alert
    reporter.send_trade_alert(signal, result, pnl)

    if not success:
        logger.warning(
            "Scan #%d: trade FAILED (%d consecutive fails). Error: %s",
            scan_count,
            risk.circuit_breaker.consecutive_fails,
            result.get("error"),
        )
        # Check if circuit breaker just tripped
        if risk.circuit_breaker.is_tripped:
            reason = (
                f"Circuit breaker tripped after "
                f"{config.MAX_CONSECUTIVE_FAILS} consecutive failures"
            )
            reporter.send_circuit_breaker_alert(reason)
    else:
        pnl_str = f"${pnl:.4f}" if pnl is not None else "N/A"
        logger.info("Scan #%d: trade SUCCESS — P&L %s", scan_count, pnl_str)


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_bot()
