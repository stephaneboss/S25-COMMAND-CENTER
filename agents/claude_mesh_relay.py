#!/usr/bin/env python3
"""
S25 Lumiere - CLAUDE mesh relay.

Read-only companion to the external CLAUDE polling worker (Claude Code, runs off-box on
its own schedule and does the actual mission execution/reasoning). This relay does NOT
claim, execute, or complete missions - it only observes memory/command_mesh/missions.json
and:
  1. Appends a state-change audit trail for target_agent=CLAUDE missions
     (memory/command_mesh/claude_relay_log.jsonl).
  2. Maintains a small index of unread completed/failed results for TRINITY/voix to poll
     cheaply instead of scanning the full mission list (memory/command_mesh/claude_relay_index.json).
  3. Refreshes a CLAUDE mesh heartbeat once per tick so mesh/status.last_seen reflects that
     the relay channel is alive (this is a liveness signal for the integration, NOT a claim
     that a mission is being executed every tick - execution still happens on the external
     Claude Code cadence).

Intentionally NOT implemented: auto-claim / auto-complete of missions. A dumb daemon cannot
safely fabricate mission results; that requires the actual Claude Code agent. See mission
mis_qHZ0y5x8iDSS output for the reasoning.

Safe to run frequently: read-only on missions.json, append-only on its own relay files,
bounded internal loop (no unbounded infinite loop), singleton lock to avoid overlap.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("s25.claude_mesh_relay")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

REPO = Path(__file__).resolve().parent.parent
MISSIONS_FILE = REPO / "memory" / "command_mesh" / "missions.json"
RELAY_LOG = REPO / "memory" / "command_mesh" / "claude_relay_log.jsonl"
RELAY_INDEX = REPO / "memory" / "command_mesh" / "claude_relay_index.json"
LOCK_FILE = Path("/tmp/claude_mesh_relay.lock")

TARGET_AGENT = "CLAUDE"
TICK_SEC = 10
MAX_TICKS = 5  # bounded loop: ~50s total, fits one 60s cron slot with margin
COCKPIT_URL = os.getenv("COCKPIT_URL", "http://localhost:7777")
S25_SHARED_SECRET = os.getenv("S25_SHARED_SECRET", "")


def acquire_singleton_lock() -> bool:
    """Best-effort singleton guard: refuse to run if a lock younger than 2 min exists."""
    try:
        if LOCK_FILE.exists():
            age = time.time() - LOCK_FILE.stat().st_mtime
            if age < 120:
                logger.info("lock held (age=%.0fs), skipping this invocation", age)
                return False
        LOCK_FILE.write_text(str(os.getpid()))
        return True
    except OSError as e:
        logger.warning("lock acquire failed, proceeding without lock: %s", e)
        return True


def release_singleton_lock() -> None:
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def load_missions() -> Dict[str, Any]:
    try:
        with open(MISSIONS_FILE, encoding="utf-8") as f:
            return json.load(f).get("items", {})
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("could not read missions.json: %s", e)
        return {}


def load_index() -> Dict[str, Any]:
    try:
        with open(RELAY_INDEX, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"seen": {}, "unread_for_trinity": [], "last_scan_ts": None}


def save_index(idx: Dict[str, Any]) -> None:
    try:
        RELAY_INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("could not write relay index: %s", e)


def append_log(entry: Dict[str, Any]) -> None:
    try:
        with open(RELAY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        logger.warning("could not append relay log: %s", e)


def scan_once(idx: Dict[str, Any]) -> Dict[str, Any]:
    missions = load_missions()
    seen = idx.setdefault("seen", {})
    unread = idx.setdefault("unread_for_trinity", [])
    now = time.time()

    for mission_id, m in missions.items():
        if m.get("target_agent") != TARGET_AGENT:
            continue
        status = m.get("status")
        updated_at = m.get("updated_at")
        prev = seen.get(mission_id)
        if prev == updated_at:
            continue  # no change since last scan

        seen[mission_id] = updated_at
        entry = {
            "ts": now,
            "mission_id": mission_id,
            "status": status,
            "intent_preview": (m.get("intent") or "")[:160],
            "updated_at": updated_at,
        }
        if status in ("completed", "failed"):
            result = m.get("result") or {}
            entry["output_preview"] = str(result.get("output_preview") or result)[:300]
            if mission_id not in unread:
                unread.append(mission_id)
        append_log(entry)
        logger.info("relay: %s -> %s", mission_id, status)

    idx["last_scan_ts"] = now
    return idx


def refresh_heartbeat() -> None:
    """Liveness signal for the CLAUDE integration channel, not a claim of active execution."""
    if not S25_SHARED_SECRET:
        return
    try:
        requests.post(
            f"{COCKPIT_URL}/api/mesh/report_health",
            json={
                "agent_id": TARGET_AGENT,
                "status": "online",
                "runtime": "claude_mesh_relay",
                "capabilities": ["relay_only_no_execution"],
            },
            headers={"X-S25-Secret": S25_SHARED_SECRET},
            timeout=5,
        )
    except requests.RequestException as e:
        logger.debug("heartbeat refresh failed (non-fatal): %s", e)


def main() -> None:
    if not acquire_singleton_lock():
        return
    try:
        idx = load_index()
        backoff = 1.0
        for tick in range(MAX_TICKS):
            try:
                idx = scan_once(idx)
                save_index(idx)
                refresh_heartbeat()
                backoff = 1.0
            except Exception as e:  # defensive: never let one bad tick kill the loop
                logger.warning("tick %d failed: %s", tick, e)
                time.sleep(min(backoff, 30))
                backoff *= 2
                continue
            if tick < MAX_TICKS - 1:
                time.sleep(TICK_SEC)
    finally:
        release_singleton_lock()


if __name__ == "__main__":
    main()
