#!/usr/bin/env python3
# ============================================================
# S25 LUMIERE - Treasury Engine v1
# Auto-Swap ATOM->AKT via Osmosis + Auto-recharge Akash
# Multi-chain: ATOM, OSMO, AKT, USDC
# ============================================================

import os
import json
import time
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
log = logging.getLogger("TREASURY")

# --- Config ------------------------------------------------
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
AKASH_ENDPOINT = os.getenv("AKASH_ENDPOINT", "http://localhost:5050")
AKASH_WALLET = os.getenv("AKASH_WALLET_ADDRESS", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "3600"))  # 1h default

# Osmosis REST API
OSMOSIS_LCD = "https://lcd.osmosis.zone"
OSMOSIS_SWAP_POOL_ATOM_AKT = 1  # Pool ID ATOM/OSMO/AKT route

# Akash REST API
AKASH_LCD = "https://rest.cosmos.directory/akash"

# Thresholds
LOW_BALANCE_THRESHOLD_USD = 5.0   # Alert at $5 remaining
CRITICAL_THRESHOLD_USD = 2.0       # Auto-swap at $2 remaining
MIN_SWAP_ATOM = 1.0                # Minimum ATOM to swap

# --- Akash Balance Check -----------------------------------
def get_akash_deployment_balance(dseq: str) -> dict:
    """Get deployment escrow balance from Akash API"""
    try:
        url = f"{AKASH_LCD}/akash/deployment/v1beta3/deployments/info"
        params = {"id.owner": AKASH_WALLET, "id.dseq": dseq}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            escrow = data.get("escrow_account", {})
            balance = escrow.get("balance", {})
            return {
                "denom": balance.get("denom", "uakt"),
                "amount": int(balance.get("amount", 0)),
                "usd": int(balance.get("amount", 0)) / 1_000_000 * get_akt_price()
            }
    except Exception as e:
        log.error(f"Akash balance error: {e}")
    return {"denom": "uakt", "amount": 0, "usd": 0}

# --- Price Feeds -------------------------------------------
def get_akt_price() -> float:
    """Get AKT/USD price from CoinGecko"""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "akash-network", "vs_currencies": "usd"},
            timeout=10
        )
        return r.json().get("akash-network", {}).get("usd", 0.34)
    except Exception:
        return 0.34

def get_atom_price() -> float:
    """Get ATOM/USD price from CoinGecko"""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "cosmos", "vs_currencies": "usd"},
            timeout=10
        )
        return r.json().get("cosmos", {}).get("usd", 6.50)
    except Exception:
        return 6.50

# --- Wallet Balance ----------------------------------------
def get_wallet_atom_balance(address: str) -> float:
    """Get ATOM balance from Cosmos Hub"""
    try:
        COSMOS_LCD = "https://rest.cosmos.directory/cosmoshub"
        r = requests.get(
            f"{COSMOS_LCD}/cosmos/bank/v1beta1/balances/{address}",
            timeout=10
        )
        balances = r.json().get("balances", [])
        for b in balances:
            if b["denom"] == "uatom":
                return int(b["amount"]) / 1_000_000
    except Exception as e:
        log.error(f"ATOM balance error: {e}")
    return 0.0

def get_wallet_akt_balance(address: str) -> float:
    """Get AKT balance from Akash"""
    try:
        r = requests.get(
            f"{AKASH_LCD}/cosmos/bank/v1beta1/balances/{address}",
            timeout=10
        )
        balances = r.json().get("balances", [])
        for b in balances:
            if b["denom"] == "uakt":
                return int(b["amount"]) / 1_000_000
    except Exception as e:
        log.error(f"AKT balance error: {e}")
    return 0.0

# --- HA Notifications --------------------------------------
def notify_ha(message: str, title: str = "S25 Treasury"):
    """Send notification to Home Assistant"""
    if not HA_TOKEN:
        return
    try:
        requests.post(
            f"{HA_URL}/api/services/notify/notify",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json={"title": title, "message": message},
            timeout=5
        )
        # Also update HA entity
        requests.post(
            f"{HA_URL}/api/states/input_text.s25_treasury_status",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json={"state": message[:255]},
            timeout=5
        )
        log.info(f"HA notified: {message}")
    except Exception as e:
        log.error(f"HA notify error: {e}")

