# S25 Knowledge Recovery Plan

S25 is not only code, trading, agents, and dashboards.

S25 also has a long strategic memory: documents, plans, architectures, future
visions, prompts, roadmaps, notes, and decisions written over time by Stef and
TRINITY.

The next major non-trading objective is to recover that memory and turn it into
an operational knowledge base.

## Goal

Find, classify, and reconnect the written future of S25.

The project should not depend only on what is currently running. It should also
use the strategic documents that already describe what S25 is supposed to
become.

## Sources to recover

Potential sources:

- Google Drive project documents
- ChatGPT exported conversations
- Claude project notes
- GitHub repository docs
- `memory/` runtime notes
- `memory/command_mesh/ops_journal.jsonl`
- architecture markdown files
- old Home Assistant notes or helpers
- Smajor website notes
- Cloudflare worker notes
- screenshots or PDFs
- local AlienStef files outside the current repo

## Categories

Recovered documents should be classified into these buckets:

### 1. Vision

Long-term purpose, philosophy, future architecture, autonomy, identity of S25.

### 2. Architecture

System design, agents, cockpit, mesh, cloud, local machine, HA, Coinbase,
Cloudflare, Smajor, memory, workflows.

### 3. Trading

Strategies, risk, wallets, Coinbase, MEXC, TradingView legacy, scanners,
governors, attribution, PnL, DCA, trailing stops.

### 4. Agents

TRINITY, MERLIN, ORACLE, ARKON5, COMET, KIMI, Claude, Gemini, local Qwen,
Home Assistant, system agents.

### 5. Infra

AlienStef host, systemd, cron, GitHub, Cloudflare, Smajor, tunnels, secrets,
ops tooling.

### 6. Product / UX

Cockpit, dashboards, voice control, mobile control, HA panels, operator flows.

### 7. Memory / Governance

How S25 remembers, audits, explains actions, governs agents, and handles risk.

### 8. Future / Roadmap

Ideas that are not implemented yet but were already designed.

## Recovery process

### Phase 1 - Inventory

List every candidate document without interpreting it.

Output:

```text
memory/knowledge_inventory.json
```

Each entry should include:

- title
- source
- path or URL reference
- date if known
- type
- short description
- confidence

### Phase 2 - Classification

Assign each document to one or more categories.

Output:

```text
memory/knowledge_classified.json
```

### Phase 3 - Extraction

Extract decisions, architecture claims, future tasks, warnings, and principles.

Output:

```text
memory/knowledge_extracted.jsonl
```

### Phase 4 - Synthesis

Create a living master map:

```text
docs/S25_MASTER_MAP.md
```

This should become the canonical overview of S25.

### Phase 5 - Reconnection

For each recovered idea, decide:

- already implemented
