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

from agents import stability_layer as _stab
from agents.mesh_registry_store import update_agent
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
# Full mission outputs live here, NOT in missions.json: that file is pushed to a
# public GitHub repo by git_auto_sync. This directory is gitignored and is read
# back through GET /missions/<id>/result (authenticated).
RESULTS_DIR    = STORE / "mission_results"


def _preview_chars() -> int:
    return int(os.getenv("MESH_RESULT_PREVIEW_CHARS", "1000"))


def _max_result_chars() -> int:
    return int(os.getenv("MESH_RESULT_MAX_CHARS", "20000"))


def _store_result_file(mission_id: str, output: str) -> Optional[str]:
    """Persist the full output next to the mesh store; return its repo-relative path."""
    try:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        path = RESULTS_DIR / f"{mission_id}.md"
        path.write_text(output, encoding="utf-8")
        try:
            return str(path.relative_to(REPO))
        except ValueError:
            return str(path)
    except OSError as e:
        logger.warning("could not write mission result file: %s", e)
        return None

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


# ═══════════════════════ MISSION TIMEOUT SWEEPER ═══════════════════════
# Missions carry constraints {timeout_sec, require_ack} but nothing enforced them:
# a mission nobody claimed stayed "assigned" forever and TRINITY waited on it blind.
# The sweeper moves such missions to "expired" (terminal but re-queueable, and a late
# /complete is still accepted) so the control plane always gets an answer.

ACK_PENDING_STATUSES = ("queued", "assigned")
SWEEP_MIN_INTERVAL_SEC = 60
_last_sweep_ts = 0.0


def _ack_timeout_sec() -> int:
    return int(os.getenv("MESH_ACK_TIMEOUT_SEC", "900"))      # 15 min without claim


def _run_timeout_sec() -> int:
    return int(os.getenv("MESH_RUN_TIMEOUT_SEC", "3600"))     # 1 h running without result


def _age_sec(raw: Optional[str], now: datetime) -> Optional[float]:
    if not raw:
        return None
    try:
        d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return (now - d).total_seconds()
    except Exception:
        return None


def sweep_stale_missions(store: Dict, now: Optional[datetime] = None) -> List[str]:
    """Expire missions that were never acknowledged or never finished.

    Mutates ``store`` in place and returns the list of expired mission ids.
    The caller is responsible for saving when the list is non-empty.
    """
    now = now or datetime.now(timezone.utc)
    ack_to, run_to = _ack_timeout_sec(), _run_timeout_sec()
    expired: List[str] = []
    for mid, m in store.get("items", {}).items():
        status = m.get("status")
        constraints = m.get("constraints") or {}
        age = _age_sec(m.get("updated_at") or m.get("created_at"), now)
        if age is None:
            continue
        reason = None
        if status in ACK_PENDING_STATUSES and constraints.get("require_ack", True):
            if age > ack_to:
                reason = f"no_ack: not claimed within {ack_to}s"
        elif status == "running":
            limit = max(run_to, int(constraints.get("timeout_sec") or 0))
            if age > limit:
                reason = f"run_timeout: no result within {limit}s"
        if reason:
            m["previous_status"] = status
            m["status"] = "expired"
            m["error"] = reason
            m["updated_at"] = now.isoformat()
            expired.append(mid)
    return expired