# --- Osmosis Swap Quote ------------------------------------
def get_osmosis_swap_quote(atom_amount: float) -> dict:
    """Get swap quote ATOM->AKT via Osmosis"""
    try:
        # Route: ATOM (uatom) -> OSMO -> AKT (uakt)
        # Pool 1: ATOM/OSMO, Pool 2: OSMO/AKT
        uatom_in = int(atom_amount * 1_000_000)
        # SQS (Sidecar Query Server) - Osmosis routing API
        r = requests.get(
            "https://sqs.osmosis.zone/router/quote",
            params={
                "tokenIn": f"{uatom_in}uatom",
                "tokenOutDenom": "uakt",
                "singleRoute": "false"
            },
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            amount_out = int(data.get("amount_out", 0)) / 1_000_000
            return {
                "atom_in": atom_amount,
                "akt_out": amount_out,
                "route": data.get("route", []),
                "price_impact": data.get("price_impact", "unknown")
            }
    except Exception as e:
        log.error(f"Osmosis quote error: {e}")
    # Fallback estimate
    atom_price = get_atom_price()
    akt_price = get_akt_price()
    estimated_akt = (atom_amount * atom_price / akt_price) * 0.99  # 1% slippage
    return {"atom_in": atom_amount, "akt_out": estimated_akt, "route": [], "price_impact": "estimated"}

# --- Treasury Status Report --------------------------------
def get_treasury_status(deployments: list = None) -> dict:
    """Full treasury status report"""
    deployments = deployments or []
    atom_price = get_atom_price()
    akt_price = get_akt_price()
    atom_bal = get_wallet_atom_balance(AKASH_WALLET) if AKASH_WALLET else 0
    akt_bal = get_wallet_akt_balance(AKASH_WALLET) if AKASH_WALLET else 0
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "prices": {"ATOM": atom_price, "AKT": akt_price},
        "wallet": {
            "address": AKASH_WALLET,
            "atom_balance": atom_bal,
            "atom_usd": atom_bal * atom_price,
            "akt_balance": akt_bal,
            "akt_usd": akt_bal * akt_price,
            "total_usd": (atom_bal * atom_price) + (akt_bal * akt_price)
        },
        "deployments": {},
        "alerts": []
    }
    for dseq in deployments:
        bal = get_akash_deployment_balance(str(dseq))
        status["deployments"][dseq] = bal
        if bal["usd"] < CRITICAL_THRESHOLD_USD:
            status["alerts"].append(f"CRITICAL: DSEQ {dseq} = ${bal['usd']:.2f} (<{CRITICAL_THRESHOLD_USD}h)")
        elif bal["usd"] < LOW_BALANCE_THRESHOLD_USD:
            status["alerts"].append(f"LOW: DSEQ {dseq} = ${bal['usd']:.2f}")
    return status

# --- Main Loop ---------------------------------------------
def run_treasury_sentinel(deployments: list = None):
    """
    Main treasury sentinel loop.
    Monitors balances and triggers alerts.

    NOTE: Actual ATOM->AKT swap requires wallet signing.
    This sentinel monitors and notifies HA when action needed.
    For fully automated swaps, deploy on Akash CentOS with wallet key.
    """
    deployments = deployments or ["25708774", "25817341"]
    log.info("S25 Treasury Sentinel starting...")
    while True:
        try:
            status = get_treasury_status(deployments)
            with open("/tmp/s25_treasury_status.json", "w") as f:
                json.dump(status, f, indent=2)
            log.info(f"Treasury: ATOM={status['wallet']['atom_balance']:.3f} "
                    f"AKT={status['wallet']['akt_balance']:.3f} "
                    f"Total=${status['wallet']['total_usd']:.2f}")
            for alert in status["alerts"]:
                log.warning(alert)
                notify_ha(alert, "S25 TREASURY ALERT")
            atom_bal = status["wallet"]["atom_balance"]
            if atom_bal >= MIN_SWAP_ATOM and status["alerts"]:
                quote = get_osmosis_swap_quote(atom_bal)
                log.info(f"Swap quote: {atom_bal:.2f} ATOM -> {quote['akt_out']:.2f} AKT")
                notify_ha(
                    f"Swap available: {atom_bal:.2f} ATOM -> {quote['akt_out']:.2f} AKT\nGo to app.osmosis.zone to execute",
                    "S25 Treasury - Action Required"
                )
        except Exception as e:
            log.error(f"Treasury sentinel error: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    import sys
    if "--status" in sys.argv:
        deployments = ["25708774", "25817341"]
        status = get_treasury_status(deployments)
        print(json.dumps(status, indent=2))
        if status["wallet"]["atom_balance"] > 0:
            quote = get_osmosis_swap_quote(status["wallet"]["atom_balance"])
            print(f"Swap quote: {quote['atom_in']:.2f} ATOM -> {quote['akt_out']:.2f} AKT")
            print(f"   Price impact: {quote['price_impact']}")
    else:
        run_treasury_sentinel()
