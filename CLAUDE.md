# CLAUDE.md — S25 LUMIÈRE Command Center

> Autonomous Multi-Agent Crypto Trading Infrastructure
> AI assistant reference guide for codebase navigation, development workflows, and conventions.

---

## Project Overview

**S25 LUMIÈRE** is a decentralized, autonomous multi-agent system for cryptocurrency trading and blockchain monitoring. It orchestrates multiple AI models (Claude, Gemini, GPT-4o, Perplexity) through a Commander-based architecture deployed on Akash decentralized compute, integrated with Home Assistant as its operational hub.

**Tech stack:** Python 3.11+, Flask 3.0+, CCXT, Home Assistant, Docker, Akash Network

---

## Repository Structure

```
S25-COMMAND-CENTER/
├── agents/                     # Core multi-agent system
│   ├── commander.py            # Central orchestrator (mission control)
│   ├── base.py                 # Abstract base class for all agents
│   ├── arkon_signal.py         # Trading signal validator (≥75% confidence)
│   ├── balance_sentinel.py     # Multi-chain wallet monitor (Cosmos/Akash/Osmosis)
│   ├── treasury_engine.py      # Akash escrow balance manager
│   ├── risk_guardian.py        # Circuit breaker + risk limit enforcer
│   ├── mexc_executor.py        # MEXC exchange order executor
│   ├── comet_bridge.py         # Perplexity AI real-time intelligence
│   ├── gouv4_planner.py        # Governance/policy layer
│   ├── agent_loop.py           # Async event loop coordinator
│   ├── ninja_routes.py         # Internal routing layer
│   ├── cockpit_lumiere.py      # Web dashboard (port 7777)
│   ├── arkon_config/           # ARKON agent prompts and config
│   ├── claude_subagents/       # 6 specialized Claude Code subagents
│   ├── kimi_config/            # Kimi Web3 agent config
│   ├── merlin_config/          # Merlin (Gemini) agent config
│   ├── trinity_config/         # Trinity TTS orchestrator config
│   └── trinity_gpt_config/     # Trinity GPT variant config
├── ha/                         # Home Assistant integration
│   ├── automations/            # 9 HA automation YAML files
│   ├── dashboards/             # Lovelace UI dashboard
│   ├── python_scripts/         # AI router script
│   └── sensors/                # Sensor definitions
├── configs/
│   ├── agents.yaml             # Runtime config for all agents
│   └── networks.yaml           # Blockchain networks + DEX routes
├── security/
│   ├── vault.py                # Encrypted API key management
│   └── audit.py                # Audit trail for sensitive operations
├── monitoring/
│   └── health.py               # System health checks
├── memory/
│   └── SHARED_MEMORY.md        # Git-backed centralized agent state
├── akash/
│   ├── deploy_cockpit.yaml     # PROD Akash SDL
│   └── deploy_sandbox.yaml     # SANDBOX Akash SDL
├── docs/
│   ├── ARCHITECTURE.md         # System architecture deep-dive
│   ├── ROADMAP.md              # 4-sprint development roadmap
│   ├── DEPLOY_RULES.md         # Critical deployment rules (read before deploying)
│   ├── network_map.md          # Blockchain network endpoints
│   └── piping_map.md           # Signal flow diagrams
├── tests/
│   └── test_agents.py          # 25+ unit tests
├── scripts/
│   ├── deploy_s25_ha.sh        # Home Assistant deployment
│   └── github_sync.sh          # Auto-commit utility
├── cockpit_lumiere.py          # Root-level cockpit launcher
├── watchdog.py                 # Self-healing service watchdog
├── Makefile                    # Primary build and run commands
├── Dockerfile                  # Container image definition
├── requirements.txt            # Python dependencies
└── .env.example                # Environment variable template
```

---

## Agent Architecture

### Core Agents

| Agent | File | Role |
|-------|------|------|
| **Commander** | `agents/commander.py` | Central orchestrator; routes signals, manages lifecycle |
| **ARKON Signal** | `agents/arkon_signal.py` | Validates trading signals (min 75% confidence) |
| **Risk Guardian** | `agents/risk_guardian.py` | Circuit breaker; enforces all risk limits |
| **MEXC Executor** | `agents/mexc_executor.py` | Places orders on MEXC exchange |
| **Treasury Engine** | `agents/treasury_engine.py` | Monitors Akash escrow balances |
| **Balance Sentinel** | `agents/balance_sentinel.py` | Multi-chain wallet monitoring |
| **COMET Bridge** | `agents/comet_bridge.py` | Perplexity AI market intelligence |
| **GOUV4 Planner** | `agents/gouv4_planner.py` | Governance and policy management |
| **Watchdog** | `watchdog.py` | Auto-restarts crashed services |

