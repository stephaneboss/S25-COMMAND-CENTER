"""The auto-pull must report pull/restart failures and start fresh Python code."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "auto_pull_cron.sh"


class AutoPullTests(unittest.TestCase):
    def run_script(self, *, pull_fails=False, restart_fails=False, changed=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            git = bin_dir / "git"
            git.write_text('''#!/bin/bash
case "$1" in
  rev-parse) if [[ -e "$S25_TEST_PULLED" ]]; then echo new; else echo old; fi ;;
  pull) if [[ "$S25_TEST_PULL_FAIL" == 1 ]]; then exit 1; fi; touch "$S25_TEST_PULLED" ;;
  diff) if [[ "$S25_TEST_CHANGED" == 1 ]]; then echo agents/command_mesh.py; fi ;;
esac
''')
            git.chmod(0o755)
            systemctl = bin_dir / "systemctl"
            systemctl.write_text('''#!/bin/bash
echo "$*" >> "$S25_TEST_CALLS"
if [[ "$1" == --user && "$2" == restart && "$S25_TEST_RESTART_FAIL" == 1 ]]; then exit 1; fi
''')
            systemctl.chmod(0o755)
            log = root / "pull.log"
            calls = root / "calls"
            env = {**os.environ,
                   "PATH": f"{bin_dir}:{os.environ['PATH']}",
                   "S25_AUTO_PULL_REPO": str(root),
                   "S25_AUTO_PULL_LOG": str(log),
                   "S25_AUTO_PULL_LOCK": str(root / "lock"),
                   "S25_TEST_PULLED": str(root / "pulled"),
                   "S25_TEST_CALLS": str(calls),
                   "S25_TEST_PULL_FAIL": str(int(pull_fails)),
                   "S25_TEST_RESTART_FAIL": str(int(restart_fails)),
                   "S25_TEST_CHANGED": str(int(changed))}
            result = subprocess.run(["bash", str(SCRIPT)], env=env, timeout=10)
            return result.returncode, log.read_text(), calls.read_text() if calls.exists() else ""

    def test_pull_failure_never_restarts(self):
        code, log, calls = self.run_script(pull_fails=True)
        self.assertNotEqual(code, 0)
        self.assertIn("AUTO-PULL FAILED", log)
        self.assertEqual(calls, "")

    def test_code_change_restarts_and_reports_success(self):
        code, log, calls = self.run_script()
        self.assertEqual(code, 0)
        self.assertIn("AUTO-PULL RESTARTED", log)
        self.assertIn("--user restart s25-cockpit", calls)
        self.assertIn("--user is-active --quiet s25-cockpit", calls)

    def test_restart_failure_is_visible(self):
        code, log, _ = self.run_script(restart_fails=True)
        self.assertNotEqual(code, 0)
        self.assertIn("AUTO-PULL RESTART FAILED", log)


if __name__ == "__main__":
    unittest.main()
