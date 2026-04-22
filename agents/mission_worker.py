#!/usr/bin/env python3
"""
S25 Mission Worker — picks up assigned missions and dispatches to agents.

Runs every 1min via cron. Per Trinity architecture:
  - Read missions where status in {queued, assigned}
  - Lock mission via stability_layer (anti-double-execution)
  - Dispatch based on target_agent + task_type
  - Update status: assigned → running → completed / failed
  - On failure: escalate via Retry Orchestrator + fallback_agents
  - Journal every transition in ops_journal

Task-type dispatchers (v1):
  - market_news         → GEMINI news scanner (python -m agents.gemini_news_scanner)
  - trading_analysis    → GEMINI orchestrator brief
  - infra_monitoring    → system_health run
  - strategy_planning   → quant_brain run
  - code_generation     → MERLIN via /api/trinity (gemini bridge)
  - fallback            → logged no-op

For each agent:
  - GEMINI     : invokes cron module directly
  - MERLIN     : POST /api/trinity (gemini bridge)
  - COMET      : flagged as "needs browser worker" (TODO)
  - ARKON5     : skipped (disabled by policy)
  - KIMI       : skipped (disabled, legacy)
  - ORACLE     : invokes oracle helpers if available
  - LOCAL_CRON : runs the matching agents/* python module
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("s25.mission_worker")

REPO = Path(__file__).resolve().parent.parent
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")
MISSIONS_PATH = REPO / "memory" / "command_mesh" / "missions.json"
AGENTS_PATH = REPO / "memory" / "command_mesh" / "agents.json"
DEGRADED_FLAG = REPO / "memory" / "command_mesh" / "degraded_mode.json"
LOCKS_PATH = REPO / "memory" / "stability" / "processing_locks.json"
OPS_JOURNAL = REPO / "memory" / "command_mesh" / "ops_journal.jsonl"

LOCK_TTL_SEC = 120  # mission lock — longer than heartbeat but safe
MAX_MISSIONS_PER_TICK = 5

# task_type -> dispatcher func-name
DISPATCHERS: Dict[str, str] = {
    # FULL-LOCAL mode (2026-04-22 Major decision: Google AI Studio retired, Gemini Pro manual only)
    "market_news": "dispatch_comet_sentiment",
    "trading_analysis": "dispatch_quant_brain",
    "infra_monitoring": "dispatch_system_health",
    "strategy_planning": "dispatch_quant_brain",
    "code_generation": "dispatch_noop_gemini_retired",
    "ha_automation": "dispatch_ha_automation",
    "ha_notify": "dispatch_ha_notify",
    "signal_scan": "dispatch_auto_signal_scanner",
    "drawdown_check": "dispatch_drawdown_guardian",
    "trade_execute": "dispatch_coinbase_executor",
    "fallback": "dispatch_noop",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    return time.time()



def _env_file_get(key: str):
    try:
        env = REPO / ".env"
        if not env.exists():
            return None
        for line in env.read_text().splitlines():
            if line.strip().startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


def _journal(actor: str, entity_type: str, entity_id: str,
             action: str, payload: Optional[Dict] = None):
    entry = {
        "ts": _now_iso(),
        "actor": actor,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "payload": payload or {},
    }
    try:
        with OPS_JOURNAL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass


# ═══════════════════════ LOCK COORDINATOR (§10) ═══════════════════════

def _load_locks() -> Dict:
    return _load(LOCKS_PATH, {"locks": {}})


def _save_locks(data: Dict):
    _save(LOCKS_PATH, data)


def acquire_lock(lock_key: str, owner: str, ttl_sec: int = LOCK_TTL_SEC) -> bool:
    """Trinity §10.3/10.4 — lease with TTL, owner-based."""
    data = _load_locks()
    locks = data.setdefault("locks", {})
    now = _now_ts()
    existing = locks.get(lock_key)
    if existing and existing.get("expires_at", 0) > now \
       and existing.get("owner") != owner:
        return False
    locks[lock_key] = {
        "lock_key": lock_key,
        "owner": owner,
        "leased_at": _now_iso(),
        "expires_at": now + ttl_sec,
        "renew_count": (existing.get("renew_count", 0) + 1) if existing else 0,
    }
    _save_locks(data)
    return True


def release_lock(lock_key: str, owner: str):
    data = _load_locks()
    locks = data.get("locks", {})
    if lock_key in locks and locks[lock_key].get("owner") == owner:
        locks.pop(lock_key)
        _save_locks(data)


# ═══════════════════════ SAFE MODE (Trinity §17) ═══════════════════════

def safe_mode_active() -> bool:
    return DEGRADED_FLAG.exists()


def should_skip_non_critical(mission: Dict) -> bool:
    """Safe mode: only execute critical + high priority missions."""
    if not safe_mode_active():
        return False
    prio = mission.get("priority", "normal")
    return prio in ("low", "normal")


# ═══════════════════════ DISPATCHERS (task_type → action) ═══════════════════════

def _run_module(module: str, timeout: int = 120) -> Dict:
    """Run a python -m agents.XXX and capture result."""
    cmd = ["python3", "-m", module]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=str(REPO))
        return {
            "ok": r.returncode == 0,
            "stdout": r.stdout[-3000:],
            "stderr": r.stderr[-1500:],
            "rc": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def dispatch_comet_sentiment(mission: Dict) -> Dict:
    return _run_module("agents.comet_sentiment", timeout=120)


def dispatch_auto_signal_scanner(mission: Dict) -> Dict:
    return _run_module("agents.auto_signal_scanner", timeout=180)


def dispatch_drawdown_guardian(mission: Dict) -> Dict:
    return _run_module("agents.drawdown_guardian", timeout=60)


def dispatch_noop_gemini_retired(mission: Dict) -> Dict:
    return {"ok": False, "error": "gemini_api_retired: route to local agent or use Gemini Pro web manually"}


def dispatch_ha_automation(mission: Dict) -> Dict:
    """Trigger a Home Assistant automation via REST."""
    import os
    url = os.getenv("HA_URL", "http://10.0.0.136:8123")
    token = _ha_token()
    if not token:
        return {"ok": False, "error": "HA_TOKEN missing"}
    automation = mission.get("input", {}).get("automation_id")
    if not automation:
        return {"ok": False, "error": "missing input.automation_id"}
    r = requests.post(
        f"{url.rstrip(chr(47))}/api/services/automation/trigger",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={"entity_id": f"automation.{automation}"},
        timeout=10,
    )
    return {"ok": r.status_code == 200, "http": r.status_code,
            "body": r.text[:300]}


def dispatch_ha_notify(mission: Dict) -> Dict:
    """Persistent notification in Home Assistant."""
    import os
    url = os.getenv("HA_URL", "http://10.0.0.136:8123")
    token = _ha_token()
    if not token:
        return {"ok": False, "error": "HA_TOKEN missing"}
    inp = mission.get("input", {})
    r = requests.post(
        f"{url.rstrip(chr(47))}/api/services/persistent_notification/create",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={
            "title": inp.get("title", "S25 Mission"),
            "message": inp.get("message", mission.get("intent", "")),
        },
        timeout=10,
    )
    return {"ok": r.status_code == 200, "http": r.status_code}


def _ha_token() -> str:
    try:
        from security.vault import vault_get
        return vault_get("HA_TOKEN", "")
    except Exception:
        return ""


def dispatch_system_health(mission: Dict) -> Dict:
    return _run_module("agents.system_health", timeout=60)


def dispatch_quant_brain(mission: Dict) -> Dict:
    return _run_module("agents.quant_brain", timeout=240)





def dispatch_coinbase_executor(mission: Dict) -> Dict:
    """Forward a trade_execute mission to /webhook/tradingview.

    Mission input schema:
      {
        "symbol": "BTC/USD" | "BTCUSD",    # required
        "action": "BUY" | "SELL",           # required
        "confidence": 0.80,                 # optional, default 0.80
        "usd_amount": 10,                   # optional — forces size
        "source": "TRINITY",                # optional — weight override
        "reason": "why this trade",
      }

    The cockpit webhook respects the `.coinbase_live.flag` file, the
    HA kill-switch, and all 12 safety layers from the trading runbook.
    If they block, status=blocked with the reason. If they allow, a
    real (or dry-run) order is placed on Coinbase Advanced.
    """
    inp = mission.get("input", {}) or {}
    symbol = str(inp.get("symbol") or "").upper()
    action = str(inp.get("action") or "").upper()
    if not symbol or action not in {"BUY", "SELL"}:
        return {"ok": False, "error": "missing_symbol_or_action",
                "received": {"symbol": symbol, "action": action}}

    conf = float(inp.get("confidence") or 0.80)
    src = str(inp.get("source") or "TRINITY").upper()
    ticker = symbol.replace("/", "").replace("-", "")
    body = {
        "ticker": ticker,
        "action": action,
        "price": float(inp.get("price") or 0.0),
        "confidence": conf,
        "source": src,
        "strategy": str(inp.get("strategy")
                        or f"mission_{mission.get('mission_id', '?')}"),
        "interval": str(inp.get("interval") or "1h"),
        "reason": str(inp.get("reason")
                      or mission.get("intent") or "trade_execute"),
    }
    if inp.get("usd_amount"):
        body["usd_amount"] = float(inp["usd_amount"])
    tv_pass = os.getenv("TV_PASSPHRASE") or _env_file_get("TV_PASSPHRASE")
    if tv_pass:
        body["passphrase"] = tv_pass

    try:
        r = requests.post(f"{COCKPIT}/webhook/tradingview",
                          json=body, timeout=20)
        out = r.json() if r.ok else {"http": r.status_code,
                                     "text": r.text[:400]}
        return {"ok": r.ok, "webhook_response": out, "sent_body": body}
    except Exception as e:
        return {"ok": False, "error": str(e), "sent_body": body}


def dispatch_noop(mission: Dict) -> Dict:
    return {"ok": True, "note": "fallback no-op"}


DISPATCH_MAP = {
    "dispatch_comet_sentiment": dispatch_comet_sentiment,
    "dispatch_auto_signal_scanner": dispatch_auto_signal_scanner,
    "dispatch_drawdown_guardian": dispatch_drawdown_guardian,
    "dispatch_system_health": dispatch_system_health,
    "dispatch_quant_brain": dispatch_quant_brain,
    "dispatch_noop_gemini_retired": dispatch_noop_gemini_retired,
    "dispatch_ha_automation": dispatch_ha_automation,
    "dispatch_ha_notify": dispatch_ha_notify,
    "dispatch_coinbase_executor": dispatch_coinbase_executor,
    "dispatch_noop": dispatch_noop,
}


# ═══════════════════════ AGENT CAPABILITY MATCHING ═══════════════════════

def choose_target(mission: Dict, agents: Dict) -> Optional[str]:
    """Trinity §15.2 — choose best agent that matches task.

    Phase 2: if preferred agent's circuit breaker is OPEN for this task_type,
    skip straight to fallback_agents (Trinity Stability §22 Test 2).
    """
    try:
        from agents.stability_layer import breaker_is_open
    except Exception:
        def breaker_is_open(_a, _t):  # graceful if stability_layer missing
            return False

    preferred = mission.get("target_agent")
    task_type = mission.get("task_type")
    # 1. Preferred if online + not disabled + has capability + breaker not open
    if preferred and preferred in agents:
        a = agents[preferred]
        caps_ok = task_type in (a.get("capabilities") or []) + ["any"]
        online_ok = a.get("status") == "online"
        breaker_ok = not breaker_is_open(preferred, task_type)
        if online_ok and caps_ok and breaker_ok:
            return preferred
        if online_ok and caps_ok and not breaker_ok:
            _journal("MissionWorker", "mission", mission.get("mission_id", "?"),
                     "breaker_reroute",
                     {"from": preferred, "task_type": task_type})
    # 2. Fallback agents from routing — also skip if breaker open
    for fb in (mission.get("routing", {}).get("fallback_agents") or []):
        if fb in agents:
            a = agents[fb]
            if a.get("status") == "online" and not breaker_is_open(fb, task_type):
                return fb
    # 3. Any online agent with capability and breaker closed
    for aid, a in agents.items():
        if (a.get("status") == "online"
                and task_type in (a.get("capabilities") or [])
                and not breaker_is_open(aid, task_type)):
            return aid
    return None


# ═══════════════════════ MISSION EXECUTION ═══════════════════════

def _update_mission(mission_id: str, updates: Dict):
    store = _load(MISSIONS_PATH, {"items": {}})
    items = store.setdefault("items", {})
    if mission_id in items:
        items[mission_id].update(updates)
        items[mission_id]["updated_at"] = _now_iso()
        _save(MISSIONS_PATH, store)


def execute_mission(mission: Dict) -> Dict:
    mid = mission["mission_id"]
    task_type = mission.get("task_type", "fallback")
    priority = mission.get("priority", "normal")

    # Safe-mode gate
    if should_skip_non_critical(mission):
        _update_mission(mid, {"status": "blocked",
                              "error": "degraded_mode_skip_non_critical"})
        _journal("MissionWorker", "mission", mid, "skipped_safe_mode",
                 {"priority": priority})
        return {"status": "skipped", "reason": "safe_mode"}

    # Choose target + dispatch
    agents = _load(AGENTS_PATH, {"items": {}}).get("items", {})
    target = choose_target(mission, agents)
    if not target:
        _update_mission(mid, {"status": "blocked",
                              "error": "no_eligible_target",
                              "target_agent": None})
        _journal("MissionWorker", "mission", mid, "no_target", mission)
        return {"status": "failed", "reason": "no_eligible_target"}

    # Update target + status=running
    _update_mission(mid, {"target_agent": target, "status": "running"})
    _journal("MissionWorker", "mission", mid, "running",
             {"target": target, "task_type": task_type})

    # Dispatch
    disp_name = DISPATCHERS.get(task_type, "dispatch_noop")
    disp_fn = DISPATCH_MAP.get(disp_name, dispatch_noop)
    logger.info("[%s] dispatching %s → %s (target=%s)",
                mid, task_type, disp_name, target)
    start = time.time()
    result = disp_fn(mission)
    dur = round(time.time() - start, 2)
    ok = result.get("ok", False)

    # Breaker outcome — record so dispatch failures eventually open the
    # breaker and choose_target reroutes to fallback (Trinity §22 Test 2)
    try:
        from agents.stability_layer import breaker_record
        breaker_record(target, task_type, success=bool(ok))
    except Exception:
        pass

    if ok:
        _update_mission(mid, {
            "status": "completed",
            "result": {
                "duration_sec": dur,
                "output_preview": (result.get("stdout") or str(result.get("response", "")))[:500],
            },
        })
        _journal("MissionWorker", "mission", mid, "completed",
                 {"target": target, "duration_sec": dur})
        return {"status": "completed", "duration": dur}
    else:
        err = result.get("error") or result.get("stderr") or "unknown"
        _update_mission(mid, {
            "status": "failed",
            "error": str(err)[:500],
        })
        _journal("MissionWorker", "mission", mid, "failed",
                 {"target": target, "error": str(err)[:200]})
        return {"status": "failed", "error": str(err)[:200]}


# ═══════════════════════ MAIN LOOP ═══════════════════════

def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    # Pick up missions in {queued, assigned}
    store = _load(MISSIONS_PATH, {"items": {}})
    items = store.get("items", {})
    candidates = [m for m in items.values()
                  if m.get("status") in ("queued", "assigned")]
    # Sort by priority: critical > high > normal > low, then created_at
    prio_rank = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    candidates.sort(key=lambda m: (
        prio_rank.get(m.get("priority", "normal"), 2),
        m.get("created_at", ""),
    ))
    candidates = candidates[:MAX_MISSIONS_PER_TICK]

    logger.info("=== mission_worker tick: %d missions to process (safe_mode=%s) ===",
                len(candidates), safe_mode_active())

    results = []
    owner = f"mission_worker@{os.uname().nodename}"
    for mission in candidates:
        mid = mission["mission_id"]
        lock_key = f"mission:{mid}"
        if not acquire_lock(lock_key, owner):
            logger.info("[%s] lock held elsewhere — skip", mid)
            continue
        try:
            r = execute_mission(mission)
            results.append({"mission_id": mid, **r})
        finally:
            release_lock(lock_key, owner)

    logger.info("summary: %s", results)
    print(json.dumps({"processed": len(results), "results": results}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
