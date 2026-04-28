# S25 Next Bricks

This is the short tactical list for the next safe improvements.

The system is alive. Do not rush control. Add bricks that improve safety and
understanding first.

## Brick 1 - Signal Source Ledger

Priority: highest.

Why:

Wallet movement happened while TradingView external was believed off. S25 must
know whether a signal came from local scanner, legacy webhook format, DCA,
manual command, HA, or real external TradingView.

Build:

```text
tools/signal_source_ledger.py
memory/signal_source_ledger.jsonl
docs/SIGNAL_SOURCE_LEDGER.md
```

Status: not built.

## Brick 2 - HA/Cockpit Sync Warning

Priority: high.

Why:

HA currently reports some flags that differ from Cockpit/Coinbase reality.

Build:

```text
tools/ha_cockpit_sync_check.py
memory/ha_cockpit_sync_state.json
docs/HA_COCKPIT_SYNC.md
```

Status: not built.

## Brick 3 - Order Mutation Journal

Priority: high.

Why:

`trailing_stop_manager` and bracket logic can modify orders/holds after entry.
Those mutations need attribution too.

Build:

```text
tools/order_mutation_journal.py
memory/order_mutation_journal.jsonl
docs/ORDER_MUTATION_JOURNAL.md
```

Status: not built.

## Brick 4 - Daily Ops Snapshot

Priority: high.

Why:

TRINITY needs one compact report to start each session.

Build:

```text
tools/daily_ops_snapshot.py
memory/daily_ops_snapshot.json
docs/DAILY_OPS_SNAPSHOT.md
```

Status: not built.

## Brick 5 - Cockpit Compact Ops Read-Only Panel

Priority: medium.

Why:

Once snapshots exist, show them in Cockpit without adding buttons.

Status: later. Requires locating cockpit routes safely.

## Brick 6 - Coinbase Accepted-Order Attribution Hook

Priority: critical, but blocked.

Why:

Every live accepted order should append to Trade Attribution Ledger.

Blocked by:

- exact executor success hook not located;
- `opsRun args` issue limits grep/log inspection.

Status: wait for Claude or fixed shell args.

## Brick 7 - Trade Governor Enforcement

Priority: critical, but later.

Why:

Before more autonomy, S25 needs limits.

Blocked by:

- signal ledger;
