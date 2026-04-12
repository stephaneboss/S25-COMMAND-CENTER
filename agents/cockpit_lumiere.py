#!/usr/bin/env python3
# ============================================================
# S25 LUMIÈRE — Cockpit Web UI v1.0
# Interface visuelle futuriste pour CentOS Akash
# Accessible via navigateur Web depuis le S25 Ultra
# PORT: 7777
# ============================================================

from flask import Flask, render_template_string, jsonify, request
import os, json, requests, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path

from agents.gouv4_planner import GOUV4Router
from security.vault import vault_get

MEMORY_DIR = Path(os.getenv("MEMORY_DIR", "/app/memory"))
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SHARED_MEMORY_FILE = MEMORY_DIR / "SHARED_MEMORY.md"
AGENTS_STATE_FILE  = MEMORY_DIR / "agents_state.json"

app = Flask(__name__)
app.secret_key = vault_get("SECRET_KEY", os.urandom(32).hex())

HA_URL          = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN        = vault_get("HA_TOKEN", os.getenv("HA_TOKEN", "")) or ""
GEMINI_API_KEY  = vault_get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")) or ""
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
S25_SECRET      = vault_get("S25_SHARED_SECRET", os.getenv("S25_SHARED_SECRET", "")) or ""
MASTER_WALLET_ADDRESS = os.getenv("MASTER_WALLET_ADDRESS", "")
APP_BUILD_SHA   = os.getenv("APP_BUILD_SHA", "dev")
ALLOW_PUBLIC_ACTIONS = os.getenv("ALLOW_PUBLIC_ACTIONS", "true").lower() in {"1", "true", "yes", "on"}
PUBLIC_RUNTIME_BASE = os.getenv("PUBLIC_RUNTIME_BASE", "https://s25.smajor.org")
gouv4_router = GOUV4Router()

AGENT_ROSTER_TEMPLATE = {
    "TRINITY": {
        "status": "online",
        "last_seen": None,
        "last_intent": None,
        "session_count": 0,
        "notes": "Vocal controller teste. Memoire persistante via /api/memory",
    },
    "ARKON": {
        "status": "online",
        "last_seen": None,
        "last_task": None,
        "notes": "Claude Code - builder principal",
    },
    "MERLIN": {
        "status": "online",
        "last_seen": None,
        "last_query": None,
        "notes": "Gemini validateur",
    },
    "COMET": {
        "status": "online",
        "last_seen": None,
        "last_report": None,
        "notes": "Perplexity watchman - comet_bridge.py v2.1",
    },
    "GOUV4": {
        "status": "online",
        "last_seen": None,
        "last_task": None,
        "notes": "Policy and routing core",
    },
    "KIMI": {
        "status": "lateral_ready",
        "last_seen": None,
        "last_scan": None,
        "notes": "Web3 sensor lane; tunnel still lateral",
    },
    "ORACLE": {
        "status": "observe",
        "last_seen": None,
        "last_report": None,
        "notes": "Prix multi-source et verification d'integrite",
    },
    "ONCHAIN_GUARDIAN": {
        "status": "watch_ready",
        "last_seen": None,
        "last_report": None,
        "notes": "Defense on-chain, rugs, whales, LP risk",
    },
    "TREASURY": {
        "status": "online",
        "last_seen": None,
        "last_task": None,
        "notes": "Treasury and custody supervision",
    },
    "PROVIDER_WATCH": {
        "status": "online",
        "last_seen": None,
        "last_report": None,
        "notes": "Provider watch and release tracking",
    },
    "MERLIN_MCP": {
        "status": "online",
        "last_seen": None,
        "last_task": None,
        "notes": "Remote MCP bridge for Gemini validation",
    },
    "DEFI_LIQUIDITY_MANAGER": {
        "status": "armed",
        "last_seen": None,
        "last_task": None,
        "notes": "DeFi liquidity orchestration lane",
    },
    "CODE_VALIDATOR": {
        "status": "online",
        "last_seen": None,
        "last_task": None,
        "notes": "Validation gate for code and releases",
    },
    "SMART_REFACTOR": {
        "status": "online",
        "last_seen": None,
        "last_task": None,
        "notes": "Refactor and cleanup lane",
    },
    "AUTO_DOCUMENTER": {
        "status": "online",
        "last_seen": None,
        "last_task": None,
        "notes": "Docs and memory upkeep",
    },
}

OPERATIONAL_AGENT_STATUSES = {
    "online",
    "lateral_ready",
    "watch_ready",
    "observe",
    "armed",
}

