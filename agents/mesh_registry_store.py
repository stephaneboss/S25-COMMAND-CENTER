"""Serialize agent heartbeat updates to the canonical mesh registry."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl


def _lock_registry(lock) -> None:
    if os.name == "nt":
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
    else:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)


def _unlock_registry(lock) -> None:
    if os.name == "nt":
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def update_agent(path: Path, body: dict, now: str) -> dict:
    """Merge one heartbeat without dropping another process's agent entry.

    A separate lock file is necessary because os.replace changes the inode of
    agents.json. Never replace a corrupt registry with an empty one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+b") as lock:
        _lock_registry(lock)
        try:
            store = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"items": {}}
            items = store["items"]
            if not isinstance(items, dict):
                raise ValueError("invalid agents registry shape")
            agent_id = body["agent_id"]
            existing = items.get(agent_id, {})
            agent = {
                "agent_id": agent_id,
                "type": body.get("type") or existing.get("type", "generic"),
                "status": body.get("status", "online"),
                "runtime": body.get("runtime") or existing.get("runtime", "local"),
                "endpoint_class": (body.get("endpoint_class")
                                   or existing.get("endpoint_class", "internal")),
                "capabilities": (body.get("capabilities")
                                 or existing.get("capabilities", [])),
                "priority": body.get("priority") or existing.get("priority", "normal"),
                "cost_tier": body.get("cost_tier") or existing.get("cost_tier", "low"),
                "reliability_score": body.get(
                    "reliability_score", existing.get("reliability_score", 1.0)),
                "last_heartbeat_at": now,
                "last_seen_at": now,
                "cooldown_until": body.get(
                    "cooldown_until", existing.get("cooldown_until")),
                "metadata": body.get("metadata", existing.get("metadata", {})),
                "latency_ms": body.get("latency_ms"),
                "error_rate": body.get("error_rate"),
            }
            items[agent_id] = agent
            fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as out:
                    json.dump(store, out, indent=2, default=str)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmp_name, path)
            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
            return agent
        finally:
            _unlock_registry(lock)
