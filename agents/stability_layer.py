"""
S25 Stability Layer v1 — Phase 1 MVP (Trinity spec)

Implements (per docs/TRINITY_STABILITY_LAYER_v1.md):
  - Event Deduplicator (dedupe_key + TTL + lock)
  - Retry Orchestrator (exp backoff + jitter + classify error)
  - Dead Letter Queue (append-only JSONL)
  - Circuit Breaker per (agent, task_type)

Storage: memory/stability/ (JSON files — migrate to Redis on Akash v2)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("s25.stability")

REPO = Path(__file__).resolve().parent.parent
STORE = REPO / "memory" / "stability"
STORE.mkdir(parents=True, exist_ok=True)

DEDUPE_PATH = STORE / "event_dedupe.json"
RETRY_PATH = STORE / "retry_queue.json"
DLQ_PATH = STORE / "dead_letters.jsonl"
BREAKER_PATH = STORE / "circuit_breakers.json"
AUDIT_PATH = STORE / "stability_audit.jsonl"

# ═══════════════════════ CONFIG — Trinity spec §5,7,8,23 ═══════════════════════

DEDUPE_TTL = {
    "agent.health": 90,
    "system.state": 120,
    "mission.command": 86400,
    "mission.status": 86400,
    "incident.open": 604800,
    "signal.ingest": 21600,
    "intent.ingest": 3600,
}
DEFAULT_DEDUPE_TTL = 3600

RETRY_POLICY = {
    "mission.command": {"base": 2,  "max": 60, "max_attempts": 5},
    "mission.status":  {"base": 1,  "max": 20, "max_attempts": 3},
    "signal.ingest":   {"base": 2,  "max": 30, "max_attempts": 4},
    "incident.open":   {"base": 1,  "max": 15, "max_attempts": 8},
    "agent.health":    {"base": 1,  "max": 5,  "max_attempts": 2},
}
DEFAULT_RETRY = {"base": 2, "max": 30, "max_attempts": 3}

# Breaker opens after 3 consecutive failures OR fail_rate>50% over last 10
BREAKER_CONSECUTIVE_THRESHOLD = 3
BREAKER_FAIL_RATE_THRESHOLD = 0.5
BREAKER_MIN_SAMPLES = 10
BREAKER_COOLDOWN_CRITICAL = 15
BREAKER_COOLDOWN_NORMAL = 30
BREAKER_HALF_OPEN_PROBES = 2


# ═══════════════════════ UTILITIES ═══════════════════════

def _now_ts() -> float:
    return time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mkid(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(10).replace('-','').replace('_','')[:12]}"


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception as e:
        logger.warning("load %s failed: %s", path, e)
    return default


def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


def _audit(action: str, detail: Dict):
    entry = {"ts": _now_iso(), "action": action, **detail}
    try:
        with AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass


# ═══════════════════════ EVENT ENVELOPE BUILDER ═══════════════════════

def make_envelope(
    event_type: str,
    payload: Dict,
    priority: str = "normal",
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    dedupe_components: Optional[List[str]] = None,
    source: str = "unknown",
    trace_id: Optional[str] = None,
    max_attempts: Optional[int] = None,
) -> Dict:
    """Build a canonical event envelope per Trinity §4."""
    policy = RETRY_POLICY.get(event_type, DEFAULT_RETRY)
    if dedupe_components:
        dedupe_raw = ":".join([event_type] + dedupe_components)
    else:
        # Fallback: hash payload + entity
        h = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                       default=str).encode()).hexdigest()[:16]
        dedupe_raw = f"{event_type}:{entity_id or ''}:{h}"
    return {
        "event_id": _mkid("evt"),
        "event_type": event_type,
        "priority": priority,
        "ts": _now_iso(),
        "source": source,
        "trace_id": trace_id or _mkid("trc"),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "dedupe_key": dedupe_raw,
        "idempotency_key": f"{entity_id or 'x'}:{event_type}",
        "attempt": 1,
        "max_attempts": max_attempts or policy["max_attempts"],
        "ttl_sec": DEDUPE_TTL.get(event_type, DEFAULT_DEDUPE_TTL),
        "payload": payload,
        "meta": {},
    }


# ═══════════════════════ EVENT DEDUPLICATOR (§5) ═══════════════════════

class Deduplicator:
    """File-based dedupe store. Thread-safety via file rename.
    For v1 — single-process Flask. v2 will be Redis-backed."""

    def __init__(self):
        self.path = DEDUPE_PATH

    def _load(self) -> Dict:
        return _load(self.path, {"items": {}})

    def _save(self, data: Dict):
        # Prune expired entries opportunistically
        now = _now_ts()
        items = data.get("items", {})
        for k in list(items.keys()):
            if items[k].get("expires_at", 0) < now:
                items.pop(k, None)
        _save(self.path, data)

    def check_and_lock(self, envelope: Dict) -> Tuple[bool, str]:
        """Returns (should_process, reason).
        Side effect: acquires a lock on dedupe_key if it's new."""
        key = envelope["dedupe_key"]
        store = self._load()
        items = store.setdefault("items", {})
        now = _now_ts()
        existing = items.get(key)
        if existing:
            status = existing.get("status")
            if status == "processed" and existing.get("expires_at", 0) > now:
                _audit("dedupe_hit",
                       {"event_id": envelope["event_id"], "key": key,
                        "status": status})
                return False, "DUPLICATE_IGNORED"
            if status == "processing" and existing.get("lock_expires_at", 0) > now:
                _audit("dedupe_race",
                       {"event_id": envelope["event_id"], "key": key})
                return False, "DUPLICATE_RACE"
        # Acquire lock
        items[key] = {
            "dedupe_key": key,
            "event_id": envelope["event_id"],
            "first_seen_at": _now_iso() if not existing else existing.get("first_seen_at"),
            "last_seen_at": _now_iso(),
            "status": "processing",
            "lock_owner": os.getenv("HOSTNAME", "worker"),
            "lock_expires_at": now + 30,
            "expires_at": now + envelope.get("ttl_sec", DEFAULT_DEDUPE_TTL),
            "attempt_count": existing.get("attempt_count", 0) + 1 if existing else 1,
        }
        self._save(store)
        return True, "OK"

    def mark_processed(self, envelope: Dict, result: Any = None):
        store = self._load()
        items = store.setdefault("items", {})
        key = envelope["dedupe_key"]
        if key in items:
            items[key]["status"] = "processed"
            items[key]["result_hash"] = hashlib.sha256(
                json.dumps(result, sort_keys=True, default=str).encode()
            ).hexdigest()[:16] if result else None
            items[key]["last_seen_at"] = _now_iso()
            self._save(store)

    def mark_failed(self, envelope: Dict, error: str):
        store = self._load()
        items = store.setdefault("items", {})
        key = envelope["dedupe_key"]
        if key in items:
            items[key]["status"] = "failed"
            items[key]["last_error"] = str(error)[:300]
            self._save(store)


