# S25-KIMI-v2 — CEX-DEX Arbitrage Bot

Automated arbitrage between Osmosis DEX (on-chain) and MEXC CEX for ATOM/USDC.

---

## What It Does

The bot continuously monitors the price of ATOM on two venues:

- **Osmosis DEX** — on-chain spot price via the GAMM liquidity pool (LCD REST API)
- **MEXC CEX** — real-time ATOMUSDT ticker via the MEXC REST API

When the price difference (spread) exceeds a configurable threshold (default 0.5%)
and the composite signal score crosses a minimum (default 60/100), the bot executes
a swap on Osmosis to capture the spread.

### Direction logic

| Condition | Action |
|-----------|--------|
| OSM price < CEX price (negative spread) | BUY on Osmosis, (would sell on CEX) |
| OSM price > CEX price (positive spread) | SELL on Osmosis, (would buy on CEX) |

> Note: CEX leg execution is out of scope for v2. The bot currently manages only
> the Osmosis leg. Multi-leg execution is planned for v3.

---

## Deployment Modes

The bot has three modes, designed as a progression:

```
DRY → PAPER → LIVE
```

### DRY (default, safe)

- No transactions. No wallets needed.
- Logs what the bot *would* do on every qualifying signal.
- All trades recorded to SQLite with status `dry`.
- Use this to validate your config and observe signal frequency.

### PAPER

- Simulates trades with theoretical P&L calculations.
- Applies real spread/score/risk logic, but no on-chain transactions.
- Records P&L estimates to SQLite (`status=paper`).
- Use this to evaluate strategy performance over days/weeks.

### LIVE

- Broadcasts real `MsgSwapExactAmountIn` transactions on Osmosis.
- Requires wallet mnemonic and explicit `LIVE_MODE_CONFIRMED=yes`.
- Has multiple safeguards: circuit breaker, daily loss cap, reserve guard.

---

## Configuration

All settings are controlled via environment variables.

### Execution

| Variable | Default | Description |
|----------|---------|-------------|
| `S25_MODE` | `dry` | Execution mode: `dry`, `paper`, or `live` |
| `LIVE_MODE_CONFIRMED` | — | Must be `yes` to allow live trading |

### Wallet (required in LIVE mode)

| Variable | Description |
|----------|-------------|
| `WALLET_MNEMONIC` | BIP39 mnemonic phrase (24 words) |
| `WALLET_ADDRESS` | Osmosis bech32 address (`osmo1...`) |

### Trade Sizing

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADE_SIZE_USD` | `5.0` | Target notional per trade in USD |
| `MAX_TRADE_USD` | `10.0` | Hard cap per trade in USD |
| `MIN_RESERVE_USD` | `2.0` | Minimum wallet balance to keep untouched |

### Risk Management

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_DAILY_LOSS_USD` | `15.0` | Daily loss limit before halting |
| `MAX_CONSECUTIVE_FAILS` | `3` | Failures before circuit breaker trips |
| `CIRCUIT_BREAKER_COOLDOWN_MIN` | `60` | Cooldown period in minutes after trip |

### Signal Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `SPREAD_THRESHOLD` | `0.005` | Minimum spread (0.5%) to consider a signal |
| `MIN_SIGNAL_SCORE` | `60` | Minimum composite score (0-100) to trade |

### Timing

| Variable | Default | Description |
|----------|---------|-------------|
| `SCAN_INTERVAL` | `30` | Seconds between scans |

### Telegram Alerts

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your chat or group ID |

If these are not set, the bot runs silently (alerts logged to console only).

### Infrastructure

| Variable | Default | Description |
|----------|---------|-------------|
| `OSMOSIS_LCD` | `https://lcd.osmosis.zone` | Osmosis REST endpoint |
| `MEXC_API` | `https://api.mexc.com/api/v3` | MEXC REST base URL |
| `DB_PATH` | `trades.db` | SQLite database file path |

---

## Running

### Local (dry mode)

```bash
pip install -r requirements.txt
S25_MODE=dry python main.py
```

### Docker