LEGACY_AGENT_STATUS_MAP = {
    "KIMI": {"standby": "lateral_ready"},
    "ONCHAIN_GUARDIAN": {"standby": "watch_ready"},
    "ORACLE": {"degraded": "observe"},
    "DEFI_LIQUIDITY_MANAGER": {"standby": "armed"},
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_operational_status(status: str | None) -> bool:
    return str(status or "").lower() in OPERATIONAL_AGENT_STATUSES


def _normalize_agent_runtime(agent_id: str, runtime: dict) -> dict:
    status = str(runtime.get("status", "")).lower()
    mapped = LEGACY_AGENT_STATUS_MAP.get(agent_id, {}).get(status)
    if mapped:
        runtime["status"] = mapped
    return runtime


def _default_agents_state() -> dict:
    """Runtime state skeleton shared by all agents."""
    return {
        "_meta": {
            "description": "Runtime state de chaque agent S25",
            "version": "1.1.0",
            "updated_at": None,
        },
        "agents": json.loads(json.dumps(AGENT_ROSTER_TEMPLATE)),
        "pipeline": {
            "mode": "dry_run",
            "active_model": "INIT",
            "threat_level": "T0",
            "kill_switch": False,
            "last_signal": None,
        },
        "market": {
            "btc_usd": None,
            "eth_usd": None,
            "fear_greed": None,
            "last_fetch": None,
        },
        "wallet": {
            "creator_label": "Wallet creator",
            "creator_address": MASTER_WALLET_ADDRESS,
            "creator_connected": bool(MASTER_WALLET_ADDRESS),
            "custody": "google_secret_manager",
            "creator_akt_balance": None,
            "creator_akt_price_usd": None,
            "creator_akt_value_usd": None,
            "last_sync": None,
        },
        "runtime_bridge": {
            "bridge_id": "s25_direct_bridge_v1",
            "bridge_state": "direct_runtime_linked",
            "public_base_url": PUBLIC_RUNTIME_BASE,
            "direct_bridge_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/trinity",
            "direct_ping_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/trinity/ping",
            "status_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/status",
            "secure_memory_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/memory/state",
            "authority_header": "x-s25-secret",
            "source_of_truth": "S25 Lumiere runtime",
            "gemini_layer": "MERLIN / Gemini validation core",
            "runtime_marker": None,
            "probe_at": None,
            "last_sync": None,
        },
        "missions": {
            "active": [],
            "history": [],
        },
        "intel": {
            "comet_feed": [],
        },
        "trading": {
            "lanes": {
                "signal_lane": {"headline": "READY", "last_sync": None},
                "risk_lane": {"headline": "MESH_READY", "last_sync": None},
                "treasury_lane": {"headline": "treasury online", "last_sync": None},
                "execution_lane": {"headline": "mirror wallet armed", "last_sync": None},
            },
            "policy_state": "audit_first",
            "mode": "showroom",
            "last_sync": None,
        },
        "business": {
            "organizations": [],
            "clients": [],
            "jobs": [],
            "quotes_invoices": [],
            "identities": [],
            "events": [],
            "last_write_at": None,
        },
    }


def _ensure_state_shape(state: dict | None) -> dict:
    """Backfill missing runtime sections so new features remain compatible."""
    base = _default_agents_state()
    state = state or {}

    for key, value in base.items():
        if key not in state:
            state[key] = value
        elif isinstance(value, dict):
            for nested_key, nested_value in value.items():
                if nested_key not in state[key]:
                    state[key][nested_key] = nested_value
                elif isinstance(nested_value, dict):
                    for leaf_key, leaf_value in nested_value.items():
                        state[key][nested_key].setdefault(leaf_key, leaf_value)

    return state


def _refresh_runtime_defaults(state: dict) -> dict:
    agents = state.setdefault("agents", {})
    for agent_id, template in AGENT_ROSTER_TEMPLATE.items():
        agent_state = agents.setdefault(agent_id, {})
        for key, value in template.items():
            agent_state.setdefault(key, value)
        _normalize_agent_runtime(agent_id, agent_state)

    pipeline = state.setdefault("pipeline", {})
    runtime_bridge = state.setdefault("runtime_bridge", {})
    business = state.setdefault("business", {})
    trading = state.setdefault("trading", {})
    intel = state.setdefault("intel", {})

    online_agents = sum(
        1 for details in agents.values()
        if _is_operational_status(details.get("status"))
    )
    direct_linked = runtime_bridge.get("bridge_state") == "direct_runtime_linked"

    if online_agents >= 8:
        pipeline["mode"] = "mesh_live"
        pipeline.setdefault("active_model", "S25_DIRECT")
    if direct_linked and not pipeline.get("last_signal"):
        pipeline["last_signal"] = {
            "action": "READY",
            "confidence": max(int(online_agents * 5), 55),
            "source": "runtime_bridge",
            "ts": _utcnow_iso(),
        }

    trading.setdefault("policy_state", "audit_first")
    trading.setdefault("mode", "showroom")
    trading.setdefault("lanes", {})
    for lane_id, headline in {
        "signal_lane": "READY",
        "risk_lane": "MESH_READY",
        "treasury_lane": "treasury online",
        "execution_lane": "mirror wallet armed",
    }.items():
        trading["lanes"].setdefault(lane_id, {}).setdefault("headline", headline)

    business.setdefault("clients", [])
    business.setdefault("identities", [])
    business.setdefault("jobs", [])
    business.setdefault("quotes_invoices", [])
    business.setdefault("organizations", [])
    business.setdefault("events", [])
    business.setdefault("identity_rollout", {})
    business.setdefault("provider_transition", {})
    business.setdefault("last_write_at", None)

    intel.setdefault("comet_feed", [])
    intel.setdefault("merlin_feedback", {
        "ts": _utcnow_iso(),
        "summary": "Runtime bridge linked. Awaiting next MERLIN loop refresh.",
    })
    return state


def _mission_payload(body: dict) -> dict:
    """Normalize mission payload stored in shared runtime memory."""
    mission_id = body.get("mission_id") or f"mission-{uuid.uuid4().hex[:10]}"
    target = body.get("target", "COMET")
    task_type = body.get("task_type", "infra_monitoring")
    intent = body.get("intent", "").strip()
    now = _utcnow_iso()

    return {
        "mission_id": mission_id,
        "created_at": now,
        "updated_at": now,
        "created_by": body.get("created_by", "TRINITY"),
        "target": target,
        "task_type": task_type,
        "priority": body.get("priority", "normal"),
        "status": body.get("status", "queued"),
        "intent": intent,
        "context": body.get("context", {}),
        "recommended_agent": gouv4_router.route(task_type),
        "result": body.get("result"),
    }


def _upsert_mission(state: dict, mission: dict) -> dict:
    """Insert or replace a mission in active/history state."""
    missions = state["missions"]["active"]
    for index, current in enumerate(missions):
        if current.get("mission_id") == mission["mission_id"]:
            missions[index] = mission
            break
    else:
        missions.insert(0, mission)
    return mission


def _archive_mission(state: dict, mission: dict):
    """Move completed mission from active queue to history."""
    state["missions"]["active"] = [
        item for item in state["missions"]["active"]
        if item.get("mission_id") != mission.get("mission_id")
    ]
    history = state["missions"]["history"]
    history.insert(0, mission)
    state["missions"]["history"] = history[:50]


def _build_mesh_status(state: dict) -> dict:
    """Expose a single GPT-friendly view of agent mesh and routing capacity."""
    report = gouv4_router.report()
    return {
        "ok": True,
        "mesh": {
            "agents": state.get("agents", {}),
            "pipeline": state.get("pipeline", {}),
            "missions_active": len(state.get("missions", {}).get("active", [])),
            "intel_entries": len(state.get("intel", {}).get("comet_feed", [])),
        },
        "gouv4": report,
        "updated_at": state.get("_meta", {}).get("updated_at"),
    }


def _record_comet_intel(state: dict, summary: str, level: str = "INFO", source: str = "TRINITY") -> dict:
    """Persist COMET-style intel into shared memory for cross-agent consumption."""
    entry = {
        "ts": _utcnow_iso(),
        "source": source,
        "level": level,
        "summary": summary,
    }
    feed = state["intel"]["comet_feed"]
    feed.insert(0, entry)
    state["intel"]["comet_feed"] = feed[:50]
    return entry


def _process_running(process_name: str) -> bool:
    """Portable process check that works on slim images without pgrep."""
    try:
        result = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return False

    return process_name in result.stdout


def _fetch_creator_wallet_snapshot(address: str) -> dict:
    """Read public wallet data for the creator wallet without exposing the seed."""
    snapshot = {
        "label": "Wallet creator",
        "address": address,
        "connected": bool(address),
        "custody": "google_secret_manager",
        "akt_balance": None,
        "akt_price_usd": None,
        "akt_value_usd": None,
        "last_fetch": _utcnow_iso(),
    }
    if not address:
        return snapshot

    try:
        response = requests.get(
            f"https://rest.cosmos.directory/akash/cosmos/bank/v1beta1/balances/{address}",
            timeout=8,
        )
        response.raise_for_status()
        balances = response.json().get("balances", [])
        for balance in balances:
            if balance.get("denom") == "uakt":
                snapshot["akt_balance"] = round(int(balance.get("amount", 0)) / 1_000_000, 6)
                break
    except Exception:
        pass

    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "akash-network", "vs_currencies": "usd"},
            timeout=8,
        )
        response.raise_for_status()
        price = response.json().get("akash-network", {}).get("usd")
        if price is not None:
            snapshot["akt_price_usd"] = price
            if snapshot["akt_balance"] is not None:
                snapshot["akt_value_usd"] = round(snapshot["akt_balance"] * price, 2)
    except Exception:
        pass

    return snapshot


def _status_summary(status: dict) -> dict:
    """Normalize status for GPT-friendly summaries."""
    pipeline_status = (status.get("pipeline_status") or "INIT").strip() or "INIT"
    action = (status.get("arkon5_action") or "HOLD").strip() or "HOLD"
    confidence = status.get("arkon5_conf") or 0
    tunnel_mode = status.get("tunnel_mode") or ("online" if status.get("tunnel_active") else "offline")
    tunnel_state = "online" if tunnel_mode == "active" else tunnel_mode
    missions_active = int(status.get("missions_active") or 0)
    mesh_agents_online = int(status.get("mesh_agents_online") or 0)
    runtime_bridge_state = status.get("runtime_bridge_state")
    runtime_direct = runtime_bridge_state == "direct_runtime_linked"
    ha_warning = status.get("ha_warning")
    ha_connected = bool(status.get("ha_connected"))
    ha_configured = bool(status.get("ha_configured", ha_connected))

    summary_parts = [f"S25 en ligne. Pipeline {pipeline_status}."]
    if action in {"READY", "OBSERVE"} and missions_active:
        summary_parts.append(
            f"Mesh actif avec {mesh_agents_online} agents online et {missions_active} mission(s)."
        )
    else:
        summary_parts.append(f"Signal {action} ({confidence}).")
    if runtime_direct:
        summary_parts.append("Ligne directe runtime active.")
    else:
        summary_parts.append(f"Tunnel {tunnel_state}.")
    if ha_warning or (ha_configured and not ha_connected):
        summary_parts.append("Nabu Casa lateral indisponible.")
    elif ha_connected:
        summary_parts.append("HA lateral disponible.")

    return {
        "ok": True,
        "availability": "available",
        "status": "online",
        "service": "S25 Lumiere Status",
        "summary_fr": " ".join(summary_parts),
        "runtime_bridge_state": status.get("runtime_bridge_state"),
        "runtime_bridge_endpoint": status.get("runtime_bridge_endpoint"),
        "runtime_bridge_marker": status.get("runtime_bridge_marker"),
        "system": {
            "pipeline": pipeline_status,
            "signal": action,
            "confidence": confidence,
            "tunnel": tunnel_state,
            "hashrate": status.get("hashrate", "--"),
            "temperature": status.get("temp", "--"),
            "intel": status.get("comet_intel", "En attente..."),
            "ha": {
                "configured": ha_configured,
                "connected": ha_connected,
                "warning": ha_warning,
            },
            "runtime_bridge": {
                "state": status.get("runtime_bridge_state"),
                "endpoint": status.get("runtime_bridge_endpoint"),
                "marker": status.get("runtime_bridge_marker"),
            },
        },
    }


def _runtime_bridge_snapshot(state: dict | None = None) -> dict:
    state = state or _load_agents_state()
    missions_active = len(state.get("missions", {}).get("active", []))
    trinity_state = state.get("agents", {}).get("TRINITY", {})
    trinity_status = trinity_state.get("status", "unknown")
    probe_at = _utcnow_iso()
    return {
        "bridge_id": "s25_direct_bridge_v1",
        "bridge_state": "direct_runtime_linked",
        "public_base_url": PUBLIC_RUNTIME_BASE,
        "direct_bridge_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/trinity",
        "direct_ping_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/trinity/ping",
        "status_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/status",
        "secure_memory_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/memory/state",
        "authority_header": "x-s25-secret",
        "source_of_truth": "S25 Lumiere runtime",
        "gemini_layer": "MERLIN / Gemini validation core",
        "trinity_agent_status": trinity_status,
        "trinity_last_intent": trinity_state.get("last_intent"),
        "missions_active": missions_active,
        "runtime_marker": f"s25-direct::{APP_BUILD_SHA}::{trinity_status}::{missions_active}::{probe_at}",
        "probe_at": probe_at,
        "last_sync": state.get("_meta", {}).get("updated_at"),
    }


def _hydrate_status_from_memory(status: dict) -> dict:
    """Backfill status from shared memory when HA data is absent or incomplete."""
    state = _load_agents_state()
    pipeline = state.get("pipeline", {})
    missions = state.get("missions", {}).get("active", [])
    feed = state.get("intel", {}).get("comet_feed", [])
    market = state.get("market", {})
    agents = state.get("agents", {})
    runtime_bridge = _runtime_bridge_snapshot(state)
    for agent_id, runtime in agents.items():
        _normalize_agent_runtime(agent_id, runtime)

    online_agents = sum(
        1 for details in agents.values()
        if _is_operational_status(details.get("status"))
    )

    last_signal = pipeline.get("last_signal") or {}
    status["arkon5_action"] = str(
        last_signal.get("trade_action")
        or last_signal.get("action")
        or status.get("arkon5_action")
        or "HOLD"
    )
    status["arkon5_conf"] = last_signal.get("confidence", status.get("arkon5_conf", 0)) or 0

    active_model = str(pipeline.get("active_model") or "").strip()
    pipeline_mode = str(pipeline.get("mode") or "").strip()
    if active_model and active_model != "INIT":
        status["pipeline_status"] = active_model
    elif missions and online_agents >= 3:
        status["pipeline_status"] = "MESH_READY"
    elif runtime_bridge.get("bridge_state") == "direct_runtime_linked" and online_agents >= 5:
        status["pipeline_status"] = "MESH_READY"
    elif pipeline_mode:
        status["pipeline_status"] = pipeline_mode.upper()

    if feed:
        status["comet_intel"] = feed[0].get("summary", status.get("comet_intel"))
    elif missions:
        status["comet_intel"] = missions[0].get("intent", status.get("comet_intel"))
    elif runtime_bridge.get("bridge_state") == "direct_runtime_linked":
        status["comet_intel"] = "Runtime bridge direct linked."

    kimi_status = agents.get("KIMI", {}).get("status")
    status["tunnel_active"] = bool(status.get("tunnel_active")) or str(kimi_status).lower() == "online"
    status["missions_active"] = len(missions)
    status["mesh_agents_online"] = online_agents
    status["ha_configured"] = bool(HA_TOKEN)
    status["ha_connected"] = bool(status.get("ha_connected"))
    if status.get("runtime_bridge_state") == "direct_runtime_linked" and not status.get("tunnel_active"):
        status["tunnel_mode"] = "lateral_optional"
    else:
        status["tunnel_mode"] = "active" if status.get("tunnel_active") else "offline"
    wallet_state = state.get("wallet", {})
    creator_snapshot = _fetch_creator_wallet_snapshot(
        wallet_state.get("creator_address", MASTER_WALLET_ADDRESS)
    )
    state["wallet"].update(
        {
            "creator_label": creator_snapshot.get("label", "Wallet creator"),
            "creator_address": creator_snapshot.get("address", MASTER_WALLET_ADDRESS),
            "creator_connected": creator_snapshot.get("connected", bool(MASTER_WALLET_ADDRESS)),
            "custody": creator_snapshot.get("custody", "google_secret_manager"),
            "creator_akt_balance": creator_snapshot.get("akt_balance"),
            "creator_akt_price_usd": creator_snapshot.get("akt_price_usd"),
            "creator_akt_value_usd": creator_snapshot.get("akt_value_usd"),
            "last_sync": creator_snapshot.get("last_fetch"),
        }
    )
    status["wallet_creator_address"] = state["wallet"].get("creator_address", MASTER_WALLET_ADDRESS)
    status["wallet_creator_connected"] = bool(state["wallet"].get("creator_connected"))
    status["wallet_custody"] = state["wallet"].get("custody", "google_secret_manager")
    status["wallet_creator_akt_balance"] = state["wallet"].get("creator_akt_balance")
    status["wallet_creator_akt_price_usd"] = state["wallet"].get("creator_akt_price_usd")
    status["wallet_creator_akt_value_usd"] = state["wallet"].get("creator_akt_value_usd")
    status["wallet"] = {
        "label": state["wallet"].get("creator_label", "Wallet creator"),
        "address": state["wallet"].get("creator_address", MASTER_WALLET_ADDRESS),
        "connected": bool(state["wallet"].get("creator_connected")),
        "custody": state["wallet"].get("custody", "google_secret_manager"),
        "akt_balance": state["wallet"].get("creator_akt_balance"),
        "akt_price_usd": state["wallet"].get("creator_akt_price_usd"),
        "akt_value_usd": state["wallet"].get("creator_akt_value_usd"),
        "last_sync": state["wallet"].get("last_sync"),
    }
    state["runtime_bridge"] = _runtime_bridge_snapshot(state)
    status["runtime_bridge"] = state["runtime_bridge"]
    status["runtime_bridge_id"] = state["runtime_bridge"]["bridge_id"]
    status["runtime_bridge_state"] = state["runtime_bridge"]["bridge_state"]
    status["runtime_bridge_endpoint"] = state["runtime_bridge"]["direct_bridge_endpoint"]
    status["runtime_bridge_marker"] = state["runtime_bridge"]["runtime_marker"]
    status["runtime_bridge_probe_at"] = state["runtime_bridge"]["probe_at"]

    # When the mesh is alive but ARKON has not emitted a fresh trade signal yet,
    # surface readiness instead of stale INIT/HOLD defaults.
    if not last_signal and runtime_bridge.get("bridge_state") == "direct_runtime_linked" and online_agents >= 5:
        status["arkon5_action"] = "READY"
        status["arkon5_conf"] = max(int(status.get("arkon5_conf") or 0), min(online_agents * 6, 75))
    elif not last_signal and missions and online_agents >= 3:
        status["arkon5_action"] = "READY"
        status["arkon5_conf"] = max(int(status.get("arkon5_conf") or 0), min(online_agents * 10, 60))
    elif not last_signal and online_agents >= 3:
        status["arkon5_action"] = "OBSERVE"
        status["arkon5_conf"] = max(int(status.get("arkon5_conf") or 0), 25)

    if market.get("btc_usd") is not None:
        status["btc_usd"] = market.get("btc_usd")
    if market.get("eth_usd") is not None:
        status["eth_usd"] = market.get("eth_usd")

    trading_state = state.get("trading", {})
    lanes_state = trading_state.get("lanes", {})

    def _lane_payload(lane_id: str, members: list[str], fallback_headline: str) -> dict:
        online = 0
        member_states = []
        for agent_id in members:
            runtime = agents.get(agent_id, {})
            agent_status = runtime.get("status", "offline")
            if _is_operational_status(agent_status):
                online += 1
            member_states.append(
                {
                    "agent_id": agent_id,
                    "status": agent_status,
                    "last_task": runtime.get("last_task"),
                    "last_seen": runtime.get("last_seen"),
                }
            )
        lane_runtime = lanes_state.get(lane_id, {})
        mission_count = len([mission for mission in missions if mission.get("target") in members])
        return {
            "lane_id": lane_id,
            "headline": lane_runtime.get("headline", fallback_headline),
            "online_count": online,
            "member_count": len(members),
            "mission_count": mission_count,
            "live_state": "online" if online else "standby",
            "members": member_states,
            "last_sync": lane_runtime.get("last_sync", trading_state.get("last_sync")),
        }

    status["trading"] = {
        "mode": trading_state.get("mode", "showroom"),
        "policy_state": trading_state.get("policy_state", "audit_first"),
        "lanes": [
            _lane_payload("signal_lane", ["TRINITY", "KIMI", "ORACLE"], status.get("arkon5_action", "READY")),
            _lane_payload("risk_lane", ["MERLIN", "ONCHAIN_GUARDIAN", "GOUV4"], status.get("pipeline_status", "MESH_READY")),
            _lane_payload("treasury_lane", ["TREASURY"], f"{status.get('wallet_creator_akt_balance') or '--'} AKT"),
            _lane_payload("execution_lane", ["ARKON"], "mirror wallet armed"),
        ],
        "last_sync": trading_state.get("last_sync"),
    }

    return status


HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ S25 LUMIÈRE — COCKPIT</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: radial-gradient(ellipse at top, #0d1b2a 0%, #0a0a0f 100%);
  color: #e0e6ff; font-family: 'Courier New', monospace;
  min-height: 100vh; overflow-x: hidden;
}
.scanlines {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,200,0.015) 2px, rgba(0,255,200,0.015) 4px);
  pointer-events: none; z-index: 1;
}
.container { max-width: 1200px; margin: 0 auto; padding: 20px; position: relative; z-index: 2; }
.header { text-align: center; margin-bottom: 30px; }
.header h1 {
  font-size: 2.5rem; color: #00ffcc;
  text-shadow: 0 0 20px #00ffcc, 0 0 40px #00ffcc;
  animation: pulse 2s ease-in-out infinite;
  letter-spacing: 0.3em;
}
@keyframes pulse {
  0%, 100% { opacity: 1; } 50% { opacity: 0.8; }
}
.subtitle { color: #4fc3f7; font-size: 0.9rem; letter-spacing: 0.2em; margin-top: 5px; }
.timestamp { color: #546e7a; font-size: 0.75rem; margin-top: 5px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px; }
.card {
  background: rgba(0, 255, 200, 0.05);
  border: 1px solid rgba(0, 255, 200, 0.2);
  border-radius: 12px; padding: 20px;
  transition: all 0.3s ease;
  position: relative; overflow: hidden;
}
.card:hover { border-color: rgba(0, 255, 200, 0.5); box-shadow: 0 0 20px rgba(0, 255, 200, 0.1); }
.card::before {
  content: ''; position: absolute; top: 0; left: -100%;
  width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, #00ffcc, transparent);
  animation: scan 3s linear infinite;
}
@keyframes scan { to { left: 200%; } }
.card-title { color: #00ffcc; font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 10px; }
.card-value { font-size: 2rem; font-weight: bold; color: #fff; }
.card-value.green { color: #00ff88; text-shadow: 0 0 10px #00ff88; }
.card-value.red { color: #ff4444; text-shadow: 0 0 10px #ff4444; }
.card-value.orange { color: #ff9800; text-shadow: 0 0 10px #ff9800; }
.card-value.blue { color: #4fc3f7; text-shadow: 0 0 10px #4fc3f7; }
.card-subtitle { color: #546e7a; font-size: 0.75rem; margin-top: 5px; }
.status-dot {
  width: 10px; height: 10px; border-radius: 50%;
  display: inline-block; margin-right: 8px;
  animation: blink 1s ease-in-out infinite;
}
.status-dot.green { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
.status-dot.red { background: #ff4444; box-shadow: 0 0 8px #ff4444; }
.status-dot.orange { background: #ff9800; box-shadow: 0 0 8px #ff9800; }
@keyframes blink { 50% { opacity: 0.3; } }
.section-title { color: #4fc3f7; font-size: 0.9rem; letter-spacing: 0.2em; margin: 20px 0 10px; border-bottom: 1px solid rgba(79, 195, 247, 0.2); padding-bottom: 5px; }
.agents-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
.agent-card {
  background: rgba(79, 195, 247, 0.05); border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 8px; padding: 15px; text-align: center;
}
.agent-name { color: #4fc3f7; font-size: 0.85rem; letter-spacing: 0.15em; margin-bottom: 8px; }
.agent-status { font-size: 0.75rem; color: #546e7a; }
.controls { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
.btn {
  padding: 10px 20px; border: 1px solid rgba(0, 255, 200, 0.4);
  background: rgba(0, 255, 200, 0.1); color: #00ffcc;
  border-radius: 6px; cursor: pointer; font-family: 'Courier New', monospace;
  font-size: 0.8rem; letter-spacing: 0.1em; transition: all 0.2s;
}
.btn:hover { background: rgba(0, 255, 200, 0.2); box-shadow: 0 0 15px rgba(0, 255, 200, 0.3); }
.btn.red { border-color: rgba(255, 68, 68, 0.4); background: rgba(255, 68, 68, 0.1); color: #ff4444; }
.btn.red:hover { background: rgba(255, 68, 68, 0.2); }
.intel-box {
  background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(0, 255, 200, 0.15);
  border-radius: 8px; padding: 15px; font-size: 0.8rem; color: #80cbc4;
  max-height: 150px; overflow-y: auto; white-space: pre-wrap;
  font-family: 'Courier New', monospace;
}
.threat-bar {
  display: flex; gap: 5px; margin: 10px 0;
}
.threat-level {
  flex: 1; padding: 8px; border-radius: 4px; text-align: center;
  font-size: 0.7rem; letter-spacing: 0.1em; border: 1px solid transparent;
}
.threat-level.active-t0 { background: rgba(0, 255, 136, 0.2); border-color: #00ff88; color: #00ff88; }
.threat-level.active-t1 { background: rgba(255, 235, 59, 0.2); border-color: #ffeb3b; color: #ffeb3b; }
.threat-level.active-t2 { background: rgba(255, 152, 0, 0.2); border-color: #ff9800; color: #ff9800; }
.threat-level.active-t3 { background: rgba(255, 68, 68, 0.2); border-color: #ff4444; color: #ff4444; }
.threat-level.inactive { background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.05); color: #37474f; }
footer { text-align: center; color: #263238; font-size: 0.7rem; margin-top: 30px; letter-spacing: 0.2em; }
</style>
</head>
<body>
<div class="scanlines"></div>
<div class="container">
  <div class="header">
    <h1>⚡ S25 LUMIÈRE</h1>
    <div class="subtitle">ARKON-5 COMMAND CENTER // COCKPIT v1.0</div>
    <div class="timestamp" id="clock">--</div>
  </div>

  <!-- THREAT LEVEL BAR -->
  <div id="threat-bar" class="threat-bar">
    <div class="threat-level active-t0">T0 🟢 NORMAL</div>
    <div class="threat-level inactive">T1 🟡 SURVEILLANCE</div>
    <div class="threat-level inactive">T2 🟠 ALERTE</div>
    <div class="threat-level inactive">T3 🔴 CRITIQUE</div>
  </div>

  <!-- STATUS CARDS -->
  <div class="grid" id="status-grid">
    <div class="card">
      <div class="card-title">🎯 SIGNAL ARKON-5</div>
      <div class="card-value" id="arkon-action">--</div>
      <div class="card-subtitle" id="arkon-conf">Confiance: --</div>
    </div>
    <div class="card">
      <div class="card-title">📊 PIPELINE S25</div>
      <div class="card-value blue" id="pipeline-status">--</div>
      <div class="card-subtitle">Modèle actif</div>
    </div>
    <div class="card">
      <div class="card-title">⛏️ HASHRATE</div>
      <div class="card-value orange" id="hashrate">-- TH/s</div>
      <div class="card-subtitle" id="temp">Temp: --°C</div>
    </div>
    <div class="card">
      <div class="card-title">🌐 TUNNEL S25</div>
      <div class="card-value" id="tunnel-status">--</div>
      <div class="card-subtitle">Cloudflare ↔ Kimi</div>
    </div>
  </div>

  <!-- AGENTS STATUS -->
  <div class="section-title">⟐ AGENTS NETWORK</div>
  <div class="agents-grid">
    <div class="agent-card">
      <div class="agent-name">🤖 MERLIN</div>
      <div><span class="status-dot green"></span><span class="agent-status">Orchestrateur HA</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🔭 COMET</div>
      <div><span class="status-dot green"></span><span class="agent-status">Watchman Radar</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🧠 GEMINI</div>
      <div><span class="status-dot green"></span><span class="agent-status">ARKON-5 Analyzer</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🌐 KIMI Web3</div>
      <div><span class="status-dot orange"></span><span class="agent-status">Signal Source</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🤝 GPT</div>
      <div><span class="status-dot green"></span><span class="agent-status">GOUV4 Planner</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">⚡ CLAUDE</div>
      <div><span class="status-dot green"></span><span class="agent-status">Builder / Deploy</span></div>
    </div>
  </div>

  <!-- COMET INTEL -->
  <div class="section-title">📡 INTEL COMET</div>
  <div class="intel-box" id="comet-intel">En attente de connexion HA...</div>

  <!-- CONTRÔLES -->
  <div class="section-title">🎛️ CONTRÔLES</div>
  <div class="controls">
    <button class="btn" onclick="startTunnel()">▶ START TUNNEL</button>
    <button class="btn" onclick="stopTunnel()">⬛ STOP TUNNEL</button>
    <button class="btn" onclick="refreshData()">⟳ REFRESH</button>
    <button class="btn" onclick="forceAnalysis()">🧠 FORCE ANALYSE</button>
    <button class="btn red" onclick="confirmPurge()">🚨 PURGE (KILL)</button>
  </div>

  <footer>S25 LUMIÈRE COCKPIT v1.0 // AKASH CENTOS // CLAUDE BUILD // {{ now }}</footer>
</div>

<script>
// Auto-refresh toutes les 30s
let refreshTimer = setInterval(refreshData, 30000);

function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleString('fr-CA');
}
setInterval(updateClock, 1000);
updateClock();

async function refreshData() {
  try {
    const r = await fetch('/api/status');
    const data = await r.json();

    // Arkon action
    const action = data.arkon5_action || 'HOLD';
    const actionEl = document.getElementById('arkon-action');
    actionEl.textContent = action;
    actionEl.className = 'card-value ' + (action === 'BUY' ? 'green' : action === 'SELL' ? 'red' : 'orange');

    document.getElementById('arkon-conf').textContent = 'Confiance: ' + (data.arkon5_conf || '--') + '%';
    document.getElementById('pipeline-status').textContent = (data.pipeline_status || '--').substring(0, 20);
    document.getElementById('hashrate').textContent = (data.hashrate || '--') + ' TH/s';
    document.getElementById('temp').textContent = 'Temp: ' + (data.temp || '--') + '°C';
    document.getElementById('comet-intel').textContent = data.comet_intel || '--';

    const tunnelEl = document.getElementById('tunnel-status');
    tunnelEl.textContent = data.tunnel_active ? '🟢 ACTIF' : '🔴 INACTIF';
    tunnelEl.className = 'card-value ' + (data.tunnel_active ? 'green' : 'red');

  } catch(e) {
    console.error('Refresh error:', e);
  }
}

async function startTunnel() {
  await fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'start_tunnel'}) });
  refreshData();
}
async function stopTunnel() {
  await fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'stop_tunnel'}) });
  refreshData();
}
async function forceAnalysis() {
  await fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'force_analysis'}) });
  alert('Analyse ARKON-5 déclenchée!');
}
function confirmPurge() {
  if (confirm('⚠️ CONFIRMER LA PURGE TOTALE S25? Cette action coupe toutes les opérations critiques.')) {
    fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'purge'}) });
    alert('🚨 PURGE EXÉCUTÉE');
  }
}
refreshData();
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML, now=datetime.now().strftime('%Y-%m-%d'))

@app.route('/api/status')
def api_status():
    """Retourne l'état du système S25 depuis HA"""
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "arkon5_action": "HOLD",
        "arkon5_conf": 0,
        "pipeline_status": "INIT",
        "hashrate": "--",
        "temp": "--",
        "comet_intel": "En attente...",
        "tunnel_active": False,
        "missions_active": 0,
        "ha_configured": bool(HA_TOKEN),
        "ha_connected": False,
        "wallet_creator_address": MASTER_WALLET_ADDRESS,
        "wallet_creator_connected": bool(MASTER_WALLET_ADDRESS),
        "wallet_custody": "google_secret_manager",
        "wallet_creator_akt_balance": None,
        "wallet_creator_akt_price_usd": None,
        "wallet_creator_akt_value_usd": None,
        "runtime_bridge_id": "s25_direct_bridge_v1",
        "runtime_bridge_state": "direct_runtime_linked",
        "runtime_bridge_endpoint": f"{PUBLIC_RUNTIME_BASE}/api/trinity",
        "runtime_bridge_marker": None,
        "runtime_bridge_probe_at": None,
    }

    if not HA_TOKEN:
        _hydrate_status_from_memory(status)
        status.update(_status_summary(status))
        return jsonify(status)

    try:
        headers = {"Authorization": f"Bearer {HA_TOKEN}"}
        entities = ["sensor.s25_arkon5_action", "sensor.s25_arkon5_conf",
                    "input_text.ai_model_actif", "sensor.antminer_hashrate",
                    "sensor.antminer_temp", "input_text.s25_comet_intel"]

        ha_requests_ok = False
        for entity in entities:
            r = requests.get(f"{HA_URL}/api/states/{entity}", headers=headers, timeout=5)
            if r.status_code == 200:
                ha_requests_ok = True
                state = r.json().get("state", "--")
                if "arkon5_action" in entity: status["arkon5_action"] = state
                elif "arkon5_conf" in entity: status["arkon5_conf"] = state
                elif "ai_model_actif" in entity: status["pipeline_status"] = state
                elif "antminer_hashrate" in entity: status["hashrate"] = state
                elif "antminer_temp" in entity: status["temp"] = state
                elif "comet_intel" in entity: status["comet_intel"] = state
        status["ha_connected"] = ha_requests_ok

        # Check tunnel without depending on pgrep, which is absent on slim images.
        status["tunnel_active"] = _process_running("cloudflared")

    except Exception as e:
        status["ha_warning"] = str(e)

    _hydrate_status_from_memory(status)
    if status.get("runtime_bridge_state") == "direct_runtime_linked":
        status.pop("error", None)
    status.update(_status_summary(status))
    return jsonify(status)

@app.route('/api/action', methods=['POST'])
def api_action():
    """Exécute une action sur le système S25"""
    data = request.get_json()
    action = data.get('action', '')
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}

    if action == 'start_tunnel':
        subprocess.Popen(["bash", "/config/scripts/start_s25_tunnel.sh"])
        return jsonify({"ok": True, "msg": "Tunnel démarré"})

    elif action == 'stop_tunnel':
        subprocess.run(["pkill", "-f", "cloudflared"])
        return jsonify({"ok": True, "msg": "Tunnel arrêté"})

    elif action == 'force_analysis':
        requests.post(f"{HA_URL}/api/services/automation/trigger",
                     headers=headers, json={"entity_id": "automation.s25_arkon5_buy_alert"})
        return jsonify({"ok": True, "msg": "Analyse déclenchée"})

    elif action == 'purge':
        requests.post(f"{HA_URL}/api/services/input_boolean/turn_on",
                     headers=headers, json={"entity_id": "input_boolean.s25_kill_switch"})
        return jsonify({"ok": True, "msg": "PURGE EXÉCUTÉE"})

    return jsonify({"ok": False, "msg": "Action inconnue"})

@app.route('/api/watchdog')
def api_watchdog():
    """Retourne le statut du watchdog"""
    try:
        with open('/tmp/s25_watchdog_status.json') as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify({"error": "Watchdog status unavailable"})

@app.route('/api/version', methods=['GET'])
def api_version():
    """Expose la version runtime pour verifier l'image active sur Akash."""
    return jsonify({
        "service": "S25 Lumiere Cockpit",
        "version": "2.0.0",
        "build_sha": APP_BUILD_SHA,
        "memory_routes": True,
        "secret_configured": bool(S25_SECRET),
    })


@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def api_health():
    """Compat health endpoint for providers and external checks."""
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "build_sha": APP_BUILD_SHA,
    })


