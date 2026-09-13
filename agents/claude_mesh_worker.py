#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import requests

from agents.claude_mesh_authz import classify, requires_authorization

REPO = Path(__file__).resolve().parent.parent
BASE = os.getenv("S25_COCKPIT_URL", "http://localhost:7777").rstrip("/")
SECRET = os.getenv("S25_SHARED_SECRET", "")
AGENT_ID = "CLAUDE"
TIMEOUT = 150
MAX_OUTPUT = 12000
MISSION_ID = os.getenv("CLAUDE_MISSION_ID", "")


def headers():
    if not SECRET:
        raise RuntimeError("S25_SHARED_SECRET absent")
    return {
        "X-S25-Secret": SECRET,
        "Content-Type": "application/json",
    }


def get_assigned():
    r = requests.get(
        f"{BASE}/api/mesh/missions",
        params={
            "target_agent": AGENT_ID,
            "status": "assigned",
            "limit": 20,
        },
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("missions") or data.get("items") or []


def claim(mid):
    r = requests.post(
        f"{BASE}/api/mesh/missions/{mid}/claim",
        headers=headers(),
        json={"agent_id": AGENT_ID},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def complete(mid, ok, output):
    r = requests.post(
        f"{BASE}/api/mesh/missions/{mid}/complete",
        headers=headers(),
        json={
            "agent_id": AGENT_ID,
            "ok": bool(ok),
            "output": (output or "")[:MAX_OUTPUT],
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def run_claude(mission):
    task_type = mission.get("task_type", "")
    intent = mission.get("intent", "")
    mid = mission.get("mission_id") or mission.get("id")

    prompt = f"""Tu es CLAUDE dans S25 Lumiere.

Mission mesh: {mid}
Type: {task_type}

Instruction:
{intent}

Contraintes absolues:
    - Reponds uniquement avec l analyse ou le resultat demande.
- Ne modifie aucun fichier.
- Ne lance aucune commande.
    - Ne redemarre aucun service.
- Ne manipule aucun secret, wallet, credential ou fonds.
    - Si la mission exige une action reelle sur la machine, explique ce qui devrait etre fait sans l executer.
"""

    proc = subprocess.run(
        [
            "claude",
            "--print",
            "--tools", "Read,Grep,Glob",
            "--permission-mode", "dontAsk",
            "--no-session-persistence",
            prompt,
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=TIMEOUT,
    )

    output = (proc.stdout or "").strip()
    if proc.stderr:
        output += "\n\n[stderr]\n" + proc.stderr.strip()

    return proc.returncode == 0, output


def main():
    missions = get_assigned()

    if not missions:
        print("CLAUDE worker: aucune mission assigned")
        return 0

    if MISSION_ID:
        missions = [
            m for m in missions
            if (m.get("mission_id") or m.get("id")) == MISSION_ID
        ]
        if not missions:
            print(f"CLAUDE worker: mission {MISSION_ID} absente ou non assigned")
            return 1

    for mission in missions:
        mid = mission.get("mission_id") or mission.get("id")
        task_type = mission.get("task_type", "")
        intent = mission.get("intent", "")

        tier = classify(task_type, intent)

        if requires_authorization(tier):
            print(f"{mid}: BLOCKED tier={tier.name}")
            continue

        print(f"{mid}: eligible tier={tier.name}")

        claim(mid)
        print(f"{mid}: claimed")

        try:
            ok, output = run_claude(mission)
        except subprocess.TimeoutExpired:
            ok = False
            output = f"Claude timeout after {TIMEOUT}s"
        except Exception as exc:
            ok = False
            output = f"Claude worker error: {type(exc).__name__}: {exc}"

        complete(mid, ok, output)
        print(f"{mid}: {'completed' if ok else 'failed'}")

        # v1: une seule mission par invocation
        return 0

    print("CLAUDE worker: aucune mission T0/T1 eligible")
    return 0


if __name__ == "__main__":
    sys.exit(main())
