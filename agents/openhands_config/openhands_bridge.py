"""
openhands_bridge.py — Flask bridge (port 9292) between S25 system and OpenHands on AlienStef.

Routes:
  POST /task        — submit a task to OpenHands
  GET  /status      — OpenHands health + last task status
  GET  /tasks       — list recent task history

Can be called by:
  - agent_loop.py
  - HA automations via webhook → shell_command
  - Manual CLI: curl -X POST http://localhost:9292/task -d '{"task": "..."}'

Run with: python agents/openhands_config/openhands_bridge.py
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, request

# ─── Config ───────────────────────────────────────────────────────────────────

OPENHANDS_URL = os.environ.get("OPENHANDS_URL", "http://10.0.0.97:3001")
BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", "9292"))
MAX_TASK_HISTORY = 50
TASK_TIMEOUT_S = 600   # 10 minutes
POLL_INTERVAL_S = 10

# Task history file for persistence across restarts
HISTORY_FILE = Path(__file__).parent / "task_history.json"

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [OPENHANDS-BRIDGE] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("openhands_bridge")

# ─── App ──────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# In-memory state
_task_history: list[dict] = []
_history_lock = threading.Lock()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_history() -> None:
    """Load task history from disk on startup."""
    global _task_history
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                _task_history = json.load(f)
            log.info(f"Loaded {len(_task_history)} tasks from history file.")
        except Exception as e:
            log.warning(f"Could not load history: {e}")
            _task_history = []


def save_history() -> None:
    """Persist task history to disk."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w") as f:
            json.dump(_task_history[-MAX_TASK_HISTORY:], f, indent=2)
    except Exception as e:
        log.warning(f"Could not save history: {e}")


def add_task_record(record: dict) -> None:
    with _history_lock:
        _task_history.append(record)
        if len(_task_history) > MAX_TASK_HISTORY:
            _task_history.pop(0)
    save_history()


def update_task_record(task_id: str, updates: dict) -> None:
    with _history_lock:
        for record in reversed(_task_history):
            if record.get("bridge_id") == task_id or record.get("openhands_id") == task_id:
                record.update(updates)
                break
    save_history()


def check_openhands_health() -> dict:
    """Ping OpenHands and return health info."""
    try:
        resp = requests.get(f"{OPENHANDS_URL}/api/options/models", timeout=5)
        return {
            "reachable": True,
            "status_code": resp.status_code,
            "url": OPENHANDS_URL,
        }
    except Exception:
        pass
    # Fallback: try root
    try:
        resp = requests.get(f"{OPENHANDS_URL}/", timeout=5)
        return {
            "reachable": True,
            "status_code": resp.status_code,
            "url": OPENHANDS_URL,
            "note": "root endpoint only",
        }
    except Exception as e:
        return {
            "reachable": False,
            "error": str(e),
            "url": OPENHANDS_URL,
        }


