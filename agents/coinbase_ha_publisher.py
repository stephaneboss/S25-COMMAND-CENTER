#!/usr/bin/env python3
"""
S25 Coinbase HA Publisher
=========================
Polls the cockpit's Coinbase endpoints (portfolio + prices + exec status)
and pushes each field to Home Assistant as an entity state via the HA
REST API.

Why we hit the cockpit (not the SDK directly): cron's environment has no
DBus session, so gnome-keyring reads fail — but the cockpit runs as a
user-level systemd service with DBus access, so it successfully reads
the keyring on behalf of cron.

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
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("s25.coinbase_ha_publisher")

COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")


def _env_file_get(key: str) -> Optional[str]:
    """Read a value from ../.env when keyring is unavailable (cron env)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return None
    try:
        for line in env_path.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def _ha_config():
    url = os.getenv("HA_URL") or _env_file_get("HA_URL") or "http://10.0.0.136:8123"
    token = os.getenv("HA_TOKEN") or _env_file_get("HA_TOKEN") or ""
    if not (url and token):
        raise RuntimeError("HA_URL or HA_TOKEN missing from env + .env")
    return url.rstrip("/"), token


def _post_state(url: str, token: str, entity_id: str, state: Any, attrs: Optional[Dict] = None) -> bool:
    try:
        r = requests.post(
            f"{url}/api/states/{entity_id}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"state": str(state), "attributes": attrs or {}},
            timeout=6,
        )
        return r.status_code in (200, 201)
    except Exception as e:
        logger.warning("HA POST %s err: %s", entity_id, e)
        return False


