# S25 Trade Attribution Ledger

The attribution ledger answers one operational question:

> Why does this trade exist?

It is a small JSONL forensic layer for Coinbase/ARKON5/MERLIN/ORACLE/TRINITY.
It is intentionally not wired into live execution yet.

## File

Default path:

```text
memory/trade_attribution_ledger.jsonl
```

Each line is one JSON object.

## Standard fields

```json
{
  "ts": "2026-04-28T16:58:00+00:00",
  "symbol": "DOGE-USD",
  "side": "BUY",
  "usd_amount": 2.0,
  "source_signal": "TRADINGVIEW",
  "source_agent": "ARKON5",
  "strategy": "stoch_rsi_bounce",
  "confidence": 0.85,
  "mission_id": "mis_xxx",
  "coinbase_order_id": "order_xxx",
  "reason": "StochRSI bounce; Coinbase spot validated",
  "price_source": "coinbase_spot",
  "execution_agent": "COINBASE",
  "mode": "authorized"
}
```

Unknown fields are preserved under `extra`.

## CLI

Explain the latest attributed trade:

```bash
python tools/trade_attribution_ledger.py latest
```

Explain the latest attributed DOGE trade:

```bash
python tools/trade_attribution_ledger.py latest DOGE-USD
```

