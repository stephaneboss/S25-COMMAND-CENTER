# S25 Signal Source Ledger

The Signal Source Ledger records where a signal appears to come from before it
can become a trade.

It does not execute trades.

## Tool

```text
tools/signal_source_ledger_min.py
```

## Ledger

```text
memory/signal_source_ledger.jsonl
```

## Why this exists

S25 may show `source=TRADINGVIEW` even when external TradingView is off.

That can happen if local S25 agents reuse a legacy TradingView-compatible
payload or webhook route.

This ledger separates:

- `source_label`: what the payload claims;
- `actual_ingress`: where TRINITY/S25 believes it really entered;
- `source_agent`: local agent responsible if known.

## Fields

- `ts`
- `symbol`
- `action`
- `source_label`
- `actual_ingress`
- `source_agent`
- `strategy`
- `confidence`
- `effective_confidence`
- `verdict`
- `payload_price`
- `price_source`
- `routed_to`
- `mission_id`
- `reason`
- `mode`

## Example

```bash
python tools/signal_source_ledger_min.py append \
  --symbol DOGE-USD \
  --action BUY \
  --source-label TRADINGVIEW \
  --actual-ingress local_mesh_signal_bridge \
  --source-agent auto_signal_scanner \
  --strategy stoch_rsi_bounce \
  --confidence 0.85 \
  --effective-confidence 0.7225 \
  --verdict EXECUTE \
  --payload-price 0 \
  --price-source coinbase_spot \
  --routed-to COINBASE \
  --reason "Legacy TradingView payload label; likely local scanner source" \
  --mode authorized
```

Explain latest signal:

```bash
