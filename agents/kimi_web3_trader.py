"""
S25 Lumière — Kimi Web3 Multi-Chain Trader
===========================================
Autonomous arbitrage sniper for Cosmos/Osmosis DEX.

Features:
- Flask REST API (port 9191)
- Real-time price fetching from Osmosis LCD API
- Arbitrage detection (spread > 0.5% threshold)
- DRY_RUN=true by default (safe)
- Background sniper loop (every SCAN_INTERVAL seconds)

Chains supported:
- Cosmos/Osmosis  (AKT/USDC, ATOM/USDC)

Config via env vars:
  WALLET_MNEMONIC     - Cosmos wallet mnemonic
  WALLET_ADDRESS      - Cosmos wallet address (akash1...)
  TRADE_SIZE_USD      - Trade size in USD (default: 5)
  DRY_RUN             - true/false (default: true)
  SCAN_INTERVAL       - Seconds between scans (default: 60)
  CHAINS              - Comma-separated chains (default: cosmos)
  FLASK_PORT          - API port (default: 9191)
"""

import os
import time
import logging
import threading
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kimi.web3")

# ─── Config ───────────────────────────────────────────────────────────────────
WALLET_MNEMONIC  = os.environ.get("WALLET_MNEMONIC", "")
WALLET_ADDRESS   = os.environ.get("WALLET_ADDRESS", "akash1mw0trq8xgmdyqqjn482r9pfr05hfw06rzq2u9v")
TRADE_SIZE_USD   = float(os.environ.get("TRADE_SIZE_USD", "5"))
DRY_RUN          = os.environ.get("DRY_RUN", "true").lower() != "false"
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "60"))
CHAINS           = os.environ.get("CHAINS", "cosmos").split(",")
FLASK_PORT       = int(os.environ.get("FLASK_PORT", "9191"))
ARBI_THRESHOLD   = 0.005  # 0.5% minimum spread to trigger

# ─── Osmosis LCD Endpoints ────────────────────────────────────────────────────
OSMOSIS_LCD      = "https://lcd.osmosis.zone"
OSMOSIS_API      = "https://api.osmosis.zone"

# Pool IDs on Osmosis mainnet
POOL_AKT_USDC    = 1093   # AKT/USDC
POOL_ATOM_USDC   = 678    # ATOM/USDC.axl
POOL_ATOM_USDT   = 960    # ATOM/USDT

# ─── State ────────────────────────────────────────────────────────────────────
state = {
    "agent_id":      "kimi-web3-trader",
    "version":       "1.0.0",
    "started_at":    datetime.now(timezone.utc).isoformat(),
    "dry_run":       DRY_RUN,
    "wallet":        WALLET_ADDRESS,
    "trade_size_usd": TRADE_SIZE_USD,
    "scan_interval": SCAN_INTERVAL,
    "chains":        CHAINS,
    "scans_done":    0,
    "signals_found": 0,
    "trades_executed": 0,
    "last_scan":     None,
    "last_prices":   {},
    "last_signals":  [],
    "errors":        [],
}

# ─── Flask App ────────────────────────────────────────────────────────────────
app = Flask(__name__)


# ─── Osmosis Price Fetcher ────────────────────────────────────────────────────

def fetch_osmosis_spot_price(pool_id: int, base_denom: str, quote_denom: str) -> float:
    """Fetch spot price from Osmosis LCD API."""
    try:
        url = f"{OSMOSIS_LCD}/osmosis/gamm/v1beta1/pools/{pool_id}/prices"
        params = {
            "base_asset_denom": base_denom,
            "quote_asset_denom": quote_denom,
        }
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            data = r.json()
            price_str = data.get("spot_price", "0")
            return float(price_str)
    except Exception as e:
        logger.warning(f"Osmosis LCD error pool {pool_id}: {e}")
    return 0.0


def fetch_osmosis_token_price(symbol: str) -> float:
    """Fetch token price via Osmosis price API."""
    try:
        # Use Osmosis API for token prices
        url = f"{OSMOSIS_API}/tokens/v2/price/{symbol}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            return float(data.get("price", 0))
    except Exception as e:
        logger.warning(f"Osmosis price API error for {symbol}: {e}")

    # Fallback: try CoinGecko
    try:
        cg_ids = {"AKT": "akash-network", "ATOM": "cosmos", "OSMO": "osmosis"}
        cg_id  = cg_ids.get(symbol.upper(), "")
        if cg_id:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
            r   = requests.get(url, timeout=8)
            if r.status_code == 200:
                return float(r.json().get(cg_id, {}).get("usd", 0))
    except Exception as e:
        logger.warning(f"CoinGecko fallback error for {symbol}: {e}")

    return 0.0


