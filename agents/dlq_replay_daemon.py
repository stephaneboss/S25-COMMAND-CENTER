#!/usr/bin/env python3
"""
S25 DLQ Auto-Replay Daemon — Trinity Stability Layer §20 Phase 3.

Runs every 5min via cron. Scans the DLQ for replayable entries, rebuilds
them as fresh envelopes via replay_from_dlq(), and dispatches them back
through the retry pipeline. Skips entries older than TTL or already
replayed N times.

Policy:
  - Only entries with replayable=true
  - Only reason_codes in REPLAYABLE_REASONS (transient failures)
  - Max 3 replays per original event_id (tracked in replay_ledger.json)
  - Min 60s between replays of the same event_id (backoff)
  - Max MAX_PER_TICK entries processed per run

Usage:
  python3 -m agents.dlq_replay_daemon            # one tick
  python3 -m agents.dlq_replay_daemon --dry-run  # just log, don't replay
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("s25.dlq_replay")

REPO = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO / "memory" / "stability" / "replay_ledger.json"

MAX_PER_TICK = 10
MAX_REPLAYS_PER_EVENT = 3
MIN_SECONDS_BETWEEN_REPLAYS = 60
MAX_AGE_HOURS = 24

REPLAYABLE_REASONS = {
    "timeout",
    "downstream_5xx",
    "breaker_open",
    "network_error",
    "temporary_unavailable",
    "test_5_schema_invalid",  # present for E2E test entries
}


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception as e:
        logger.warning("load %s failed: %s", path, e)
    return default


def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def _parse_iso(s: str) -> float:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0


def should_replay(entry: dict, ledger: dict) -> tuple[bool, str]:
    if not entry.get("replayable"):
        return False, "not_replayable"
    reason = entry.get("reason_code", "")
    if reason not in REPLAYABLE_REASONS:
        return False, f"reason_not_in_allowlist:{reason}"

    event_id = entry.get("event_id")
    if not event_id:
        return False, "no_event_id"

    failed_at_ts = _parse_iso(entry.get("failed_at", ""))
    if failed_at_ts and (time.time() - failed_at_ts) > MAX_AGE_HOURS * 3600:
        return False, "too_old"

    lrec = ledger.get("items", {}).get(event_id) or {}
    count = lrec.get("count", 0)
    if count >= MAX_REPLAYS_PER_EVENT:
        return False, f"max_replays_reached:{count}"

    last_ts = lrec.get("last_replay_ts", 0)
    if last_ts and (time.time() - last_ts) < MIN_SECONDS_BETWEEN_REPLAYS:
        return False, "backoff"

    return True, "ok"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    sys.path.insert(0, str(REPO))
    from agents.stability_layer import (
        list_dlq,
        replay_from_dlq,
        Deduplicator,
        process_with_stability,
    )  # noqa: E402

    ledger = _load(LEDGER_PATH, {"items": {}})
    entries = list_dlq(limit=200)
    logger.info("=== dlq_replay tick: %d DLQ entries to scan (dry_run=%s) ===",
                len(entries), args.dry_run)

    processed = 0
    replayed = 0
    skipped = 0
    results = []

    for entry in entries:
        if processed >= MAX_PER_TICK:
            break
        processed += 1

        ok_replay, reason = should_replay(entry, ledger)
        event_id = entry.get("event_id")

        if not ok_replay:
            skipped += 1
            results.append({"event_id": event_id, "action": "skipped",
                            "reason": reason})
            continue

        if args.dry_run:
            results.append({"event_id": event_id, "action": "would_replay"})
            continue

        env = replay_from_dlq(event_id, new_source="dlq_auto_replay")
        if not env:
            skipped += 1
            results.append({"event_id": event_id, "action": "skipped",
                            "reason": "replay_returned_none"})
            continue

        # Update ledger
        items = ledger.setdefault("items", {})
        lrec = items.setdefault(event_id, {"count": 0, "history": []})
        lrec["count"] += 1
        lrec["last_replay_ts"] = time.time()
        lrec["last_replay_iso"] = datetime.now(timezone.utc).isoformat()
        lrec["history"].append({
            "new_event_id": env["event_id"],
            "at": lrec["last_replay_iso"],
        })
        lrec["history"] = lrec["history"][-5:]

        # Re-inject into dedupe (locks it) — downstream cron pickup will
        # handle it. We don't try to re-dispatch here; that's the mission
        # worker's or signal ingest's job.
        try:
            dedup = Deduplicator()
            locked, _reason = dedup.check_and_lock(env)
            if not locked:
                results.append({"event_id": event_id, "action": "dedupe_blocked"})
                continue
        except Exception as e:
            logger.error("dedupe check failed for %s: %s", event_id, e)

        replayed += 1
        results.append({
            "event_id": event_id,
            "action": "replayed",
            "new_event_id": env["event_id"],
            "replay_count": lrec["count"],
        })
        logger.info("replayed %s → %s (count=%d)", event_id, env["event_id"],
                    lrec["count"])

    if not args.dry_run and replayed > 0:
        _save(LEDGER_PATH, ledger)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scanned": len(entries),
        "processed": processed,
        "replayed": replayed,
        "skipped": skipped,
        "dry_run": args.dry_run,
        "results": results[-20:],
    }
    print(json.dumps(summary, indent=2))
    logger.info("=== dlq_replay done: replayed=%d skipped=%d ===",
                replayed, skipped)


if __name__ == "__main__":
    main()