### External AI Models

| Name | Model | Role |
|------|-------|------|
| **TRINITY** | GPT-4o | Vocal orchestrator |
| **ARKON** | Claude Code | Analyzer and builder |
| **MERLIN** | Gemini | Web validator |
| **COMET** | Perplexity | Real-time watchman |
| **KIMI** | Kimi Web3 | 1M-token signal scanner |

### Claude Code Subagents (`agents/claude_subagents/`)

1. `defi-liquidity-manager` — DeFi positions, APY, impermanent loss tracking
2. `onchain-guardian` — On-chain monitoring, rug-pull detection
3. `oracle-agent` — Real-time multi-source price feeds
4. `code-validator` — Pre-deployment code validation
5. `smart-refactor` — Async/Flask code refactoring
6. `auto-documenter` — Automated documentation pipeline

---

## Development Commands

```bash
make install       # Install all Python dependencies
make run           # Start Cockpit dashboard on :7777
make run-agents    # Start Commander + all agents
make health        # Run system health check
make audit         # Security audit
make test          # Run pytest suite
make lint          # Run flake8 linter
make deploy-ha     # Deploy to Home Assistant
make sync          # Push to GitHub
make akash-deploy  # Deploy to Akash network
make clean         # Remove build artifacts
```

### Running Tests

```bash
make test
# or directly:
python3 -m pytest tests/ -v
```

### Running Locally

```bash
cp .env.example .env        # Fill in your secrets
make install
make run                    # Dashboard at http://localhost:7777
```

---

## Environment Configuration

All secrets are managed through `security/vault.py`. **Never use `os.environ` directly** — always go through the vault.

**Required variables:**
```
HA_URL=http://homeassistant.local:8123
HA_TOKEN=<long_lived_token>
GEMINI_API_KEY=<key>
```

**Trading variables (needed for live mode):**
```
MEXC_API_KEY=<key>
MEXC_SECRET=<secret>
```

**Optional AI providers:**
```
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
PERPLEXITY_API_KEY=<key>
KIMI_API_KEY=<key>
AKASH_ENDPOINT=http://localhost:5050
AKASH_WALLET_ADDRESS=<address>
```

**Service config:**
```
PORT=7777
SECRET_KEY=<random_string>
CHECK_INTERVAL=60
MAX_RETRIES=3
```

---

## Risk & Safety Rules

These are enforced by `agents/risk_guardian.py` and must not be bypassed:

| Parameter | Limit |
|-----------|-------|
| Max daily loss | 5% |
| Max position size | 20% of portfolio |
| Max open positions | 5 |
| Stop-loss | 3% |
| Take-profit | 6% |
| Max drawdown | 15% |

**MEXC Executor is in dry-run mode by default.** Live trading requires explicit configuration. Do not enable live trading without confirming the intent with the user.

**Signal confidence threshold:** ARKON signals must have ≥75% confidence to be acted upon.

---

## Deployment Architecture

### Two-Container Rule (CRITICAL — see `docs/DEPLOY_RULES.md`)

Always maintain two separate containers:

| Container | Image Tag | Purpose |
|-----------|-----------|---------|
| **SANDBOX** | `:main` | Testing; auto-built on every push |
| **PROD** | `:latest` | Production; only built on `vX.X.X` release tags |

### Deployment Flow

```
code push → :main built → sandbox tested → git tag vX.X.X → :latest built → akash PROD updated
```

### Docker Image

Built and pushed to: `ghcr.io/stephaneboss/S25-COMMAND-CENTER`

Tags:
- `:main` — latest commit on main branch
- `:latest` — latest stable production release
- `:sha-<hash>` — pinned to specific commit (use for rollbacks)

### Akash Deployments

- **PROD Cockpit:** DSEQ 25838342 (SDL: `akash/deploy_cockpit.yaml`)
- **Phoenix AI:** DSEQ 25708774 (10 CPU + RTX 4090 GPU, ~$0.24/hr)
- **Secondary:** DSEQ 25817341 (general compute, ~$0.04/hr)

**Never put secrets in SDL files** — use placeholder environment variable names only.

---

## CI/CD Pipelines

### `ci.yml` — triggered on push/PR

- Lints Python with `flake8`
- Validates YAML configs
- Runs `pytest` suite
- **Scans for hardcoded secrets** (API keys, Bearer tokens, `os.environ` for secret vars)
- Validates Akash SDL structure

### `docker.yml` — triggered on changes to key files

Watches: `cockpit_lumiere.py`, `Dockerfile`, `requirements.txt`, `ninja_routes.py`

