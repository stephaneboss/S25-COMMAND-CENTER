#!/usr/bin/env python3

from __future__ import annotations

import json
import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from agents.cockpit_client import CockpitClient


log = logging.getLogger("s25.merlin_mcp")

MCP_HOST = os.getenv("MERLIN_MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MERLIN_MCP_PORT", "8000"))
MCP_PATH = os.getenv("MERLIN_MCP_PATH", "/mcp")

client = CockpitClient()
mcp = FastMCP(
    name="S25 Merlin MCP Bridge",
    instructions=(
        "Tools-only MCP bridge for Gemini and MERLIN. "
        "Use these tools to inspect S25 state, route work, create missions, "
        "and write structured feedback back into shared memory."
    ),
    host=MCP_HOST,
    port=MCP_PORT,
    streamable_http_path=MCP_PATH,
    log_level=os.getenv("MERLIN_MCP_LOG_LEVEL", "INFO"),
)


def _json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


@mcp.tool(description="Get current S25 system status from the cockpit.")
def get_system_status() -> str:
    return _json(client.get_status() or {"ok": False, "error": "status_unavailable"})


@mcp.tool(description="Get the shared S25 memory document and runtime context.")
def get_shared_memory() -> str:
    return _json(client.get_shared_memory() or {"ok": False, "error": "memory_unavailable"})


@mcp.tool(description="Get lightweight runtime state for all S25 agents.")
def get_agents_state() -> str:
    return _json(client.get_agents_state() or {"ok": False, "error": "agents_state_unavailable"})


@mcp.tool(description="Get the unified mesh status for agents, pipeline, and GOUV4 quotas.")
def get_mesh_status() -> str:
    return _json(client.get_mesh_status() or {"ok": False, "error": "mesh_unavailable"})


@mcp.tool(description="Get the current GOUV4 routing and quota report.")
def get_router_report() -> str:
    return _json(client.get_router_report() or {"ok": False, "error": "router_unavailable"})


@mcp.tool(description="Route a task type through GOUV4 and get the recommended S25 agent.")
def route_task(task_type: str) -> str:
    return _json(client.route_task(task_type) or {"ok": False, "error": "route_failed", "task_type": task_type})


@mcp.tool(description="Get active and recent S25 missions.")
def get_missions() -> str:
    return _json(client.get_missions() or {"ok": False, "error": "missions_unavailable"})


@mcp.tool(description="Create a mission for COMET, MERLIN, ARKON, KIMI, ORACLE, or ONCHAIN_GUARDIAN.")
def create_mission(
    target: str,
    task_type: str,
    intent: str,
    priority: str = "normal",
    context_json: str = "{}",
) -> str:
    try:
        context = json.loads(context_json or "{}")
    except json.JSONDecodeError:
        context = {"raw_context": context_json}
    result = client.create_mission(
        created_by="MERLIN_MCP",
        target=target,
        task_type=task_type,
        intent=intent,
        priority=priority,
        context=context,
    )
    return _json(result or {"ok": False, "error": "create_mission_failed"})


@mcp.tool(description="Write agent state feedback back into shared S25 memory.")
def write_feedback(
    summary: str,
    level: str = "INFO",
    source: str = "MERLIN_MCP",
    mission_id: str = "",
    feedback_json: str = "{}",
) -> str:
    try:
        feedback = json.loads(feedback_json or "{}")
    except json.JSONDecodeError:
        feedback = {"raw_feedback": feedback_json}

    feedback_entry = {
        "summary": summary,
        "level": level,
        "source": source,
        "mission_id": mission_id or None,
        "feedback": feedback,
    }
    result = client.update_state(
        "MERLIN",
        updates={
            "status": "online",
            "last_query": summary,
            "last_feedback_at": feedback.get("ts") or None,
        },
        intel={"merlin_feedback": feedback_entry},
    )
    return _json(result or {"ok": False, "error": "write_feedback_failed"})


@mcp.tool(description="Send a MERLIN heartbeat into shared memory.")
def heartbeat(note: str = "mcp heartbeat") -> str:
    return _json(client.heartbeat("MERLIN", note=note) or {"ok": False, "error": "heartbeat_failed"})


def main() -> None:
    logging.basicConfig(level=os.getenv("MERLIN_MCP_LOG_LEVEL", "INFO"))
    log.info("Starting MERLIN MCP bridge on %s:%s%s", MCP_HOST, MCP_PORT, MCP_PATH)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
