"""
S25 Command Mesh API — TRINITY control plane v1.0

Implements Trinity's architecture spec (docs/TRINITY_ARCHITECTURE_v1.md):
- 5 canonical objects: agent, mission, signal, incident, system_state
- 6 logical routes: ingest_intent, route_intent, create_mission,
                    report_health, commit_signal, resolve_incident
- JSON-file State Store (local for v1, migrate to Akash in v2)
- Append-only ops_journal.jsonl
- Policy engine with confidence thresholds + fallback rules

All reads (GET /api/mesh/*) are safe + non-consequential.
Writes (POST) are exposed under /api/mesh/* and require X-S25-Secret.
"""
from __future__ import annotations

import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

logger = logging.getLogger("s25.command_mesh")
mesh_bp = Blueprint("s25_command_mesh", __name__, url_prefix="/api/mesh")

REPO = Path(__file__).resolve().parent.parent
STORE = REPO / "memory" / "command_mesh"
STORE.mkdir(parents=True, exist_ok=True)
JOURNAL_PATH = STORE / "ops_journal.jsonl"

AGENTS_PATH    = STORE / "agents.json"
MISSIONS_PATH  = STORE / "missions.json"
SIGNALS_PATH   = STORE / "signals.json"
INCIDENTS_PATH = STORE / "incidents.json"
STATE_PATH     = STORE / "system_state.json"

# ═══════════════════════ UTILITIES ═══════════════════════

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mkid(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(10).replace('-','').replace('_','')[:12]}"


def _auth_ok() -> bool:
    if os.getenv("ALLOW_PUBLIC_ACTIONS", "0") == "1":
        return True
    try:
        from security.vault import vault_get
        secret = vault_get("S25_SHARED_SECRET", "") or os.getenv("S25_SHARED_SECRET", "")
    except Exception:
        secret = os.getenv("S25_SHARED_SECRET", "")
    if not secret:
        return True
    return request.headers.get("X-S25-Secret", "") == secret


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception as e:
        logger.warning("failed loading %s: %s", path, e)
    return default


def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


def _journal(actor: str, entity_type: str, entity_id: str,
             action: str, payload: Optional[Dict] = None):
    entry = {
        "journal_id": _mkid("jnl"),
        "ts": _now_iso(),
        "actor": actor,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "payload": payload or {},
    }
    try:
        with JOURNAL_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        logger.warning("journal write failed: %s", e)
    return entry


# ═══════════════════════ POLICY ENGINE ═══════════════════════

CONFIDENCE_IGNORE = 0.45
CONFIDENCE_WATCH = 0.60
CRITICAL_AGENT_RATIO = 0.70


def policy_decide_signal(signal: Dict, system_state: Dict) -> str:
    """Return verdict given signal + current system state."""
    conf = float(signal.get("effective_confidence")
                 or signal.get("confidence", 0))
    # Severe system state = block aggressively
    if system_state.get("global_status") == "severe":
        return "BLOCKED_BY_POLICY"
    # Active critical incident + non-HOLD action = review
    if system_state.get("active_incidents", 0) > 0 and \
       str(signal.get("action", "")).upper() in ("BUY", "SELL"):
        # Only if incident is critical
        incs = _load(INCIDENTS_PATH, {"items": {}}).get("items", {})
        critical_open = any(i.get("severity") == "critical"
                            and i.get("status") in ("open", "mitigating")
                            for i in incs.values())
        if critical_open:
            return "REVIEW_REQUIRED"
    if conf < CONFIDENCE_IGNORE:
        return "IGNORE"
    if conf < CONFIDENCE_WATCH:
        return "WATCH"
    # Blocklist check (reuse ops_routes blocklist)
    try:
        bl = _load(REPO / "memory" / "signal_source_blocklist.json",
                   {"blocked_sources": []}).get("blocked_sources", [])
        if str(signal.get("source_agent", "")).upper() in bl:
            return "BLOCKED_BY_POLICY"
    except Exception:
        pass
    return "SIMULATE_EXECUTE"


