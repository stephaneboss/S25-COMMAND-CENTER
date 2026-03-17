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
WALLET_ADDRESS   = os.environ.get("WALLET_ADDRESS", "akash1mw0trq8xgmdyqqjn482r9pfr05hfw06rzq2u9v")
TRADE_SIZE_USD   = float(os.environ.get("TRADE_SIZE_USD", "5"))
DRY_RUN          = os.environ.get("DRY_RUN", "true").lower() != "false"
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "30"))
ARBI_THRESHOLD   = float(os.environ.get("ARBI_THRESHOLD", "0.003"))  # 0.3%
CHAINS           = os.environ.get("CHAINS", "cosmos").split(",")
FLASK_PORT       = int(os.environ.get("FLASK_PORT", "9191"))

# ─── Osmosis Config ───────────────────────────────────────────────────────────
OSMOSIS_LCD      = "https://lcd.osmosis.zone"
# Confirmed pool IDs (Osmosis mainnet 2026)
POOL_ATOM_OSMO   = 1      # ATOM/OSMO
POOL_AKT_OSMO    = 3      # AKT/OSMO
POOL_OSMO_USDC   = 678    # OSMO/axlUSDC
# Correct IBC denoms
DENOM_ATOM = "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
DENOM_AKT  = "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E3674D0F2ABC"
DENOM_OSMO = "uosmo"
DENOM_USDC = "ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858"

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
    Fetch real Osmosis DEX spot prices via LCD gamm v2 pool queries.
    Confirmed working pools (2026):
      Pool 678  → OSMO/USDC direct USD price
      Pool 1    → ATOM/OSMO × OSMO_USD = ATOM_USD
      Pool 3    → AKT/OSMO  × OSMO_USD = AKT_USD
    """
    prices = {}

    def lcd_spot(pool_id, base, quote) -> float:
        try:
            r = requests.get(
                f"{OSMOSIS_LCD}/osmosis/gamm/v2/pools/{pool_id}/prices"
                f"?base_asset_denom={base}&quote_asset_denom={quote}",
                timeout=8, headers={"Accept": "application/json"}
            )
            if r.status_code == 200:
                val = r.json().get("spot_price", "0")
                return float(val) if val else 0.0
            logger.warning(f"LCD pool {pool_id} HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"LCD pool {pool_id} error: {e}")
        return 0.0

    # Step 1: OSMO/USD from pool 678 (axlUSDC)
    osmo_usd = lcd_spot(POOL_OSMO_USDC, DENOM_OSMO, DENOM_USDC)
    if osmo_usd > 0:
        prices["OSMO"] = osmo_usd
        logger.info(f"Osmosis LCD OSMO/USD: ${osmo_usd:.6f}")

        # Step 2: ATOM/OSMO from pool 1 → convert to USD
        atom_osmo = lcd_spot(POOL_ATOM_OSMO, DENOM_ATOM, DENOM_OSMO)
        if atom_osmo > 0:
            prices["ATOM"] = atom_osmo * osmo_usd
            logger.info(f"Osmosis LCD ATOM/USD: ${prices['ATOM']:.4f} ({atom_osmo:.4f} OSMO)")

        # Step 3: AKT/OSMO from pool 3 → convert to USD
        akt_osmo = lcd_spot(POOL_AKT_OSMO, DENOM_AKT, DENOM_OSMO)
        if akt_osmo > 0:
            prices["AKT"] = akt_osmo * osmo_usd
            logger.info(f"Osmosis LCD AKT/USD: ${prices['AKT']:.4f} ({akt_osmo:.4f} OSMO)")
        else:
            # Pool 3 may need reversed query
            osmo_akt = lcd_spot(POOL_AKT_OSMO, DENOM_OSMO, DENOM_AKT)
            if osmo_akt > 0:
                prices["AKT"] = (1.0 / osmo_akt) * osmo_usd
                logger.info(f"Osmosis LCD AKT/USD (inv): ${prices['AKT']:.4f}")
    else:
        logger.warning("Osmosis LCD: OSMO/USD failed — skipping all LCD prices")

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


# ─── Protobuf Wire Encoding ───────────────────────────────────────────────────

def _varint(n: int) -> bytes:
    """Encode integer as protobuf varint."""
    out = bytearray()
    while n > 0x7F:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n & 0x7F)
    return bytes(out)

def _pb_str(field: int, val: str) -> bytes:
    """Encode protobuf string field (wire type 2)."""
    b = val.encode()
    return _varint((field << 3) | 2) + _varint(len(b)) + b

def _pb_u64(field: int, val: int) -> bytes:
    """Encode protobuf uint64 field (wire type 0)."""
    return _varint((field << 3) | 0) + _varint(val)

def _pb_msg(field: int, data: bytes) -> bytes:
    """Encode embedded protobuf message (wire type 2)."""
    return _varint((field << 3) | 2) + _varint(len(data)) + data

def encode_swap_msg(sender: str, pool_id: int,
                    in_denom: str, in_amount: int,
                    out_denom: str, min_out: int = 1) -> bytes:
    """
    Encode osmosis.gamm.v1beta1.MsgSwapExactAmountIn as raw protobuf bytes.
    No external Osmosis proto dependency required.
    """
    route = _pb_u64(1, pool_id) + _pb_str(2, out_denom)          # SwapAmountInRoute
    coin  = _pb_str(1, in_denom) + _pb_str(2, str(in_amount))     # Coin
    return (
        _pb_str(1, sender) +      # sender
        _pb_msg(2, route)  +      # routes[0]
        _pb_msg(3, coin)   +      # token_in
        _pb_str(4, str(min_out))  # token_out_min_amount
    )


def execute_swap_live(signal: dict):
    """
    Execute real swap on Osmosis via cosmpy + MsgSwapExactAmountIn.
    Requires WALLET_MNEMONIC env var.
    """
    if not WALLET_MNEMONIC:
        logger.error("❌ WALLET_MNEMONIC not set — cannot execute live swap!")
        return

    sym    = signal["symbol"]
    action = signal["action"]
    is_buy = action.startswith("BUY")

    # Pool routing — confirmed Osmosis mainnet 2026
    pool_map = {"OSMO": POOL_OSMO_USDC, "ATOM": POOL_ATOM_OSMO, "AKT": POOL_AKT_OSMO}
    pool_id  = pool_map.get(sym, POOL_OSMO_USDC)

    # Denom routing
    sym_denom = {"OSMO": DENOM_OSMO, "ATOM": DENOM_ATOM, "AKT": DENOM_AKT}
    if is_buy:
        in_denom  = DENOM_USDC
        out_denom = sym_denom.get(sym, DENOM_OSMO)
        in_amount = int(TRADE_SIZE_USD * 1_000_000)
    else:
        in_denom  = sym_denom.get(sym, DENOM_OSMO)
        out_denom = DENOM_USDC
        in_amount = int(TRADE_SIZE_USD / signal["osm_price"] * 1_000_000)

    # BUILD14: full manual tx build — bypass cosmpy Transaction/SigningCfg entirely
    # Uses raw cosmos protobufs + coincurve secp256k1, pure REST broadcast

    try:
        import base64, hashlib
        from cosmpy.aerial.wallet import LocalWallet
        from google.protobuf.any_pb2 import Any as ProtoAny

        # ── Step 1: Wallet (local) ─────────────────────────────────────────
        wallet    = LocalWallet.from_mnemonic(WALLET_MNEMONIC, prefix="osmo")
        osmo_addr = str(wallet.address())
        logger.info(f"🚀 SWAP: {action} pool={pool_id} wallet={osmo_addr[:24]}...")

        # ── Step 2: Account info via LCD REST ─────────────────────────────
        acc_r = requests.get(
            f"{OSMOSIS_LCD}/cosmos/auth/v1beta1/accounts/{osmo_addr}",
            timeout=8, headers={"Accept": "application/json"}
        )
        if acc_r.status_code == 200:
            d       = acc_r.json().get("account", {})
            seq_num = int(d.get("sequence",       "0"))
            acc_num = int(d.get("account_number", "0"))
            logger.info(f"Account: acc_num={acc_num} seq={seq_num}")
        else:
            logger.warning(f"Account HTTP {acc_r.status_code} → seq=0/acc=0")
            seq_num, acc_num = 0, 0

        # ── Step 3: Cosmos protobuf types ──────────────────────────────────
        try:  # cosmpy v1.x
            from cosmpy.protos.cosmos.tx.v1beta1.tx_pb2 import (
                Tx, TxBody, AuthInfo, SignerInfo, ModeInfo, Fee, SignDoc)
            from cosmpy.protos.cosmos.tx.signing.v1beta1.signing_pb2 import SignMode
            from cosmpy.protos.cosmos.crypto.secp256k1.keys_pb2 import PubKey as Secp256k1PubKey
            from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin
        except ImportError:  # cosmpy v0.x
            from cosmos.tx.v1beta1.tx_pb2 import (
                Tx, TxBody, AuthInfo, SignerInfo, ModeInfo, Fee, SignDoc)
            from cosmos.tx.signing.v1beta1.signing_pb2 import SignMode
            from cosmos.crypto.secp256k1.keys_pb2 import PubKey as Secp256k1PubKey
            from cosmos.base.v1beta1.coin_pb2 import Coin

        # ── Step 4: Public key bytes via coincurve ─────────────────────────
        priv_key      = wallet.signer()                               # coincurve.PrivateKey
        pub_key_bytes = priv_key.public_key.format(compressed=True)   # 33 bytes

        # ── Step 5: TxBody ─────────────────────────────────────────────────
        msg_bytes = encode_swap_msg(
            sender=osmo_addr, pool_id=pool_id,
            in_denom=in_denom, in_amount=in_amount,
            out_denom=out_denom, min_out=1,
        )
        any_msg = ProtoAny(type_url="/osmosis.gamm.v1beta1.MsgSwapExactAmountIn", value=msg_bytes)
        tx_body = TxBody(messages=[any_msg], memo="")

        # ── Step 6: AuthInfo ───────────────────────────────────────────────
        pub_any = ProtoAny(
            type_url="/cosmos.crypto.secp256k1.PubKey",
            value=Secp256k1PubKey(key=pub_key_bytes).SerializeToString(),
        )
        signer_info = SignerInfo(
            public_key=pub_any,
            mode_info=ModeInfo(single=ModeInfo.Single(mode=SignMode.SIGN_MODE_DIRECT)),
            sequence=seq_num,
        )
        gas_limit = 300000
        auth_info = AuthInfo(
            signer_infos=[signer_info],
            fee=Fee(
                amount=[Coin(denom="uosmo", amount=str(int(gas_limit * 0.025 * 1.5)))],
                gas_limit=gas_limit,
            ),
        )

        # ── Step 7: Sign ───────────────────────────────────────────────────
        sign_doc  = SignDoc(
            body_bytes      = tx_body.SerializeToString(),
            auth_info_bytes = auth_info.SerializeToString(),
            chain_id        = "osmosis-1",
            account_number  = acc_num,
        )
        msg_hash  = hashlib.sha256(sign_doc.SerializeToString()).digest()
        raw_sig   = priv_key.sign(msg_hash, hasher=None)  # 65 bytes (r+s+recovery)
        signature = raw_sig[:64]                           # Cosmos uses 64 bytes (r+s)

        # ── Step 8: Broadcast via LCD REST ────────────────────────────────
        final_tx = Tx(body=tx_body, auth_info=auth_info, signatures=[signature])
        tx_b64   = base64.b64encode(final_tx.SerializeToString()).decode()

        bcast_r = requests.post(
            f"{OSMOSIS_LCD}/cosmos/tx/v1beta1/txs",
            json={"tx_bytes": tx_b64, "mode": "BROADCAST_MODE_SYNC"},
            timeout=15, headers={"Content-Type": "application/json"},
        )
        result  = bcast_r.json()
        tx_resp = result.get("tx_response", {})
        tx_hash = tx_resp.get("txhash", "unknown")
        code    = int(tx_resp.get("code", -1))
        raw_log = tx_resp.get("raw_log", "")

        if code == 0:
            logger.info(f"✅ SWAP TX SENT: {tx_hash}")
            status = "sent"
        else:
            logger.error(f"❌ TX code={code}: {raw_log[:200]}")
            raise Exception(f"TX code={code}: {raw_log[:150]}")

        state["trades_executed"] += 1
        state["pnl_usd"] += signal["profit_est"]
        state["trade_log"].append({
            **signal, "mode": "live", "status": status,
            "wallet": osmo_addr, "pool_id": pool_id,
            "in_amount": in_amount, "in_denom": in_denom, "tx_hash": tx_hash,
        })
        state["trade_log"] = state["trade_log"][-50:]

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
    except Exception as e:
        err = f"Live swap error: {e}"
        logger.error(err)
        state["errors"].append({"ts": datetime.now(timezone.utc).isoformat(), "msg": err})
        state["errors"] = state["errors"][-20:]


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