# ═══════════════════════════════════════════════════════════════
#  TRINITY BRIDGE — GPT Custom Action endpoint
#  TRINITY (GPT) parle ici -> S25 reseau repond
# ═══════════════════════════════════════════════════════════════

def _trinity_auth() -> bool:
    """Verifie S25_SHARED_SECRET si configure."""
    if ALLOW_PUBLIC_ACTIONS or not S25_SECRET:
        return True
    return request.headers.get("X-S25-Secret", "") == S25_SECRET

def _merlin_query(prompt: str) -> str:
    """Appel direct Merlin (Gemini) pour reponse intelligente."""
    if not GEMINI_API_KEY:
        return "MERLIN OFFLINE: GEMINI_API_KEY non configuree"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        r = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        if r.status_code == 200:
            candidates = r.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Merlin error: {e}"
    return "Merlin: pas de reponse"

def _market_snapshot() -> dict:
    """Snapshot marche crypto gratuit via CoinGecko + Fear&Greed."""
    snapshot = {"timestamp": datetime.utcnow().isoformat(), "prices": {}, "fear_greed": {}, "source": "ninja_free"}
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,akash-network,cosmos,solana",
                    "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10)
        if r.status_code == 200:
            snapshot["prices"] = r.json()
    except Exception:
        pass
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        if r.status_code == 200:
            d = r.json()["data"][0]
            snapshot["fear_greed"] = {"value": d["value"], "label": d["value_classification"]}
    except Exception:
        pass
    return snapshot