def _maybe_sweep(actor: str, force: bool = False) -> List[str]:
    """Throttled sweep: at most once per SWEEP_MIN_INTERVAL_SEC per process."""
    global _last_sweep_ts
    if not force and time.time() - _last_sweep_ts < SWEEP_MIN_INTERVAL_SEC:
        return []
    _last_sweep_ts = time.time()
    try:
        store = _load(MISSIONS_PATH, {"items": {}})
        expired = sweep_stale_missions(store)
        if expired:
            _save(MISSIONS_PATH, store)
            for mid in expired:
                _journal(actor, "mission", mid, "expired",
                         {"error": store["items"][mid].get("error")})
        return expired
    except Exception as e:
        logger.warning("mission sweep failed (non-fatal): %s", e)
        return []


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

    # Age-aware (2027 spec): les statuts perimes ne comptent jamais comme actifs.
    _now = datetime.now(timezone.utc)
    _stale_sec = int(os.getenv("MESH_HEARTBEAT_STALE_SEC", "7200"))        # 2h
    _expected_sec = int(os.getenv("MESH_EXPECTED_WINDOW_SEC", "604800"))   # 7 jours

    def _hb_age(a):
        raw = a.get("last_seen_at") or a.get("last_heartbeat_at")
        if not raw:
            return None
        try:
            return (_now - datetime.fromisoformat(raw)).total_seconds()
        except Exception:
            return None

    online = sum(
        1 for a in agents.values()
        if a.get("status") == "online"
        and (lambda ag: ag is not None and ag <= _stale_sec)(_hb_age(a))
    )
    expected = sum(
        1 for a in agents.values()
        if a.get("status") != "disabled"
        and (lambda ag: ag is not None and ag <= _expected_sec)(_hb_age(a))
    ) or 1
    active_inc = sum(1 for i in incidents.values()
                     if i.get("status") in ("open", "acknowledged", "mitigating"))
    last_sig = None
    if signals:
        last_sig = max((s.get("ts") for s in signals.values() if s.get("ts")), default=None)

    # A signal timestamp is historical evidence, not proof of a live pipeline.
    # Derive an explicit freshness state instead of carrying "unknown" forever.
    signal_stale_sec = int(os.getenv("MESH_SIGNAL_STALE_SEC", "7200"))
    signal_age = _age_sec(last_sig, _now)
    if last_sig is None:
        pipeline_status = "NO_SIGNAL"
    elif signal_age is not None and signal_age <= signal_stale_sec:
        pipeline_status = "SIGNAL_FRESH"
    else:
        pipeline_status = "SIGNAL_STALE"

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
        "pipeline_status": pipeline_status,
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
        "signal_age_sec": int(signal_age) if signal_age is not None else None,
        "signal_stale_after_sec": signal_stale_sec,
    }
    _save(STATE_PATH, state)

    # Safe mode must follow global_status (P0 2026-09-29: flag set in April was
    # never cleared and blocked 295 non-critical missions).
    try:
        from agents import safe_mode as _safe_mode
        _safe_mode.reconcile(global_status)
    except Exception as e:  # never break state recompute
        logging.getLogger(__name__).warning("safe_mode reconcile failed: %s", e)

    # Auto-resolve mesh_degradation incidents once the agent ratio has recovered
    # (avoids mission_worker staying stuck in degraded_mode_skip_non_critical
    # forever after a transient dip, since nothing else ever closed these).
    if expected > 0 and online >= CRITICAL_AGENT_RATIO * expected:
        healed = [i for i in incidents.values()
                  if i.get("source") == "Policy"
                  and i.get("category") == "mesh_degradation"
                  and i.get("status") in ("open", "acknowledged", "mitigating")]
        if healed:
            inc_store = _load(INCIDENTS_PATH, {"items": {}})
            for inc in healed:
                inc["status"] = "resolved"
                inc["resolved_at"] = _now_iso()
                inc_store.setdefault("items", {})[inc["incident_id"]] = inc
                _journal("Policy", "incident", inc["incident_id"], "resolved", inc)
            _save(INCIDENTS_PATH, inc_store)

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
    agent_filter = request.args.get("target_agent")
    if agent_filter:
        items = [m for m in items if m.get("target_agent") == agent_filter]
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


