# S25 Strategy Registry

The Strategy Registry is the inventory and control layer for S25 strategies.

It is not an executor and it does not trade.

## Files

```text
config/strategy_registry.json
tools/strategy_registry.py
```

## Current mode

The initial registry is observe-only.

No registered strategy has live execution authority.

## Initial strategies

- `stoch_rsi_bounce`
- `bollinger_bounce`
- `btc_daily_dca`
- `doge_opportunistic_accumulation`

## Why this exists

S25 already has wallet movement and repeated DOGE accumulation behavior.

The registry gives that behavior a name and a control surface before additional
autonomy is granted.

Every strategy should declare:

- family
- symbols
- suspected source agent
- signal permission
- live execution permission
- trade size limits
- cooldown
- required journals

## Usage

Summary:

```bash
python tools/strategy_registry.py summary
```

List JSON:

```bash
python tools/strategy_registry.py list
```

Show one strategy:

```bash
python tools/strategy_registry.py show stoch_rsi_bounce
```

Check live authority:

```bash
python tools/strategy_registry.py live-report
```

## Safety rule

A strategy being present in the registry does not mean it is allowed to trade.

Live execution requires:
