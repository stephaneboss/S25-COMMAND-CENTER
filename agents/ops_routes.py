"""
S25 Ops Routes — backend control endpoints for GPT Trinity command.

Exposes safe ops primitives so Trinity can:
  - read agent logs
  - restart cron agents (via systemd-user or log-touch)
  - view git status / recent commits
  - read whitelisted infra files
  - check cloudflare tunnel
  - block/unblock signal sources (executor-side)
  - emergency kill-switch

All READS public (isConsequential=false in OpenAPI).
All WRITES require X-S25-Secret.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

logger = logging.getLogger("s25.ops_routes")
ops_bp = Blueprint("s25_ops", __name__, url_prefix="/api/ops")

REPO = Path(__file__).resolve().parent.parent
BLOCKLIST_PATH = REPO / "memory" / "signal_source_blocklist.json"
KILL_SWITCH_PATH = REPO / "memory" / "emergency_stop.flag"

FILE_READ_WHITELIST = {
    "agents/", "strategies/", "trinity_config/", "memory/",
    "docs/", "ha/", "cloudflare/",
}
FILE_READ_BLOCKLIST = {".env", "secret", "vault", "key", ".pem", ".p12"}
FILE_READ_MAX_BYTES = 200_000

KNOWN_AGENTS = {
    "coinbase_ha_publisher":  {"log": "/tmp/coinbase_ha_publisher.log", "type": "cron", "cron": "* * * * *"},
    "mesh_signal_bridge":     {"log": "/tmp/mesh_bridge.log",           "type": "cron", "cron": "*/2 * * * *"},
    "trailing_stop_manager":  {"log": "/tmp/trailing_stop.log",         "type": "cron", "cron": "*/3 * * * *"},
    "auto_signal_scanner":    {"log": "/tmp/auto_signal_scanner.log",   "type": "cron", "cron": "*/5 * * * *"},
    "comet_sentiment":        {"log": "/tmp/comet_sentiment.log",       "type": "cron", "cron": "*/10 * * * *"},
    "drawdown_guardian":      {"log": "/tmp/drawdown.log",              "type": "cron", "cron": "*/10 * * * *"},
    "dca_scheduler":          {"log": "/tmp/dca_scheduler.log",         "type": "cron", "cron": "*/15 * * * *"},
    "git_auto_sync":          {"log": "/tmp/git_sync.log",              "type": "cron", "cron": "*/30 * * * *"},
    "quant_brain":            {"log": "/tmp/quant_brain.log",           "type": "cron", "cron": "0 * * * *"},
    "gemini_orchestrator":    {"log": "/tmp/gemini_orchestrator.log",   "type": "cron", "cron": "0 */2 * * *"},
    "gemini_news_scanner":    {"log": "/tmp/gemini_news.log",           "type": "cron", "cron": "17 * * * *"},
    "system_health":          {"log": "/tmp/system_health.log",         "type": "cron", "cron": "*/5 * * * *"},
    "cockpit":                {"log": "/tmp/cockpit_lumiere.log",       "type": "systemd", "unit": "cockpit-lumiere"},
}


def _auth() -> bool:
    if os.getenv("ALLOW_PUBLIC_ACTIONS", "0") == "1":
        return True
    secret = os.getenv("S25_SHARED_SECRET", "") or os.getenv("S25_SECRET", "")
    if not secret:
        return True
    return request.headers.get("X-S25-Secret", "") == secret


def _run(cmd: List[str], timeout: int = 10) -> Dict[str, Any]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"ok": r.returncode == 0, "rc": r.returncode,
                "stdout": r.stdout[-4000:], "stderr": r.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _safe_path(rel_path: str):
    try:
        p = (REPO / rel_path).resolve()
        if REPO not in p.parents and p != REPO:
            return None
        rel = p.relative_to(REPO).as_posix()
        if any(bad in rel.lower() for bad in FILE_READ_BLOCKLIST):
            return None
        if not any(rel.startswith(prefix) for prefix in FILE_READ_WHITELIST):
            return None
        return p
    except Exception:
        return None


@ops_bp.route("/agents", methods=["GET"])
def list_agents():
    now = time.time()
    rows = []
    for name, meta in KNOWN_AGENTS.items():
        p = Path(meta["log"])
        entry = {"name": name, **meta, "log_exists": p.exists()}
        if p.exists():
            age = now - p.stat().st_mtime
            entry["last_run_sec_ago"] = int(age)
            entry["last_run_min_ago"] = round(age / 60, 1)
            entry["log_size"] = p.stat().st_size
        rows.append(entry)
    return jsonify({"ok": True, "agents": rows})


@ops_bp.route("/agent/<name>/log", methods=["GET"])
def agent_log(name):
    if name not in KNOWN_AGENTS:
        return jsonify({"ok": False, "error": f"unknown agent: {name}"}), 404
    n = int(request.args.get("n", "50"))
    n = max(1, min(n, 500))
    p = Path(KNOWN_AGENTS[name]["log"])
    if not p.exists():
        return jsonify({"ok": True, "name": name, "lines": [], "note": "no log file"})
    try:
        lines = p.read_text(errors="replace").splitlines()[-n:]
        return jsonify({"ok": True, "name": name, "count": len(lines), "lines": lines})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@ops_bp.route("/agent/<name>/trigger", methods=["POST"])
def agent_trigger(name):
    if not _auth():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if name not in KNOWN_AGENTS:
        return jsonify({"ok": False, "error": f"unknown agent: {name}"}), 404
    mod = f"agents.{name}"
    cmd = ["python3", "-m", mod]
    result = _run(cmd, timeout=90)
    return jsonify({"ok": result.get("ok", False), "agent": name,
                    "cmd": " ".join(cmd), **result})


@ops_bp.route("/agent/<name>/restart", methods=["POST"])
def agent_restart(name):
    if not _auth():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if name not in KNOWN_AGENTS:
        return jsonify({"ok": False, "error": f"unknown agent: {name}"}), 404
    meta = KNOWN_AGENTS[name]
    if meta.get("type") != "systemd":
        return jsonify({"ok": False, "error": f"{name} is not a systemd unit"}), 400
    unit = meta["unit"]
    result = _run(["systemctl", "--user", "restart", unit], timeout=15)
    return jsonify({"ok": result.get("ok", False), "unit": unit, **result})


@ops_bp.route("/git", methods=["GET"])
def git_status():
    log = _run(["git", "-C", str(REPO), "log", "--oneline", "-10"])
    status = _run(["git", "-C", str(REPO), "status", "--short"])
    branch = _run(["git", "-C", str(REPO), "branch", "--show-current"])
    return jsonify({
        "ok": True,
        "branch": (branch.get("stdout") or "").strip(),
        "recent_commits": (log.get("stdout") or "").splitlines(),
        "dirty_files": (status.get("stdout") or "").splitlines(),
    })


@ops_bp.route("/git/pull", methods=["POST"])
def git_pull():
    if not _auth():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    result = _run(["git", "-C", str(REPO), "pull", "--ff-only", "origin", "main"], timeout=30)
    return jsonify({"ok": result.get("ok", False), **result})


@ops_bp.route("/file", methods=["GET"])
def file_read():
    rel = (request.args.get("path") or "").strip()
    if not rel:
        return jsonify({"ok": False, "error": "missing ?path="}), 400
    p = _safe_path(rel)
    if not p or not p.exists() or not p.is_file():
        return jsonify({"ok": False, "error": "not found or not allowed"}), 404
    try:
        size = p.stat().st_size
        if size > FILE_READ_MAX_BYTES:
            return jsonify({"ok": False, "error": f"file too large ({size} bytes)"}), 413
        content = p.read_text(errors="replace")
        return jsonify({"ok": True, "path": rel, "size": size, "content": content})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@ops_bp.route("/dir", methods=["GET"])
def dir_list():
    rel = (request.args.get("path") or "agents").strip()
    p = _safe_path(rel) if rel != "agents" else (REPO / "agents")
    if not p or not p.exists() or not p.is_dir():
        return jsonify({"ok": False, "error": "not found or not allowed"}), 404
    items = []
    for child in sorted(p.iterdir()):
        items.append({
            "name": child.name,
            "type": "dir" if child.is_dir() else "file",
            "size": child.stat().st_size if child.is_file() else None,
        })
    return jsonify({"ok": True, "path": rel, "items": items})


@ops_bp.route("/cf/tunnel", methods=["GET"])
def cf_tunnel_status():
    result = _run(["systemctl", "is-active", "cloudflared"], timeout=5)
    ps = _run(["pgrep", "-a", "cloudflared"], timeout=5)
    return jsonify({
        "ok": True,
        "systemd_active": (result.get("stdout") or "").strip(),
        "processes": (ps.get("stdout") or "").splitlines(),
    })


@ops_bp.route("/crontab", methods=["GET"])
def crontab_view():
    result = _run(["crontab", "-l"], timeout=5)
    return jsonify({
        "ok": True,
        "entries": (result.get("stdout") or "").splitlines(),
    })


def _load_blocklist() -> List[str]:
    try:
        if BLOCKLIST_PATH.exists():
            data = json.loads(BLOCKLIST_PATH.read_text())
            return [str(s).upper() for s in data.get("blocked_sources", [])]
    except Exception:
        pass
    return []


def _save_blocklist(sources: List[str]):
    BLOCKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    BLOCKLIST_PATH.write_text(json.dumps({
        "blocked_sources": sorted(set(s.upper() for s in sources)),
        "updated_at": time.time(),
    }, indent=2))


@ops_bp.route("/signal/blocklist", methods=["GET"])
def signal_blocklist_get():
    return jsonify({"ok": True, "blocked_sources": _load_blocklist()})


@ops_bp.route("/signal/block", methods=["POST"])
def signal_block():
    if not _auth():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    source = str(body.get("source", "")).strip().upper()
    if not source:
        return jsonify({"ok": False, "error": "missing source"}), 400
    cur = _load_blocklist()
    if source not in cur:
        cur.append(source)
        _save_blocklist(cur)
    return jsonify({"ok": True, "blocked_sources": cur, "added": source})


@ops_bp.route("/signal/unblock", methods=["POST"])
def signal_unblock():
    if not _auth():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    source = str(body.get("source", "")).strip().upper()
    cur = [s for s in _load_blocklist() if s != source]
    _save_blocklist(cur)
    return jsonify({"ok": True, "blocked_sources": cur, "removed": source})


@ops_bp.route("/kill-switch", methods=["GET"])
def kill_switch_get():
    return jsonify({
        "ok": True,
        "active": KILL_SWITCH_PATH.exists(),
        "since": (KILL_SWITCH_PATH.stat().st_mtime if KILL_SWITCH_PATH.exists() else None),
    })


@ops_bp.route("/kill-switch", methods=["POST"])
def kill_switch_set():
    body = request.get_json(silent=True) or {}
    activate = bool(body.get("activate", True))
    KILL_SWITCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    if activate:
        KILL_SWITCH_PATH.write_text(json.dumps({
            "activated_at": time.time(),
            "reason": body.get("reason", "triggered via /api/ops/kill-switch"),
        }))
    else:
        if not _auth():
            return jsonify({"ok": False, "error": "unauthorized to deactivate"}), 401
        if KILL_SWITCH_PATH.exists():
            KILL_SWITCH_PATH.unlink()
    return jsonify({"ok": True, "active": KILL_SWITCH_PATH.exists()})
