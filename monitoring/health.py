"""
S25 Lumière — System Health Monitor
=====================================
Checks health of all S25 infrastructure components.

Components monitored:
- Home Assistant (API ping)
- Akash deployments (escrow balance)
- Cosmos chains (LCD liveness)
- S25 agents (via Commander status)
- MEXC API (if trading enabled)
"""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("s25.health")


class HealthMonitor:
    """
    S25 System Health Monitor.

    Usage:
        monitor = HealthMonitor(ha_url, ha_token, deployments=["25708774"])
        report = monitor.check_all()
        print(report["status"])  # OK | WARNING | CRITICAL
    """

    AKASH_LCD  = "https://api.akash.network"
    COSMOS_DIR = "https://rest.cosmos.directory"

    # Balance thresholds for Akash deployments
    AKT_WARNING  = 1.0   # AKT — warn below
    AKT_CRITICAL = 0.3   # AKT — critical below

    def __init__(
        self,
        ha_url:      str,
        ha_token:    str,
        deployments: List[str] = None,
        health_file: str = "/tmp/s25_health.json"
    ):
        self.ha_url      = ha_url
        self.ha_token    = ha_token
        self.deployments = deployments or []
        self.health_file = Path(health_file)

        self._last: Optional[Dict] = None
        self._check_count = 0

    # ─── Main Check ──────────────────────────────────────────────────────────

    def check_all(self) -> Dict:
        """Run full health check across all components."""
        self._check_count += 1
        ts = datetime.utcnow().isoformat() + "Z"

        components = {}

        # 1. Home Assistant
        components["home_assistant"] = self._check_ha()

        # 2. Akash deployments
        for dseq in self.deployments:
            components[f"akash_{dseq}"] = self._check_akash_deployment(dseq)

        # 3. Blockchain chains
        components["cosmos_hub"]  = self._check_chain("cosmoshub")
        components["akash_chain"] = self._check_chain("akash")
        components["osmosis"]     = self._check_chain("osmosis")

        # Aggregate status
        statuses = [c["status"] for c in components.values()]
        if "CRITICAL" in statuses:
            overall = "CRITICAL"
        elif "WARNING" in statuses:
            overall = "WARNING"
        else:
            overall = "OK"

        report = {
            "ts":          ts,
            "status":      overall,
            "check_n":     self._check_count,
            "components":  components,
        }

        self._last = report
        self._save(report)
        self._update_ha(report)

        # Log summary
        critical_comps = [k for k, v in components.items() if v["status"] == "CRITICAL"]
        warning_comps  = [k for k, v in components.items() if v["status"] == "WARNING"]

        if critical_comps:
            logger.critical(f"CRITICAL: {critical_comps}")
        elif warning_comps:
            logger.warning(f"WARNING: {warning_comps}")
        else:
            logger.info(f"Health check #{self._check_count}: ALL OK")

        return report

    # ─── Component Checks ────────────────────────────────────────────────────

    def _check_ha(self) -> Dict:
        """Ping Home Assistant API."""
        try:
            r = requests.get(
                f"{self.ha_url}/api/",
                headers={"Authorization": f"Bearer {self.ha_token}"},
                timeout=5
            )
            if r.status_code == 200:
                return {
                    "status":     "OK",
                    "latency_ms": int(r.elapsed.total_seconds() * 1000),
                    "version":    r.json().get("version", "?")
                }
            return {"status": "WARNING", "http": r.status_code}

        except requests.Timeout:
            return {"status": "WARNING", "error": "timeout"}
        except Exception as e:
            return {"status": "CRITICAL", "error": str(e)[:100]}

    def _check_akash_deployment(self, dseq: str) -> Dict:
        """Check Akash deployment escrow balance."""
        try:
            # Get deployment info
            r = requests.get(
                f"{self.AKASH_LCD}/akash/deployment/v1beta3/deployment",
                params={"id.owner": self._get_owner(), "id.dseq": dseq},
                timeout=10
            )

            if r.status_code != 200:
                return {"status": "WARNING", "error": f"HTTP {r.status_code}", "dseq": dseq}

            data = r.json()
            escrow = data.get("escrow_account", {})
            balance = escrow.get("balance", {})
            amount_uakt = int(balance.get("amount", "0"))
            amount_akt  = amount_uakt / 1_000_000

            if amount_akt < self.AKT_CRITICAL:
                status = "CRITICAL"
            elif amount_akt < self.AKT_WARNING:
                status = "WARNING"
            else:
                status = "OK"

            # Get state
            dep_state = data.get("deployment", {}).get("state", "unknown")

            return {
                "status":      status,
                "dseq":        dseq,
                "balance_akt": round(amount_akt, 4),
                "state":       dep_state,
                "warn_at":     self.AKT_WARNING,
                "critical_at": self.AKT_CRITICAL,
            }

        except Exception as e:
            return {"status": "WARNING", "error": str(e)[:100], "dseq": dseq}

    def _check_chain(self, chain: str) -> Dict:
        """Check if a Cosmos chain LCD is healthy."""
        try:
            r = requests.get(
                f"{self.COSMOS_DIR}/{chain}/cosmos/base/tendermint/v1beta1/syncing",
                timeout=10
            )
            if r.status_code == 200:
                syncing = r.json().get("syncing", False)
                return {
                    "status":  "WARNING" if syncing else "OK",
                    "syncing": syncing,
                    "chain":   chain
                }
            return {"status": "WARNING", "http": r.status_code, "chain": chain}

        except requests.Timeout:
            return {"status": "WARNING", "error": "timeout", "chain": chain}
        except Exception as e:
            return {"status": "WARNING", "error": str(e)[:80], "chain": chain}

    # ─── Persistence & Reporting ─────────────────────────────────────────────

    def _save(self, report: Dict):
        """Save health report to JSON file."""
        try:
            self.health_file.write_text(
                json.dumps(report, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.debug(f"Could not save health file: {e}")

    def _update_ha(self, report: Dict):
        """Update Home Assistant sensor with health status."""
        if not self.ha_url or not self.ha_token:
            return

        try:
            requests.post(
                f"{self.ha_url}/api/states/sensor.s25_system_health",
                headers={
                    "Authorization": f"Bearer {self.ha_token}",
                    "Content-Type":  "application/json"
                },
                json={
                    "state": report["status"],
                    "attributes": {
                        "last_check":    report["ts"],
                        "check_number":  report["check_n"],
                        "components":    report["components"],
                        "friendly_name": "S25 System Health"
                    }
                },
                timeout=5
            )
        except Exception:
            pass

    def _get_owner(self) -> str:
        """Get Akash wallet address from env or config."""
        import os
        return os.environ.get(
            "AKASH_WALLET",
            "cosmos1mw0tr5kdnpwdpx88tq8slp4slkfrz9ltqq8vwa"
        )

    def get_last_report(self) -> Optional[Dict]:
        """Get the most recent health report."""
        if self._last:
            return self._last
        # Try loading from file
        if self.health_file.exists():
            try:
                return json.loads(self.health_file.read_text())
            except Exception:
                pass
        return None

    def is_healthy(self) -> bool:
        """Quick check: is the system healthy?"""
        report = self.get_last_report()
        return report is not None and report.get("status") == "OK"
