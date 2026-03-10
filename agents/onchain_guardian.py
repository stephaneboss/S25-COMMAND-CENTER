#!/usr/bin/env python3

import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from agents.cockpit_client import CockpitClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GUARDIAN] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("/tmp/onchain_guardian.log", mode="a")],
)
log = logging.getLogger("s25.guardian")

POLL_SECONDS = int(os.getenv("ONCHAIN_POLL_SECONDS", "420"))
TOKENS = [item.strip() for item in os.getenv("ONCHAIN_TOKEN_LIST", "").split(",") if item.strip()]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_dexscreener(token: str) -> Optional[Dict[str, object]]:
    response = requests.get(
        f"https://api.dexscreener.com/latest/dex/tokens/{token}",
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    pairs = payload.get("pairs") or []
    if not pairs:
        return None
    pairs.sort(key=lambda pair: pair.get("liquidity", {}).get("usd", 0) or 0, reverse=True)
    best = pairs[0]
    return {
        "token": token,
        "chain": best.get("chainId"),
        "dex": best.get("dexId"),
        "price_usd": best.get("priceUsd"),
        "liquidity_usd": best.get("liquidity", {}).get("usd"),
        "volume_24h": best.get("volume", {}).get("h24"),
        "price_change_24h": best.get("priceChange", {}).get("h24"),
        "fdv": best.get("fdv"),
        "pair_address": best.get("pairAddress"),
        "url": best.get("url"),
    }


def classify_risk(snapshot: Dict[str, object]) -> Dict[str, object]:
    risk_flags: List[str] = []
    liquidity = float(snapshot.get("liquidity_usd") or 0)
    price_change = float(snapshot.get("price_change_24h") or 0)

    if liquidity and liquidity < 50000:
        risk_flags.append("low_liquidity")
    if abs(price_change) > 40:
        risk_flags.append("extreme_price_move")

    if not risk_flags:
        score = 8.5
        verdict = "MONITOR"
    elif len(risk_flags) == 1:
        score = 6.0
        verdict = "CAUTION"
    else:
        score = 3.5
        verdict = "HIGH_RISK"

    return {
        "token": snapshot["token"],
        "safety_score": score,
        "verdict": verdict,
        "risk_flags": risk_flags,
        "snapshot": snapshot,
        "updated_at": utcnow(),
    }


def scan_tokens(tokens: List[str]) -> Dict[str, Dict[str, object]]:
    reports: Dict[str, Dict[str, object]] = {}
    for token in tokens:
        try:
            snapshot = fetch_dexscreener(token)
            if snapshot:
                reports[token] = classify_risk(snapshot)
        except Exception as exc:
            log.warning("guardian fetch failed for %s: %s", token, exc)
    return reports


def update_active_guardian_missions(client: CockpitClient, reports: Dict[str, Dict[str, object]]):
    missions = client.get_missions() or {}
    for mission in missions.get("active", []):
        if mission.get("target") != "ONCHAIN_GUARDIAN":
            continue
        token = str(mission.get("context", {}).get("token") or "")
        result = reports.get(token) if token else {"tokens": list(reports.keys()), "reports": reports}
        status = "active" if result else "failed"
        client.update_mission(
            mission_id=mission["mission_id"],
            status=status,
            actor="ONCHAIN_GUARDIAN",
            result=result or {"error": "token_not_found"},
            context={"last_guardian_run": utcnow()},
        )


def main():
    client = CockpitClient()
    log.info("onchain-guardian started for %s tracked tokens", len(TOKENS))

    while True:
        reports = scan_tokens(TOKENS)
        latest = next(iter(reports.values()), None)

        client.heartbeat("ONCHAIN_GUARDIAN", note=f"tracked={len(reports)}")
        client.update_state(
            "ONCHAIN_GUARDIAN",
            updates={
                "status": "online" if reports else "standby",
                "last_report": utcnow(),
                "notes": f"{len(reports)} token reports available",
            },
            intel={"onchain_guardian_latest": latest, "onchain_guardian_reports": reports},
        )
        update_active_guardian_missions(client, reports)

        if latest:
            log.info("guardian latest verdict=%s token=%s", latest["verdict"], latest["token"])
        else:
            log.info("guardian cycle completed with no tracked tokens configured")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