@mesh_bp.route("/missions/<mission_id>/claim", methods=["POST"])
def mesh_claim_mission(mission_id):
    """External agent (e.g. CLAUDE) takes ownership: queued/assigned -> running."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    agent_id = str(body.get("agent_id", "")).strip() or "EXTERNAL"
    store = _load(MISSIONS_PATH, {"items": {}})
    item = store.get("items", {}).get(mission_id)
    if not item:
        return jsonify({"ok": False, "error": "not found"}), 404
    if item.get("status") not in ("queued", "assigned"):
        return jsonify({"ok": False, "error": f"not claimable (status={item.get('status')})"}), 409
    item["status"] = "running"
    item["target_agent"] = agent_id
    item["updated_at"] = _now_iso()
    _save(MISSIONS_PATH, store)
    _journal(agent_id, "mission", mission_id, "claimed", {"agent": agent_id})
    return jsonify({"ok": True, "mission_id": mission_id, "status": "running"})


@mesh_bp.route("/missions/<mission_id>/complete", methods=["POST"])
def mesh_complete_mission(mission_id):
    """External agent reports result: running -> completed/failed."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    agent_id = str(body.get("agent_id", "")).strip() or "EXTERNAL"
    success = bool(body.get("ok", True))
    blocked = bool(body.get("blocked", False))
    output = str(body.get("output", ""))[:_max_result_chars()]
    store = _load(MISSIONS_PATH, {"items": {}})
    item = store.get("items", {}).get(mission_id)
    if not item:
        return jsonify({"ok": False, "error": "not found"}), 404
    if item.get("status") not in ("running", "queued", "assigned", "expired"):
        return jsonify({"ok": False, "error": f"not completable (status={item.get('status')})"}), 409
    if item.get("status") == "expired":
        item["late_result"] = True  # result arrived after the sweeper expired it
    result_file = _store_result_file(mission_id, output) if output else None
    preview = _preview_chars()
    if blocked:
        # Agent refuses on policy grounds (e.g. authz tier T3): terminal, needs a human.
        item["status"] = "blocked"
        item["error"] = output[:preview] or "blocked by agent policy"
        success = False
    elif success:
        item["status"] = "completed"
        item["result"] = {
            "completed_by": agent_id,
            "output_preview": output[:preview],
            "output_chars": len(output),
            "truncated": len(output) > preview,
            "result_file": result_file,
        }
    else:
        item["status"] = "failed"
        item["error"] = output[:preview] or "external agent reported failure"
        if result_file:
            item["result"] = {"completed_by": agent_id, "result_file": result_file,
                              "output_chars": len(output)}
    item["updated_at"] = _now_iso()
    _save(MISSIONS_PATH, store)
    _journal(agent_id, "mission", mission_id, item["status"], {"agent": agent_id})
    if not blocked:  # a policy refusal is not an agent fault: keep breakers clean
        try:
            from agents.stability_layer import breaker_record
            breaker_record(item.get("target_agent") or agent_id,
                           item.get("task_type", "fallback"), success=success)
        except Exception:
            pass
    return jsonify({"ok": True, "mission_id": mission_id, "status": item["status"]})


@mesh_bp.route("/missions/<mission_id>/result", methods=["GET"])
def mesh_get_mission_result(mission_id):
    """Full mission output (missions.json only keeps a short preview)."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    store = _load(MISSIONS_PATH, {"items": {}})
    item = store.get("items", {}).get(mission_id)
    if not item:
        return jsonify({"ok": False, "error": "not found"}), 404
    path = RESULTS_DIR / f"{mission_id}.md"
    if path.exists():
        try:
            return jsonify({"ok": True, "mission_id": mission_id, "source": "file",
                            "status": item.get("status"),
                            "output": path.read_text(encoding="utf-8")})
        except OSError as e:
            logger.warning("could not read mission result file: %s", e)
    fallback = (item.get("result") or {}).get("output_preview") or item.get("error") or ""
    return jsonify({"ok": True, "mission_id": mission_id, "source": "preview",
                    "status": item.get("status"), "output": fallback})


@mesh_bp.route("/missions/<mission_id>/requeue", methods=["POST"])
def mesh_requeue_mission(mission_id):
    """Give an expired/failed/blocked mission another chance: -> queued (or assigned)."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    actor = str(body.get("actor", "")).strip() or "TRINITY"
    store = _load(MISSIONS_PATH, {"items": {}})
    item = store.get("items", {}).get(mission_id)
    if not item:
        return jsonify({"ok": False, "error": "not found"}), 404
    if item.get("status") not in ("expired", "failed", "blocked"):
        return jsonify({"ok": False, "error": f"not requeueable (status={item.get('status')})"}), 409
    if body.get("target_agent"):
        item["target_agent"] = str(body["target_agent"]).strip()
    if not item.get("target_agent"):
        return jsonify({"ok": False, "error": "target_agent required to requeue"}), 400
    agents = _load(AGENTS_PATH, {"items": {}}).get("items", {})
    target = agents.get(item["target_agent"])
    item["status"] = "assigned" if target and target.get("status") == "online" else "queued"
    item["error"] = None
    item["requeue_count"] = int(item.get("requeue_count") or 0) + 1
    item["updated_at"] = _now_iso()
    _save(MISSIONS_PATH, store)
    _journal(actor, "mission", mission_id, "requeued", {"status": item["status"]})
    return jsonify({"ok": True, "mission_id": mission_id, "status": item["status"]})


