# S25 Compact Ops Runbook

S25 Compact Ops is the reduced-cost operating mode for the S25 Lumiere mesh.

The goal is simple: keep the critical path alive without depending on every
expensive external brain.

```text
signal or manual intent -> mesh/cockpit -> Coinbase LIVE -> positions/PnL -> attribution
```

## Current compact-mode assumptions

- Coinbase is the source of live portfolio, balances, order holds, and spot prices.
- TradingView may be off or unavailable.
- Gemini/Garmin may be unavailable.
- Claude/Kimi may be unavailable.
- MERLIN and ORACLE may operate as local/periodic observers.
- No agent is trusted blindly without attribution.

## Golden rules

1. Preserve the live trading path, but keep changes small.
2. Do not wire new automation directly into Coinbase without a clear order-success hook.
3. Every real trade should eventually write one attribution event.
4. Price source and signal source must be tracked separately.
5. Degraded is acceptable; unknown is not.

## Health checklist

Use this checklist before changing execution logic.

- Pipeline mode is `authorized` only when LIVE trading is expected.
- Kill switch is false.
- Coinbase portfolio endpoint responds.
- Spot prices respond.
- Backpressure level is ok.
- Breakers open count is 0.
- Missions queued is 0 or explainable.
- DLQ entries are old/test or explainable.
- Service `s25-cockpit` is active.
- Disk has enough free space.
- RAM and GPU are not saturated.

## Attribution checklist

For every real trade, capture:

- timestamp
- symbol
- side
- USD amount
- source signal
- source agent
- strategy
- confidence
- mission id
- Coinbase order id
- reason
- price source
- execution agent
- mode

Target file:

```text
memory/trade_attribution_ledger.jsonl
```

Tools:

```bash
python tools/trade_attribution_ledger.py latest
python tools/trade_attr_cli.py list DOGE-USD --limit 5
python tools/trade_attr_cli.py append --symbol DOGE-USD --side BUY --usd-amount 2 --reason "manual attribution"
```

## Decision source map

| Layer | Role | Compact-mode source |
| --- | --- | --- |
| Price | valuation / PnL / execution reference | Coinbase spot |
| Portfolio | balances / holds / USD availability | Coinbase portfolio |
| Signal | market trigger | TradingView, local scanner, manual intent, or cached signal |
| Review | non-binding analysis | MERLIN / ORACLE / local cron |
| Execution | order creation | COINBASE task path |
| Forensics | why trade exists | Trade Attribution Ledger |

## Safe next integrations

### Phase 1: Manual attribution

Use `tools/trade_attr_cli.py append` after a real trade is confirmed in Coinbase.

This is already safe because it cannot execute orders.

### Phase 2: Executor hook

Add `append_trade_event()` immediately after Coinbase returns an accepted order id.

Do not log before acceptance.

Do not log rejected orders as trades; rejected orders should go to incidents or audit logs.

### Phase 3: Cockpit explain endpoint

Expose a read-only command:

```text
explain latest trade
explain DOGE latest
```

This should read the ledger only.

### Phase 4: Governor
