# S25 Lumière — Architecture

## Vision

**S25 Lumière** est une infrastructure multi-agent autonome pour le trading crypto.
Le système opère 24/7 sans intervention manuelle, gérant l'infrastructure Akash,
les balances multi-chain, et les signaux de trading ARKON-5.

```
┌─────────────────────────────────────────────────────────────────┐
│                     S25 LUMIÈRE ECOSYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Kimi Web3          ARKON-5 Model        Home Assistant        │
│   (Signal)    ───►  (Gemini/Ollama)  ◄──► (Hub Central)        │
│      │                    │                    │                │
│      ▼                    ▼                    ▼                │
│   ┌──────────────────────────────────────────────────────┐     │
│   │              S25 COMMANDER (Orchestrator)            │     │
│   │                                                      │     │
│   │  ┌─────────┐  ┌──────────┐  ┌────────────┐          │     │
│   │  │ Treasury │  │ Balance  │  │   ARKON    │          │     │
│   │  │ Engine  │  │Sentinel  │  │  Signal    │          │     │
│   │  │ATOM→AKT │  │Multi-    │  │ Processor  │          │     │
│   │  └─────────┘  │Chain     │  └────────────┘          │     │
│   │               └──────────┘                          │     │
│   │  ┌─────────┐  ┌──────────┐  ┌────────────┐          │     │
│   │  │  Risk   │  │  MEXC    │  │  Watchdog  │          │     │
│   │  │Guardian │  │ Executor │  │  (Health)  │          │     │
│   │  │Circuit  │  │ Orders   │  │            │          │     │
│   │  │Breaker  │  └──────────┘  └────────────┘          │     │
│   │  └─────────┘                                        │     │
│   └──────────────────────────────────────────────────────┘     │
│                           │                                     │
│              ┌────────────┼────────────┐                        │
│              ▼            ▼            ▼                        │
│          Akash Net      MEXC        Cosmos                      │
│         (Infra)        (Trading)   (Wallets)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Signal Flow

```
1. Kimi Web3 generates market signal
2. → HTTPS → Cloudflare Tunnel → Kimi Proxy (port 9191)
3. → HA Webhook (s25_kimi_scan_secret_xyz)
4. → HA Automation → input_text.ai_prompt updated
5. → ai_router.py → Gemini validates signal
6. → Commander.dispatch(ARKON_SIGNAL)
7. → ArkonSignal.validate() → confidence check
8. → RiskGuardian.approve() → risk check
9. → MexcExecutor.execute() → place order
10. → HA sensor update → Dashboard notification
```

## Components

### Commander (`agents/commander.py`)
- Central orchestrator
- Routes signals between agents
- Manages circuit breaker
- Lifecycle management (start/stop all agents)

### Treasury Engine (`agents/treasury_engine.py`)
- Monitors Akash deployment escrow balances
- Alerts when AKT balance low
- Future: auto-swap ATOM→AKT via Osmosis

### Balance Sentinel (`agents/balance_sentinel.py`)
- Tracks ATOM, AKT, OSMO balances
- Updates HA sensors in real-time
- Portfolio valuation in USD

### ARKON Signal (`agents/arkon_signal.py`)
- Receives signals from Kimi Web3
- Validates confidence threshold (min 75%)
- Enriches with market context

### Risk Guardian (`agents/risk_guardian.py`)
- Hard limits: 5% daily loss max
- Circuit breaker on limit breach
- Position sizing enforcement

### MEXC Executor (`agents/mexc_executor.py`)
- Order placement on MEXC exchange
- Dry-run mode by default
- Fills tracked and reported to HA

### Watchdog (`agents/watchdog.py`)
- Monitors all agent health
- Auto-restarts crashed agents
- Escalates to HA if restart fails

## Security Model

```
.env file          → Local dev only, NEVER committed
Environment vars   → Akash container env (production)
Vault (vault.py)   → Single access point for all secrets
Audit (audit.py)   → All sensitive ops logged + hashed
CI/CD              → Scans for hardcoded secrets on every push
```

## Akash Infrastructure

| DSEQ      | Label        | Spec                  | Cost/hr |
|-----------|-------------|----------------------|---------|
| 25708774  | s25-phoenix  | 10 CPU + RTX 4090 GPU | ~$0.24  |
| 25817341  | s25-secondary| General compute       | ~$0.04  |

## Home Assistant Integration

Entities managed by S25:
- `sensor.s25_commander`         — Commander status
- `sensor.s25_system_health`     — Overall system health
- `sensor.s25_arkon_signal`      — Latest ARKON-5 signal
- `sensor.s25_wallet_cosmos`     — ATOM balance
- `sensor.s25_wallet_akash`      — AKT balance
- `sensor.s25_wallet_osmosis`    — OSMO balance
- `sensor.s25_portfolio_total`   — Total portfolio USD
- `sensor.s25_agent_*`           — Individual agent status
- `input_text.ai_prompt`         — Current AI prompt
- `input_select.ai_model`        — Active AI model
- `input_text.ai_model_actif`    — Pipeline status

## Roadmap

### Phase 1 (Current) — Foundation
- [x] Commander + Base Agent framework
- [x] Treasury Engine (monitoring)
- [x] Balance Sentinel (multi-chain)
- [x] ARKON Signal processor
- [x] Risk Guardian
- [x] Security Vault + Audit
- [x] CI/CD pipeline

### Phase 2 — Live Trading
- [ ] MEXC Executor (live orders)
- [ ] Osmosis auto-swap (ATOM→AKT)
- [ ] Gemini signal validation
- [ ] Telegram alerts

### Phase 3 — Scale
- [ ] 10+ Akash deployments
- [ ] 10+ Cosmos chains monitored
- [ ] Multi-exchange support
- [ ] IA Humanoïde interface
