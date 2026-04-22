#!/usr/bin/env python3
"""
S25 System Health Monitor
==========================
Cron */5. Checks each critical cron agent has run recently + key endpoints
are responding. Pushes consolidated health sensor to HA + sends notification
if anything is stuck for more than 2x its expected interval.

Agents watched:
  coinbase_ha_publisher   should run every 1 min
  mesh_signal_bridge      every 2 min
  trailing_stop_manager   every 3 min
  auto_signal_scanner     every 5 min
  comet_sentiment         every 10 min
  drawdown_guardian       every 10 min
  dca_scheduler           every 15 min
  git_auto_sync           every 30 min
  quant_brain             every 60 min
  gemini_orchestrator     every 120 min
  gemini_news_scanner     every 60 min

Endpoint health:
  /api/status
  /api/coinbase/portfolio
  /api/trading/pnl
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import requests

logger = logging.getLogger("s25.system_health")

REPO = Path(__file__).resolve().parent.parent
HEALTH_PATH = REPO / "memory" / "system_health.json"
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")

# agent name -> (log path, max_age_minutes, priority)
CRONS = {
    "coinbase_ha_publisher":  ("/tmp/coinbase_ha_publisher.log", 3,   "critical"),
    "mesh_signal_bridge":     ("/tmp/mesh_bridge.log",           5,   "high"),
    "trailing_stop_manager":  ("/tmp/trailing_stop.log",         8,   "high"),
    "auto_signal_scanner":    ("/tmp/auto_signal_scanner.log",   10,  "high"),
    "comet_sentiment":        ("/tmp/comet_sentiment.log",       25,  "medium"),
    "drawdown_guardian":      ("/tmp/drawdown.log",              25,  "critical"),
    "dca_scheduler":          ("/tmp/dca_scheduler.log",         35,  "medium"),
    "git_auto_sync":          ("/tmp/git_sync.log",              70,  "low"),
    "quant_brain":            ("/tmp/quant_brain.log",           130, "high"),
    "gemini_orchestrator":    ("/tmp/gemini_orchestrator.log",   250, "medium"),
    "gemini_news_scanner":    ("/tmp/gemini_news.log",           130, "medium"),
}

ENDPOINTS = [
    "/api/status",
    "/api/coinbase/portfolio",
    "/api/trading/pnl",
    "/api/trading/strategies",
    "/api/trading/brief",
    "/api/trading/news",
]


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def check_crons() -> List[Dict]:
    rows = []
    now = time.time()
    for name, (log_path, max_age_min, prio) in CRONS.items():
        entry = {
            "name": name,
            "log_path": log_path,
            "max_age_min": max_age_min,
            "priority": prio,
            "last_run_min_ago": None,
            "status": "unknown",
            "last_line": "",
        }
        p = Path(log_path)
        if p.exists():
            try:
                mtime = p.stat().st_mtime
                age_sec = now - mtime
                entry["last_run_min_ago"] = round(age_sec / 60, 1)
                entry["status"] = (
                    "healthy" if age_sec < max_age_min * 60
                    else ("stale" if age_sec < max_age_min * 60 * 3 else "stuck")
                )
                # Last line of log (trimmed)
                try:
                    txt = p.read_text()
                    last = (txt.splitlines() or [""])[-1]
                    entry["last_line"] = last[:120]
                except Exception:
                    pass
            except Exception as e:
                entry["status"] = f"error: {e}"
        else:
            entry["status"] = "no_log"
        rows.append(entry)
    return rows


def check_endpoints() -> List[Dict]:
    rows = []
    for path in ENDPOINTS:
        r = {"path": path, "status": "unknown", "latency_ms": None}
        try:
            start = time.time()
            resp = requests.get(f"{COCKPIT}{path}", timeout=5)
            r["latency_ms"] = int((time.time() - start) * 1000)
            r["http"] = resp.status_code
            r["status"] = "healthy" if resp.status_code == 200 else "error"
        except Exception as e:
            r["status"] = f"error: {type(e).__name__}"
        rows.append(r)
    return rows


def push_ha(summary: Dict):
    url = _env_get("HA_URL") or "http://10.0.0.136:8123"
    token = _env_get("HA_TOKEN")
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}",
               "Content-Type": "application/json"}
    try:
        requests.post(
            f"{url.rstrip('/')}/api/states/sensor.s25_system_health",
            headers=headers,
            json={
                "state": summary["overall_status"],
                "attributes": {
                    "friendly_name": "S25 System Health",
                    "icon": {
                        "healthy": "mdi:check-circle",
                        "degraded": "mdi:alert-circle",
                        "critical": "mdi:close-circle",
                    }.get(summary["overall_status"], "mdi:help-circle"),
                    "crons_healthy": summary["crons_healthy"],
                    "crons_stale": summary["crons_stale"],
                    "crons_stuck": summary["crons_stuck"],
                    "endpoints_ok": summary["endpoints_ok"],
                    "endpoints_fail": summary["endpoints_fail"],
                    "stuck_agents": summary["stuck_agent_names"],
                    "generated_at": summary["generated_at"],
                },
            },
            timeout=6,
        )
        # Notification if critical
        if summary["overall_status"] == "critical":
            requests.post(
                f"{url.rstrip('/')}/api/services/persistent_notification/create",
                headers=headers,
                json={
                    "title": "🚨 S25 System Health CRITICAL",
                    "message": "Stuck agents: " + ", ".join(summary["stuck_agent_names"]),
                },
                timeout=6,
            )
    except Exception as e:
        logger.warning("HA push failed: %s", e)


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    crons = check_crons()
    endpoints = check_endpoints()

    healthy = sum(1 for c in crons if c["status"] == "healthy")
    stale = sum(1 for c in crons if c["status"] == "stale")
    stuck = sum(1 for c in crons if c["status"] in ("stuck", "no_log"))
    stuck_critical = [c["name"] for c in crons
                      if c["status"] in ("stuck", "no_log")
                      and c["priority"] in ("critical", "high")]

    ep_ok = sum(1 for e in endpoints if e["status"] == "healthy")
    ep_fail = len(endpoints) - ep_ok

    overall = "healthy"
    if stuck_critical or ep_fail:
        overall = "critical"
    elif stuck or stale or ep_fail > 0:
        overall = "degraded"

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "crons_healthy": healthy,
        "crons_stale": stale,
        "crons_stuck": stuck,
        "endpoints_ok": ep_ok,
        "endpoints_fail": ep_fail,
        "stuck_agent_names": stuck_critical,
        "details": {"crons": crons, "endpoints": endpoints},
    }

    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_PATH.write_text(json.dumps(summary, indent=2, default=str))
    push_ha(summary)

    logger.info("overall=%s crons: %d healthy / %d stale / %d stuck | endpoints: %d/%d ok",
                overall, healthy, stale, stuck, ep_ok, len(endpoints))
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