# ═══════════════════════ DEAD LETTER QUEUE (§11) ═══════════════════════

def send_to_dlq(envelope: Dict, reason_code: str, reason_detail: str = ""):
    entry = {
        "dlq_id": _mkid("dlq"),
        "event_id": envelope.get("event_id"),
        "event_type": envelope.get("event_type"),
        "entity_type": envelope.get("entity_type"),
        "entity_id": envelope.get("entity_id"),
        "priority": envelope.get("priority"),
        "failed_at": _now_iso(),
        "reason_code": reason_code,
        "reason_detail": reason_detail[:500],
        "payload_snapshot": envelope.get("payload", {}),
        "replayable": reason_code not in ("schema_invalid", "policy_denied_def"),
    }
    try:
        with DLQ_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        logger.error("DLQ write failed: %s", e)
    _audit("dlq_written", {"event_id": entry["event_id"],
                           "reason": reason_code})
    # Critical → auto-open incident via command_mesh
    if envelope.get("priority") == "critical":
        try:
            from agents.command_mesh import _load as _cm_load, _save as _cm_save, _mkid as _cm_mkid
            inc_path = REPO / "memory" / "command_mesh" / "incidents.json"
            inc_id = _cm_mkid("inc")
            inc = {
                "incident_id": inc_id,
                "opened_at": _now_iso(),
                "severity": "critical",
                "status": "open",
                "source": "StabilityLayer",
                "category": "stability_dlq_critical",
                "title": f"Critical event DLQ'd: {envelope.get('event_type')}",
                "summary": reason_detail[:200],
                "evidence": {"dlq_id": entry["dlq_id"], "reason": reason_code},
                "recommended_actions": ["inspect_dlq", "replay_if_transient"],
                "owner": "TRINITY",
                "resolved_at": None,
            }
            store = _cm_load(inc_path, {"items": {}})
            store.setdefault("items", {})[inc_id] = inc
            _cm_save(inc_path, store)
        except Exception as e:
            logger.warning("auto-incident on DLQ failed: %s", e)
    return entry