def fetch_all_prices() -> dict:
    """Fetch current prices for all tracked pairs."""
    prices = {}
    try:
        prices["AKT"]  = fetch_osmosis_token_price("AKT")
        prices["ATOM"] = fetch_osmosis_token_price("ATOM")
        prices["OSMO"] = fetch_osmosis_token_price("OSMO")
        logger.info(f"Prices fetched: {prices}")
    except Exception as e:
        logger.error(f"fetch_all_prices error: {e}")
    return prices


def detect_arbitrage(prices: dict) -> list:
    """
    Detect arbitrage opportunities.
    Compare price from Osmosis vs expected cross-chain price.
    Returns list of signal dicts.
    """
    signals = []
    # Example: AKT price spread between two sources
    # In real multi-chain setup: compare Osmosis vs Uniswap/Jupiter
    # For now: detect if AKT is mispriced vs ATOM ratio
    try:
        akt  = prices.get("AKT", 0)
        atom = prices.get("ATOM", 0)

        if akt > 0 and atom > 0:
            # Theoretical: AKT/ATOM ratio
            ratio = akt / atom
            logger.info(f"AKT/ATOM ratio: {ratio:.4f} | AKT=${akt:.4f} | ATOM=${atom:.4f}")

            # Detect if AKT is underpriced relative to historical ratio (~0.08)
            # This is a simplified signal — real arb would compare across chains
            historical_ratio = 0.08
            spread = abs(ratio - historical_ratio) / historical_ratio

            if spread > ARBI_THRESHOLD:
                direction = "BUY AKT" if ratio < historical_ratio else "SELL AKT"
                signal = {
                    "ts":        datetime.now(timezone.utc).isoformat(),
                    "pair":      "AKT/ATOM",
                    "action":    direction,
                    "spread_pct": round(spread * 100, 2),
                    "akt_price": akt,
                    "atom_price": atom,
                    "ratio":     round(ratio, 6),
                    "confidence": min(0.9, spread * 10),
                    "chain":     "osmosis",
                }
                signals.append(signal)
                logger.info(f"🎯 SIGNAL: {direction} | spread={spread*100:.2f}%")

    except Exception as e:
        logger.error(f"detect_arbitrage error: {e}")

    return signals


def execute_swap_dry_run(signal: dict):
    """Simulate a swap — log only, no real transaction."""
    logger.info(
        f"📋 DRY RUN SWAP: {signal['action']} "
        f"${TRADE_SIZE_USD} on {signal['chain']} "
        f"| spread={signal['spread_pct']}% "
        f"| pair={signal['pair']}"
    )
    state["trades_executed"] += 1


def execute_swap_live(signal: dict):
    """
    Execute real swap on Osmosis via cosmpy.
    Only called when DRY_RUN=false AND WALLET_MNEMONIC is set.
    """
    if not WALLET_MNEMONIC:
        logger.error("Cannot execute live swap: WALLET_MNEMONIC not set")
        return

    try:
        from cosmpy.aerial.client import LedgerClient, NetworkConfig
        from cosmpy.aerial.wallet import LocalWallet
        from cosmpy.crypto.keypairs import Secp256k1

        # Connect to Osmosis
        cfg    = NetworkConfig(
            chain_id="osmosis-1",
            url="grpc+https://osmosis-grpc.lavenderfive.com:443",
            fee_minimum_gas_price=0.025,
            fee_denomination="uosmo",
            staking_denomination="uosmo",
        )
        client = LedgerClient(cfg)
        wallet = LocalWallet.from_mnemonic(WALLET_MNEMONIC)

        logger.info(
            f"🚀 LIVE SWAP: {signal['action']} "
            f"${TRADE_SIZE_USD} on Osmosis "
            f"| wallet={wallet.address()}"
        )
        # TODO: construct MsgSwapExactAmountIn transaction
        # This requires building the Osmosis swap message
        # Implementation pending cosmpy Osmosis module integration

        state["trades_executed"] += 1

    except ImportError:
        logger.error("cosmpy not installed — cannot execute live swap")
    except Exception as e:
        logger.error(f"Live swap error: {e}")


# ─── Arbitrage Sniper Loop ────────────────────────────────────────────────────