@app.route('/api/trinity/ping', methods=['GET'])
def trinity_ping():
    """Healthcheck pour GPT Custom Action."""
    return jsonify({
        "ok": True,
        "service": "S25 Lumiere — TRINITY Bridge",
        "version": "2.0.0",
        "merlin": "online" if GEMINI_API_KEY else "offline",
        "ha": "connected" if HA_TOKEN else "disconnected",
    })

@app.route('/api/trinity', methods=['POST'])
def trinity_dispatch():
    """
    Endpoint principal TRINITY (GPT).
    Body JSON:
      intent  : texte de l'intention de Stef
      action  : "query" | "signal" | "analyze" | "status"
      data    : {} payload optionnel
    """
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body   = request.get_json(silent=True) or {}
    intent = body.get("intent", "").strip()
    action = body.get("action", "query").lower()
    data   = body.get("data", {})

    # ── STATUS: etat du systeme ──────────────────────────────────────
    if action == "status":
        snap = _market_snapshot()
        live_status = api_status().get_json()
        state = _load_agents_state()
        return jsonify({
            "ok": True,
            "action": "status",
            "availability": "available",
            "summary_fr": live_status.get("summary_fr", "S25 en ligne."),
            "system": {
                "ha_connected": bool(HA_TOKEN),
                "merlin_online": bool(GEMINI_API_KEY),
                "cockpit": "ACTIVE",
            },
            "status_payload": live_status,
            "mesh": _build_mesh_status(state)["mesh"],
            "market": snap,
        })

    # ── ANALYZE: Merlin analyse un intent specifique ─────────────────
    if action == "analyze":
        snap = _market_snapshot()
        prices = snap.get("prices", {})
        btc = prices.get("bitcoin", {}).get("usd", 0)
        eth = prices.get("ethereum", {}).get("usd", 0)
        fg  = snap.get("fear_greed", {})
        prompt = f"""Tu es MERLIN, analyste senior du reseau S25 Lumiere (multi-agent crypto trading).
Stef te demande: "{intent}"

Contexte marche actuel:
- BTC: ${btc:,.0f} USD
- ETH: ${eth:,.2f} USD
- Fear & Greed: {fg.get('value','?')}/100 ({fg.get('label','?')})

Reponds de facon concise et actionnable. Donne une recommandation claire (BUY/HOLD/SELL/WATCH) si applicable."""
        analysis = _merlin_query(prompt)
        return jsonify({
            "ok": True,
            "action": "analyze",
            "intent": intent,
            "merlin_response": analysis,
            "market_context": snap,
        })

    # ── SIGNAL: injection d'un signal de trade ───────────────────────
    if action == "signal":
        signal_data = {
            "type":   "MANUAL",
            "source": "TRINITY_GPT",
            "data": {
                "intent":     intent,
                "trade_action": data.get("trade_action", "HOLD"),
                "symbol":     data.get("symbol", ""),
                "confidence": data.get("confidence", 0.7),
                "reason":     intent,
            },
            "ts": datetime.utcnow().isoformat(),
        }
        # Push vers HA si connecte
        if HA_TOKEN:
            try:
                requests.post(
                    f"{HA_URL}/api/states/sensor.s25_trinity_signal",
                    headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
                    json={"state": data.get("trade_action", "HOLD"),
                          "attributes": {"intent": intent, "source": "TRINITY", "ts": signal_data["ts"]}},
                    timeout=5)
            except Exception:
                pass
        return jsonify({"ok": True, "action": "signal", "signal": signal_data})

    if action == "mission":
        state = _load_agents_state()
        mission = _mission_payload({
            "created_by": "TRINITY",
            "target": data.get("target", "COMET"),
            "task_type": data.get("task_type", "infra_monitoring"),
            "priority": data.get("priority", "normal"),
            "intent": intent,
            "context": data.get("context", {}),
        })
        _upsert_mission(state, mission)
        state["agents"]["TRINITY"]["last_intent"] = intent
        if mission["target"] in state["agents"]:
            state["agents"][mission["target"]]["last_task"] = intent
        _record_comet_intel(
            state,
            summary=f"Mission queued for {mission['target']}: {intent}",
            level="INFO",
            source="TRINITY",
        )
        _save_agents_state(state)
        return jsonify({
            "ok": True,
            "action": "mission",
            "mission": mission,
            "mesh": _build_mesh_status(state)["mesh"],
        })

    if action == "route":
        task_type = data.get("task_type", "strategy_planning")
        chosen = gouv4_router.route(task_type)
        report = gouv4_router.report()
        return jsonify({
            "ok": True,
            "action": "route",
            "task_type": task_type,
            "recommended_agent": chosen,
            "gouv4": report,
        })

    # ── QUERY: snapshot intel + reponse Merlin (default) ────────────
    snap = _market_snapshot()
    prices = snap.get("prices", {})
    btc = prices.get("bitcoin", {}).get("usd", 0)
    btc_chg = prices.get("bitcoin", {}).get("usd_24h_change", 0)
    eth = prices.get("ethereum", {}).get("usd", 0)
    fg  = snap.get("fear_greed", {})

    merlin_prompt = f"""Tu es MERLIN du reseau S25 Lumiere. Stef dit: "{intent or 'Donne-moi un update marche'}"

BTC: ${btc:,.0f} ({btc_chg:+.1f}% 24h) | ETH: ${eth:,.2f} | F&G: {fg.get('value','?')}/100 {fg.get('label','')}

Reponds en 2-3 phrases max, direct et actionnable."""

    merlin_resp = _merlin_query(merlin_prompt) if intent else "Pret a recevoir tes ordres, Stef."

    return jsonify({
        "ok": True,
        "action": "query",
        "intent": intent,
        "merlin_response": merlin_resp,
        "mesh_hint": _build_mesh_status(_load_agents_state())["mesh"],
        "market": snap,
    })




# ═══════════════════════════════════════════════════════════════
#  MEMORY SYSTEM — Mémoire persistante centralisée S25
#  Tous les agents lisent/écrivent ici
#  GET  /api/memory         → contexte complet
#  GET  /api/memory/state   → état runtime agents_state.json
#  POST /api/memory/state   → mise à jour état par un agent
# ═══════════════════════════════════════════════════════════════

def _load_agents_state() -> dict:
    """Charge agents_state.json depuis disque."""
    try:
        if AGENTS_STATE_FILE.exists():
            return _refresh_runtime_defaults(_ensure_state_shape(json.loads(AGENTS_STATE_FILE.read_text(encoding="utf-8"))))
    except Exception:
        pass
    return _refresh_runtime_defaults(_ensure_state_shape({}))

def _save_agents_state(state: dict):
    """Sauvegarde agents_state.json sur disque."""
    state = _refresh_runtime_defaults(_ensure_state_shape(state))
    state.setdefault("_meta", {})["updated_at"] = _utcnow_iso()
    AGENTS_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


@app.route('/api/memory', methods=['GET'])
def api_memory_get():
    """Retourne le contexte partagé complet (SHARED_MEMORY.md + agents_state.json)."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    shared_md = ""
    if SHARED_MEMORY_FILE.exists():
        shared_md = SHARED_MEMORY_FILE.read_text(encoding="utf-8")

    state = _load_agents_state()
    state["runtime_bridge"] = _runtime_bridge_snapshot(state)

    return jsonify({
        "ok": True,
        "shared_memory": shared_md,
        "agents_state": state,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    })


@app.route('/api/memory/state', methods=['GET'])
def api_memory_state_get():
    """Retourne uniquement agents_state.json (léger, pour polling fréquent)."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    state = _load_agents_state()
    state["runtime_bridge"] = _runtime_bridge_snapshot(state)
    return jsonify({"ok": True, "state": state})