def submit_to_openhands(task_description: str) -> dict:
    """
    Submit a task to OpenHands.
    Tries /api/conversations first (newer API), falls back to /api/tasks.
    Returns {"openhands_id": ..., "endpoint": ...} or raises.
    """
    # Try conversations endpoint (OpenHands >= 0.14)
    try:
        payload = {"initial_user_msg": task_description, "selected_repository": None}
        resp = requests.post(
            f"{OPENHANDS_URL}/api/conversations",
            json=payload,
            timeout=15,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            oid = data.get("conversation_id") or data.get("id") or data.get("task_id")
            if oid:
                return {"openhands_id": str(oid), "endpoint": "conversations"}
    except Exception as e:
        log.debug(f"conversations endpoint failed: {e}")

    # Try tasks endpoint (older API)
    try:
        payload = {"task": task_description}
        resp = requests.post(
            f"{OPENHANDS_URL}/api/tasks",
            json=payload,
            timeout=15,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            oid = data.get("task_id") or data.get("id")
            if oid:
                return {"openhands_id": str(oid), "endpoint": "tasks"}
    except Exception as e:
        log.debug(f"tasks endpoint failed: {e}")

    raise RuntimeError(f"Could not submit task to OpenHands at {OPENHANDS_URL}")


def poll_task_status(openhands_id: str, endpoint: str) -> str:
    """
    Poll OpenHands for task status.
    Returns: 'running', 'completed', 'failed', 'unknown'
    """
    urls = [
        f"{OPENHANDS_URL}/api/conversations/{openhands_id}",
        f"{OPENHANDS_URL}/api/tasks/{openhands_id}",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                raw = (data.get("status") or data.get("state") or "unknown").lower()
                if raw in ("finished", "completed", "done", "success"):
                    return "completed"
                if raw in ("error", "failed", "failure"):
                    return "failed"
                if raw in ("running", "in_progress", "pending", "started"):
                    return "running"
                return "unknown"
        except Exception:
            continue
    return "unknown"


def async_poll(bridge_id: str, openhands_id: str, endpoint: str) -> None:
    """Background thread that polls OpenHands until done or timeout."""
    deadline = time.time() + TASK_TIMEOUT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
        status = poll_task_status(openhands_id, endpoint)
        update_task_record(bridge_id, {
            "openhands_status": status,
            "last_polled_at": datetime.utcnow().isoformat() + "Z",
        })
        log.info(f"Task {bridge_id} ({openhands_id}): {status}")
        if status in ("completed", "failed"):
            update_task_record(bridge_id, {"finished_at": datetime.utcnow().isoformat() + "Z"})
            return

    update_task_record(bridge_id, {
        "openhands_status": "timeout",
        "finished_at": datetime.utcnow().isoformat() + "Z",
    })
    log.warning(f"Task {bridge_id} timed out after {TASK_TIMEOUT_S}s.")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/task", methods=["POST"])
def post_task():
    """
    Submit a task to OpenHands.

    Body (JSON):
      task (str, required): task description
      source (str, optional): caller name for logging (e.g. "agent_loop", "HA")
      priority (str, optional): "low" | "normal" | "high"

    Returns:
      201: { "bridge_id": "...", "openhands_id": "...", "status": "submitted" }
      400: { "error": "..." }
      503: { "error": "..." }
    """
    data = request.get_json(silent=True) or {}
    task = data.get("task", "").strip()

    if not task:
        return jsonify({"error": "task is required"}), 400

    source = data.get("source", "unknown")
    priority = data.get("priority", "normal")

    log.info(f"New task from {source} [{priority}]: {task[:80]}...")

    # Check health first
    health = check_openhands_health()
    if not health.get("reachable"):
        return jsonify({
            "error": f"OpenHands unreachable at {OPENHANDS_URL}",
            "detail": health.get("error"),
        }), 503

    # Submit
    try:
        result = submit_to_openhands(task)
    except RuntimeError as e:
        log.error(f"Submit failed: {e}")
        return jsonify({"error": str(e)}), 503

    bridge_id = f"bridge-{int(time.time())}-{result['openhands_id'][:8]}"

    record = {
        "bridge_id": bridge_id,
        "openhands_id": result["openhands_id"],
        "endpoint": result["endpoint"],
        "task": task,
        "source": source,
        "priority": priority,
        "openhands_status": "submitted",
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "finished_at": None,
        "last_polled_at": None,
    }
    add_task_record(record)

    # Start background polling
    t = threading.Thread(
        target=async_poll,
        args=(bridge_id, result["openhands_id"], result["endpoint"]),
        daemon=True,
    )
    t.start()

    log.info(f"Task submitted: bridge_id={bridge_id}, openhands_id={result['openhands_id']}")
    return jsonify({
        "bridge_id": bridge_id,
        "openhands_id": result["openhands_id"],
        "status": "submitted",
    }), 201


@app.route("/status", methods=["GET"])
def get_status():
    """
    Returns OpenHands health and the most recent task.
    """
    health = check_openhands_health()

    with _history_lock:
        last_task = _task_history[-1] if _task_history else None

    return jsonify({
        "bridge": "openhands_bridge",
        "version": "1.0.0",
        "openhands": health,
        "last_task": last_task,
        "total_tasks_submitted": len(_task_history),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/tasks", methods=["GET"])
def get_tasks():
    """
    Returns recent task history (newest first).
    Query params:
      limit (int, default=20): max results
      status (str, optional): filter by openhands_status
    """
    limit = int(request.args.get("limit", 20))
    status_filter = request.args.get("status", "").strip()

    with _history_lock:
        tasks = list(reversed(_task_history))

    if status_filter:
        tasks = [t for t in tasks if t.get("openhands_status") == status_filter]

    tasks = tasks[:limit]

    return jsonify({
        "tasks": tasks,
        "total": len(_task_history),
        "returned": len(tasks),
    })


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "OpenHands Bridge",
        "version": "1.0.0",
        "openhands_url": OPENHANDS_URL,
        "endpoints": {
            "POST /task": "Submit a task",
            "GET /status": "Health + last task",
            "GET /tasks": "Task history",
        },
    })


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_history()
    log.info(f"OpenHands Bridge starting on port {BRIDGE_PORT}")
    log.info(f"Target OpenHands: {OPENHANDS_URL}")
    app.run(host="0.0.0.0", port=BRIDGE_PORT, debug=False, threaded=True)