def arbitrage_sniper():
    """Main loop — runs in background thread."""
    logger.info(
        f"🎯 Arbitrage sniper started | DRY_RUN={DRY_RUN} | "
        f"interval={SCAN_INTERVAL}s | threshold={ARBI_THRESHOLD*100:.1f}%"
    )

    while True:
        try:
            scan_start = time.time()
            logger.info(f"🔍 Scan #{state['scans_done']+1} starting...")

            # Fetch prices
            prices = fetch_all_prices()
            state["last_prices"] = prices
            state["last_scan"]   = datetime.now(timezone.utc).isoformat()
            state["scans_done"] += 1

            if not prices:
                logger.warning("No prices fetched — skipping scan")
            else:
                # Detect opportunities
                signals = detect_arbitrage(prices)

                if signals:
                    state["signals_found"] += len(signals)
                    state["last_signals"]   = signals[-10:]  # keep last 10

                    for sig in signals:
                        if DRY_RUN:
                            execute_swap_dry_run(sig)
                        else:
                            execute_swap_live(sig)
                else:
                    logger.info("No arbitrage opportunity detected this scan")

            elapsed = time.time() - scan_start
            logger.info(f"✅ Scan complete in {elapsed:.2f}s")

        except Exception as e:
            err = f"Sniper loop error: {e}"
            logger.error(err)
            state["errors"].append({"ts": datetime.now(timezone.utc).isoformat(), "msg": err})
            state["errors"] = state["errors"][-20:]  # keep last 20

        time.sleep(SCAN_INTERVAL)


# ─── Flask Routes ─────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "agent":  state["agent_id"],
        "ts":     datetime.now(timezone.utc).isoformat(),
    })


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        **state,
        "uptime_s": (
            datetime.now(timezone.utc) -
            datetime.fromisoformat(state["started_at"])
        ).seconds,
    })


@app.route("/intel", methods=["GET"])
def intel():
    """Return live price intelligence and last signals."""
    # Try a quick fresh price fetch
    try:
        fresh_prices = fetch_all_prices()
    except Exception:
        fresh_prices = state["last_prices"]

    return jsonify({
        "ts":            datetime.now(timezone.utc).isoformat(),
        "prices":        fresh_prices,
        "last_scan":     state["last_scan"],
        "last_signals":  state["last_signals"],
        "scans_done":    state["scans_done"],
        "signals_found": state["signals_found"],
        "wallet":        WALLET_ADDRESS,
        "dry_run":       DRY_RUN,
        "chains":        CHAINS,
    })


@app.route("/command", methods=["POST"])
def command():
    """Accept manual trading commands."""
    data   = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "").lower()
    pair   = data.get("pair", "AKT/USDC")

    if action == "snipe":
        prices = fetch_all_prices()
        signals = detect_arbitrage(prices)
        if signals:
            for sig in signals:
                if DRY_RUN:
                    execute_swap_dry_run(sig)
                else:
                    execute_swap_live(sig)
            return jsonify({"ok": True, "signals": signals, "dry_run": DRY_RUN})
        return jsonify({"ok": True, "msg": "No opportunity found", "prices": prices})

    elif action == "prices":
        return jsonify({"ok": True, "prices": fetch_all_prices()})

    elif action == "status":
        return jsonify({"ok": True, "state": state})

    else:
        return jsonify({"ok": False, "error": f"Unknown action: {action}"}), 400


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "agent":   "kimi-web3-trader",
        "version": "1.0.0",
        "routes":  ["/health", "/status", "/intel", "/command"],
        "dry_run": DRY_RUN,
    })


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = "DRY RUN" if DRY_RUN else "⚠️  LIVE TRADING"
    logger.info(f"{'='*60}")
    logger.info(f"  Kimi Web3 Trader — S25 Lumière")
    logger.info(f"  Mode: {mode}")
    logger.info(f"  Wallet: {WALLET_ADDRESS}")
    logger.info(f"  Trade size: ${TRADE_SIZE_USD}")
    logger.info(f"  Chains: {CHAINS}")
    logger.info(f"  Scan interval: {SCAN_INTERVAL}s")
    logger.info(f"{'='*60}")

    if not DRY_RUN and not WALLET_MNEMONIC:
        logger.error("LIVE mode requires WALLET_MNEMONIC env var!")
        exit(1)

    # Start sniper in background thread
    sniper_thread = threading.Thread(target=arbitrage_sniper, daemon=True)
    sniper_thread.start()

    # Start Flask API
    app.run(host="0.0.0.0", port=FLASK_PORT)