def policy_incident_trigger(state: Dict) -> Optional[Dict]:
    """Return an incident-template if state triggers auto-open."""
    expected = state.get("agents_expected", 0) or 1
    online = state.get("agents_online", 0)
    if expected and online < CRITICAL_AGENT_RATIO * expected:
        return {
            "severity": "critical",
            "category": "mesh_degradation",
            "title": f"Moins de {int(CRITICAL_AGENT_RATIO * expected)+1} agents online",
            "summary": f"Only {online}/{expected} online",
            "evidence": state,
            "recommended_actions": ["reroute_to_akash", "disable_noncritical_dispatch"],
        }
    pipeline = str(state.get("pipeline_status", "")).upper()
    if "CRITIQUE" in pipeline or "CRITICAL" in pipeline:
        return {
            "severity": "critical",
            "category": "pipeline_critical",
            "title": "Pipeline critique",
            "summary": f"pipeline_status={pipeline}",
            "evidence": state,
            "recommended_actions": ["halt_non_critical", "review_signals"],
        }
    if not state.get("tunnel_active", True):
        return {
            "severity": "severe",
            "category": "tunnel_down",
            "title": "Cloudflare tunnel down",
            "summary": "No public exposure — check cloudflared",
            "evidence": state,
            "recommended_actions": ["restart_cloudflared", "fallback_to_local_relay"],
        }
    return None


# ═══════════════════════ STATE HELPERS ═══════════════════════

def get_system_state() -> Dict:
    return _load(STATE_PATH, {
        "ts": _now_iso(),
        "global_status": "unknown",
        "pipeline_status": "unknown",
        "mesh_status": "unknown",
        "tunnel_active": True,
        "agents_online": 0,
        "agents_expected": 0,
        "active_incidents": 0,
        "router_quota_state": "ok",
        "last_signal_at": None,
        "control_plane_runtime": "local",
        "local_dependency": "required",
        "notes": [],
    })


def _recompute_system_state():
    """Recompute system_state from agents + incidents + recent signals."""
    agents = _load(AGENTS_PATH, {"items": {}}).get("items", {})
    incidents = _load(INCIDENTS_PATH, {"items": {}}).get("items", {})
    signals = _load(SIGNALS_PATH, {"items": {}}).get("items", {})

    online = sum(1 for a in agents.values() if a.get("status") == "online")
    expected = len(agents) or 1
    active_inc = sum(1 for i in incidents.values()
                     if i.get("status") in ("open", "acknowledged", "mitigating"))
    last_sig = None
    if signals:
        last_sig = max((s.get("ts") for s in signals.values() if s.get("ts")), default=None)

    # Decide global_status
    if any(i.get("severity") == "severe" and
           i.get("status") in ("open", "mitigating") for i in incidents.values()):
        global_status = "severe"
    elif any(i.get("severity") == "critical" and
             i.get("status") in ("open", "mitigating") for i in incidents.values()):
        global_status = "critical"
    elif online < 0.70 * expected:
        global_status = "degraded"
    else:
        global_status = "healthy"

    mesh_status = "online" if online >= 0.70 * expected else "degraded"

    state = {
        "ts": _now_iso(),
        "global_status": global_status,
        "pipeline_status": get_system_state().get("pipeline_status", "unknown"),
        "mesh_status": mesh_status,
        "tunnel_active": get_system_state().get("tunnel_active", True),
        "agents_online": online,
        "agents_expected": expected,
        "active_incidents": active_inc,
        "router_quota_state": "ok",
        "last_signal_at": last_sig,
        "control_plane_runtime": "local",
        "local_dependency": "required",
        "notes": [],
    }
    _save(STATE_PATH, state)

    # Auto-open incident if state triggers policy
    template = policy_incident_trigger(state)
    if template:
        # Check if a similar open incident already exists
        already = any(i.get("category") == template["category"] and
                      i.get("status") in ("open", "acknowledged", "mitigating")
                      for i in incidents.values())
        if not already:
            inc_id = _mkid("inc")
            inc = {
                "incident_id": inc_id,
                "opened_at": _now_iso(),
                "severity": template["severity"],
                "status": "open",
                "source": "Policy",
                "category": template["category"],
                "title": template["title"],
                "summary": template["summary"],
                "evidence": template["evidence"],
                "recommended_actions": template["recommended_actions"],
                "owner": "TRINITY",
                "resolved_at": None,
            }
            store = _load(INCIDENTS_PATH, {"items": {}})
            store.setdefault("items", {})[inc_id] = inc
            _save(INCIDENTS_PATH, store)
            _journal("Policy", "incident", inc_id, "open", inc)
    return state


