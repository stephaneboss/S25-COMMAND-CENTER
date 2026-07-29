"""
S25 Lumière — Position Tracker / PnL consistency tests
=======================================================
Run: python3 -m pytest tests/test_position_tracker.py -v

Covers the audit requested in mission mis_kE667jmyWxK0 / mis_tO7cMHi7A4BO
priority 4: PnL correctness, fee accounting, FIFO matching, dedup, missing data.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import position_tracker as pt  # noqa: E402


def _write_log(tmp_path, lines):
    log = tmp_path / "trades_log.jsonl"
    with log.open("w", encoding="utf-8") as f:
        for entry in lines:
            f.write(json.dumps(entry) + "\n")
    return log


def _trade(trade_id, symbol, side, base_size, avg_price, fee, ts, mode="live", success=True):
    return {
        "ts": ts, "trade_id": trade_id, "order_id": trade_id, "symbol": symbol,
        "side": side, "usd_amount": round((base_size or 0) * (avg_price or 0), 4),
        "base_size": base_size, "avg_price": avg_price, "fee": fee,
        "mode": mode, "strategy": "test", "source": "test", "success": success,
        "notes": "",
    }


def test_pnl_basic_profit(tmp_path, monkeypatch):
    """BUY then SELL higher, zero fees -> pnl_usd == exact price delta * qty."""
    log = _write_log(tmp_path, [
        _trade("t1", "BTC-USD", "BUY", 1.0, 100.0, 0.0, 1000),
        _trade("t2", "BTC-USD", "SELL", 1.0, 110.0, 0.0, 2000),
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    assert result["realized_pnl_count"] == 1
    r = result["realized_trades"][0]
    assert r["pnl_usd"] == 10.0  # (110-100)*1.0, no fees
    assert round(r["pnl_pct"], 3) == 10.0  # 10/100 * 100


def test_pnl_fees_subtracted_both_sides(tmp_path, monkeypatch):
    """Fees on both BUY and SELL reduce realized pnl_usd by exactly fee_buy+fee_sell."""
    log = _write_log(tmp_path, [
        _trade("t1", "BTC-USD", "BUY", 1.0, 100.0, 1.0, 1000),   # $1 fee on buy
        _trade("t2", "BTC-USD", "SELL", 1.0, 100.0, 1.0, 2000),  # $1 fee on sell, flat price
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    r = result["realized_trades"][0]
    # gross pnl = 0 (flat price), fees = -1 (entry) -1 (exit) = -2 total
    assert r["pnl_usd"] == -2.0


def test_fifo_matching_multiple_lots(tmp_path, monkeypatch):
    """A SELL larger than the first BUY lot consumes lots in FIFO (oldest-first) order."""
    log = _write_log(tmp_path, [
        _trade("b1", "ETH-USD", "BUY", 1.0, 100.0, 0.0, 1000),
        _trade("b2", "ETH-USD", "BUY", 1.0, 200.0, 0.0, 2000),
        _trade("s1", "ETH-USD", "SELL", 1.5, 300.0, 0.0, 3000),
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    assert result["realized_pnl_count"] == 2
    first, second = result["realized_trades"]
    assert first["entry_price"] == 100.0 and first["qty"] == 1.0  # oldest lot fully consumed first
    assert second["entry_price"] == 200.0 and second["qty"] == 0.5  # remainder from 2nd lot
    # Remaining open position: 0.5 ETH left in the 2nd lot
    assert result["open_position_count"] == 1
    assert result["positions"][0]["qty"] == 0.5


def test_missing_price_or_size_skipped_not_crashed(tmp_path, monkeypatch):
    """Trades with null avg_price/base_size (unfilled/unenriched) are skipped, not counted."""
    log = _write_log(tmp_path, [
        _trade("t1", "BTC-USD", "BUY", None, None, None, 1000),  # e.g. dry_run fallback record
        _trade("t2", "BTC-USD", "BUY", 1.0, 100.0, 0.0, 2000),
        _trade("t3", "BTC-USD", "SELL", 1.0, 105.0, 0.0, 3000),
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    assert result["ok"] is True
    assert result["realized_pnl_count"] == 1  # the None-price trade contributed nothing


def test_failed_orders_excluded(tmp_path, monkeypatch):
    """success=False orders (rejected/failed) must never enter position/PnL math."""
    log = _write_log(tmp_path, [
        _trade("t1", "DOGE-USD", "BUY", 100.0, 0.1, 0.0, 1000, success=False),
        _trade("t2", "DOGE-USD", "BUY", 100.0, 0.1, 0.0, 2000, success=True),
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    assert result["open_position_count"] == 1
    assert result["positions"][0]["qty"] == 100.0  # only the successful BUY counted


def test_dry_run_mode_excluded_from_live_compute(tmp_path, monkeypatch):
    """compute_positions(mode filter) only counts mode='live' trades."""
    log = _write_log(tmp_path, [
        _trade("t1", "SOL-USD", "BUY", 1.0, 80.0, 0.0, 1000, mode="dry_run"),
        _trade("t2", "SOL-USD", "BUY", 1.0, 80.0, 0.0, 2000, mode="live"),
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    assert result["positions"][0]["qty"] == 1.0  # only the live BUY


def test_duplicate_trade_id_deduplicated(tmp_path, monkeypatch):
    """Same trade_id appended twice (e.g. retry after apparent timeout) counts once."""
    log = _write_log(tmp_path, [
        _trade("dup1", "BTC-USD", "BUY", 1.0, 100.0, 0.0, 1000),
        _trade("dup1", "BTC-USD", "BUY", 1.0, 100.0, 0.0, 1000),  # exact duplicate line
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    assert result["positions"][0]["qty"] == 1.0  # not 2.0 - dedup worked


def test_win_rate_and_avg_loss_math(tmp_path, monkeypatch):
    """win_rate_pct / avg_win_usd / avg_loss_usd match manual aggregation of realized trades."""
    log = _write_log(tmp_path, [
        _trade("b1", "BTC-USD", "BUY", 1.0, 100.0, 0.0, 1000),
        _trade("s1", "BTC-USD", "SELL", 1.0, 110.0, 0.0, 1100),   # +10 win
        _trade("b2", "BTC-USD", "BUY", 1.0, 100.0, 0.0, 2000),
        _trade("s2", "BTC-USD", "SELL", 1.0, 95.0, 0.0, 2100),    # -5 loss
    ])
    monkeypatch.setattr(pt, "LOG_PATH", log)
    result = pt.compute_positions()
    assert result["realized_pnl_count"] == 2
    assert result["win_rate_pct"] == 50.0
    assert result["avg_win_usd"] == 10.0
    assert result["avg_loss_usd"] == -5.0
    assert result["realized_pnl_total"] == 5.0
