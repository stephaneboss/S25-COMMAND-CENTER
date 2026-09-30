"""Read-only status projection of the canonical command-mesh files."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def snapshot(agents_path: Path, missions_path: Path, *, now: datetime,
             stale_sec: int = 7200) -> dict:
    agents = json.loads(agents_path.read_text(encoding="utf-8"))["items"]
    missions = json.loads(missions_path.read_text(encoding="utf-8"))["items"]
    if not isinstance(agents, dict) or not isinstance(missions, dict):
        raise ValueError("invalid mesh store shape")

    statuses = {}
    for agent_id, agent in agents.items():
        last_seen = agent.get("last_seen_at") or agent.get("last_heartbeat_at")
        fresh = False
        if last_seen:
            try:
                seen_at = datetime.fromisoformat(str(last_seen).replace("Z", "+00:00"))
                if seen_at.tzinfo is None:
                    seen_at = seen_at.replace(tzinfo=timezone.utc)
                age = (now - seen_at).total_seconds()
                fresh = 0 <= age <= stale_sec
            except ValueError:
                pass
        reported = agent.get("status", "unknown")
        statuses[agent_id] = {
            "status": reported if reported != "online" or fresh else "stale",
            "last_seen": last_seen,
        }

    online = sum(agent["status"] == "online" for agent in statuses.values())
    active = sum(m.get("status") in ("queued", "assigned", "running")
                 for m in missions.values())
    return {
        "total_agents": len(statuses),
        "online": online,
        "offline": len(statuses) - online,
        "agents": statuses,
        "missions_active": active,
        "source": "command_mesh",
    }


def pipeline_control_evidence(pipeline: dict, ha_state: str) -> dict:
    """Expose control sources without changing the execution policy."""
    local = bool(pipeline.get("kill_switch", False))
    ha_state = ha_state if ha_state in ("on", "off") else "unknown"
    effective = True if local or ha_state == "on" else (False if ha_state == "off" else None)
    return {
        **pipeline,
        "local_kill_switch": local,
        "ha_kill_switch_state": ha_state,
        "effective_kill_switch": effective,
        "kill_switch_sources_consistent": None if ha_state == "unknown" else local == (ha_state == "on"),
    }
