#!/usr/bin/env python3

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from agents.cockpit_client import CockpitClient


log = logging.getLogger("s25.merlin_feedback_loop")

POLL_SECONDS = int(os.getenv("MERLIN_FEEDBACK_SECONDS", "300"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    logging.basicConfig(level=os.getenv("MERLIN_FEEDBACK_LOG_LEVEL", "INFO"))
    client = CockpitClient()
    log.info("Starting MERLIN feedback loop every %ss", POLL_SECONDS)

    while True:
        try:
            status = client.get_status() or {}
            mesh = client.get_mesh_status() or {}
            missions = client.get_missions() or {}
            active_count = len((missions.get("active") or []))
            summary = (
                f"MERLIN loop tick. "
                f"Pipeline={status.get('pipeline_status', 'unknown')} "
                f"Signal={status.get('arkon5_action', 'unknown')} "
                f"Missions={active_count}"
            )
            client.heartbeat("MERLIN", note="feedback loop tick")
            client.update_state(
                "MERLIN",
                updates={
                    "status": "online",
                    "last_query": "feedback_loop",
                    "last_feedback_at": _utcnow_iso(),
                },
                intel={
                    "merlin_feedback": {
                        "ts": _utcnow_iso(),
                        "summary": summary,
                        "status": status,
                        "mesh": mesh.get("mesh", {}),
                        "missions_active": active_count,
                    }
                },
            )
        except Exception as exc:
            log.warning("MERLIN feedback loop tick failed: %s", exc)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
