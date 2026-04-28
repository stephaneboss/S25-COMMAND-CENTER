# S25 Micro Scanner Observe-Only

The micro scanner is a safe, local, observe-only component.

It never executes trades.

It prepares S25 for fast market scanning without giving the scanner direct
authority over Coinbase.

## Tool

```text
tools/micro_scanner_observe.py
```

## Purpose

Input:

- Coinbase spot price snapshot, or any JSON map of prices.

Output:

- JSON observation to stdout.
- JSONL journal entry.
- Rolling local state file.

Default files:

```text
memory/micro_scanner_state.json
memory/micro_scanner_observe.jsonl
```

## Signals

The scanner currently computes:

- RSI
- Bollinger bands
- short momentum
- simple score

Signals are non-binding:

- `WATCH_BUY`
- `WATCH_SELL`
- `HOLD_OBSERVE`
- `INSUFFICIENT_DATA`

## Example input

```json
{
  "prices": {
    "BTC-USD": 76000,
    "DOGE-USD": 0.099,
    "SOL-USD": 83.4
  }
}
```

## Example usage

From a file:

```bash
python tools/micro_scanner_observe.py --prices /tmp/s25_prices.json
```

From stdin:

```bash
echo '{"prices":{"DOGE-USD":0.099,"BTC-USD":76000}}' | python tools/micro_scanner_observe.py
```

## Safety rules

- The scanner does not import Coinbase execution code.
- The scanner does not create missions.
- The scanner does not call `trade_execute`.
- The scanner only journals observations.
- Live trading requires a future governor and explicit executor hook.

## Future wiring

Recommended path:

```text
Coinbase spot -> micro scanner observe -> journal -> cockpit read-only -> governor -> Coinbase executor
```

Do not skip the governor.