@mesh_bp.route("/missions/sweep", methods=["POST"])
def mesh_sweep_missions():
    """Force an immediate timeout sweep (normally piggy-backs on heartbeats)."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    expired = _maybe_sweep("TRINITY", force=True)
    return jsonify({"ok": True, "expired": expired, "count": len(expired),
                    "ack_timeout_sec": _ack_timeout_sec(),
                    "run_timeout_sec": _run_timeout_sec()})


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



# ═══════════════════════ STABILITY LAYER READS ═══════════════════════

@mesh_bp.route("/stability/stats", methods=["GET"])
def stability_stats():
    """Snapshot: dedup entries, retry queue, DLQ count, open breakers."""
    return jsonify({"ok": True, "stats": _stab.stats()})


@mesh_bp.route("/stability/dlq", methods=["GET"])
def stability_dlq():
    """Last N DLQ entries (dead letter queue)."""
    n = max(1, min(int(request.args.get("n", "50")), 500))
    return jsonify({"ok": True, "entries": _stab.list_dlq(n)})


@mesh_bp.route("/stability/breakers", methods=["GET"])
def stability_breakers():
    """Current circuit-breaker states (agent:task_type)."""
    return jsonify({"ok": True, **_stab.list_breakers()})


@mesh_bp.route("/stability/retry_queue", methods=["GET"])
def stability_retry_queue():
    """Retries pending or due."""
    from pathlib import Path as _P
    import json as _j
    path = _P(__file__).resolve().parent.parent / "memory" / "stability" / "retry_queue.json"
    data = _j.loads(path.read_text()) if path.exists() else {"items": []}
    due = _stab.due_retries()
    return jsonify({"ok": True,
                    "total": len(data.get("items", [])),
                    "due_now": len(due),
                    "items": data.get("items", [])[-50:],
                    "due_items": due})


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
    if not str(body.get("target_agent") or "").strip():
        return jsonify({"ok": False, "error": "missing target_agent"}), 400
    _maybe_sweep(body.get("created_by", "TRINITY"))
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
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    agent_id = body.get("agent_id")
    if not agent_id:
        return jsonify({"ok": False, "error": "missing agent_id"}), 400
    now = _now_iso()
    try:
        agent = update_agent(AGENTS_PATH, body, now)
    except (OSError, ValueError, KeyError) as exc:
        logger.error("agent registry update failed for %s: %s", agent_id, exc)
        return jsonify({"ok": False, "error": "agent registry unavailable"}), 503
    _journal(agent_id, "agent", agent_id, "heartbeat",
             {"status": agent["status"], "latency_ms": agent.get("latency_ms")})
    _maybe_sweep("MeshSweeper")
    return jsonify({
        "accepted": True,
        "agent_status": agent["status"],
        "next_probe_sec": 30,
    })


def stability_wrapped_commit(body):
    """Wrap commit_signal with dedupe via stability_layer."""
    envelope = _stab.make_envelope(
        event_type="signal.ingest",
        payload=body,
        priority=("critical" if str(body.get("action","")).upper() in ("BUY","SELL") else "normal"),
        entity_type="signal",
        entity_id=None,
        source=str(body.get("source_agent", "unknown")),
        dedupe_components=[
            str(body.get("source_agent", "")).upper(),
            str(body.get("symbol", "")).upper(),
            str(body.get("action", "")).upper(),
            # Bucket confidence by 0.05
            f"{round(float(body.get('confidence', 0)) / 0.05) * 0.05:.2f}",
            # Time bucket = 60s
            str(int(time.time() // 60)),
        ],
    )
    ok, reason = _stab._dedup.check_and_lock(envelope)
    if not ok:
        return {"status": "duplicate", "reason": reason}, envelope
    return None, envelope


@mesh_bp.route("/commit_signal", methods=["POST"])
def route_commit_signal():
    """5.5 Register a signal with policy guard."""
    if not _auth_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    _dup_result, _envelope = stability_wrapped_commit(body)
    if _dup_result is not None:
        return jsonify({
            "ok": True,
            "skipped": True,
            "reason": _dup_result.get("reason"),
            "note": "signal already seen in current time bucket",
        }), 200
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
    _stab._dedup.mark_processed(_envelope, {"signal_id": sid, "verdict": signal["verdict"]})
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

