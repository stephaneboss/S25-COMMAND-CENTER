#!/usr/bin/env python3

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from agents.cockpit_client import CockpitClient
from agents.treasury_engine import (
    CRITICAL_THRESHOLD_USD,
    LOW_BALANCE_THRESHOLD_USD,
    get_osmosis_swap_quote,
    get_treasury_status,
)


log = logging.getLogger("s25.treasury_autopilot")

POLL_SECONDS = int(os.getenv("TREASURY_POLL_SECONDS", "900"))
DEPLOYMENTS = [item.strip() for item in os.getenv("TREASURY_DEPLOYMENTS", "25708774,25817341").split(",") if item.strip()]
AUTOMISSION = os.getenv("TREASURY_AUTOMISSION", "true").lower() in {"1", "true", "yes", "on"}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_summary(status: dict) -> str:
    wallet = status.get("wallet", {})
    return (
        f"Treasury tick. ATOM={wallet.get('atom_balance', 0):.3f} "
        f"AKT={wallet.get('akt_balance', 0):.3f} "
        f"Total=${wallet.get('total_usd', 0):.2f} "
        f"Alerts={len(status.get('alerts', []))}"
    )


def main() -> None:
    logging.basicConfig(level=os.getenv("TREASURY_LOG_LEVEL", "INFO"))
    client = CockpitClient()
    log.info("Starting treasury autopilot every %ss for deployments=%s", POLL_SECONDS, DEPLOYMENTS)

    while True:
        try:
            status = get_treasury_status(DEPLOYMENTS)
            quote = None
            atom_balance = status.get("wallet", {}).get("atom_balance", 0) or 0
            if atom_balance > 0:
                quote = get_osmosis_swap_quote(atom_balance)

            intel_payload = {
                "treasury_status": {
                    "ts": _utcnow_iso(),
                    "summary": _build_summary(status),
                    "status": status,
                    "quote": quote,
                }
            }
            client.heartbeat("TREASURY", note="autopilot tick")
            client.update_state(
                "TRINITY",
                updates={"last_treasury_tick": _utcnow_iso()},
                intel=intel_payload,
            )

            if AUTOMISSION:
                for alert in status.get("alerts", []):
                    priority = "critical" if "CRITICAL" in alert else "high"
                    result = client.create_mission(
                        created_by="TREASURY_AUTOPILOT",
                        target="COMET",
                        task_type="infra_monitoring",
                        intent=f"Treasury alert detected: {alert}. Review AKT funding and swap path.",
                        priority=priority,
                        context={
                            "kind": "treasury_alert",
                            "thresholds": {
                                "low_usd": LOW_BALANCE_THRESHOLD_USD,
                                "critical_usd": CRITICAL_THRESHOLD_USD,
                            },
                            "deployments": DEPLOYMENTS,
                            "quote": quote,
                        },
                    )
                    log.info("Treasury mission result: %s", result)
        except Exception as exc:
            log.warning("Treasury autopilot tick failed: %s", exc)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