# ═══════════════════════ CANONICAL OBJECT READS ═══════════════════════

@mesh_bp.route("/agents", methods=["GET"])
def mesh_list_agents():
    store = _load(AGENTS_PATH, {"items": {}})
    return jsonify({"ok": True, "agents": list(store.get("items", {}).values())})


@mesh_bp.route("/agents/<agent_id>", methods=["GET"])
def mesh_get_agent(agent_id):
    store = _load(AGENTS_PATH, {"items": {}})
    item = store.get("items", {}).get(agent_id)
    if not item:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "agent": item})


@mesh_bp.route("/missions", methods=["GET"])
def mesh_list_missions():
    store = _load(MISSIONS_PATH, {"items": {}})
    items = list(store.get("items", {}).values())
    status_filter = request.args.get("status")
    if status_filter:
        items = [m for m in items if m.get("status") == status_filter]
    items.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    limit = int(request.args.get("limit", "50"))
    return jsonify({"ok": True, "count": len(items), "missions": items[:limit]})


@mesh_bp.route("/missions/<mission_id>", methods=["GET"])
def mesh_get_mission(mission_id):
    store = _load(MISSIONS_PATH, {"items": {}})
    item = store.get("items", {}).get(mission_id)
    if not item:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "mission": item})


@mesh_bp.route("/signals", methods=["GET"])
def mesh_list_signals():
    store = _load(SIGNALS_PATH, {"items": {}})
    items = list(store.get("items", {}).values())
    items.sort(key=lambda s: s.get("ts", ""), reverse=True)
    limit = int(request.args.get("limit", "50"))
    return jsonify({"ok": True, "count": len(items), "signals": items[:limit]})


@mesh_bp.route("/incidents", methods=["GET"])
def mesh_list_incidents():
    store = _load(INCIDENTS_PATH, {"items": {}})
    items = list(store.get("items", {}).values())
    status_filter = request.args.get("status")
    if status_filter:
        items = [i for i in items if i.get("status") == status_filter]
    items.sort(key=lambda i: i.get("opened_at", ""), reverse=True)
    return jsonify({"ok": True, "count": len(items), "incidents": items})


@mesh_bp.route("/state", methods=["GET"])
def mesh_state():
    # Recompute on every read for freshness
    state = _recompute_system_state()
    return jsonify({"ok": True, "state": state})


@mesh_bp.route("/journal", methods=["GET"])
def mesh_journal():
    n = max(1, min(int(request.args.get("n", "100")), 500))
    if not JOURNAL_PATH.exists():
        return jsonify({"ok": True, "entries": []})
    lines = JOURNAL_PATH.read_text().splitlines()[-n:]
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return jsonify({"ok": True, "count": len(entries), "entries": entries})


# ═══════════════════════ 6 LOGICAL ROUTES ═══════════════════════

@mesh_bp.route("/ingest_intent", methods=["POST"])
def route_ingest_intent():
    """5.1 Canonical entry for voice/text intents."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    req_id = _mkid("req")
    intent = body.get("intent", "")
    evt = {
        "event_id": _mkid("evt"),
        "event_type": "intent.ingest",
        "ts": _now_iso(),
        "request_id": req_id,
        "sender": body.get("sender", "unknown"),
        "channel": body.get("channel", "text"),
        "intent": intent,
        "context": body.get("context", {}),
        "priority": body.get("priority", "normal"),
    }
    _journal(evt["sender"], "intent", req_id, "ingest", evt)
    return jsonify({
        "request_id": req_id,
        "accepted": True,
        "routed_to": "IntentRouter",
        "ts": evt["ts"],
    })


@mesh_bp.route("/route_intent", methods=["POST"])
def route_intent_classify():
    """5.2 Classify intent → route decision."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    intent = (body.get("intent") or "").lower()
    # Simple keyword classifier (replace with LLM later)
    if any(kw in intent for kw in ["status", "etat", "health", "sante"]):
        route, action = "query", "read_system_state"
    elif any(kw in intent for kw in ["lance", "start", "démarre", "demarre", "run"]):
        route, action = "mission", "create_mission"
    elif any(kw in intent for kw in ["signal", "trade", "buy", "sell", "achete", "vend"]):
        route, action = "signal", "commit_signal"
    elif any(kw in intent for kw in ["incident", "alerte", "resolve", "ack"]):
        route, action = "incident", "resolve_incident"
    elif any(kw in intent for kw in ["stop", "kill", "pause", "urgence"]):
        route, action = "kill_switch", "activate_emergency_stop"
    else:
        route, action = "noop", "none"
    state = get_system_state()
    policy_result = "allowed"
    if state.get("global_status") == "severe" and action != "read_system_state":
        policy_result = "blocked_by_severe_state"
    resp = {
        "request_id": body.get("request_id"),
        "route": route,
        "action": action,
        "policy_result": policy_result,
    }
    _journal(body.get("sender", "unknown"), "intent",
             body.get("request_id", "?"), "route", resp)
    return jsonify(resp)


