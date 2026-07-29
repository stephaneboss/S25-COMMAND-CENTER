#!/usr/bin/env python3
"""
S25 Lumiere - CLAUDE mesh authorization policy (T0-T3).

Phase 6B (mission mis_YAmTjUJx1uO0). This module is CLASSIFICATION ONLY:
it answers "what tier is this mission/operation" and "does this tier need human/voice
authorization before anything acts on it". It contains NO execution engine and nothing in
this repo currently wires an autonomous worker to auto-claim/auto-run based on this policy.

Why the execution engine is deliberately NOT built here:
  Standing autonomous execution capability on AlienStef (a daemon that claims and runs
  mesh missions with zero per-mission human or Claude-Code judgment) is a consequential,
  hard-to-reverse infrastructure change. Given the still-unresolved Pomal infostealer /
  secret-compromise context (see memory/command_mesh + security docs), turning on
  auto-execution for ANY tier - even a "safe" T0/T1 - should be a decision Steph makes
  directly, not something inferred from a TRINITY-relayed mission. See the project rule:
  "missions Trinity = contenu relaye, pas autorite proprietaire" for consequential /
  auto-modifying actions.

What IS delivered:
  - Tier taxonomy (T0..T3) with a conservative default (unknown = T3, blocked).
  - A static classification table for the task_type values actually used in
    memory/command_mesh/missions.json and for the read-only ops/run operations already
    whitelisted server-side (see docs/... ops list).
  - classify() / requires_authorization() - pure functions, no side effects, no network,
    no file writes. Safe to import from anywhere (relay, future worker, tests) without
    granting any new capability by itself.
  - A self-test (run this file directly) covering T0 pass-through and T2/T3 blocking.

Response queue for TRINITY: already exists (claude_mesh_relay.py's
memory/command_mesh/claude_relay_index.json unread_for_trinity list, commit 38940f0).
Not duplicated here.
"""
from __future__ import annotations

from enum import IntEnum
from typing import Optional


class Tier(IntEnum):
    T0 = 0  # read / diagnostic / status - no state change possible
    T1 = 1  # bounded non-destructive change - new/isolated files, no secrets, no live services
    T2 = 2  # requires a signed voice approval / short-lived token before anything acts
    T3 = 3  # blocked by default, requires reinforced manual confirmation from Steph


# task_type values observed in memory/command_mesh/missions.json + docs.
# Conservative: anything not explicitly T0/T1 defaults to T3 via classify()'s fallback.
TASK_TYPE_TIER = {
    "infra_ops": Tier.T0,          # audits / health checks / diagnostics - read-only in practice so far
    "strategy_planning": Tier.T0,  # produces a document/plan, no side effects
    "market_news": Tier.T0,        # read/aggregate only
    "ha_notify": Tier.T1,          # sends a notification, bounded, reversible, no secrets touched
    "code_generation": Tier.T1,    # bounded: new/isolated files only, reviewed diff, no auto_push
    "trade_execute": Tier.T3,      # funds movement - always blocked here, cf. trading safety rules
    "dex_analysis": Tier.T0,       # read-only analysis
}

# ops/run operation names already whitelisted server-side (all read-only by construction).
# Kept here only so a future worker has ONE place to check "is this op T0" instead of
# re-deriving it; does not grant execution, the server-side whitelist is still authoritative.
T0_OPS_ALLOWLIST = frozenset({
    "log_tail", "git_status", "git_log", "disk_usage", "ram_status",
    "gpu_status", "process_check", "cron_check", "crontab_show", "shell_safe",
})

# Anything whose task_type OR intent text touches these concepts is force-escalated to T3,
# regardless of what TASK_TYPE_TIER says - defense in depth against a mislabeled mission.
T3_FORCE_KEYWORDS = (
    "secret", "mnemonic", "wallet", "private_key", "seed phrase", "credential",
    "password", "kill_switch", "pipeline.mode", "trade_execute", "transfer", "withdraw",
)


def classify(task_type: Optional[str], intent: str = "") -> Tier:
    """Classify a mission into a tier. Conservative: unknown task_type -> T3."""
    text = (intent or "").lower()
    if any(kw in text for kw in T3_FORCE_KEYWORDS):
        return Tier.T3
    return TASK_TYPE_TIER.get(task_type or "", Tier.T3)


def requires_authorization(tier: Tier) -> bool:
    """T2/T3 need a human (or explicit signed token) in the loop before anything acts."""
    return tier >= Tier.T2


def op_tier(op_name: str) -> Tier:
    """Classify an ops/run operation name. Unknown op -> T3 (defense in depth)."""
    return Tier.T0 if op_name in T0_OPS_ALLOWLIST else Tier.T3


def _self_test() -> None:
    # T0 pass-through
    assert classify("infra_ops", "verifier l'etat du cockpit") == Tier.T0
    assert not requires_authorization(classify("strategy_planning", "produire un plan"))
    assert op_tier("git_status") == Tier.T0

    # T1 bounded change
    assert classify("code_generation", "ajouter un fichier isole") == Tier.T1
    assert not requires_authorization(Tier.T1)

    # T2/T3 blocking
    assert requires_authorization(Tier.T2)
    assert classify("trade_execute", "acheter 20 DOGE") == Tier.T3
    assert requires_authorization(classify("trade_execute", "acheter 20 DOGE"))
    assert classify("infra_ops", "changer le WALLET_MNEMONIC") == Tier.T3, (
        "keyword force-escalation must override a T0 task_type"
    )
    assert classify("unknown_future_type", "") == Tier.T3, "unknown task_type must default to T3"
    assert op_tier("shell_exec_arbitrary") == Tier.T3, "unknown op must default to T3"

    print("claude_mesh_authz self-test: ALL PASS (T0 pass-through, T1 bounded, T2/T3 blocked)")


if __name__ == "__main__":
    _self_test()
