# S25 Stabilization Roadmap

This roadmap keeps S25 alive, cheaper, and controllable.

## Stage 0 - Freeze the live core

Status: active.

Do not make large live-execution changes while the system is trading.

Allowed work:

- docs
- read-only commands
- forensic ledger
- manual attribution
- health checks
- governor design

Avoid:

- changing Coinbase order logic without exact hook location
- changing signal thresholds without test mode
- restarting services during active positions unless required

## Stage 1 - Explain every wallet movement

Status: started.

Deliverables:

- `tools/trade_attribution_ledger.py`
- `tools/trade_attr_cli.py`
- `memory/trade_attribution_ledger.jsonl`
- runbook usage

Definition of done:

- latest DOGE/BTC/AKT movement can be manually attributed
- every future Coinbase order can be explained by source + agent + strategy

## Stage 2 - Read-only cockpit visibility

Goal: add cockpit/API views that cannot trade.

Views:

- latest attributed trade
- latest signal
- current positions
- Coinbase holds
- PnL summary
- source map: signal source vs price source
- compact-mode health

Definition of done:

- operator can see why S25 is alive without opening logs

## Stage 3 - Executor attribution hook

Goal: automatic attribution only after Coinbase confirms accepted order.

Rules:

- no order id, no trade attribution
- rejected orders go to audit/incidents, not trade ledger
- price source must be explicit
- source signal must be explicit or marked unknown

Definition of done:

