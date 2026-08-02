"""
S25 Lumière — Coinbase preflight / heartbeat / canary guard tests
====================================================================
Run: python3 -m pytest tests/test_coinbase_preflight.py -v

No real Coinbase API calls - a fake executor stands in for CoinbaseExecutor.
Mission mis_PG7Ig33AFRLs priority 6: proves the guardrails actually block
execution at the real current balance ($0.52-0.53).
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import coinbase_preflight as cp  # noqa: E402


class FakeClient:
    def __init__(self, open_orders=None, product_overrides=None, trading_disabled=False):
        self._open_orders = open_orders or []
        self._product_overrides = product_overrides or {}
        self._trading_disabled = trading_disabled

    def get_product(self, product_id):
        base = {"base_min_size": "0.00001", "quote_min_size": "1.00",
                "base_increment": "0.00001", "price_increment": "0.01",
                "status": "online", "trading_disabled": self._trading_disabled}
        base.update(self._product_overrides)
        return base

    def list_orders(self, order_status=None):
        return {"orders": self._open_orders}


class FakeExecutor:
    """Minimal stand-in for CoinbaseExecutor - same attribute/method surface
    coinbase_preflight.py actually touches, nothing more."""

    def __init__(self, available_usd, price=60000.0, dry_run=False, client=None,
                 order_result=None):
        self._available_usd = available_usd
        self._price = price
        self.dry_run = dry_run
        self._client = client or FakeClient()
        self._order_result = order_result or {"ok": True, "dry_run": False,
                                               "order": {"success": True}}

    def refresh_mode_from_ha(self):
        return not self.dry_run

    def _get_client(self):
        return self._client

    def get_accounts(self):
        return {"ok": True, "balances": {"USD": self._available_usd}, "count": 1}

    def get_product_price(self, product_id):
        return self._price

    def place_market_order(self, product_id, side, usd_amount, reason="", source=""):
        return self._order_result


def test_preflight_blocks_at_real_current_balance():
    """The actual production case right now: $0.52 available, $5 canary -> blocked."""
    exe = FakeExecutor(available_usd=0.52)
    result = cp.preflight_check(exe, "BTC-USD", cp.CANARY_USD, "BUY")
    assert result["can_proceed"] is False
    assert any("insufficient_balance" in r for r in result["blocking_reasons"])


def test_preflight_passes_when_funded_and_clean():
    exe = FakeExecutor(available_usd=50.0)
    result = cp.preflight_check(exe, "BTC-USD", cp.CANARY_USD, "BUY")
    assert result["can_proceed"] is True
    assert result["blocking_reasons"] == []


def test_preflight_flags_open_orders():
    client = FakeClient(open_orders=[{"order_id": "abc123"}])
    exe = FakeExecutor(available_usd=50.0, client=client)
    result = cp.preflight_check(exe, "BTC-USD", cp.CANARY_USD, "BUY")
    assert result["can_proceed"] is False
    assert any("open_orders_present" in r for r in result["blocking_reasons"])


def test_preflight_flags_below_product_minimum():
    client = FakeClient(product_overrides={"quote_min_size": "10.00"})
    exe = FakeExecutor(available_usd=50.0, client=client)
    result = cp.preflight_check(exe, "BTC-USD", cp.CANARY_USD, "BUY")  # 5 < 10
    assert result["can_proceed"] is False
    assert any("below_product_minimum" in r for r in result["blocking_reasons"])


def test_preflight_flags_trading_disabled():
    client = FakeClient(trading_disabled=True)
    exe = FakeExecutor(available_usd=50.0, client=client)
    result = cp.preflight_check(exe, "BTC-USD", cp.CANARY_USD, "BUY")
    assert result["can_proceed"] is False
    assert "product_trading_disabled" in result["blocking_reasons"]


def test_non_financial_heartbeat_never_writes_trades_log(tmp_path, monkeypatch):
    log = tmp_path / "coinbase_heartbeat_log.jsonl"
    monkeypatch.setattr(cp, "HEARTBEAT_LOG", log)
    exe = FakeExecutor(available_usd=0.52)
    entry = cp.non_financial_heartbeat(exe, "BTC-USD", 5.0)
    assert entry["type"] == "non_financial_heartbeat"
    assert entry["would_be_blocked"] is True  # insufficient balance
    assert log.exists()
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["simulated_base_size"] == round(5.0 / 60000.0, 8)
    # Must never touch the real trades ledger
    assert not (tmp_path / "trades_log.jsonl").exists()


def test_canary_blocked_at_real_current_balance():
    """Proves the guardrail: with $0.52 available, run_canary_order refuses
    and never calls place_market_order."""
    calls = []

    class TrackingExecutor(FakeExecutor):
        def place_market_order(self, *a, **kw):
            calls.append((a, kw))
            return super().place_market_order(*a, **kw)

    exe = TrackingExecutor(available_usd=0.52)
    result = cp.run_canary_order(exe, "BTC-USD", cp.CANARY_USD)
    assert result["blocked"] is True
    assert result["ok"] is False
    assert calls == []  # no order was ever attempted


def test_canary_cap_enforced_even_if_funded():
    exe = FakeExecutor(available_usd=1000.0)
    result = cp.run_canary_order(exe, "BTC-USD", 50.0)  # way above CANARY_USD
    assert result["blocked"] is True
    assert any("canary_cap_exceeded" in r for r in result["reasons"])


def test_canary_proceeds_when_funded_and_within_cap():
    exe = FakeExecutor(available_usd=50.0)
    result = cp.run_canary_order(exe, "BTC-USD", cp.CANARY_USD)
    assert result["blocked"] is False
    assert result["ok"] is True
    assert result["idempotency_key"].startswith("s25-canary-")


def test_reconcile_portfolio_no_crash_and_explains():
    exe = FakeExecutor(available_usd=0.52)
    result = cp.reconcile_portfolio(exe)
    assert result["ok"] is True
    assert result["live_usd_available"] == 0.52
    assert "explanation" in result
