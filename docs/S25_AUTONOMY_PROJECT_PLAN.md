# S25 Autonomy Project Plan

S25 has one clear direction: become a living, explainable, governed, multi-agent
system that can operate in compact mode, recover its strategic memory, and
deploy autonomy step by step.

This plan exists so every daily brick moves the system toward that direction.

## North Star

S25 is not only a trading robot.

S25 is a control plane for local and cloud agents, wallets, infrastructure,
memory, automation, Home Assistant, cockpit operations, and strategic planning.

Trading is the best live proof that the system is alive, but the larger goal is
controlled autonomy.

## Operating principle

Each day, add one small brick that improves at least one of these dimensions:

1. Visibility
2. Traceability
3. Stability
4. Governance
5. Memory recovery
6. Operator control
7. Safe autonomy

Avoid large, risky rewrites while live systems are active.

## Current foundation

Already live or partially live:

- S25 Cockpit Lumiere
- Command Mesh
- TRINITY operator layer
- Coinbase LIVE executor
- auto_signal_scanner
- mesh_signal_bridge
- trailing_stop_manager
- dca_scheduler
- drawdown_guardian
- quant_brain
- MERLIN
- ORACLE
- Home Assistant bridge/dashboard
- MEXC/paper legacy layer
- system_health
- git_auto_sync
- stability layer
- DLQ/retry/breakers
- repo-level patch/commit ability

Recently added control bricks:

- Trade Attribution Ledger
- Manual Trade Attribution CLI
- Compact Ops Runbook
- Stabilization Roadmap
- Strategy Inventory Tool
- Observe-Only Micro Scanner
- Claude opsRun args fix note
- Agent Governor minimal read-only inventory
- Knowledge Recovery Plan

## Strategic memory recovery

The long-term project architecture likely exists in Google Drive and historical
documents.

Expected source owner from old design:

- Gemini/Gemini orchestrator may have been responsible for Google Drive access.

Current limitation:

- TRINITY does not currently have direct Google Drive access through active
  tooling.

Near-term workaround:

- recover from repo docs and memory files first;
- later reconnect Drive through Gemini, Claude, or a dedicated Drive ingestion
  agent;
- avoid forcing Stef to manually rewrite everything.

## Project phases

### Phase 1 - Stabilize the living core

Goal: keep the system alive and explainable.

Deliverables:

- compact ops runbook
- agent inventory
- Coinbase/HA/MEXC state map
- no blind live changes
- daily health snapshot

Definition of done:

- operator can answer what is alive, what is degraded, and what can act.

### Phase 2 - Explain every action

Goal: no wallet movement or automation action is opaque.

Deliverables:

- trade attribution ledger
- signal source ledger
- order/hold attribution
- latest action explanation

Definition of done:

- every new Coinbase order has source, strategy, agent, reason, amount, and mode.

### Phase 3 - Recover the written future

Goal: reconnect S25 to the Drive/project documents.

Deliverables:

- knowledge inventory
- document classification
- extracted decisions
- S25 master map
- implementation gap map

Definition of done:

- old project documents become actionable tasks and architecture references.

### Phase 4 - Build the control plane

Goal: make TRINITY and Cockpit the central living map.

Deliverables:

- agent governor state
- cockpit read-only control panel
- HA/Coinbase sync warning
- MEXC legacy status
- scanner/DCA/trailing visibility

Definition of done:

- the operator can see agent power and system state without digging through logs.

### Phase 5 - Add safe autonomy

Goal: let agents act only through rules.

Deliverables:

- trade governor
- source allowlist/blocklist
- max USD per trade
- max exposure per symbol
- cooldowns
- max trades per hour
- observe-only modes
- approval thresholds

Definition of done:

- autonomy can be increased or decreased deliberately.

### Phase 6 - Reactivate advanced brains only when useful

Goal: restore Claude/Gemini/Kimi only where they add measurable value.

Suggested order:

1. Claude for code and repo refactors
2. Gemini/Drive ingestion for strategic memory
