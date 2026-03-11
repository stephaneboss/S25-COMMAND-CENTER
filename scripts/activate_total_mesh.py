#!/usr/bin/env python3
import json
import sys
from urllib import error, request


BASE_URL = "https://api.smajor.org"

AGENTS = [
    {"agent": "TRINITY", "role_id": "trinity_orchestrator", "badge_id": "ai_badge", "scope_id": "mission_scope_global", "notes": "Mesh total command and orchestration"},
    {"agent": "MERLIN", "role_id": "merlin_validator", "badge_id": "ai_badge", "scope_id": "validation_scope_global", "notes": "Validation and memory lane"},
    {"agent": "COMET", "role_id": "comet_watch", "badge_id": "ai_badge", "scope_id": "intel_scope_global", "notes": "Provider watch and ops follow-up"},
    {"agent": "GOUV4", "role_id": "policy_admin", "badge_id": "major_badge", "scope_id": "policy_scope_global", "notes": "Routing and arbitration"},
    {"agent": "KIMI", "role_id": "kimi_sensor", "badge_id": "ai_badge", "scope_id": "web3_scope", "notes": "Web3 sensor lane"},
    {"agent": "ORACLE", "role_id": "oracle_sensor", "badge_id": "ai_badge", "scope_id": "market_scope", "notes": "Price verification lane"},
    {"agent": "ONCHAIN_GUARDIAN", "role_id": "guardian_watch", "badge_id": "ai_badge", "scope_id": "risk_scope", "notes": "Onchain risk lane"},
    {"agent": "ARKON", "role_id": "builder_operator", "badge_id": "employee_badge", "scope_id": "build_scope", "notes": "Build and runtime wiring"},
    {"agent": "TREASURY", "role_id": "treasury_watch", "badge_id": "ai_badge", "scope_id": "treasury_scope", "notes": "Treasury and balances"},
    {"agent": "PROVIDER_WATCH", "role_id": "provider_watch", "badge_id": "ai_badge", "scope_id": "provider_scope", "notes": "Provider feature watch"},
    {"agent": "MERLIN_MCP", "role_id": "mcp_bridge", "badge_id": "ai_badge", "scope_id": "mcp_scope", "notes": "MCP bridge lane"},
    {"agent": "DEFI_LIQUIDITY_MANAGER", "role_id": "defi_liquidity_manager", "badge_id": "ai_badge", "scope_id": "defi_scope", "notes": "DeFi liquidity lane"},
    {"agent": "CODE_VALIDATOR", "role_id": "code_validator", "badge_id": "employee_badge", "scope_id": "build_scope", "notes": "Code validation lane"},
    {"agent": "SMART_REFACTOR", "role_id": "smart_refactor", "badge_id": "employee_badge", "scope_id": "build_scope", "notes": "Refactor lane"},
    {"agent": "AUTO_DOCUMENTER", "role_id": "auto_documenter", "badge_id": "employee_badge", "scope_id": "docs_scope", "notes": "Documentation lane"},
]


def call(method: str, path: str, payload=None):
    data = None
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SmajorTotalMesh/1.0 (+https://smajor.org)",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method.upper())
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_agent_exists(agent_name: str):
    call(
        "POST",
        "/api/missions",
        {
            "created_by": "TRINITY",
            "target": agent_name,
            "task_type": "mesh_sync",
            "priority": "critical",
            "intent": f"TOTAL_MESH protocol sync for {agent_name}",
            "context": {"protocol": "mesh_total"},
        },
    )


def sync_agent(agent_record):
    call(
        "POST",
        "/api/memory/state",
        {
            "agent": agent_record["agent"],
            "updates": {
                "status": "online",
                "last_task": "TOTAL_MESH_PROTOCOL",
                "role_id": agent_record["role_id"],
                "badge_id": agent_record["badge_id"],
                "scope_id": agent_record["scope_id"],
                "notes": agent_record["notes"],
                "mesh_protocol": "mesh_total",
            },
        },
    )
    call("POST", "/api/memory/ping", {"agent": agent_record["agent"]})


def main():
    memory = call("GET", "/api/memory")
    existing = set(memory["agents_state"]["agents"].keys())

    for record in AGENTS:
        if record["agent"] not in existing:
            ensure_agent_exists(record["agent"])

    for record in AGENTS:
        sync_agent(record)

    call(
        "POST",
        "/api/missions",
        {
            "created_by": "TRINITY",
            "target": "COMET",
            "task_type": "mesh_sync",
            "priority": "critical",
            "intent": "TOTAL_MESH protocol active. Report all agent status to the hub and optimize the system.",
            "context": {"protocol": "mesh_total", "headcount": len(AGENTS)},
        },
    )

    mesh = call("GET", "/api/mesh/status")
    status = call("GET", "/api/status")

    online = [
        name
        for name, details in mesh["mesh"]["agents"].items()
        if str(details.get("status", "")).lower() == "online"
    ]

    print(json.dumps({
        "ok": True,
        "protocol": "mesh_total",
        "target_headcount": len(AGENTS),
        "online_agents": online,
        "online_count": len(online),
        "missions_active": mesh["mesh"]["missions_active"],
        "pipeline_status": status.get("pipeline_status"),
        "arkon5_action": status.get("arkon5_action"),
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"ok": False, "error": f"http_{exc.code}", "body": body}, indent=2))
        sys.exit(1)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        sys.exit(1)
