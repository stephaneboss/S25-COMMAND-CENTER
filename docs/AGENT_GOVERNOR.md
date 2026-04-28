# S25 Agent Governor

The Agent Governor is the control-plane map for S25 Compact Ops.

The first implementation is intentionally read-only:

```text
tools/agent_governor_min.py
```

It does not trade, restart services, mutate Home Assistant, or change agent
state. It only reads the agent registry and produces a compact state snapshot.

## Purpose

Answer these questions:

- Which agents are visible?
- Which agents can emit signals?
- Which agents can execute trades?
- Which agents can modify orders?
- Which agents are candidates in the trade path?

## Input

Default input:

```text
memory/command_mesh/agents.json
```

## Output

Default output:

```text
memory/agent_governor_state.json
```

## Usage

```bash
python tools/agent_governor_min.py
```

## Current trade-path suspects

Based on live mesh observations, the likely trade path is:

```text
auto_signal_scanner
  -> mesh_signal_bridge
  -> COINBASE trade_execute
  -> trailing_stop_manager / brackets / holds
```

Secondary candidates:

- `dca_scheduler`
- `quant_brain`
- `drawdown_guardian`
- `HOME_ASSISTANT` as control plane, not confirmed as Coinbase authority

## Promotion path

Phase 1: read-only inventory. Current.

