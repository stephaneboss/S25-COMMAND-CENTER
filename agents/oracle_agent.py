#!/usr/bin/env python3

import logging
import os
import statistics
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from agents.cockpit_client import CockpitClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ORACLE] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("/tmp/oracle_agent.log", mode="a")],
)
log = logging.getLogger("s25.oracle")

POLL_SECONDS = int(os.getenv("ORACLE_POLL_SECONDS", "300"))
SYMBOLS = [symbol.strip().upper() for symbol in os.getenv("ORACLE_SYMBOLS", "BTC,ETH,AKT,ATOM").split(",") if symbol.strip()]
COINGECKO_IDS = {"BTC": "bitcoin", "ETH": "ethereum", "AKT": "akash-network", "ATOM": "cosmos"}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_binance(symbol: str) -> Optional[float]:
    response = requests.get(
        "https://api.binance.com/api/v3/ticker/price",
        params={"symbol": f"{symbol}USDT"},
        timeout=10,
    )
    response.raise_for_status()
    return float(response.json()["price"])


def fetch_mexc(symbol: str) -> Optional[float]:
    response = requests.get(
        "https://api.mexc.com/api/v3/ticker/price",
        params={"symbol": f"{symbol}USDT"},
        timeout=10,
    )
    response.raise_for_status()
    return float(response.json()["price"])


def fetch_coingecko(symbol: str) -> Optional[float]:
    coin_id = COINGECKO_IDS.get(symbol)
    if not coin_id:
        return None
    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": coin_id, "vs_currencies": "usd"},
        timeout=10,
    )
    response.raise_for_status()
    return float(response.json()[coin_id]["usd"])


def collect_prices(symbol: str) -> Dict[str, float]:
    prices: Dict[str, float] = {}
    for source, fn in (
        ("binance", fetch_binance),
        ("mexc", fetch_mexc),
        ("coingecko", fetch_coingecko),
    ):
        try:
            value = fn(symbol)
            if value:
                prices[source] = value
        except Exception as exc:
            log.warning("%s %s fetch failed: %s", symbol, source, exc)
    return prices


def validate_prices(symbol: str) -> Optional[Dict[str, object]]:
    prices = collect_prices(symbol)
    if len(prices) < 2:
        return None

    values: List[float] = list(prices.values())
    median_price = statistics.median(values)
    max_dev_pct = max(abs(price - median_price) / median_price * 100 for price in values)
    confidence = max(0.0, 1.0 - (max_dev_pct / 2.0))
    flags = []
    if max_dev_pct > 0.5:
        flags.append("oracle_drift")
    if max_dev_pct > 2.0:
        flags.append("manipulation_suspected")

    return {
        "asset": f"{symbol}/USDT",
        "validated_price": round(median_price, 6),
        "confidence": round(confidence, 4),
        "sources_checked": len(prices),
        "prices": prices,
        "max_deviation_pct": round(max_dev_pct, 4),
        "manipulation_flags": flags,
        "s25_signal": "PRICE_VALID" if not flags else "PRICE_CAUTION",
        "updated_at": utcnow(),
    }


def update_active_oracle_missions(client: CockpitClient, snapshot: Dict[str, Dict[str, object]]):
    missions = client.get_missions() or {}
    for mission in missions.get("active", []):
        if mission.get("target") != "ORACLE":
            continue
        symbol = str(mission.get("context", {}).get("symbol") or "").upper()
        result = snapshot.get(symbol) if symbol else {"symbols": list(snapshot.keys()), "reports": snapshot}
        client.update_mission(
            mission_id=mission["mission_id"],
            status="active",
            actor="ORACLE",
            result=result,
            context={"last_oracle_run": utcnow()},
        )


def main():
    client = CockpitClient()
    log.info("oracle-agent started for symbols=%s", ",".join(SYMBOLS))

    while True:
        reports: Dict[str, Dict[str, object]] = {}
        for symbol in SYMBOLS:
            report = validate_prices(symbol)
            if report:
                reports[symbol] = report

        if reports:
            first_symbol = next(iter(reports))
            first_report = reports[first_symbol]
            client.heartbeat("ORACLE", note=f"validated {len(reports)} assets")
            client.update_state(
                "ORACLE",
                updates={
                    "status": "online",
                    "last_report": utcnow(),
                    "notes": f"{len(reports)} assets validates",
                },
                market={
                    "last_fetch": utcnow(),
                    "oracle_reports": reports,
                    "btc_usd": reports.get("BTC", {}).get("validated_price"),
                    "eth_usd": reports.get("ETH", {}).get("validated_price"),
                },
                intel={"oracle_latest": first_report},
            )
            update_active_oracle_missions(client, reports)
            log.info("validated %s assets; first=%s", len(reports), first_report["asset"])
        else:
            client.update_state(
                "ORACLE",
                updates={"status": "degraded", "last_report": utcnow(), "notes": "no sufficient price quorum"},
            )
            log.warning("no valid oracle report this cycle")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
