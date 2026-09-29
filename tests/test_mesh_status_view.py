"""The dashboard mesh summary must reflect the command-mesh queue."""
import json
import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "agents" / "mesh_status_view.py"
_SPEC = importlib.util.spec_from_file_location("mesh_status_view", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
snapshot = _MODULE.snapshot


class MeshStatusViewTests(unittest.TestCase):
    def test_counts_canonical_agents_and_active_missions(self):
        now = datetime(2026, 9, 29, 19, 30, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents = root / "agents.json"
            missions = root / "missions.json"
            agents.write_text(json.dumps({"items": {
                "system_health": {"status": "online", "last_seen_at": now.isoformat()},
                "CLAUDE": {"status": "online", "last_heartbeat_at":
                           (now - timedelta(hours=3)).isoformat()},
                "MERLIN": {"status": "degraded", "last_seen_at": now.isoformat()},
            }}), encoding="utf-8")
            missions.write_text(json.dumps({"items": {
                "one": {"status": "queued"},
                "two": {"status": "running"},
                "three": {"status": "completed"},
                "four": {"status": "blocked"},
            }}), encoding="utf-8")

            result = snapshot(agents, missions, now=now)

            self.assertEqual(result["source"], "command_mesh")
            self.assertEqual(result["total_agents"], 3)
            self.assertEqual(result["online"], 1)
            self.assertEqual(result["missions_active"], 2)
            self.assertEqual(result["agents"]["CLAUDE"]["status"], "stale")

    def test_missing_store_is_not_reported_as_zero_online(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FileNotFoundError):
                snapshot(root / "agents.json", root / "missions.json",
                         now=datetime.now(timezone.utc))


if __name__ == "__main__":
    unittest.main()