---

## Home Assistant Integration

### Key Sensors

| Entity ID | Description |
|-----------|-------------|
| `sensor.s25_commander` | Commander agent status |
| `sensor.s25_system_health` | Overall system health |
| `sensor.s25_arkon_signal` | Latest trading signal (BUY/SELL/HOLD) |
| `sensor.s25_wallet_cosmos` | ATOM balance |
| `sensor.s25_wallet_akash` | AKT balance |
| `sensor.s25_wallet_osmosis` | OSMO balance |
| `sensor.s25_portfolio_total` | Total USD portfolio value |
| `input_text.ai_prompt` | Active AI prompt |
| `input_select.ai_model` | Currently active AI model |

### Automations (`ha/automations/s25_automations.yaml`)

9 automations handle: Intel ingestion, threat-level alerts (T1/T2/T3), kill switch, BUY/SELL/HOLD trading signals, and Antminer monitoring.

### Kill Switch

Triggered via `POST /api/trinity` or the HA `s25_protocole_de_purge` automation. This performs a total system purge. Confirm with the user before invoking.

---

## Security Conventions

1. **All secrets via vault:** Use `security/vault.py` — never `os.environ` directly for API keys.
2. **Audit trail:** All sensitive operations must go through `security/audit.py`.
3. **No secrets in code:** CI blocks commits with hardcoded keys.
4. **No secrets in SDLs:** Akash deployment files use placeholder variable names.
5. **Gitignore:** `.env*`, `secrets.yaml`, `*.key`, `*.pem` are all ignored.

---

## Shared Memory

`memory/SHARED_MEMORY.md` is the Git-backed centralized state file. All agents read/write state through this file. It contains:
- Current infrastructure status
- Agent states and Roadmap progress
- Active Cockpit URL, HA URL, tunnel info
- Akash deployment DSEQs

**Update this file** when infrastructure changes occur (new deployments, endpoint changes, etc.).

---

## Code Conventions

### Adding a New Agent

1. Extend `agents/base.py` (`BaseAgent` abstract class)
2. Implement `start()`, `stop()`, and the main monitoring loop
3. Report status to HA via the inherited `report_to_ha()` method
4. Register in `configs/agents.yaml`
5. Register with Commander in `agents/commander.py`
6. Add unit tests in `tests/test_agents.py`

### Agent Lifecycle

All agents follow this pattern:
```python
class MyAgent(BaseAgent):
    async def start(self):
        # initialization
    async def stop(self):
        # cleanup
    async def _run_loop(self):
        # main monitoring/action loop
```

### API Endpoints (Cockpit — port 7777)

Key endpoints exposed by `cockpit_lumiere.py`:
- `GET /health` — Health check (used by Docker)
- `GET /api/status` — Full system status
- `POST /api/signal` — Ingest a trading signal
- `POST /api/trinity` — Trigger Trinity / kill switch
- `GET /api/vocal/status` — TRINITY vocal status
- `POST /api/vocal/say` — TRINITY vocal command

### Error Handling

- Use `try/except` with specific exception types
- Log errors through the standard Python `logging` module
- Report agent failures to HA via `report_to_ha(status="error")`
- The Commander handles circuit-breaker logic — don't implement it per-agent

---

## Sprint Roadmap

| Sprint | Status | Scope |
|--------|--------|-------|
| **SPRINT 1** | ✅ Done | Infra foundation — repo, vault, MEXC executor, Docker, CI/CD, COMET bridge |
| **SPRINT 2** | 🔄 In Progress | Signal flow — Akash image, ARKON sensors, Kimi webhook, live MEXC, Treasury |
| **SPRINT 3** | ⏳ Planned | IA Layer — GOUV4, TRINITY vocal, MERLIN, Balance Sentinel, Antminer |
| **SPRINT 4** | ⏳ Planned | Humanoïde Layer — humanoid agent perception, decision engine, HA actions |

---

## Key Files to Read First

When starting work on this codebase, read in this order:

1. `docs/ARCHITECTURE.md` — System design and signal flow
2. `docs/DEPLOY_RULES.md` — Deployment rules (critical before any deploy)
3. `memory/SHARED_MEMORY.md` — Current system state
4. `configs/agents.yaml` — Agent runtime parameters
5. `agents/commander.py` — Core orchestration logic
6. `agents/base.py` — Agent base class contract

---

## Threat Levels

| Level | Color | Trigger |
|-------|-------|---------|
| T0 | Green | Normal operation |
| T1 | Yellow | Surveillance mode |
| T2 | Orange | Alert mode |
| T3 | Red | Critical — auto-purge triggered |

---

*Last updated: 2026-03-09*
