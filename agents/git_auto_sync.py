#!/usr/bin/env python3
"""
S25 Git Auto-Sync
=================
Runs every 30 min via cron. Auto-commits trade + state files so the
git history is the canonical record of every order. If the repo has
no changes in the tracked paths, does nothing (no noise commits).
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("s25.git_auto_sync")

REPO = Path(__file__).resolve().parent.parent
TRACKED_PATHS = [
    "memory/trades_log.jsonl",
    "memory/dca_schedules.json",
    "memory/dca_state.json",
    "memory/trailing_state.json",
    "memory/strategies_state.json",
    "memory/risk_config.json",
]


def run(cmd: list, cwd=None):
    return subprocess.run(cmd, cwd=cwd or REPO, capture_output=True, text=True)


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    # Check if any tracked path has actual changes
    diff = run(["git", "status", "--porcelain"] + TRACKED_PATHS)
    if not diff.stdout.strip():
        logger.info("no tracked state changes, skipping")
        return 0

    # Pull first so we don't clash (fast-forward only)
    pull = run(["git", "pull", "--ff-only", "origin", "main"])
    if pull.returncode != 0:
        logger.warning("git pull ff-only failed: %s", pull.stderr.strip())

    # Stage + commit the tracked paths only
    run(["git", "add"] + TRACKED_PATHS)
    status = run(["git", "status", "--porcelain"])
    if not any(p in status.stdout for p in TRACKED_PATHS):
        logger.info("nothing staged, bailing")
        return 0

    msg = "chore(auto-sync): S25 state snapshot"
    commit = run(["git", "commit", "-m", msg])
    if commit.returncode != 0:
        logger.warning("commit failed: %s", commit.stderr.strip() + commit.stdout.strip())
        return 1

    push = run(["git", "push", "origin", "main"])
    if push.returncode != 0:
        logger.error("push failed: %s", push.stderr.strip())
        return 2

    logger.info("auto-sync pushed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
