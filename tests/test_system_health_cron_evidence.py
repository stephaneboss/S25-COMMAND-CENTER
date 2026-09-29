"""Missing execution evidence is different from a stale execution log."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.modules.setdefault("requests", types.ModuleType("requests"))
_path = Path(__file__).resolve().parents[1] / "agents" / "system_health.py"
_spec = importlib.util.spec_from_file_location("system_health_cron_evidence", _path)
health = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(health)


class CronEvidenceTests(unittest.TestCase):
    def test_missing_gemini_logs_are_unobserved_and_keep_health_degraded(self):
        crons = [
            {"name": "system_a", "status": "healthy", "priority": "high"},
            {"name": "gemini_orchestrator", "status": "no_log", "priority": "medium"},
            {"name": "gemini_news_scanner", "status": "no_log", "priority": "medium"},
        ]
        endpoints = [{"status": "healthy"}]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "health.json"
            with patch.object(health, "check_crons", return_value=crons), \
                 patch.object(health, "check_endpoints", return_value=endpoints), \
                 patch.object(health, "push_ha"), \
                 patch.object(health, "HEALTH_PATH", output):
                self.assertEqual(health.main(), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["overall_status"], "degraded")
        self.assertEqual(result["crons_stuck"], 0)
        self.assertEqual(result["crons_unobserved"], 2)
        self.assertEqual(result["unobserved_agent_names"],
                         ["gemini_orchestrator", "gemini_news_scanner"])

    def test_old_log_remains_stuck(self):
        crons = [{"name": "system_a", "status": "stuck", "priority": "high"}]
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(health, "check_crons", return_value=crons), \
                 patch.object(health, "check_endpoints", return_value=[]), \
                 patch.object(health, "push_ha"), \
                 patch.object(health, "HEALTH_PATH", Path(directory) / "health.json"):
                health.main()
                result = json.loads(health.HEALTH_PATH.read_text(encoding="utf-8"))
        self.assertEqual(result["overall_status"], "critical")
        self.assertEqual(result["crons_stuck"], 1)
        self.assertEqual(result["crons_unobserved"], 0)


if __name__ == "__main__":
    unittest.main()
