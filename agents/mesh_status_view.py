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
