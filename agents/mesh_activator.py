#!/usr/bin/env python3
"""
S25 Mesh Activator — keeps the pipeline warm by seeding recurring missions.

Qwen's self-audit pointed out that the mesh often has 0 active missions
between external triggers. This daemon ensures continuous autonomous
flow by seeding a rotating set of scheduled missions:

  - infra_monitoring   → every 10 min  (LOCAL_CRON / system_health)
  - market_news        → every 30 min  (COMET → fallback GEMINI retired)
  - strategy_planning  → every 60 min  (quant_brain)

A mission is only seeded if there isn't already a queued/running one of
the same task_type (dedupe via task_type + hour_bucket). This avoids
stacking duplicates when the cron runs faster than the previous worker.

Runs every 5 min via cron.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("s25.mesh_activator")

REPO = Path(__file__).resolve().parent.parent
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")

ACTIVATION_PATH = REPO / "memory" / "mesh_activator_state.json"
MISSIONS_PATH = REPO / "memory" / "command_mesh" / "missions.json"

# (task_type, interval_sec, target_agent, intent, priority)
SCHEDULE = [
    ("infra_monitoring",  600,  "LOCAL_CRON",
     "Auto scan system health — periodic", "normal"),
    ("trading_analysis",  1800, "quant_brain",
     "Auto trading analysis brief — periodic", "normal"),
    ("strategy_planning", 3600, "LOCAL_CRON",
     "Auto strategy review — periodic", "low"),
]


def _env_file_get(key: str) -> Optional[str]:
    env = REPO / ".env"
    if not env.exists():
        return None
    try:
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def has_pending(task_type: str) -> bool:
    """Check if a mission of this task_type is already queued/running/assigned."""
    data = _load(MISSIONS_PATH, {"items": {}})
    for m in data.get("items", {}).values():
        if (m.get("task_type") == task_type
                and m.get("status") in {"queued", "assigned", "running"}):
            return True
    return False


def create_mission(
    task_type: str,
    target_agent: str,
    intent: str,
    priority: str,
    secret: str,
) -> Dict:
    body = {
        "created_by": "mesh_activator",
        "target_agent": target_agent,
        "task_type": task_type,
        "intent": intent,
        "priority": priority,
        "input": {},
        "constraints": {"timeout_sec": 120},
        "routing": {"fallback_agents": ["LOCAL_CRON"]},
    }
    r = requests.post(
        f"{COCKPIT}/api/mesh/create_mission",
        headers={"Content-Type": "application/json",
                 "X-S25-Secret": secret},
        json=body,
        timeout=10,
    )
    return r.json() if r.ok else {"ok": False, "http": r.status_code,
                                   "text": r.text[:300]}


def tick():
    secret = os.getenv("S25_SHARED_SECRET") or _env_file_get("S25_SHARED_SECRET")
    if not secret:
        raise RuntimeError("S25_SHARED_SECRET missing")

    state = _load(ACTIVATION_PATH, {"last_seed": {}})
    last_seed = state.setdefault("last_seed", {})
    now = time.time()

    results = []
    for task_type, interval, target, intent, prio in SCHEDULE:
        last = last_seed.get(task_type, 0)
        due = (now - last) >= interval

        if not due:
            results.append({"task_type": task_type, "action": "not_due",
                            "seconds_to_next": int(interval - (now - last))})
            continue

        if has_pending(task_type):
            results.append({"task_type": task_type, "action": "skipped_pending",
                            "reason": "existing mission queued/running"})
            # Don't update last_seed — retry next tick
            continue

        resp = create_mission(task_type, target, intent, prio, secret)
        if resp.get("mission_id"):
            last_seed[task_type] = now
            results.append({
                "task_type": task_type,
                "action": "seeded",
                "mission_id": resp["mission_id"],
                "target": target,
                "priority": prio,
            })
            logger.info("seeded %s (target=%s prio=%s) → %s",
                        task_type, target, prio, resp["mission_id"])
        else:
            results.append({"task_type": task_type, "action": "create_failed",
                            "error": resp})

    _save(ACTIVATION_PATH, state)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    tick()