@mesh_bp.route("/create_mission", methods=["POST"])
def route_create_mission():
    """5.3 Create exec mission."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    mid = _mkid("mis")
    now = _now_iso()
    mission = {
        "mission_id": mid,
        "created_at": now,
        "created_by": body.get("created_by", "TRINITY"),
        "target_agent": body.get("target_agent"),
        "task_type": body.get("task_type", "fallback"),
        "intent": body.get("intent", ""),
        "priority": body.get("priority", "normal"),
        "status": "queued",
        "input": body.get("input", {}),
        "constraints": body.get("constraints",
                                {"timeout_sec": 120, "max_retries": 2, "require_ack": True}),
        "routing": body.get("routing",
                            {"selected_by": "TRINITY", "runtime_preference": "akash",
                             "fallback_agents": []}),
        "result": None,
        "error": None,
        "updated_at": now,
    }
    # Check target agent exists + online → assign
    agents = _load(AGENTS_PATH, {"items": {}}).get("items", {})
    target = agents.get(mission["target_agent"])
    if target and target.get("status") == "online":
        mission["status"] = "assigned"

    store = _load(MISSIONS_PATH, {"items": {}})
    store.setdefault("items", {})[mid] = mission
    _save(MISSIONS_PATH, store)
    _journal(mission["created_by"], "mission", mid, "create", mission)
    return jsonify({
        "mission_id": mid,
        "status": mission["status"],
        "target_agent": mission["target_agent"],
    })


@mesh_bp.route("/report_health", methods=["POST"])
def route_report_health():
    """5.4 Agent heartbeat + health telemetry."""
    # Health reports are frequent and don't need auth (idempotent writes)
    body = request.get_json(silent=True) or {}
    agent_id = body.get("agent_id")
    if not agent_id:
        return jsonify({"ok": False, "error": "missing agent_id"}), 400
    store = _load(AGENTS_PATH, {"items": {}})
    items = store.setdefault("items", {})
    existing = items.get(agent_id, {})
    now = _now_iso()
    agent = {
        "agent_id": agent_id,
        "type": body.get("type") or existing.get("type", "generic"),
        "status": body.get("status", "online"),
        "runtime": body.get("runtime") or existing.get("runtime", "local"),
        "endpoint_class": body.get("endpoint_class")
                          or existing.get("endpoint_class", "internal"),
        "capabilities": body.get("capabilities")
                        or existing.get("capabilities", []),
        "priority": body.get("priority") or existing.get("priority", "normal"),
        "cost_tier": body.get("cost_tier") or existing.get("cost_tier", "low"),
        "reliability_score": body.get("reliability_score",
                                      existing.get("reliability_score", 1.0)),
        "last_heartbeat_at": now,
        "last_seen_at": now,
        "cooldown_until": body.get("cooldown_until", existing.get("cooldown_until")),
        "metadata": body.get("metadata", existing.get("metadata", {})),
        "latency_ms": body.get("latency_ms"),
        "error_rate": body.get("error_rate"),
    }
    items[agent_id] = agent
    _save(AGENTS_PATH, store)
    _journal(agent_id, "agent", agent_id, "heartbeat",
             {"status": agent["status"], "latency_ms": agent.get("latency_ms")})
    return jsonify({
        "accepted": True,
        "agent_status": agent["status"],
        "next_probe_sec": 30,
    })


@mesh_bp.route("/commit_signal", methods=["POST"])
def route_commit_signal():
    """5.5 Register a signal with policy guard."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    sid = _mkid("sig")
    conf = float(body.get("confidence", 0))
    weight = float(body.get("weight", 1.0))
    weighted = conf * weight
    consensus = bool(body.get("consensus", False))
    bonus = 0.15 if consensus else 0.0
    effective = min(1.0, weighted + bonus)

    signal = {
        "signal_id": sid,
        "ts": _now_iso(),
        "source_agent": body.get("source_agent", "unknown"),
        "symbol": body.get("symbol"),
        "action": str(body.get("action", "HOLD")).upper(),
        "confidence": conf,
        "weight": weight,
        "weighted_confidence": round(weighted, 4),
        "consensus": consensus,
        "consensus_bonus": bonus,
        "effective_confidence": round(effective, 4),
        "verdict": "PENDING",
        "reason": body.get("reason", ""),
        "context": body.get("context", {}),
        "linked_incident_id": None,
    }
    state = get_system_state()
    signal["verdict"] = policy_decide_signal(signal, state)
    policy_result = "allowed" if signal["verdict"] in (
        "SIMULATE_EXECUTE", "WATCH") else signal["verdict"].lower()

    store = _load(SIGNALS_PATH, {"items": {}})
    store.setdefault("items", {})[sid] = signal
    # Cap store at 500 recent signals
    if len(store["items"]) > 500:
        sorted_keys = sorted(store["items"].keys(),
                             key=lambda k: store["items"][k].get("ts", ""))
        for k in sorted_keys[:-500]:
            store["items"].pop(k, None)
    _save(SIGNALS_PATH, store)
    _journal(signal["source_agent"], "signal", sid, "commit",
             {"verdict": signal["verdict"], "conf": conf})
    return jsonify({
        "signal_id": sid,
        "verdict": signal["verdict"],
        "policy_result": policy_result,
    })


