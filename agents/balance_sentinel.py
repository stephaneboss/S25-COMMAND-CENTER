#!/usr/bin/env python3
# ============================================================
# S25 LUMIERE - Balance Sentinel
# Multi-chain wallet monitoring: ATOM, AKT, BTC, ETH, SOL
# Integrates with HA + GOUV4 + Treasury Engine
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
log = logging.getLogger("SENTINEL")

HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
AKASH_WALLET = os.getenv("AKASH_WALLET_ADDRESS", "")
MEXC_API_KEY = os.getenv("MEXC_API_KEY", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))  # 5min

CHAINS = {
    "cosmos": {
        "name": "Cosmos Hub (ATOM)",
        "lcd": "https://rest.cosmos.directory/cosmoshub",
        "denom": "uatom",
        "decimals": 6,
        "symbol": "ATOM",
        "coingecko_id": "cosmos"
    },
    "akash": {
        "name": "Akash Network (AKT)",
        "lcd": "https://rest.cosmos.directory/akash",
        "denom": "uakt",
        "decimals": 6,
        "symbol": "AKT",
        "coingecko_id": "akash-network"
    },
    "osmosis": {
        "name": "Osmosis (OSMO)",
        "lcd": "https://rest.cosmos.directory/osmosis",
        "denom": "uosmo",
        "decimals": 6,
        "symbol": "OSMO",
        "coingecko_id": "osmosis"
    }
}

def get_prices(coin_ids: list) -> dict:
    """Batch price fetch from CoinGecko"""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ",".join(coin_ids), "vs_currencies": "usd"},
            timeout=10
        )
        return {k: v.get("usd", 0) for k, v in r.json().items()}
    except Exception:
        return {}

def get_cosmos_balance(lcd: str, address: str, denom: str, decimals: int) -> float:
    """Get balance for any Cosmos SDK chain"""
    try:
        r = requests.get(
            f"{lcd}/cosmos/bank/v1beta1/balances/{address}",
            timeout=10
        )
        for b in r.json().get("balances", []):
            if b["denom"] == denom:
                return int(b["amount"]) / (10 ** decimals)
    except Exception as e:
        log.error(f"Balance error {lcd}: {e}")
    return 0.0

def update_ha_entity(entity_id: str, state: str, attributes: dict = None):
    """Update HA entity state"""
    if not HA_TOKEN:
        return
    try:
        requests.post(
            f"{HA_URL}/api/states/{entity_id}",
            headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
            json={"state": state, "attributes": attributes or {}},
            timeout=5
        )
    except Exception as e:
        log.error(f"HA update error: {e}")

def run_balance_sentinel():
    """Monitor all wallets and push to HA"""
    log.info("S25 Balance Sentinel starting...")
    while True:
        try:
            prices = get_prices([c["coingecko_id"] for c in CHAINS.values()])
            portfolio = {
                "timestamp": datetime.utcnow().isoformat(),
                "chains": {},
                "total_usd": 0
            }
            if AKASH_WALLET:
                for chain_id, chain in CHAINS.items():
                    bal = get_cosmos_balance(
                        chain["lcd"], AKASH_WALLET,
                        chain["denom"], chain["decimals"]
                    )
                    price = prices.get(chain["coingecko_id"], 0)
                    usd_val = bal * price
                    portfolio["chains"][chain_id] = {
                        "symbol": chain["symbol"],
                        "balance": bal,
                        "price_usd": price,
                        "value_usd": usd_val
                    }
                    portfolio["total_usd"] += usd_val
                    log.info(f"{chain['symbol']}: {bal:.4f} (${usd_val:.2f})")
                    # Update HA sensor
                    update_ha_entity(
                        f"sensor.s25_wallet_{chain_id}",
                        f"{bal:.4f}",
                        {"unit_of_measurement": chain['symbol'], "usd_value": round(usd_val, 2)}
                    )
            # Save portfolio
            with open("/tmp/s25_portfolio.json", "w") as f:
                json.dump(portfolio, f, indent=2)
            log.info(f"Portfolio total: ${portfolio['total_usd']:.2f}")
            # Update total in HA
            update_ha_entity(
                "sensor.s25_portfolio_total",
                f"{portfolio['total_usd']:.2f}",
                {"unit_of_measurement": "USD", "chains": list(portfolio['chains'].keys())}
            )
        except Exception as e:
            log.error(f"Sentinel error: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        # Single check and exit
        prices = get_prices([c["coingecko_id"] for c in CHAINS.values()])
        print(json.dumps({"prices": prices, "wallet": AKASH_WALLET}, indent=2))
    else:
        run_balance_sentinel()
