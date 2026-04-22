#!/usr/bin/env python3
"""
S25 Mesh Heartbeat Cron — Boucle vitale (Trinity spec)
========================================================
Runs every 1 min. For each local cron-based agent, checks its /tmp log mtime
and sends a /api/mesh/report_health heartbeat with derived status:
  - online    : log age < 2× expected cron interval
  - degraded  : 2× ≤ age < 4× (2 missed heartbeats)
  - offline   : age ≥ 4× expected interval (4+ missed)

Also reports LLM agents (GEMINI, TRINITY) based on their process / cockpit uptime.

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
        "capabilities": ["auto_tune_strategies", "re_enable_rules"],
    },
    "gemini_orchestrator": {
        "log": "/tmp/gemini_orchestrator.log", "interval": 7200,
        "type": "brain", "runtime": "google_cloud",
        "capabilities": ["strategic_brief", "portfolio_health_score"],
    },
    "gemini_news_scanner": {
        "log": "/tmp/gemini_news.log", "interval": 3600,
        "type": "intel", "runtime": "google_cloud",
        "capabilities": ["news_grounding", "google_search_citations"],
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
}


def derive_status(log_path: Path, interval_sec: int) -> tuple[str, int | None]:
    """Returns (status, age_sec) derived from log mtime."""
    if not log_path.exists():
        return "offline", None
    age = time.time() - log_path.stat().st_mtime
    if age < 2 * interval_sec:
        return "online", int(age * 1000)
    if age < 4 * interval_sec:
        return "degraded", int(age * 1000)
    return "offline", int(age * 1000)


def post_heartbeat(agent_id: str, meta: Dict):
    log_path = Path(meta["log"])
    status, latency_ms = derive_status(log_path, meta["interval"])
    payload = {
        "agent_id": agent_id,
        "type": meta["type"],
        "status": status,
        "runtime": meta["runtime"],
        "capabilities": meta["capabilities"],
        "latency_ms": latency_ms,
        "error_rate": 0.0,
        "reliability_score": 1.0 if status == "online" else (0.5 if status == "degraded" else 0.0),
    }
    try:
        r = requests.post(f"{COCKPIT}/api/mesh/report_health",
                          json=payload, timeout=5)
        ok = r.status_code == 200
    except Exception as e:
        ok = False
        logger.warning("heartbeat POST failed for %s: %s", agent_id, e)
    logger.info("%s → %s (latency=%sms, pushed=%s)",
                agent_id, status, latency_ms, ok)
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
    # Report TRINITY Core itself via cockpit uptime
    try:
        r = requests.get(f"{COCKPIT}/api/status", timeout=3)
        cockpit_ok = r.status_code == 200
        payload = {
            "agent_id": "COCKPIT_LUMIERE",
            "type": "gateway",
            "status": "online" if cockpit_ok else "offline",
            "runtime": "local",
            "capabilities": ["api_gateway", "command_mesh", "ops_routes"],
            "error_rate": 0.0,
            "reliability_score": 1.0 if cockpit_ok else 0.0,
        }
        requests.post(f"{COCKPIT}/api/mesh/report_health",
                      json=payload, timeout=5)
    except Exception:
        pass
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