@app.route('/api/memory/state', methods=['POST'])
def api_memory_state_post():
    """
    Un agent met à jour son état ou une section du state.
    Body JSON attendu:
      agent   : "TRINITY" | "ARKON" | "MERLIN" | "COMET" | "KIMI"
      updates : dict — champs à fusionner dans agents[agent]
      pipeline: dict (optionnel) — champs pipeline à mettre à jour
    """
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    agent   = body.get("agent", "").upper()
    updates = body.get("updates", {})
    pipeline_updates = body.get("pipeline", {})
    market_updates = body.get("market", {})
    wallet_updates = body.get("wallet", {})
    intel_updates = body.get("intel", {})
    trading_updates = body.get("trading", {})
    business_updates = body.get("business", {})
    runtime_bridge_updates = body.get("runtime_bridge", {})

    state = _load_agents_state()

    if agent and agent in state.get("agents", {}):
        state["agents"][agent].update(updates)
        state["agents"][agent]["last_seen"] = datetime.now(timezone.utc).isoformat()

    if pipeline_updates and "pipeline" in state:
        state["pipeline"].update(pipeline_updates)

    if market_updates and "market" in state:
        state["market"].update(market_updates)

    if wallet_updates and "wallet" in state:
        state["wallet"].update(wallet_updates)
        state["wallet"]["last_sync"] = datetime.now(timezone.utc).isoformat()

    if intel_updates and "intel" in state:
        for key, value in intel_updates.items():
            state["intel"][key] = value

    if trading_updates and "trading" in state:
        for key, value in trading_updates.items():
            if key == "lanes" and isinstance(value, dict):
                for lane_id, lane_payload in value.items():
                    state["trading"].setdefault("lanes", {}).setdefault(lane_id, {})
                    if isinstance(lane_payload, dict):
                        state["trading"]["lanes"][lane_id].update(lane_payload)
                        state["trading"]["lanes"][lane_id]["last_sync"] = datetime.now(timezone.utc).isoformat()
            else:
                state["trading"][key] = value
        state["trading"]["last_sync"] = datetime.now(timezone.utc).isoformat()

    if business_updates and "business" in state:
        for key, value in business_updates.items():
            if key in {"clients", "jobs", "quotes_invoices", "identities", "organizations", "events"} and isinstance(value, list):
                state["business"][key] = value
            elif key in {"identity_rollout", "provider_transition"} and isinstance(value, dict):
                state["business"][key] = value
            elif key == "last_write_at":
                state["business"][key] = value
        state["business"]["last_write_at"] = datetime.now(timezone.utc).isoformat()

    if runtime_bridge_updates and "runtime_bridge" in state:
        state["runtime_bridge"].update(runtime_bridge_updates)

    state["runtime_bridge"] = _runtime_bridge_snapshot(state)
    _save_agents_state(state)

    return jsonify({"ok": True, "agent": agent, "state": state["agents"].get(agent, {})})


@app.route('/api/mesh/status', methods=['GET'])
def api_mesh_status():
    """Vue unifiee du reseau d'agents, du pipeline et des quotas GOUV4."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    return jsonify(_build_mesh_status(_load_agents_state()))


@app.route('/api/router/report', methods=['GET'])
def api_router_report():
    """Expose le rapport de quotas/routage GOUV4."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    return jsonify({
        "ok": True,
        "router": "GOUV4",
        "report": gouv4_router.report(),
    })


@app.route('/api/router/route', methods=['POST'])
def api_router_route():
    """Choisit l'agent recommande pour un type de tache."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    task_type = body.get("task_type", "strategy_planning")
    chosen = gouv4_router.route(task_type)
    return jsonify({
        "ok": True,
        "task_type": task_type,
        "recommended_agent": chosen,
        "report": gouv4_router.report(),
    })


@app.route('/api/missions', methods=['GET'])
def api_missions_get():
    """Liste les missions actives et l'historique recent."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    state = _load_agents_state()
    missions = state.get("missions", {})
    return jsonify({
        "ok": True,
        "active": missions.get("active", []),
        "history": missions.get("history", [])[:10],
    })


@app.route('/api/missions', methods=['POST'])
def api_missions_post():
    """Cree une mission multi-agent persistante pour COMET, MERLIN, ARKON ou KIMI."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    state = _load_agents_state()
    mission = _mission_payload(body)
    _upsert_mission(state, mission)

    target = mission["target"]
    state["agents"].setdefault(target, {})
    state["agents"][target]["last_task"] = mission["intent"]
    state["agents"][target]["last_seen"] = _utcnow_iso()
    _record_comet_intel(
        state,
        summary=f"Mission queued for {target}: {mission['intent']}",
        level="INFO",
        source=mission["created_by"],
    )
    _save_agents_state(state)

    return jsonify({
        "ok": True,
        "mission": mission,
        "mesh": _build_mesh_status(state)["mesh"],
    })


@app.route('/api/missions/update', methods=['POST'])
def api_missions_update():
    """Met a jour le statut d'une mission et l'archive si terminee."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    mission_id = body.get("mission_id", "")
    state = _load_agents_state()
    missions = state.get("missions", {}).get("active", [])
    mission = next((item for item in missions if item.get("mission_id") == mission_id), None)

    if not mission:
        return jsonify({"ok": False, "error": f"Mission {mission_id} inconnue"}), 404

    mission["status"] = body.get("status", mission.get("status", "queued"))
    mission["updated_at"] = _utcnow_iso()
    mission["result"] = body.get("result", mission.get("result"))
    mission["context"] = {**mission.get("context", {}), **body.get("context", {})}

    actor = body.get("actor", mission.get("target", "TRINITY"))
    if actor in state.get("agents", {}):
        state["agents"][actor]["last_seen"] = _utcnow_iso()
        state["agents"][actor]["last_task"] = mission.get("intent")

    if mission["status"] in {"done", "completed", "failed", "cancelled"}:
        _archive_mission(state, mission)

    _record_comet_intel(
        state,
        summary=f"Mission {mission_id} -> {mission['status']}",
        level="INFO" if mission["status"] in {"done", "completed"} else "WARNING",
        source=actor,
    )
    _save_agents_state(state)

    return jsonify({"ok": True, "mission": mission})


@app.route('/api/comet/feed', methods=['GET'])
def api_comet_feed():
    """Retourne le feed COMET/intel conserve en memoire partagee."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    state = _load_agents_state()
    feed = state.get("intel", {}).get("comet_feed", [])
    n = int(request.args.get("n", 20))
    return jsonify({
        "ok": True,
        "feed": feed[:n],
        "count": len(feed),
    })


@app.route('/api/memory/ping', methods=['POST'])
def api_memory_ping():
    """Agent envoie un heartbeat — met à jour last_seen seulement."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body  = request.get_json(silent=True) or {}
    agent = body.get("agent", "").upper()
    state = _load_agents_state()

    if agent in state.get("agents", {}):
        state["agents"][agent]["last_seen"] = datetime.now(timezone.utc).isoformat()
        state["agents"][agent]["status"] = "online"
        _save_agents_state(state)
        return jsonify({"ok": True, "agent": agent, "ts": datetime.now(timezone.utc).isoformat()})

    return jsonify({"ok": False, "error": f"Agent {agent} inconnu"}), 404


@app.route('/api/intel', methods=['POST'])
def api_intel():
    """
    Reception d'intel depuis agent_loop.py, oracle_agent, KIMI, etc.
    Endpoint public leger — authentification par secret optionnel.
    Stocke dans comet_feed pour cross-agent consumption.

    Body JSON: {source, summary, level, details}
    """
    body    = request.get_json(silent=True) or {}
    source  = body.get("source", "UNKNOWN")[:50]
    summary = body.get("summary", "")[:500]
    level   = body.get("level", "INFO")
    _details = body.get("details", "")[:500]  # noqa: F841

    state = _load_agents_state()
    entry = _record_comet_intel(state, summary=summary, level=level, source=source)
    # Aussi mettre a jour le compteur intel
    state.setdefault("intel", {})["last_source"] = source
    state["intel"]["last_level"] = level
    _save_agents_state(state)

    return jsonify({"ok": True, "entry": entry})


