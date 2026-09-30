#!/usr/bin/env python3
"""Read-only S25 development diagnostics. No secrets or trading actions."""
from __future__ import annotations
import getpass
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "https://cockpit-alien.smajor.org"


def command(args, timeout=15):
    try:
        result = subprocess.run(args, cwd=REPO, capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=timeout)
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None, ""


def fetch(path):
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        return {"ok": False, "diagnostic_error": "curl_missing"}
    rc, output = command([curl, "--silent", "--show-error", "--fail",
                          "--max-time", "12", BASE + path])
    if rc != 0:
        return {"ok": False, "diagnostic_error": "http_read_failed"}
    try:
        return json.loads(output)
    except ValueError:
        return {"ok": False, "diagnostic_error": "invalid_json"}


def main():
    versions = {}
    for name, args in [("node", ["node", "--version"]),
                       ("git", ["git", "--version"]),
                       ("python", [sys.executable, "--version"])]:
        rc, value = command(args)
        versions[name] = value if rc == 0 else "unavailable"
    gh_rc, _ = command(["gh", "auth", "status"])
    _, local_sha = command(["git", "rev-parse", "HEAD"])
    _, dirty = command(["git", "--no-optional-locks", "status", "--short"])
    version = fetch("/api/version")
    mesh = fetch("/api/mesh/agents")
    ha = fetch("/api/ha/test")
    ha_states = fetch("/api/ha/status")
    cf = fetch("/api/ops/cf/tunnel")
    missions = fetch("/api/mesh/missions?limit=2")
    mesh_status = fetch("/api/mesh/status")
    local_stop = mesh_status.get("pipeline", {}).get("kill_switch")
    ha_stop = ha_states.get("ha", {}).get("controls", {}).get("s25_kill_switch")
    report = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "dell": {"hostname": platform.node(), "user": getpass.getuser(),
                 "repo": str(REPO), "versions": versions,
                 "github_authenticated": gh_rc == 0,
                 "checkout_sha": local_sha, "dirty_entries": len(dirty.splitlines())},
        "alien": {"runtime_sha": version.get("build_sha"),
                  "sha_source": version.get("build_sha_source"),
                  "started_at": version.get("started_at")},
        "ha": {"connected": ha.get("ha_connected"),
               "http_status": ha.get("ping", {}).get("status_code")},
        "cloudflare": {"service": cf.get("systemd_active"),
                       "observed_processes": len(cf.get("processes", []))},
        "controls": {"cockpit_local_kill_switch": local_stop,
                     "ha_kill_switch": ha_stop,
                     "disagreement": (local_stop != (ha_stop == "on"))
                     if isinstance(local_stop, bool) and ha_stop in ("on", "off") else None},
        "agents": [{"id": a.get("agent_id"), "status": a.get("status"),
                    "heartbeat": a.get("last_heartbeat_at"),
                    "capabilities": a.get("capabilities", [])}
                   for a in mesh.get("agents", [])],
        "recent_receipts": [{"id": m.get("mission_id"), "status": m.get("status"),
                             "agent": m.get("target_agent"), "updated_at": m.get("updated_at")}
                            for m in missions.get("missions", [])],
        "read_failures": [name for name, data in [
            ("version", version), ("mesh", mesh), ("ha_test", ha),
            ("ha_status", ha_states), ("cloudflare", cf), ("missions", missions),
            ("mesh_status", mesh_status)] if data.get("diagnostic_error") or data.get("ok") is False],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["read_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())

