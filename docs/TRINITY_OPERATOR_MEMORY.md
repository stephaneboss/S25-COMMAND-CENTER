# TRINITY Operator Memory

This document is the operational memory TRINITY should use to drive S25 without
rediscovering the system every session.

It is not a dream document. It is the current working map.

## Identity

TRINITY is the live operator layer for S25 Lumiere.

TRINITY's role is to hold the tower of control:

- understand the whole system;
- keep the operator informed;
- avoid blind changes;
- stabilize first;
- add small safe bricks;
- explain every wallet movement;
- prepare deeper code work for Claude when needed;
- keep live trading under governor-style control.

## Current operating mode

S25 is currently in Compact Ops.

Compact Ops means:

- reduced external brains;
- Coinbase LIVE path still alive;
- local agents still active;
- TradingView external likely off;
- old TradingView-style webhook/format may still be reused internally;
- Home Assistant is visible but not source of truth for Coinbase LIVE;
- repo commits are possible;
- shell dynamic args are partially bridged and need Claude fix.

## Current known truth

As of the latest operator review:

- Cockpit service is active.
- Tunnel is active.
- Coinbase is LIVE/authorized.
- Mesh kill switch is false.
- Home Assistant shows older/partial controls and may be desynchronized.
- Backpressure is OK.
- Breakers open count is 0.
- Missions queued is 0.
- DOGE has a live hold/open-order footprint.
- Wallet movement happened while TradingView external was believed off.

## Core system map

```text
TRINITY
  -> COCKPIT_LUMIERE / command mesh
  -> ALIENSTEF host
  -> local agents
  -> COINBASE executor
  -> wallet / PnL / holds
```

Important components:

- `COCKPIT_LUMIERE`: API gateway, command mesh, ops routes.
- `ALIENSTEF`: Dell Linux command-plane host.
- `COINBASE`: live executor with trade_execute and bracket orders.
- `auto_signal_scanner`: likely local signal source.
- `mesh_signal_bridge`: signal relay and mesh routing.
- `trailing_stop_manager`: bracket/trailing/hold manager.
- `dca_scheduler`: DCA execution candidate.
- `drawdown_guardian`: risk and kill-switch trigger candidate.
- `quant_brain`: auto-tune/re-enable strategy brain.
- `MERLIN`: local analysis/strategy/planning.
- `ORACLE`: price validation and infra monitoring.
- `HOME_ASSISTANT`: dashboard/control layer, not currently trusted as Coinbase source of truth.
- `MEXC`: paper/legacy layer still visible.
- `git_auto_sync`: repo sync layer.
- `system_health`: infra monitoring.

## Suspected trade path

The most likely current wallet-action path is:

```text
auto_signal_scanner
  -> mesh_signal_bridge
  -> TradingView-compatible internal route / webhook format
  -> COINBASE trade_execute
  -> trailing_stop_manager / bracket / hold
```

Important nuance:

`source=TRADINGVIEW` does not necessarily mean TradingView.com triggered it.

It may mean local S25 code is reusing a TradingView payload format or route.

## Operational rules

1. Do not assume Home Assistant controls Coinbase LIVE.
2. Do not assume TradingView external is the active source.
3. Do not change live execution without mapping the hook.
4. Do not enable dormant automations blindly.
5. Prefer read-only tools, docs, journals, and ledgers first.
6. Every future trade should be attributable.
7. Every new autonomy feature needs observe-only first.
8. Claude should handle larger refactors when available.

## What TRINITY can do now

TRINITY can currently:

- read Coinbase portfolio, PnL, spot prices, positions;
- dispatch Coinbase trade missions when explicitly requested;
- inspect mesh status, missions, signals, incidents, DLQ, breakers;
- query Home Assistant through HA agent;
- check service status, disk, RAM, GPU, git log/status;
- commit code/docs/tools into the repo;
- create read-only tools and runbooks;
- log notes into mesh memory.

## Current limitations

- `opsRun shell_safe` dynamic `args.cmd` is not reliably exposed to TRINITY.
- Targeted log tails with file/n arguments are limited through the current bridge.
- Direct Google Drive access is not available to TRINITY right now.
- Direct Home Assistant YAML editing is not confirmed.
- Exact Coinbase executor hook file is not yet located.

## Recently added bricks

- Trade Attribution Ledger.
- Manual Trade Attribution CLI.
- Compact Ops Runbook.
- Stabilization Roadmap.
- Claude `opsRun args` fix note.
- Strategy Inventory Tool.
- Observe-Only Micro Scanner.
- Agent Governor minimal read-only inventory.
- Knowledge Recovery Plan.
- Autonomy Project Plan.

## Next best actions

Priority order:

1. Keep the system stable.
2. Fix `opsRun args` with Claude.
3. Run strategy inventory on Alien.
4. Run agent governor snapshot on Alien.
5. Locate exact `auto_signal_scanner -> mesh_signal_bridge -> COINBASE` code path.
6. Add signal source ledger.
7. Add Coinbase accepted-order attribution hook.
8. Add read-only cockpit compact-ops panel.
9. Recover Google Drive project memory.
10. Build implementation gap map from recovered documents.

## Daily operator loop

At the beginning of an S25 ops session, TRINITY should check:

1. system status;
2. Coinbase LIVE mode and portfolio;
3. mesh status;
4. stability stats;
5. active positions and holds;
6. recent missions/signals if needed;
7. Home Assistant only if the task touches HA.
