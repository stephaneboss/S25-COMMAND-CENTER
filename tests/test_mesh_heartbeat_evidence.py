"""Heartbeat evidence must not claim operational success from a touched log."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import mesh_heartbeat_cron as heartbeat


class HeartbeatEvidenceTests(unittest.TestCase):
    def test_log_activity_boundaries_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.log"
            self.assertEqual(heartbeat.derive_status(log, 60), ("offline", None))
            log.write_text("ERROR: task failed\n")
            with patch.object(heartbeat.time, "time", return_value=1000):
                for age, status in [(0, "online"), (119, "online"),
                                    (120, "degraded"), (239, "degraded"),
                                    (240, "offline"), (-1, "degraded")]:
                    with self.subTest(age=age):
                        os.utime(log, (1000 - age, 1000 - age))
                        result, age_ms = heartbeat.derive_status(log, 60)
                        self.assertEqual(result, status)
                        self.assertEqual(age_ms, age * 1000 if age >= 0 else None)

    def test_fresh_error_log_is_not_reported_as_success(self):
        meta = {"log": "/unused", "interval": 60, "type": "infra",
                "runtime": "local", "capabilities": []}
        with patch.object(heartbeat, "derive_status", return_value=("online", 9000)):
            payload = heartbeat.build_heartbeat("example", meta)
        self.assertEqual(payload["status"], "online")
        self.assertIsNone(payload["latency_ms"])
        self.assertIsNone(payload["error_rate"])
        self.assertEqual(payload["metadata"]["log_age_ms"], 9000)
        self.assertEqual(payload["metadata"]["operational_status"], "unknown")
        self.assertFalse(payload["metadata"]["task_success_verified"])

    def test_stat_failure_and_invalid_interval(self):
        with patch.object(Path, "stat", side_effect=PermissionError):
            self.assertEqual(heartbeat.derive_status(Path("/unused"), 60), ("offline", None))
        with self.assertRaises(ValueError):
            heartbeat.derive_status(Path("/unused"), 0)

    def test_report_preserves_evidence_and_authentication(self):
        meta = {"log": "/unused", "interval": 60, "type": "infra",
                "runtime": "local", "capabilities": []}
        with patch.object(heartbeat, "derive_status", return_value=("online", 9000)), \
             patch.object(heartbeat.requests, "post") as post:
            post.return_value.status_code = 200
            self.assertEqual(heartbeat.post_heartbeat("example", meta), "online")
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["headers"], heartbeat.HEADERS)
        self.assertIsNone(kwargs["json"]["error_rate"])
        self.assertEqual(kwargs["json"]["metadata"]["health_basis"], "log_mtime")


if __name__ == "__main__":
    unittest.main()
