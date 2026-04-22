#!/usr/bin/env python3
"""Trinity Stability §22 — Phase 2 acceptance tests.

Tests 2, 3, 4, 5 (Test 1 already passed per prior commit).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.stability_layer import (  # noqa: E402
    breaker_is_open,
    breaker_record,
    backpressure_level,
    should_throttle,
    replay_from_dlq,
    send_to_dlq,
    make_envelope,
    Deduplicator,
)
from agents import mission_worker  # noqa: E402


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def ok(msg):
    print(f"{GREEN}PASS{RESET} {msg}")


def fail(msg):
    print(f"{RED}FAIL{RESET} {msg}")
    sys.exit(1)


def info(msg):
    print(f"{YELLOW}INFO{RESET} {msg}")


# ─────────────────────────────────────────────────────────────────────
# Test 2: COMET KO → breaker open, reroute MERLIN/KIMI, mission continue
# ─────────────────────────────────────────────────────────────────────
def test_2_breaker_reroute():
    print("\n═══ Test 2: COMET breaker open → reroute ═══")

    # Force-open breaker for COMET on market_news
    for _ in range(5):
        breaker_record("COMET", "market_news", success=False)

    assert breaker_is_open("COMET", "market_news"), \
        "breaker should be OPEN after repeated failures"
    ok("COMET:market_news breaker is OPEN after 5 failures")

    # Build a fake mission pointing at COMET with MERLIN as fallback
    mission = {
        "mission_id": "mis_TEST_2",
        "target_agent": "COMET",
        "task_type": "market_news",
        "priority": "high",
        "routing": {"fallback_agents": ["MERLIN"]},
    }
    agents = {
        "COMET":  {"status": "online",
                   "capabilities": ["market_news", "sentiment"]},
        "MERLIN": {"status": "online",
                   "capabilities": ["market_news", "code_generation"]},
    }

    target = mission_worker.choose_target(mission, agents)
    if target != "MERLIN":
        fail(f"expected MERLIN reroute, got {target}")
    ok(f"choose_target rerouted COMET → {target}")

    # Cleanup — close the breaker
    for _ in range(5):
        breaker_record("COMET", "market_news", success=True)
    info("breaker reset for COMET:market_news")


# ─────────────────────────────────────────────────────────────────────
# Test 3: Flood 300 signals → congested → normal throttled, high passes
# ─────────────────────────────────────────────────────────────────────
def test_3_backpressure_throttle():
    print("\n═══ Test 3: backpressure throttle ═══")

    # Directly seed signals.json with 300 fresh items to trigger congested
    sig_path = Path("memory/command_mesh/signals.json")
    original = sig_path.read_text() if sig_path.exists() else '{"items":{}}'
    try:
        items = {}
        now_ts = time.time()
        for i in range(300):
            items[f"sig_load_{i}"] = {
                "signal_id": f"sig_load_{i}",
                "ingested_ts": now_ts,
                "ingested_at": "2026-04-22T02:00:00+00:00",
                "symbol": "BTC/USD",
                "action": "BUY",
            }
        sig_path.write_text(json.dumps({"items": items}))

        bp = backpressure_level()
        if bp["level"] != "congested":
            fail(f"expected congested, got {bp}")
        ok(f"backpressure_level = congested (signal_rate_60s={bp['signal_rate_60s']})")

        throttle_normal, reason_n = should_throttle("normal")
        throttle_high, _ = should_throttle("high")
        throttle_crit, _ = should_throttle("critical")

        if not throttle_normal:
            fail("normal priority should be throttled when congested")
        if throttle_high:
            fail("high priority must pass under congested")
        if throttle_crit:
            fail("critical priority must pass under congested")

        ok(f"normal → throttled ({reason_n})")
        ok("high   → passes")
        ok("critical → passes")
    finally:
        sig_path.write_text(original)
        info("signals.json restored")


# ─────────────────────────────────────────────────────────────────────
# Test 4: 2 workers same mission → 1 wins via lock coordinator
# ─────────────────────────────────────────────────────────────────────
def test_4_lock_race():
    print("\n═══ Test 4: lock coordinator race ═══")

    mission_id = "mis_TEST_4_race"
    # Clear any prior lock
    try:
        locks_path = Path("memory/stability/processing_locks.json")
        if locks_path.exists():
            data = json.loads(locks_path.read_text())
            data.get("locks", {}).pop(mission_id, None)
            locks_path.write_text(json.dumps(data))
    except Exception:
        pass

    # Two "workers" race via mission_worker acquire_lock
    worker_a = mission_worker.acquire_lock(mission_id, "worker_A")
    worker_b = mission_worker.acquire_lock(mission_id, "worker_B")

    if not worker_a:
        fail("worker_A failed to acquire initial lock")
    if worker_b:
        fail("worker_B acquired lock but worker_A already holds it")
    ok("worker_A won the race, worker_B blocked")

    mission_worker.release_lock(mission_id, "worker_A")
    worker_b_retry = mission_worker.acquire_lock(mission_id, "worker_B")
    if not worker_b_retry:
        fail("worker_B could not acquire after release")
    ok("worker_B acquires after release")
    mission_worker.release_lock(mission_id, "worker_B")


# ─────────────────────────────────────────────────────────────────────
# Test 5: DLQ replay produces new event_id, dedupe does not block
# ─────────────────────────────────────────────────────────────────────
def test_5_dlq_replay():
    print("\n═══ Test 5: DLQ replay ═══")

    env = make_envelope(
        event_type="signal.ingest",
        source="TEST_PHASE2",
        entity_type="signal",
        entity_id="BTC-USD-phase2test",
        payload={"symbol": "BTC/USD", "action": "BUY",
                 "target_agent": "MERLIN", "task_type": "market_news"},
        priority="normal",
    )
    send_to_dlq(env, reason_code="test_5_schema_invalid",
                reason_detail="forced to DLQ for replay test")
    ok(f"envelope sent to DLQ: {env['event_id']}")

    replayed = replay_from_dlq(env["event_id"], new_source="phase2_test")
    if not replayed:
        fail("replay_from_dlq returned None")
    if replayed["event_id"] == env["event_id"]:
        fail("replay must produce a NEW event_id")
    if replayed.get("replay_of") != env["event_id"]:
        fail("replay envelope missing replay_of lineage")
    ok(f"replay produced new event_id={replayed['event_id']} "
       f"replay_of={replayed['replay_of']}")

    # Dedupe must NOT block the replayed envelope
    dedup = Deduplicator()
    locked, reason = dedup.check_and_lock(replayed)
    if not locked:
        fail(f"dedupe blocked replay envelope: {reason}")
    ok("dedupe accepts replay envelope (new event_id, new dedupe_key)")
    dedup.mark_processed(replayed, result={"test": "ok"})


if __name__ == "__main__":
    test_2_breaker_reroute()
    test_3_backpressure_throttle()
    test_4_lock_race()
    test_5_dlq_replay()
    print(f"\n{GREEN}═══ ALL PHASE 2 ACCEPTANCE TESTS PASSED ═══{RESET}")