def list_dlq(limit: int = 50) -> List[Dict]:
    if not DLQ_PATH.exists():
        return []
    lines = DLQ_PATH.read_text().splitlines()[-limit:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


# ═══════════════════════ RETRY ORCHESTRATOR (§7) ═══════════════════════

def classify_error(error: str) -> str:
    """Trinity §15.4"""
    s = str(error).lower()
    if any(k in s for k in ["schema", "invalid payload", "policy_denied_def",
                              "validation", "missing field"]):
        return "fatal"
    if any(k in s for k in ["timeout", "429", "502", "503", "504",
                              "lock_conflict", "connection", "temporary"]):
        return "transient"
    if any(k in s for k in ["offline", "breaker_open", "quota",
                              "disabled", "unreachable"]):
        return "persistent"
    return "transient"


def compute_backoff(event_type: str, attempt: int) -> float:
    """Trinity §7.3: delay = min(base * 2^(attempt-1), max) + jitter(0..20%)"""
    cfg = RETRY_POLICY.get(event_type, DEFAULT_RETRY)
    base = cfg["base"]
    max_delay = cfg["max"]
    delay = min(base * (2 ** max(0, attempt - 1)), max_delay)
    jitter = delay * 0.2 * random.random()
    return delay + jitter


def schedule_retry(envelope: Dict, error: str) -> Optional[Dict]:
    """Schedule a retry or send to DLQ."""
    ec = classify_error(error)
    if ec == "fatal":
        send_to_dlq(envelope, "fatal_error", str(error))
        return None
    if envelope["attempt"] >= envelope["max_attempts"]:
        send_to_dlq(envelope, "max_attempts_reached", str(error))
        return None
    delay = compute_backoff(envelope["event_type"], envelope["attempt"])
    next_at = _now_ts() + delay
    rty = {
        "retry_id": _mkid("rty"),
        "event_id": envelope["event_id"],
        "event_type": envelope["event_type"],
        "entity_id": envelope.get("entity_id"),
        "attempt": envelope["attempt"] + 1,
        "max_attempts": envelope["max_attempts"],
        "next_retry_at": next_at,
        "next_retry_iso": datetime.fromtimestamp(next_at, timezone.utc).isoformat(),
        "error_class": ec,
        "last_error": str(error)[:200],
        "priority": envelope.get("priority", "normal"),
        "target_agent": envelope.get("meta", {}).get("target_agent"),
        "payload": envelope.get("payload", {}),
        "status": "scheduled",
    }
    store = _load(RETRY_PATH, {"items": []})
    store.setdefault("items", []).append(rty)
    # Cap
    if len(store["items"]) > 500:
        store["items"] = store["items"][-500:]
    _save(RETRY_PATH, store)
    _audit("retry_scheduled",
           {"event_id": envelope["event_id"],
            "attempt": rty["attempt"], "delay_sec": round(delay, 2),
            "error_class": ec})
    return rty


def due_retries() -> List[Dict]:
    store = _load(RETRY_PATH, {"items": []})
    now = _now_ts()
    return [r for r in store.get("items", [])
            if r.get("status") == "scheduled" and r.get("next_retry_at", 0) <= now]


# ═══════════════════════ CIRCUIT BREAKER (§8) ═══════════════════════

def _breaker_key(agent_id: str, task_type: str) -> str:
    return f"{agent_id}:{task_type}"


def breaker_state(agent_id: str, task_type: str) -> Dict:
    store = _load(BREAKER_PATH, {"breakers": {}})
    return store.get("breakers", {}).get(
        _breaker_key(agent_id, task_type),
        {"state": "closed", "consecutive_failures": 0,
         "recent_outcomes": [], "probe_count": 0})


def breaker_is_open(agent_id: str, task_type: str) -> bool:
    b = breaker_state(agent_id, task_type)
    if b.get("state") != "open":
        return False
    # Check cooldown
    cooldown_until = b.get("cooldown_until", 0)
    if cooldown_until <= _now_ts():
        # Transition to half_open
        _set_breaker(agent_id, task_type, state="half_open", probe_count=0)
        return False
    return True


def breaker_record(agent_id: str, task_type: str, success: bool,
                    is_critical: bool = False):
    key = _breaker_key(agent_id, task_type)
    store = _load(BREAKER_PATH, {"breakers": {}})
    breakers = store.setdefault("breakers", {})
    b = breakers.get(key, {
        "breaker_key": key, "state": "closed",
        "consecutive_failures": 0, "recent_outcomes": [],
        "probe_count": 0, "opened_at": None, "cooldown_until": None,
    })
    # Update rolling window of last 10 outcomes
    outcomes = b.setdefault("recent_outcomes", [])
    outcomes.append(1 if success else 0)
    if len(outcomes) > BREAKER_MIN_SAMPLES:
        outcomes.pop(0)
    if success:
        b["consecutive_failures"] = 0
        if b["state"] == "half_open":
            b["probe_count"] += 1
            if b["probe_count"] >= BREAKER_HALF_OPEN_PROBES:
                b["state"] = "closed"
                b["opened_at"] = None
                b["cooldown_until"] = None
                _audit("breaker_closed", {"breaker_key": key})
    else:
        b["consecutive_failures"] = b.get("consecutive_failures", 0) + 1
        # Should we open?
        fail_rate = outcomes.count(0) / len(outcomes) if outcomes else 0
        should_open = (
            b["consecutive_failures"] >= BREAKER_CONSECUTIVE_THRESHOLD or
            (len(outcomes) >= BREAKER_MIN_SAMPLES and fail_rate >= BREAKER_FAIL_RATE_THRESHOLD)
        )
        if should_open and b["state"] != "open":
            b["state"] = "open"
            b["opened_at"] = _now_iso()
            cooldown = BREAKER_COOLDOWN_CRITICAL if is_critical else BREAKER_COOLDOWN_NORMAL
            b["cooldown_until"] = _now_ts() + cooldown
            b["failure_rate"] = fail_rate
            _audit("breaker_opened",
                   {"breaker_key": key,
                    "consecutive_failures": b["consecutive_failures"],
                    "fail_rate": round(fail_rate, 2),
                    "cooldown_sec": cooldown})
    breakers[key] = b
    _save(BREAKER_PATH, store)


def _set_breaker(agent_id: str, task_type: str, **fields):
    key = _breaker_key(agent_id, task_type)
    store = _load(BREAKER_PATH, {"breakers": {}})
    breakers = store.setdefault("breakers", {})
    b = breakers.get(key, {"breaker_key": key})
    b.update(fields)
    breakers[key] = b
    _save(BREAKER_PATH, store)


def list_breakers() -> Dict:
    return _load(BREAKER_PATH, {"breakers": {}})


# ═══════════════════════ HIGH-LEVEL HELPERS ═══════════════════════

_dedup = Deduplicator()


def process_with_stability(
    envelope: Dict,
    processor: Callable[[Dict], Any],
    target_agent: Optional[str] = None,
    task_type: Optional[str] = None,
) -> Dict:
    """Apply dedupe + breaker + retry around a processor call.
    Returns {status: processed|duplicate|failed|breaker_open|dlq, result, error}.
    """
    # 1. Dedupe check
    ok, reason = _dedup.check_and_lock(envelope)
    if not ok:
        return {"status": "duplicate", "reason": reason}

    # 2. Breaker check
    if target_agent and task_type:
        if breaker_is_open(target_agent, task_type):
            _dedup.mark_failed(envelope, "breaker_open")
            rty = schedule_retry(envelope, f"breaker_open:{target_agent}:{task_type}")
            return {"status": "breaker_open",
                    "agent": target_agent, "task_type": task_type,
                    "retry_scheduled": bool(rty)}

    # 3. Process
    try:
        result = processor(envelope)
        _dedup.mark_processed(envelope, result)
        if target_agent and task_type:
            breaker_record(target_agent, task_type, success=True,
                           is_critical=envelope.get("priority") == "critical")
        return {"status": "processed", "result": result}
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        _dedup.mark_failed(envelope, err)
        if target_agent and task_type:
            breaker_record(target_agent, task_type, success=False,
                           is_critical=envelope.get("priority") == "critical")
        rty = schedule_retry(envelope, err)
        return {"status": "failed",
                "error": err,
                "retry": bool(rty)}


def stats() -> Dict:
    """Quick observability snapshot."""
    dedup = _load(DEDUPE_PATH, {"items": {}})
    retry = _load(RETRY_PATH, {"items": []})
    breakers = _load(BREAKER_PATH, {"breakers": {}})
    dlq_count = 0
    if DLQ_PATH.exists():
        dlq_count = sum(1 for _ in DLQ_PATH.open())
    return {
        "dedup_entries": len(dedup.get("items", {})),
        "retry_scheduled": sum(1 for r in retry.get("items", [])
                               if r.get("status") == "scheduled"),
        "retry_due_now": len(due_retries()),
        "breakers_open": sum(1 for b in breakers.get("breakers", {}).values()
                             if b.get("state") == "open"),
        "breakers_total": len(breakers.get("breakers", {})),
        "dlq_total": dlq_count,
    }
