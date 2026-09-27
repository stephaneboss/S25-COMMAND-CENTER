#!/usr/bin/env python3
"""
S25 Mesh Heartbeat Cron — Boucle vitale (Trinity spec)
========================================================
Runs every 1 min. For each local cron-based agent, checks its /tmp log mtime
and sends a /api/mesh/report_health heartbeat with derived status:
  - online    : log age < 2× expected cron interval
  - degraded  : 2× ≤ age < 4× (2 missed heartbeats)
  - offline   : age ≥ 4× expected interval (4+ missed)

Reports cockpit HTTP availability separately. Neither probe verifies task success.

Per Trinity architecture spec:
  "heartbeat agent: toutes les 30s
   agent déclaré degraded: après 2 heartbeats manqués
   agent déclaré offline: après 4 heartbeats manqués"
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict

import requests

logger = logging.getLogger("s25.mesh_heartbeat")

REPO = Path(__file__).resolve().parent.parent
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")
# report_health requires X-S25-Secret once S25_SHARED_SECRET is set (since 2026-09-13);
# without it every heartbeat got 401 and the mesh fell to 1/14 online.
_SECRET = os.getenv("S25_SHARED_SECRET", "")
HEADERS = {"X-S25-Secret": _SECRET} if _SECRET else {}

# agent_id -> (log_path, expected_interval_sec, type, runtime, capabilities)
LOCAL_AGENTS: Dict[str, Dict] = {
    "coinbase_ha_publisher": {
        "log": "/tmp/coinbase_ha_publisher.log", "interval": 60,
        "type": "infra", "runtime": "local",
        "capabilities": ["ha_state_push", "coinbase_portfolio"],
    },
    "mesh_signal_bridge": {
        "log": "/tmp/mesh_bridge.log", "interval": 120,
        "type": "signal", "runtime": "local",
        "capabilities": ["signal_relay", "mesh_routing"],
    },
    "trailing_stop_manager": {
        "log": "/tmp/trailing_stop.log", "interval": 180,
        "type": "exec", "runtime": "local",
        "capabilities": ["bracket_update", "trailing_stops"],
    },
    "auto_signal_scanner": {
        "log": "/tmp/auto_signal_scanner.log", "interval": 300,
        "type": "signal", "runtime": "local",
        "capabilities": ["strategy_scan", "multi_coin"],
    },
    "comet_sentiment": {
        "log": "/tmp/comet_sentiment.log", "interval": 600,
        "type": "intel", "runtime": "local",
        "capabilities": ["sentiment_scan", "comet_proxy"],
    },
    "drawdown_guardian": {
        "log": "/tmp/drawdown.log", "interval": 600,
        "type": "risk", "runtime": "local",
        "capabilities": ["drawdown_24h_rolling", "kill_switch_trigger"],
    },
    "dca_scheduler": {
        "log": "/tmp/dca_scheduler.log", "interval": 900,
        "type": "exec", "runtime": "local",
        "capabilities": ["dca_schedules"],
    },
    "quant_brain": {
        "log": "/tmp/quant_brain.log", "interval": 3600,
        "type": "brain", "runtime": "local",
        "capabilities": ["auto_tune_strategies", "re_enable_rules",
                          "trading_analysis", "strategy_planning"],
    },
    "system_health": {
        "log": "/tmp/system_health.log", "interval": 300,
        "type": "infra", "runtime": "local",
        "capabilities": ["cron_monitor", "endpoint_health"],
    },
    "git_auto_sync": {
        "log": "/tmp/git_sync.log", "interval": 1800,
        "type": "infra", "runtime": "local",
        "capabilities": ["git_pull"],
    },
    "perplexity_news_scanner": {
        "log": "/tmp/perplexity_news.log", "interval": 1800,
        "type": "intel", "runtime": "local",
        "capabilities": ["market_news", "sentiment_scan", "perplexity_api"],
    },
}


def derive_status(log_path: Path, interval_sec: int) -> tuple[str, int | None]:
    """Return log-activity status and age in milliseconds, never request latency."""
    if interval_sec <= 0:
        raise ValueError("interval_sec must be positive")
    try:
        age = time.time() - log_path.stat().st_mtime
    except OSError:
        return "offline", None
    # A future timestamp is not evidence of a healthy cron.
    if age < 0:
        return "degraded", None
    if age < 2 * interval_sec:
        return "online", int(age * 1000)
    if age < 4 * interval_sec:
        return "degraded", int(age * 1000)
    return "offline", int(age * 1000)


def build_heartbeat(agent_id: str, meta: Dict) -> Dict:
    """Separate observed log activity from unmeasured operational success."""
    status, log_age_ms = derive_status(Path(meta["log"]), meta["interval"])
    return {
        "agent_id": agent_id,
        "type": meta["type"],
        "status": status,
        "runtime": meta["runtime"],
        "capabilities": meta["capabilities"],
        "latency_ms": None,
        "error_rate": None,
        # Retained for compatibility; this is only the legacy activity score.
        "reliability_score": 1.0 if status == "online" else (0.5 if status == "degraded" else 0.0),
        "metadata": {
            "health_basis": "log_mtime",
            "log_age_ms": log_age_ms,
            "expected_interval_sec": meta["interval"],
            "operational_status": "unknown",
            "task_success_verified": False,
            "reliability_score_basis": "log_activity_only",
        },
    }


def post_heartbeat(agent_id: str, meta: Dict):
    payload = build_heartbeat(agent_id, meta)
    status = payload["status"]
    try:
        r = requests.post(f"{COCKPIT}/api/mesh/report_health",
                          json=payload, headers=HEADERS, timeout=5)
        ok = r.status_code == 200
        if r.status_code == 401:
            logger.error("heartbeat REFUSED (401) for %s: S25_SHARED_SECRET missing or wrong in env", agent_id)
    except Exception as e:
        ok = False
        logger.warning("heartbeat POST failed for %s: %s", agent_id, e)
    logger.info("%s → %s (log_age_ms=%s, task_success=unknown, pushed=%s)",
                agent_id, status, payload["metadata"]["log_age_ms"], ok)
    return status


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info("=== mesh heartbeat tick (%d agents) ===", len(LOCAL_AGENTS))
    summary = {"online": 0, "degraded": 0, "offline": 0}
    for agent_id, meta in LOCAL_AGENTS.items():
        try:
            s = post_heartbeat(agent_id, meta)
            summary[s] = summary.get(s, 0) + 1
        except Exception as e:
            logger.warning("heartbeat error %s: %s", agent_id, e)

    logger.info("summary: %s", summary)
    # Report cockpit HTTP availability, not TRINITY execution or pipeline health
    try:
        r = requests.get(f"{COCKPIT}/api/status", timeout=3)
        cockpit_ok = r.status_code == 200
        payload = {
            "agent_id": "COCKPIT_LUMIERE",
            "type": "gateway",
            "status": "online" if cockpit_ok else "offline",
            "runtime": "local",
            "capabilities": ["api_gateway", "command_mesh", "ops_routes"],
            "error_rate": None,
            "reliability_score": 1.0 if cockpit_ok else 0.0,
            "metadata": {
                "health_basis": "http_status",
                "http_status": r.status_code,
                "operational_status": "unknown",
                "task_success_verified": False,
                "reliability_score_basis": "http_availability_only",
            },
        }
        requests.post(f"{COCKPIT}/api/mesh/report_health",
                      json=payload, headers=HEADERS, timeout=5)
    except Exception:
        pass
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
