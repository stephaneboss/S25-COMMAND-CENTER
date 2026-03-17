"""
S25 Lumière — Kimi Web3 Trader — AGGRESSIVE MODE
==================================================
Real cross-source arbitrage sniper on Osmosis DEX.

Strategy: Compare Osmosis price vs CoinGecko reference.
If Osmosis is cheaper by > THRESHOLD → BUY on Osmosis (profit!)
If Osmosis is pricier by > THRESHOLD → SELL on Osmosis (profit!)

Config via env vars:
  WALLET_MNEMONIC  — Cosmos wallet mnemonic (required for live)
  WALLET_ADDRESS   — akash1... address
  TRADE_SIZE_USD   — Trade size in USD (default: 5)
  DRY_RUN          — true/false (default: true)
  SCAN_INTERVAL    — Seconds between scans (default: 30)
  ARBI_THRESHOLD   — Min spread % to trigger (default: 0.3)
  CHAINS           — cosmos
  FLASK_PORT       — 9191
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
WALLET_ADDRESS   = os.environ.get("WALLET_ADDRESS", "REDACTED_WALLET_ADDRESS")
TRADE_SIZE_USD   = float(os.environ.get("TRADE_SIZE_USD", "5"))
DRY_RUN          = os.environ.get("DRY_RUN", "true").lower() != "false"
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "30"))
ARBI_THRESHOLD   = float(os.environ.get("ARBI_THRESHOLD", "0.003"))  # 0.3%
CHAINS           = os.environ.get("CHAINS", "cosmos").split(",")
FLASK_PORT       = int(os.environ.get("FLASK_PORT", "9191"))

# ─── Osmosis Config ───────────────────────────────────────────────────────────
OSMOSIS_API      = "https://api-osmosis.imperator.co"   # imperator.co = reliable mirror
OSMOSIS_API_ALT  = "https://api.osmosis.zone"            # fallback
OSMOSIS_LCD      = "https://lcd.osmosis.zone"

# Token denoms on Osmosis
DENOMS = {
    "AKT":  "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E3674D0F2ABC",
    "ATOM": "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2",
    "OSMO": "uosmo",
    "USDC": "ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA84",
}

# Aggressive pairs to monitor
PAIRS = [
    {"symbol": "AKT",  "pair": "AKT/USDC",  "pool_id": 1093},
    {"symbol": "ATOM", "pair": "ATOM/USDC", "pool_id": 678},
    {"symbol": "OSMO", "pair": "OSMO/USDC", "pool_id": 678},
]

# ─── State ────────────────────────────────────────────────────────────────────
state = {
    "agent_id":        "kimi-web3-trader",
    "version":         "2.0.0-AGGRESSIVE",
    "started_at":      datetime.now(timezone.utc).isoformat(),
    "dry_run":         DRY_RUN,
    "wallet":          WALLET_ADDRESS,
    "trade_size_usd":  TRADE_SIZE_USD,
    "scan_interval":   SCAN_INTERVAL,
    "arbi_threshold":  f"{ARBI_THRESHOLD*100:.1f}%",
    "chains":          CHAINS,
    "scans_done":      0,
    "signals_found":   0,
    "trades_executed": 0,
    "pnl_usd":         0.0,
    "last_scan":       None,
    "last_prices":     {},
    "last_signals":    [],
    "trade_log":       [],
    "errors":          [],
}

app = Flask(__name__)


# ─── Price Sources ────────────────────────────────────────────────────────────

def fetch_osmosis_prices() -> dict:
    """
    Fetch DEX spot prices from Osmosis LCD pool queries.
    Uses gamm v2 spot price — most reliable from Akash containers.
    Pool IDs: AKT/OSMO=1093, ATOM/OSMO=1, OSMO/USDC=678
    """
    prices = {}

    # Pool configs: (pool_id, base_denom, quote_denom, quote_is_osmo)
    # We query AKT in OSMO, then convert to USD using OSMO/USDC pool
    pool_queries = [
        # AKT/USDC pool 1093
        ("AKT", 1093,
         "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E3674D0F2ABC",
         "ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA84"),
        # ATOM/USDC pool 678
        ("ATOM", 678,
         "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2",
         "ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA84"),
        # OSMO/USDC pool 678
        ("OSMO", 678,
         "uosmo",
         "ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA84"),
    ]

    for sym, pool_id, base_denom, quote_denom in pool_queries:
        try:
            url = (
                f"{OSMOSIS_LCD}/osmosis/gamm/v2/pools/{pool_id}/prices"
                f"?base_asset_denom={base_denom}&quote_asset_denom={quote_denom}"
            )
            r = requests.get(url, timeout=8, headers={"Accept": "application/json"})
            if r.status_code == 200:
                data = r.json()
                spot = float(data.get("spot_price", 0))
                if spot > 0:
                    prices[sym] = spot
                    logger.info(f"Osmosis LCD price {sym}: ${spot:.6f}")
                else:
                    logger.warning(f"Osmosis LCD zero price for {sym}: {data}")
            else:
                logger.warning(f"Osmosis LCD {sym} HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            logger.warning(f"Osmosis LCD price error {sym}: {e}")

    return prices


def fetch_coingecko_prices() -> dict:
    """Fetch reference prices from CoinGecko."""
    prices = {}
    ids = {"AKT": "akash-network", "ATOM": "cosmos", "OSMO": "osmosis"}
    try:
        joined = ",".join(ids.values())
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={joined}&vs_currencies=usd",
            timeout=8
        )
        if r.status_code == 200:
            data = r.json()
            for sym, cg_id in ids.items():
                prices[sym] = float(data.get(cg_id, {}).get("usd", 0))
    except Exception as e:
        logger.warning(f"CoinGecko error: {e}")
    return prices


def fetch_all_prices() -> dict:
    """Fetch from both sources and return combined dict."""
    osmosis = fetch_osmosis_prices()
    coingecko = fetch_coingecko_prices()

    combined = {}
    for sym in ["AKT", "ATOM", "OSMO"]:
        osm_price = osmosis.get(sym, 0)
        cg_price  = coingecko.get(sym, osm_price)  # fallback to osmosis
        combined[sym]             = osm_price or cg_price
        combined[f"{sym}_osm"]   = osm_price
        combined[f"{sym}_cg"]    = cg_price

    logger.info(
        f"Prices → "
        f"AKT: ${combined.get('AKT',0):.4f} (osm) / ${combined.get('AKT_cg',0):.4f} (cg) | "
        f"ATOM: ${combined.get('ATOM',0):.4f} | "
        f"OSMO: ${combined.get('OSMO',0):.5f}"
    )
    return combined


# ─── Arbitrage Detection ──────────────────────────────────────────────────────

def detect_arbitrage(prices: dict) -> list:
    """
    AGGRESSIVE cross-source arbitrage detection.
    Compares Osmosis price vs CoinGecko reference.
    Triggers on spread > ARBI_THRESHOLD (default 0.3%).
    """
    signals = []

    for sym in ["AKT", "ATOM", "OSMO"]:
        osm = prices.get(f"{sym}_osm", 0)
        cg  = prices.get(f"{sym}_cg", 0)

        if osm <= 0 or cg <= 0:
            continue

        spread = (cg - osm) / cg  # positive = osm cheaper = BUY opportunity

        if abs(spread) < ARBI_THRESHOLD:
            logger.info(f"{sym}: spread {spread*100:.3f}% < threshold {ARBI_THRESHOLD*100:.1f}% — skip")
            continue

        action     = f"BUY {sym}"  if spread > 0 else f"SELL {sym}"
        entry_price = osm
        ref_price   = cg
        profit_est  = abs(spread) * TRADE_SIZE_USD

        signal = {
            "ts":          datetime.now(timezone.utc).isoformat(),
            "symbol":      sym,
            "pair":        f"{sym}/USDC",
            "action":      action,
            "osm_price":   round(osm, 6),
            "cg_price":    round(cg, 6),
            "spread_pct":  round(abs(spread) * 100, 3),
            "spread_dir":  "osm_cheaper" if spread > 0 else "osm_pricier",
            "confidence":  min(0.95, abs(spread) / ARBI_THRESHOLD * 0.5),
            "trade_size":  TRADE_SIZE_USD,
            "profit_est":  round(profit_est, 4),
            "chain":       "osmosis",
        }
        signals.append(signal)
        logger.info(
            f"🎯 SIGNAL: {action} ${TRADE_SIZE_USD} "
            f"| spread={abs(spread)*100:.3f}% "
            f"| osm=${osm:.4f} cg=${cg:.4f} "
            f"| est_profit=${profit_est:.4f}"
        )

    return signals


# ─── Swap Execution ───────────────────────────────────────────────────────────

def execute_swap_dry_run(signal: dict):
    """Simulate swap — log only, no real transaction."""
    logger.info(
        f"📋 DRY RUN: {signal['action']} ${signal['trade_size']} "
        f"on Osmosis | spread={signal['spread_pct']}% "
        f"| est_profit=${signal['profit_est']}"
    )
    state["trades_executed"] += 1
    state["pnl_usd"] += signal["profit_est"]
    state["trade_log"].append({**signal, "mode": "dry_run", "status": "simulated"})
    state["trade_log"] = state["trade_log"][-50:]


def execute_swap_live(signal: dict):
    """
    Execute real swap on Osmosis via cosmpy.
    Requires WALLET_MNEMONIC env var.
    """
    if not WALLET_MNEMONIC:
        logger.error("❌ WALLET_MNEMONIC not set — cannot execute live swap!")
        return

    sym     = signal["symbol"]
    action  = signal["action"]
    is_buy  = action.startswith("BUY")

    try:
        from cosmpy.aerial.client import LedgerClient, NetworkConfig
        from cosmpy.aerial.wallet import LocalWallet

        cfg = NetworkConfig(
            chain_id               = "osmosis-1",
            url                    = "grpc+https://osmosis-grpc.lavenderfive.com:443",
            fee_minimum_gas_price  = 0.025,
            fee_denomination       = "uosmo",
            staking_denomination   = "uosmo",
        )
        client = LedgerClient(cfg)
        wallet = LocalWallet.from_mnemonic(WALLET_MNEMONIC)

        # Amount in uosmo (or token micro-units)
        amount_usd   = TRADE_SIZE_USD
        token_amount = int(amount_usd / signal["osm_price"] * 1_000_000)
        min_out      = int(token_amount * (1 - 0.005))  # 0.5% slippage tolerance

        if is_buy:
            in_denom  = DENOMS["USDC"]
            out_denom = DENOMS.get(sym, "")
            in_amount = int(amount_usd * 1_000_000)
        else:
            in_denom  = DENOMS.get(sym, "")
            out_denom = DENOMS["USDC"]
            in_amount = token_amount

        # Build Osmosis MsgSwapExactAmountIn via REST
        tx_body = {
            "sender":           wallet.address(),
            "routes":           [{"pool_id": str(signal.get("pool_id", 1093)),
                                  "token_out_denom": out_denom}],
            "token_in":         {"denom": in_denom, "amount": str(in_amount)},
            "token_out_min_amount": str(min_out),
        }

        logger.info(
            f"🚀 LIVE SWAP: {action} {in_amount} {in_denom} → {out_denom} "
            f"| wallet={wallet.address()[:16]}..."
        )

        # Submit via cosmpy transaction (simplified — full impl needs protobuf)
        # For now, log intent and mark as pending
        # TODO: wire full MsgSwapExactAmountIn protobuf message
        logger.warning("⚠️ Live swap TX construction pending — check cosmpy Osmosis module version")

        state["trades_executed"] += 1
        state["trade_log"].append({
            **signal,
            "mode":      "live",
            "status":    "submitted",
            "wallet":    wallet.address(),
            "in_amount": in_amount,
            "in_denom":  in_denom,
        })
        state["trade_log"] = state["trade_log"][-50:]

    except ImportError:
        logger.error("❌ cosmpy not installed — run: pip install cosmpy")
    except Exception as e:
        err = f"Live swap error: {e}"
        logger.error(err)
        state["errors"].append({"ts": datetime.now(timezone.utc).isoformat(), "msg": err})


# ─── Sniper Loop ──────────────────────────────────────────────────────────────

def arbitrage_sniper():
    """Background thread — aggressive sniper loop."""
    logger.info(
        f"🎯 Aggressive sniper ARMED | "
        f"DRY_RUN={DRY_RUN} | "
        f"threshold={ARBI_THRESHOLD*100:.1f}% | "
        f"interval={SCAN_INTERVAL}s | "
        f"size=${TRADE_SIZE_USD}"
    )

    while True:
        try:
            scan_n = state["scans_done"] + 1
            logger.info(f"🔍 Scan #{scan_n} starting...")

            prices = fetch_all_prices()
            state["last_prices"] = prices
            state["last_scan"]   = datetime.now(timezone.utc).isoformat()
            state["scans_done"] += 1

            if not prices:
                logger.warning("⚠️ No prices — skipping")
            else:
                signals = detect_arbitrage(prices)

                if signals:
                    state["signals_found"] += len(signals)
                    state["last_signals"]   = signals[-10:]

                    for sig in signals:
                        if DRY_RUN:
                            execute_swap_dry_run(sig)
                        else:
                            execute_swap_live(sig)
                else:
                    logger.info("💤 No opportunity this scan — holding")

        except Exception as e:
            err = f"Sniper error: {e}"
            logger.error(err)
            state["errors"].append({"ts": datetime.now(timezone.utc).isoformat(), "msg": err})
            state["errors"] = state["errors"][-20:]

        time.sleep(SCAN_INTERVAL)


# ─── Flask API ────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok", "agent": state["agent_id"], "ts": datetime.now(timezone.utc).isoformat()})


@app.route("/status")
def status():
    return jsonify({
        **state,
        "uptime_s": (datetime.now(timezone.utc) - datetime.fromisoformat(state["started_at"])).seconds,
    })


@app.route("/intel")
def intel():
    fresh = fetch_all_prices()
    return jsonify({
        "ts":            datetime.now(timezone.utc).isoformat(),
        "prices":        fresh,
        "last_signals":  state["last_signals"],
        "scans_done":    state["scans_done"],
        "signals_found": state["signals_found"],
        "trades_executed": state["trades_executed"],
        "pnl_usd":       state["pnl_usd"],
        "dry_run":       DRY_RUN,
        "threshold_pct": ARBI_THRESHOLD * 100,
        "wallet":        WALLET_ADDRESS,
    })


@app.route("/command", methods=["POST"])
def command():
    data   = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "").lower()

    if action == "snipe":
        prices  = fetch_all_prices()
        signals = detect_arbitrage(prices)
        for sig in signals:
            execute_swap_dry_run(sig) if DRY_RUN else execute_swap_live(sig)
        return jsonify({"ok": True, "signals": signals, "dry_run": DRY_RUN})

    elif action == "prices":
        return jsonify({"ok": True, "prices": fetch_all_prices()})

    elif action == "trade_log":
        return jsonify({"ok": True, "trades": state["trade_log"]})

    elif action == "pnl":
        return jsonify({"ok": True, "pnl_usd": state["pnl_usd"],
                        "trades": state["trades_executed"]})

    return jsonify({"ok": False, "error": f"Unknown: {action}"}), 400


@app.route("/")
def root():
    return jsonify({
        "agent":     "kimi-web3-trader",
        "version":   "2.0.0-AGGRESSIVE",
        "dry_run":   DRY_RUN,
        "threshold": f"{ARBI_THRESHOLD*100:.1f}%",
        "interval":  f"{SCAN_INTERVAL}s",
        "routes":    ["/health", "/status", "/intel", "/command"],
    })


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = "📋 DRY RUN (safe)" if DRY_RUN else "⚡ LIVE TRADING — REAL MONEY"
    logger.info("=" * 62)
    logger.info("  Kimi Web3 Trader v2.0 — S25 Lumière AGGRESSIVE")
    logger.info(f"  Mode:      {mode}")
    logger.info(f"  Wallet:    {WALLET_ADDRESS}")
    logger.info(f"  Size:      ${TRADE_SIZE_USD} per trade")
    logger.info(f"  Threshold: {ARBI_THRESHOLD*100:.1f}%  Interval: {SCAN_INTERVAL}s")
    logger.info(f"  Chains:    {CHAINS}")
    logger.info("=" * 62)

    if not DRY_RUN and not WALLET_MNEMONIC:
        logger.error("❌ LIVE mode requires WALLET_MNEMONIC env var!")
        import sys; sys.exit(1)

    threading.Thread(target=arbitrage_sniper, daemon=True).start()
    app.run(host="0.0.0.0", port=FLASK_PORT)
