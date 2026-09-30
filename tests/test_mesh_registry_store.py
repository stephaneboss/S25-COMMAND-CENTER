"""Concurrent heartbeats must preserve every agent and any valid prior state."""
import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path

from agents.mesh_registry_store import update_agent


def _heartbeat(path, agent_id):
    for tick in range(10):
        update_agent(Path(path), {"agent_id": agent_id, "status": "online"},
                     f"2026-09-30T16:00:{tick:02d}+00:00")


class RegistryStoreTests(unittest.TestCase):
    def test_parallel_processes_keep_all_agents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agents.json"
            processes = [multiprocessing.Process(
                target=_heartbeat, args=(str(path), f"agent_{i}"))
                for i in range(8)]
            for process in processes:
                process.start()
            for process in processes:
                process.join(15)
                self.assertEqual(process.exitcode, 0)
            items = json.loads(path.read_text(encoding="utf-8"))["items"]
            self.assertEqual(set(items), {f"agent_{i}" for i in range(8)})

    def test_corrupt_registry_fails_without_erasing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agents.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                update_agent(path, {"agent_id": "CLAUDE"}, "now")
            self.assertEqual(path.read_text(encoding="utf-8"), "{bad")


if __name__ == "__main__":
    unittest.main()
