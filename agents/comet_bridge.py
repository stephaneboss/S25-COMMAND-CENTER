#!/usr/bin/env python3

"""
S25 Lumiere - COMET operator bridge.

COMET is treated as a web operations arm:
- reads S25 status
- writes intel into shared memory
- creates and updates missions
- mirrors high-signal intel to Home Assistant when available
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from agents.cockpit_client import CockpitClient
from security.vault import vault_get
from agents.ha_bridge import ha as ha_bridge


logger = logging.getLogger("s25.comet")

COCKPIT_URL = os.getenv("COCKPIT_URL", "http://localhost:7777")
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = vault_get("HA_TOKEN", os.getenv("HA_TOKEN", "")) or ""
COMET_BRIDGE_KEY = vault_get("S25_SHARED_SECRET", os.getenv("S25_SHARED_SECRET", "")) or ""

HA_ENTITY_INTEL = "input_text.comet_intel"
HA_ENTITY_THREAT = "input_select.s25_threat_level"

client = CockpitClient(base_url=COCKPIT_URL, shared_secret=COMET_BRIDGE_KEY)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_intel_payload(
    source: str,
    summary: str,
    level: str = "INFO",
    data: Optional[Dict[str, Any]] = None,
    threat_level: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "source": source,
        "summary": summary,
        "level": level,
        "data": data or {},
        "threat_level": threat_level,
        "ts": _utcnow_iso(),
        "version": "2.0",
    }


def _current_feed(limit: int = 50) -> list[dict[str, Any]]:
    state = client.get_agents_state() or {}
    feed = (((state.get("state") or {}).get("intel") or {}).get("comet_feed")) or []
    return list(feed[:limit])


def push_intel_to_cockpit(payload: Dict[str, Any]) -> bool:
    entry = {
        "ts": payload.get("ts", _utcnow_iso()),
        "source": payload.get("source", "comet"),
        "level": payload.get("level", "INFO"),
        "summary": payload.get("summary", ""),
        "data": payload.get("data", {}),
        "threat_level": payload.get("threat_level"),
    }
    feed = [entry, *_current_feed()]
    result = client.update_state(
        "COMET",
        updates={
            "status": "online",
            "last_report": entry["summary"],
            "last_payload_ts": entry["ts"],
        },
        intel={"comet_feed": feed[:50]},
    )
    ok = bool(result and result.get("ok"))
    if ok:
        logger.info("COMET intel pushed: [%s] %s", entry["level"], entry["summary"])
    else:
        logger.warning("COMET intel push failed")
    return ok


def push_threat_to_cockpit(level: int, reason: str = "") -> bool:
    level = max(0, min(int(level), 3))
    result = client.update_state(
        "COMET",
        updates={
            "status": "alert" if level >= 2 else "online",
            "last_report": reason or f"Threat update T{level}",
        },
        pipeline={"threat_level": f"T{level}"},
    )
    if reason:
        push_intel_to_cockpit(
            build_intel_payload(
                source="comet",
                summary=reason,
                level="CRITICAL" if level >= 3 else "ALERT" if level >= 2 else "WARNING",
                threat_level=level,
            )
        )
    return bool(result and result.get("ok"))


def push_intel_to_ha(payload: Dict[str, Any]) -> bool:
    summary = f"[{payload['level']}] {payload['summary']}"[:255]
    return ha_bridge.push_sensor(HA_ENTITY_INTEL, summary, {
        "source": payload.get("source", "comet"),
        "level": payload.get("level", "INFO"),
        "data": json.dumps(payload.get("data", {}))[:255],
        "ts": payload.get("ts", ""),
        "friendly_name": "COMET Intel Feed",
    })


def push_threat_to_ha(level: int) -> bool:
    level = max(0, min(int(level), 3))
    level_map = {0: "T0", 1: "T1", 2: "T2", 3: "T3"}
    return ha_bridge.call_service("input_select", "select_option", {
        "entity_id": HA_ENTITY_THREAT,
        "option": level_map.get(level, "T0"),
    })


def get_system_status() -> Optional[Dict[str, Any]]:
    return client.get_status()


def get_current_signal() -> Optional[Dict[str, Any]]:
    status = get_system_status() or {}
    return status.get("signal") or status.get("system")


def heartbeat(note: str = "comet operator heartbeat") -> bool:
    result = client.heartbeat("COMET", note=note)
    return bool(result and result.get("ok"))


def create_web_mission(
    intent: str,
    priority: str = "normal",
    task_type: str = "web_operations",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    return client.create_mission(
        created_by="COMET",
        target="COMET",
        task_type=task_type,
        intent=intent,
        priority=priority,
        context=context or {},
    )


def update_web_mission(
    mission_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    return client.update_mission(
        mission_id=mission_id,
        status=status,
        actor="COMET",
        result=result,
        context=context,
    )


def comet_send(
    summary: str,
    level: str = "INFO",
    data: Optional[Dict[str, Any]] = None,
    threat: Optional[int] = None,
) -> bool:
    payload = build_intel_payload(
        source="COMET",
        summary=summary,
        level=level,
        data=data,
        threat_level=threat,
    )
    ok_cockpit = push_intel_to_cockpit(payload)
    ok_ha = push_intel_to_ha(payload)

    if threat is not None:
        push_threat_to_cockpit(threat, summary)
        push_threat_to_ha(threat)

    return ok_cockpit or ok_ha


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    status = get_system_status()
    print("=== COMET Operator Bridge Test ===")
    print(f"Cockpit: {COCKPIT_URL}")
    if status:
        print(json.dumps(status, indent=2))
    else:
        print("Cockpit unreachable")
    print(f"Heartbeat: {'OK' if heartbeat() else 'FAILED'}")