@mesh_bp.route("/resolve_incident", methods=["POST"])
def route_resolve_incident():
    """5.6 Acknowledge/resolve incident."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    inc_id = body.get("incident_id")
    action = body.get("action", "acknowledge")
    actor = body.get("actor", "TRINITY")
    store = _load(INCIDENTS_PATH, {"items": {}})
    inc = store.get("items", {}).get(inc_id)
    if not inc:
        return jsonify({"ok": False, "error": "not found"}), 404
    if action == "acknowledge":
        inc["status"] = "acknowledged"
    elif action == "mitigate":
        inc["status"] = "mitigating"
    elif action == "resolve":
        inc["status"] = "resolved"
        inc["resolved_at"] = _now_iso()
    elif action == "close":
        inc["status"] = "closed"
        inc["resolved_at"] = inc.get("resolved_at") or _now_iso()
    else:
        return jsonify({"ok": False, "error": f"unknown action: {action}"}), 400
    store["items"][inc_id] = inc
    _save(INCIDENTS_PATH, store)
    _journal(actor, "incident", inc_id, action,
             {"note": body.get("note", "")})
    return jsonify({"incident_id": inc_id, "status": inc["status"]})


# ═══════════════════════ HELPER — OPEN INCIDENT MANUALLY ═══════════════════════

@mesh_bp.route("/open_incident", methods=["POST"])
def route_open_incident():
    """Manual incident creation (for tests or external watchdogs)."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    inc_id = _mkid("inc")
    inc = {
        "incident_id": inc_id,
        "opened_at": _now_iso(),
        "severity": body.get("severity", "warning"),
        "status": "open",
        "source": body.get("source", "manual"),
        "category": body.get("category", "generic"),
        "title": body.get("title", ""),
        "summary": body.get("summary", ""),
        "evidence": body.get("evidence", {}),
        "impact": body.get("impact", {}),
        "recommended_actions": body.get("recommended_actions", []),
        "owner": body.get("owner", "TRINITY"),
        "resolved_at": None,
    }
    store = _load(INCIDENTS_PATH, {"items": {}})
    store.setdefault("items", {})[inc_id] = inc
    _save(INCIDENTS_PATH, store)
    _journal(inc["owner"], "incident", inc_id, "open", inc)
    return jsonify({"incident_id": inc_id, "status": "open"})