def _cockpit_get(path: str, timeout: float = 6.0) -> Dict[str, Any]:
    try:
        r = requests.get(f"{COCKPIT}{path}", timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return {"ok": False, "error": f"http_{r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def collect_and_publish() -> Dict[str, Any]:
    url, token = _ha_config()

    portfolio = _cockpit_get("/api/coinbase/portfolio")
    fee_tier = _cockpit_get("/api/coinbase/fee-tier")
    exec_status = _cockpit_get("/api/trading/coinbase/status")
    spot = _cockpit_get("/api/coinbase/spot-prices")
    pnl = _cockpit_get("/api/trading/pnl")
    strat_data = _cockpit_get("/api/trading/strategies")

    pushed = {}

    # Portfolio
    ok_p = portfolio.get("ok", False)
    pushed["sensor.s25_coinbase_total_usd"] = _post_state(
        url, token, "sensor.s25_coinbase_total_usd",
        portfolio.get("total_usd", 0) if ok_p else 0,
        {"unit_of_measurement": "USD", "friendly_name": "S25 Coinbase Total USD", "icon": "mdi:cash-multiple", "coins": portfolio.get("coins", [])},
    )
    pushed["sensor.s25_coinbase_total_cad_fiat"] = _post_state(
        url, token, "sensor.s25_coinbase_total_cad_fiat",
        portfolio.get("total_cad_fiat", 0) if ok_p else 0,
        {"unit_of_measurement": "CAD", "friendly_name": "S25 Coinbase CAD Fiat", "icon": "mdi:cash"},
    )
    pushed["sensor.s25_coinbase_coin_count"] = _post_state(
        url, token, "sensor.s25_coinbase_coin_count",
        portfolio.get("coin_count", 0) if ok_p else 0,
        {"friendly_name": "S25 Coinbase Coin Count", "icon": "mdi:currency-usd"},
    )
    pushed["binary_sensor.s25_coinbase_api_healthy"] = _post_state(
        url, token, "binary_sensor.s25_coinbase_api_healthy",
        "on" if ok_p else "off",
        {"friendly_name": "S25 Coinbase API Healthy", "device_class": "connectivity"},
    )

    # Spot prices
    prices = spot.get("prices", {}) if spot.get("ok") else {}
    for product, price in prices.items():
        base = product.split("-")[0].lower()
        pushed[f"sensor.s25_{base}_spot"] = _post_state(
            url, token, f"sensor.s25_{base}_spot", price if price else 0,
            {"unit_of_measurement": "USD", "friendly_name": f"S25 {base.upper()} Spot", "icon": "mdi:chart-line", "product_id": product},
        )

    # Fee tier
    if fee_tier.get("ok"):
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

    # Exec status
    if exec_status.get("ok"):
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

    # P&L sensors
    if pnl.get("ok"):
        pushed["sensor.s25_trading_total_pnl"] = _post_state(
            url, token, "sensor.s25_trading_total_pnl",
            round(float(pnl.get("total_pnl") or 0), 4),
            {"unit_of_measurement": "USD", "friendly_name": "S25 Total P&L", "icon": "mdi:chart-line-variant",
             "realized": pnl.get("realized_pnl_total"), "unrealized": pnl.get("unrealized_pnl_total")},
        )
        pushed["sensor.s25_trading_realized_pnl"] = _post_state(
            url, token, "sensor.s25_trading_realized_pnl",
            round(float(pnl.get("realized_pnl_total") or 0), 4),
            {"unit_of_measurement": "USD", "friendly_name": "S25 Realized P&L", "icon": "mdi:cash-check"},
        )
        pushed["sensor.s25_trading_unrealized_pnl"] = _post_state(
            url, token, "sensor.s25_trading_unrealized_pnl",
            round(float(pnl.get("unrealized_pnl_total") or 0), 4),
            {"unit_of_measurement": "USD", "friendly_name": "S25 Unrealized P&L", "icon": "mdi:chart-timeline-variant"},
        )
        wr = pnl.get("win_rate_pct")
        pushed["sensor.s25_trading_win_rate"] = _post_state(
            url, token, "sensor.s25_trading_win_rate",
            wr if wr is not None else "unknown",
            {"unit_of_measurement": "%", "friendly_name": "S25 Win Rate", "icon": "mdi:trophy",
             "realized_trades": pnl.get("realized_trades_count"),
             "avg_win_usd": pnl.get("avg_win_usd"),
             "avg_loss_usd": pnl.get("avg_loss_usd")},
        )
        pushed["sensor.s25_trading_open_positions"] = _post_state(
            url, token, "sensor.s25_trading_open_positions",
            int(pnl.get("open_position_count") or 0),
            {"friendly_name": "S25 Open Positions", "icon": "mdi:briefcase-variant"},
        )

    # Strategies
    if strat_data.get("ok"):
        strategies = strat_data.get("strategies", [])
        pushed["sensor.s25_strategies_total"] = _post_state(
            url, token, "sensor.s25_strategies_total", len(strategies),
            {"friendly_name": "S25 Strategies Total", "icon": "mdi:robot"},
        )
        pushed["sensor.s25_strategies_enabled"] = _post_state(
            url, token, "sensor.s25_strategies_enabled",
            sum(1 for s in strategies if s.get("enabled")),
            {"friendly_name": "S25 Strategies Enabled", "icon": "mdi:robot-happy"},
        )
        for s in strategies:
            ent = f"sensor.s25_strategy_{s['name']}"
            pushed[ent] = _post_state(
                url, token, ent,
                "ON" if s.get("enabled") else "OFF",
                {
                    "friendly_name": f"Strategy {s['name']}",
                    "description": s.get("description"),
                    "usd_size": s.get("usd_size"),
                    "total_signals": s.get("total_signals"),
                    "last_signal_symbol": s.get("last_signal_symbol"),
                    "last_signal_action": s.get("last_signal_action"),
                },
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
        import json
        print(json.dumps(collect_and_publish(), indent=2))
        return 0
    logger.info("looping every %ds", args.loop)
    while True:
        try:
            collect_and_publish()
        except Exception as e:
            logger.error("publish cycle failed: %s", e)
        time.sleep(args.loop)


if __name__ == "__main__":
    sys.exit(main())