```bash
docker build -t s25-kimi-v2 .

# Dry mode
docker run --rm \
  -e S25_MODE=dry \
  -e TELEGRAM_TOKEN=your_token \
  -e TELEGRAM_CHAT_ID=your_chat_id \
  -v $(pwd)/data:/data \
  s25-kimi-v2

# Paper mode
docker run --rm \
  -e S25_MODE=paper \
  -e TELEGRAM_TOKEN=your_token \
  -e TELEGRAM_CHAT_ID=your_chat_id \
  -v $(pwd)/data:/data \
  s25-kimi-v2

# Live mode
docker run --rm \
  -e S25_MODE=live \
  -e LIVE_MODE_CONFIRMED=yes \
  -e WALLET_MNEMONIC="word1 word2 ... word24" \
  -e WALLET_ADDRESS="osmo1..." \
  -e TELEGRAM_TOKEN=your_token \
  -e TELEGRAM_CHAT_ID=your_chat_id \
  -v $(pwd)/data:/data \
  s25-kimi-v2
```

---

## Tests

```bash
# From the kimi_v2/ directory
pytest tests/ -v
```

Tests use mocked HTTP sessions — no real API calls are made.

---

## How Telegram Alerts Work

Every trade attempt (successful or failed) generates an alert:

```
✅ Trade Alert [🧪 DRY]
Symbol: ATOM  ⬆️ BUY
OSM: $9.0500  |  CEX: $9.6000
Spread: 0.573%  Score: 72
P&L: 📈 $0.0120
```

### Alert types

| Icon | Meaning |
|------|---------|
| ✅ | Trade executed successfully |
| ❌ | Trade failed |
| 🔴 | Circuit breaker tripped |
| ⚠️ | General warning |
| 📊 | Daily report |
| 🚀 | Bot started |
| 🛑 | Bot stopped |
| 💓 | Heartbeat (every 100 scans) |

Mode is always shown in brackets: `[🧪 DRY]`, `[📄 PAPER]`, or `[🔴 LIVE]`.

---

## Circuit Breaker

The circuit breaker prevents runaway losses during adverse market conditions
or API instability.

**Trips when:** `MAX_CONSECUTIVE_FAILS` trade executions fail in a row (default: 3).

**While tripped:** All trade execution is blocked. The bot continues scanning
and logging signals, but will not execute any swaps.

**Auto-reset:** After `CIRCUIT_BREAKER_COOLDOWN_MIN` minutes (default: 60),
the breaker resets automatically and trading resumes.

**Alert:** A `🔴 CIRCUIT BREAKER TRIPPED` Telegram message is sent immediately.

---

## P&L Calculation

### Paper mode

P&L is estimated using the formula:

```
gross_pnl = notional_usd * abs(spread_pct)
fees       = notional_usd * 0.002 + 0.05   (0.2% pool fee + ~$0.05 gas flat)
net_pnl    = gross_pnl - fees
```

This is theoretical — actual P&L may vary due to price impact and slippage.

### Live mode

P&L is calculated from the actual amounts in/out reported by the on-chain
transaction, converted to USD using the CEX price at execution time:

```
BUY:  pnl = (tokens_received × cex_price) - usdc_spent
SELL: pnl = usdc_received - (tokens_sent × cex_price)
```

---

## Osmosis Pool Reference

| Pool | Pair | Pool ID |
|------|------|---------|
| ATOM/OSMO | Cosmos Hub ATOM | 1 |
| AKT/OSMO  | Akash Network   | 3 |
| OSMO/USDC | Stablecoin hub  | 678 |

---

## Architecture

```
main.py
  └─ Config.from_env()          # all settings
  └─ PriceOracle                # oracle.py  → Osmosis LCD + MEXC REST
  └─ RiskManager                # risk.py    → circuit breaker, guards, sizer
       └─ CircuitBreaker
       └─ BalanceGuard
       └─ PositionSizer
       └─ DailyLossTracker
  └─ SwapExecutor               # executor.py → dry / paper / live
  └─ TradeLedger                # ledger.py  → SQLite persistence
  └─ TelegramReporter           # reporter.py → Telegram Bot API
```

---

## Safety Checklist Before Going Live

- [ ] Run in DRY mode for at least 48 hours and inspect logs
- [ ] Run in PAPER mode for at least 7 days and review P&L stats
- [ ] Set `MAX_DAILY_LOSS_USD` to an amount you can afford to lose entirely
- [ ] Set `MIN_RESERVE_USD` to a meaningful buffer
- [ ] Verify `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` are working (you get startup message)
- [ ] Test CTRL+C produces a clean shutdown report
- [ ] Confirm wallet has enough USDC and OSMO for gas
- [ ] Set `LIVE_MODE_CONFIRMED=yes` — this is a deliberate, irreversible gate
