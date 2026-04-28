# S25 Control Hardening Plan

This document defines how TRINITY should increase control over S25 without
destabilizing the live system.

The system already has real actions happening. Therefore control must be taken
gradually.

## Current stance

S25 is alive and partially automated.

Current mode:

```text
Compact Ops / guarded observation
```

Do not assume inactive external services mean inactive automation. Local agents
can still scan, relay, execute, update brackets, and move wallet state.

## Control-speed ladder

TRINITY should climb this ladder in order:

### Level 0 - Observe

- Read system state.
- Read Coinbase state.
- Read mesh and stability state.
- Read HA state when relevant.
- Make no changes.

### Level 1 - Record

- Write docs.
- Write operator memory.
- Write runbooks.
- Write read-only inventory tools.
- Log ops notes into mesh.

### Level 2 - Explain

- Build attribution ledgers.
- Map agents and trade-path candidates.
- Explain latest signal, trade, hold, and position.

### Level 3 - Recommend

- Produce action plans.
- Propose safe next bricks.
- Prepare Claude tasks.
- Recommend governor policies.

### Level 4 - Guard

- Add pre-execution checks.
- Add max trade limits.
- Add source allowlists.
- Add cooldowns.
- Add exposure limits.

### Level 5 - Act

- Execute only with explicit operator intent or governor-approved automation.
- Every action must be attributable.
- Every failure must be journaled.

Current target:

```text
Level 0 -> Level 3, with limited Level 1 repo changes
```

Do not jump to Level 4/5 until the exact execution hook is mapped.

## Tools currently available

### Read/state tools

- System status
- Mesh status
- Agent list
- Mission list/get
- Signals list
- Incidents
- Stability stats
- Breakers
- DLQ
- Coinbase portfolio
- Coinbase positions
- PnL
- Spot prices
- Home Assistant status
- HA agent read/query
- Service status
- Git status/log
- Disk/RAM/GPU status

### Write/build tools

- Repo patch/commit
- Mesh intent journal
- New read-only tools
- Docs/runbooks

### Live-action tools

- Coinbase trade mission dispatch exists.
- HA agent action likely exists.
- Agent restart likely exists.

Live-action tools should remain guarded until mapping is complete.

## Immediate security priorities

### 1. Prevent invisible trade authority

Risk:

An agent emits or routes a signal that becomes a Coinbase order without clear
operator understanding.

Mitigation:

- maintain Agent Governor map;
- identify `auto_signal_scanner`, `mesh_signal_bridge`, `COINBASE`,
  `trailing_stop_manager`, and `dca_scheduler` roles;
- add signal source ledger;
- add accepted-order attribution hook.

### 2. Separate price source from signal source

Risk:

Payloads tagged `TRADINGVIEW` may actually be local scanner events.

Mitigation:

- treat `source=TRADINGVIEW` as a label until proven external;
- record actual ingress route separately;
- record price source separately, likely Coinbase spot.

### 3. Handle HA/Cockpit desync

Risk:

Home Assistant shows kill/live flags that differ from Cockpit/Coinbase reality.

Mitigation:

- do not trust HA as Coinbase source of truth;
- add a sync warning panel/check;
- classify HA as dashboard/control layer until proven authoritative.

### 4. Control DCA and trailing managers

Risk:

DCA or trailing logic can create or modify orders without obvious signal flow.

Mitigation:

- map `dca_scheduler` activity;
- map `trailing_stop_manager` activity;
- require mutation journal for bracket/trailing changes.

### 5. Fix opsRun args

Risk:

TRINITY cannot inspect targeted logs or run inventory tools directly.

Mitigation:

