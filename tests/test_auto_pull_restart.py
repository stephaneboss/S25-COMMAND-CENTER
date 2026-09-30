"""The auto-pull must report pull/restart failures and start fresh Python code."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "auto_pull_cron.sh"


class AutoPullTests(unittest.TestCase):
    def run_script(self, *, pull_fails=False, restart_fails=False, changed=True,
                   runtime="new", noop=False, state=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            git = bin_dir / "git"
            git.write_text('''#!/bin/bash
case "$1" in
  rev-parse) if [[ -e "$S25_TEST_PULLED" ]]; then echo new; else echo old; fi ;;
  pull) if [[ "$S25_TEST_PULL_FAIL" == 1 ]]; then exit 1; fi; [[ "$S25_TEST_NOOP" == 1 ]] && exit 0; touch "$S25_TEST_PULLED" ;;
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
            curl = bin_dir / "curl"
            curl.write_text('''#!/bin/bash
[[ -z "$S25_TEST_RUNTIME" ]] && exit 7
printf '{"build_sha":"%s"}' "$S25_TEST_RUNTIME"
''')
            curl.chmod(0o755)
            state_file = root / "deploy.json"
            if state is not None:
                state_file.write_text(state)
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
                   "S25_TEST_CHANGED": str(int(changed)),
                   "S25_TEST_RUNTIME": runtime,
                   "S25_TEST_NOOP": str(int(noop)),
                   "S25_DEPLOY_STATE": str(state_file),
                   "S25_VERIFY_TRIES": "2",
                   "S25_VERIFY_SLEEP": "0"}
            result = subprocess.run(["bash", str(SCRIPT)], env=env, timeout=10)
            self.state = state_file.read_text() if state_file.exists() else ""
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

    # ── chantier 1: deterministic deploy (runtime_sha == HEAD) ──
    def test_restart_is_verified_against_runtime_sha(self):
        code, log, _ = self.run_script(runtime="new")
        self.assertEqual(code, 0)
        self.assertIn("DEPLOY VERIFIED: runtime_sha == new", log)
        self.assertIn('"status":"verified"', self.state)

    def test_runtime_still_old_after_restart_is_a_failure(self):
        code, log, _ = self.run_script(runtime="dev")
        self.assertNotEqual(code, 0)
        self.assertIn("DEPLOY MISMATCH: expected new, runtime reports 'dev'", log)
        self.assertIn('"status":"mismatch"', self.state)

    def test_stale_runtime_without_pull_is_healed_once(self):
        # nothing to pull (HEAD=old) but the process reports dev -> one restart
        code, log, calls = self.run_script(runtime="dev", noop=True)
        self.assertNotEqual(code, 0)          # still dev after restart -> mismatch
        self.assertIn("DEPLOY DRIFT: runtime 'dev' != HEAD old, healing", log)
        self.assertIn("--user restart s25-cockpit", calls)

    def test_persisting_drift_does_not_restart_loop(self):
        prev = '{"status":"mismatch","expected_sha":"old","runtime_sha":"dev"}'
        code, log, calls = self.run_script(runtime="dev", noop=True, state=prev)
        self.assertNotEqual(code, 0)
        self.assertIn("DEPLOY DRIFT PERSISTS", log)
        self.assertEqual(calls, "")

    def test_in_sync_runtime_is_left_alone(self):
        code, log, calls = self.run_script(runtime="old", noop=True)
        self.assertEqual(code, 0)
        self.assertEqual(calls, "")
        self.assertIn('"status":"verified"', self.state)

    def test_unreachable_cockpit_is_reported_not_restarted(self):
        code, log, calls = self.run_script(runtime="", noop=True)
        self.assertEqual(code, 0)
        self.assertIn("DEPLOY DRIFT UNKNOWN", log)
        self.assertEqual(calls, "")


if __name__ == "__main__":
    unittest.main()
