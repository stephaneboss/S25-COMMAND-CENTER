#!/usr/bin/env python3
"""
S25 Coinbase HA Publisher
=========================
Polls the Coinbase executor (portfolio + prices + executor state) and pushes
them to Home Assistant as entity states via the HA REST API.

Why push (not pull): editing HA's configuration.yaml requires filesystem
access to the HA host (denied here). POSTing to /api/states/<entity_id>
creates or updates entities on the fly — they become visible in HA without
any yaml edit.

Entities produced:
  sensor.s25_coinbase_total_usd
  sensor.s25_coinbase_total_cad_fiat
  sensor.s25_coinbase_coin_count
  sensor.s25_btc_spot / s25_eth_spot / s25_akt_spot / s25_sol_spot / s25_atom_spot
  sensor.s25_coinbase_mode           (DRY_RUN | LIVE)
  sensor.s25_coinbase_maker_fee_bps
  sensor.s25_coinbase_taker_fee_bps
  sensor.s25_coinbase_dry_run_orders
  sensor.s25_coinbase_live_orders
  binary_sensor.s25_coinbase_api_healthy
  binary_sensor.s25_coinbase_keys_configured

Run modes:
  python3 -m agents.coinbase_ha_publisher           # one-shot publish then exit
  python3 -m agents.coinbase_ha_publisher --loop 60 # publish every 60s forever
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("s25.coinbase_ha_publisher")


def _ha_config():
    from security.vault import vault_get
    url = (vault_get("HA_URL", os.getenv("HA_URL", "")) or "").rstrip("/")
    token = vault_get("HA_TOKEN", os.getenv("HA_TOKEN", ""))
    if not (url and token):
        raise RuntimeError("HA_URL or HA_TOKEN missing — check vault")
    return url, token


def _post_state(url: str, token: str, entity_id: str, state: Any, attrs: Optional[Dict] = None) -> bool:
    payload = {"state": str(state), "attributes": attrs or {}}
    try:
        r = requests.post(
            f"{url}/api/states/{entity_id}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=6,
        )
        if r.status_code in (200, 201):
            return True
        logger.warning("HA POST %s -> %s: %s", entity_id, r.status_code, r.text[:200])
        return False
    except Exception as e:
        logger.warning("HA POST %s err: %s", entity_id, e)
        return False


def collect_and_publish() -> Dict[str, Any]:
    """Snapshot + push. Returns a summary of pushed entities."""
    from agents.coinbase_executor import get_executor

    url, token = _ha_config()
    exe = get_executor()

    portfolio = exe.get_portfolio()
    fee_tier = exe.get_fee_tier()
    exec_status = exe.exec_status()

    pushed = {}

    # Portfolio
    total_usd = portfolio.get("total_usd", 0) if portfolio.get("ok") else 0
    total_cad = portfolio.get("total_cad_fiat", 0) if portfolio.get("ok") else 0
    coin_count = portfolio.get("coin_count", 0) if portfolio.get("ok") else 0
    pushed["s25_coinbase_total_usd"] = _post_state(
        url, token, "sensor.s25_coinbase_total_usd", total_usd,
        {"unit_of_measurement": "USD", "friendly_name": "S25 Coinbase Total USD", "icon": "mdi:cash-multiple", "coins": portfolio.get("coins", [])},
    )
    pushed["s25_coinbase_total_cad_fiat"] = _post_state(
        url, token, "sensor.s25_coinbase_total_cad_fiat", total_cad,
        {"unit_of_measurement": "CAD", "friendly_name": "S25 Coinbase CAD Fiat", "icon": "mdi:cash"},
    )
    pushed["s25_coinbase_coin_count"] = _post_state(
        url, token, "sensor.s25_coinbase_coin_count", coin_count,
        {"friendly_name": "S25 Coinbase Coin Count", "icon": "mdi:currency-usd"},
    )
    pushed["binary_sensor.s25_coinbase_api_healthy"] = _post_state(
        url, token, "binary_sensor.s25_coinbase_api_healthy",
        "on" if portfolio.get("ok") else "off",
        {"friendly_name": "S25 Coinbase API Healthy", "device_class": "connectivity"},
    )

    # Spot prices for each whitelisted product
    for product in sorted(exe.allowed_products):
        base = product.split("-")[0].lower()
        price = exe.get_product_price(product)
        entity = f"sensor.s25_{base}_spot"
        pushed[entity] = _post_state(
            url, token, entity, price if price else 0,
            {"unit_of_measurement": "USD", "friendly_name": f"S25 {base.upper()} Spot", "icon": "mdi:chart-line", "product_id": product},
        )

    # Fee tier
    maker_bps = int(float(fee_tier.get("maker_fee") or 0) * 10000)
    taker_bps = int(float(fee_tier.get("taker_fee") or 0) * 10000)
    pushed["sensor.s25_coinbase_maker_fee_bps"] = _post_state(
        url, token, "sensor.s25_coinbase_maker_fee_bps", maker_bps,
        {"unit_of_measurement": "bps", "friendly_name": "S25 Coinbase Maker Fee", "tier": fee_tier.get("tier_name")},
    )
    pushed["sensor.s25_coinbase_taker_fee_bps"] = _post_state(
        url, token, "sensor.s25_coinbase_taker_fee_bps", taker_bps,
        {"unit_of_measurement": "bps", "friendly_name": "S25 Coinbase Taker Fee", "tier": fee_tier.get("tier_name")},
    )

    # Executor state
    pushed["sensor.s25_coinbase_mode"] = _post_state(
        url, token, "sensor.s25_coinbase_mode",
        "DRY_RUN" if exec_status.get("dry_run") else "LIVE",
        {"friendly_name": "S25 Coinbase Mode", "icon": "mdi:shield-check" if exec_status.get("dry_run") else "mdi:rocket-launch", "max_usd_per_trade": exec_status.get("max_usd_per_trade")},
    )
    pushed["sensor.s25_coinbase_dry_run_orders"] = _post_state(
        url, token, "sensor.s25_coinbase_dry_run_orders", exec_status.get("dry_run_orders", 0),
        {"friendly_name": "S25 Coinbase Dry-Run Orders", "icon": "mdi:counter"},
    )
    pushed["sensor.s25_coinbase_live_orders"] = _post_state(
        url, token, "sensor.s25_coinbase_live_orders", exec_status.get("orders_placed", 0),
        {"friendly_name": "S25 Coinbase Live Orders", "icon": "mdi:counter"},
    )
    pushed["binary_sensor.s25_coinbase_keys_configured"] = _post_state(
        url, token, "binary_sensor.s25_coinbase_keys_configured",
        "on" if exec_status.get("api_key_configured") else "off",
        {"friendly_name": "S25 Coinbase Keys Configured", "device_class": "connectivity"},
    )

    ok_count = sum(1 for v in pushed.values() if v)
    logger.info("published %d/%d entities to HA", ok_count, len(pushed))
    return {"ok": True, "published": ok_count, "total": len(pushed), "entities": list(pushed.keys())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", type=int, default=0, help="Seconds between pushes, 0 = one-shot")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.loop <= 0:
        result = collect_and_publish()
        import json
        print(json.dumps(result, indent=2))
        return 0

    logger.info("looping every %ds (Ctrl-C to stop)", args.loop)
    while True:
        try:
            collect_and_publish()
        except Exception as e:
            logger.error("publish cycle failed: %s", e)
        time.sleep(args.loop)


if __name__ == "__main__":
    sys.exit(main())