@app.route('/api/signal', methods=['POST'])
def api_signal():
    """
    Reception d'un signal de trading depuis agent_loop.py, KIMI, ou ORACLE.
    Multi-source confidence weighting + consensus bonus (2+ sources agree -> +0.15).
    Mode authorized -> verdict EXECUTE | Mode dry_run -> verdict SIMULATE_EXECUTE.

    Body JSON: {action, symbol, confidence, price, reason, source}

    Poids par source (fiabilite historique):
      TRINITY=0.80, MERLIN=0.70, KIMI=0.65, ORACLE=0.60, AGENT_LOOP/ONCHAIN=0.55, COMET=0.50
    Formule: effective_confidence = (confidence * weight) + consensus_bonus
    Seuil arkon_pass: effective_confidence >= 0.60
    """
    SOURCE_WEIGHTS = {
        "TRINITY":    0.80,
        "MERLIN":     0.70,
        "KIMI":       0.65,
        "ORACLE":     0.60,
        "AGENT_LOOP": 0.55,
        "ONCHAIN":    0.55,
        "COMET":      0.50,
    }

    body       = request.get_json(silent=True) or {}
    action     = body.get("action", "HOLD").upper()
    symbol     = body.get("symbol", "BTC/USDT")
    confidence = float(body.get("confidence", 0.5))
    price      = float(body.get("price", 0.0))
    reason     = body.get("reason", "")[:300]
    source     = body.get("source", "AGENT")

    state    = _load_agents_state()
    pipeline = state.get("pipeline", {})
    ts       = _utcnow_iso()

    # --- Ponderation par source ---
    weight              = SOURCE_WEIGHTS.get(source.upper(), 0.55)
    weighted_confidence = round(confidence * weight, 4)

    # --- Consensus: meme symbole + meme action, source differente, dans 5 derniere min ---
    signals_buffer = pipeline.get("signals_buffer", [])
    # Purge entrees > 5 min (comparaison lexicographique ISO valide)
    cutoff = ts[:11] + "00:00:00Z"  # fallback grossier; utilise ts reel via slice
    # Calcul cutoff 5 min: on garde les ts >= ts[0:16] - 5min (string approx)
    signals_buffer = [s for s in signals_buffer if s.get("ts", "1970") >= ts[:10]]
    consensus_sources = [
        s for s in signals_buffer
        if s.get("symbol") == symbol
        and s.get("action") == action
        and s.get("source", "").upper() != source.upper()
    ]
    consensus       = len(consensus_sources) >= 1
    consensus_bonus = 0.15 if consensus else 0.0
    effective_confidence = round(weighted_confidence + consensus_bonus, 4)

    # --- Evaluation pipeline ---
    kill_switch  = pipeline.get("kill_switch", False)
    threat_level = pipeline.get("threat_level", "T0")
    mode         = pipeline.get("mode", "dry_run")

    arkon_pass = effective_confidence >= 0.60
    risk_pass  = arkon_pass and not kill_switch and threat_level in ("T0", "T1")

    if risk_pass:
        verdict = "EXECUTE" if mode == "authorized" else "SIMULATE_EXECUTE"
    else:
        verdict = "NO_TRADE"

    # --- Mise a jour buffer (max 20 entrees) ---
    signals_buffer.append({
        "symbol": symbol,
        "action": action,
        "source": source,
        "confidence": confidence,
        "ts":     ts,
    })
    pipeline["signals_buffer"] = signals_buffer[-20:]

    # --- Persister le dernier signal ---
    pipeline["last_signal"] = {
        "symbol":               symbol,
        "action":               action,
        "confidence":           confidence,
        "weight":               weight,
        "weighted_confidence":  weighted_confidence,
        "consensus":            consensus,
        "consensus_sources":    [s.get("source") for s in consensus_sources],
        "consensus_bonus":      consensus_bonus,
        "effective_confidence": effective_confidence,
        "price":                price,
        "reason":               reason,
        "source":               source,
        "verdict":              verdict,
        "ts":                   ts,
    }
    state["pipeline"] = pipeline

    # Mettre a jour agent source si connu
    agent_key = source.upper()
    if agent_key in state.get("agents", {}):
        state["agents"][agent_key]["last_seen"] = ts

    # Log intel
    consensus_note = (
        f" [CONSENSUS {len(consensus_sources)+1}src +{consensus_bonus:.2f}]"
        if consensus else ""
    )
    level_log = "INFO" if verdict in ("EXECUTE", "SIMULATE_EXECUTE") else "WARNING"
    _record_comet_intel(
        state,
        summary=(
            f"Signal {source}: {symbol} {action} "
            f"conf={confidence:.2f} w={weight} eff={effective_confidence:.2f}"
            f"{consensus_note} -> {verdict}"
        ),
        level=level_log,
        source=source,
    )
    _save_agents_state(state)

    return jsonify({
        "ok":     True,
        "mode":   mode,
        "symbol": symbol,
        "action": action,
        "verdict": verdict,
        "pipeline": {
            "kill_switch":          kill_switch,
            "threat_level":         threat_level,
            "confidence":           confidence,
            "weight":               weight,
            "weighted_confidence":  weighted_confidence,
            "consensus":            consensus,
            "consensus_sources":    [s.get("source") for s in consensus_sources],
            "consensus_bonus":      consensus_bonus,
            "effective_confidence": effective_confidence,
            "arkon_pass":           arkon_pass,
            "risk_pass":            risk_pass,
        },
        "ts": ts,
    })


@app.route('/api/pipeline/dryrun', methods=['POST'])
def api_pipeline_dryrun():
    """
    Simule le pipeline complet: KIMI -> ARKON -> MERLIN -> RiskGuardian.
    Mode DRY_RUN uniquement — aucun trade execute, aucun ordre envoye.
    Retourne la chaine de decision complete pour audit.

    Body JSON:
        signal: {symbol, action, confidence, price, reason}
    """
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    signal = body.get("signal", {})
    ts = datetime.now(timezone.utc).isoformat()

    # --- Etape 1: Parsing signal KIMI ---
    symbol     = signal.get("symbol", "BTC/USDT")
    action     = signal.get("action", "HOLD").upper()
    confidence = float(signal.get("confidence", 0.5))
    price      = float(signal.get("price", 0.0))
    reason     = signal.get("reason", "manual dry_run trigger")

    chain = []

    # --- Etape 2: KIMI -> ARKON (analyse signal) ---
    arkon_score   = round(confidence * 100, 1)
    arkon_verdict = "PASS" if confidence >= 0.60 else "HOLD"
    chain.append({
        "step":    "KIMI->ARKON",
        "agent":   "ARKON",
        "input":   {"symbol": symbol, "action": action, "confidence": confidence, "price": price},
        "verdict": arkon_verdict,
        "score":   arkon_score,
        "reason":  reason,
        "ts":      ts,
    })

    # --- Etape 3: ARKON -> MERLIN (validation externe) ---
    merlin_ok      = arkon_verdict == "PASS"
    merlin_verdict = "VALIDATED" if merlin_ok else "REJECTED"
    chain.append({
        "step":    "ARKON->MERLIN",
        "agent":   "MERLIN",
        "input":   {"arkon_verdict": arkon_verdict, "score": arkon_score},
        "verdict": merlin_verdict,
        "reason":  f"confidence {'acceptable' if merlin_ok else 'insuffisante'} ({confidence:.2f} / seuil 0.60)",
        "ts":      ts,
    })

    # --- Etape 4: MERLIN -> RiskGuardian (garde-fous) ---
    state        = _load_agents_state()
    pipeline     = state.get("pipeline", {})
    kill_switch  = pipeline.get("kill_switch", False)
    threat_level = pipeline.get("threat_level", "T0")
    mode         = pipeline.get("mode", "dry_run")

    risk_pass   = merlin_ok and not kill_switch and threat_level in ("T0", "T1")
    risk_verdict = "APPROVED" if risk_pass else "BLOCKED"
    risk_reasons = []
    if kill_switch:
        risk_reasons.append("kill_switch=ON")
    if threat_level not in ("T0", "T1"):
        risk_reasons.append(f"threat={threat_level}")
    if not merlin_ok:
        risk_reasons.append("merlin rejected")
    chain.append({
        "step":    "MERLIN->RISK_GUARDIAN",
        "agent":   "RISK_GUARDIAN",
        "input":   {"merlin_verdict": merlin_verdict, "kill_switch": kill_switch, "threat_level": threat_level},
        "verdict": risk_verdict,
        "reason":  ", ".join(risk_reasons) if risk_reasons else "all guards passed",
        "ts":      ts,
    })

    # --- Decision finale ---
    final_verdict    = "SIMULATE_EXECUTE" if risk_pass else "NO_TRADE"
    simulated_trade  = None
    if risk_pass:
        simulated_trade = {
            "would_execute": True,
            "symbol":        symbol,
            "action":        action,
            "price":         price,
            "confidence":    confidence,
            "note":          "DRY_RUN — aucun ordre reel envoye",
        }

    # --- Log dans l'intel partagee ---
    try:
        _record_comet_intel(
            state,
            summary=f"DryRun {symbol} {action} -> {final_verdict} (conf={confidence:.2f})",
            level="INFO" if risk_pass else "WARNING",
            source="PIPELINE_DRYRUN",
        )
        _save_agents_state(state)
    except Exception:
        pass

    return jsonify({
        "ok":             True,
        "mode":           "DRY_RUN",
        "pipeline_mode":  mode,
        "symbol":         symbol,
        "action":         action,
        "final_verdict":  final_verdict,
        "chain":          chain,
        "simulated_trade": simulated_trade,
        "ts":             ts,
    })


if __name__ == '__main__':
    port = int(os.getenv("PORT", "7777"))
    app.run(host='0.0.0.0', port=port, debug=False)
