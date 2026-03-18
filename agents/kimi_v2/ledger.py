"""
S25-KIMI-v2 Trade Ledger
========================
SQLite-backed persistent record of every trade attempt.

All timestamps are stored as ISO-8601 UTC strings.
All financial values are stored as REAL (float64).
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator, Optional

from config import Config

logger = logging.getLogger(__name__)

# ─── Schema ───────────────────────────────────────────────────────────────────

_CREATE_TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT    NOT NULL,          -- ISO-8601 UTC
    mode             TEXT    NOT NULL,          -- dry | paper | live
    symbol           TEXT    NOT NULL,          -- e.g. ATOM
    direction        TEXT    NOT NULL,          -- BUY | SELL
    signal_score     INTEGER NOT NULL,
    spread_pct       REAL    NOT NULL,
    in_denom         TEXT    NOT NULL,          -- IBC denom of input token
    out_denom        TEXT    NOT NULL,          -- IBC denom of output token
    in_amount        REAL    NOT NULL,          -- in micro-units
    out_amount       REAL,                      -- actual received micro-units
    tx_hash          TEXT,                      -- on-chain tx hash (live mode)
    status           TEXT    NOT NULL,          -- success | failed | dry | paper
    gas_fee          REAL,                      -- gas paid in OSMO (micro-units)
    pnl_usd          REAL,                      -- realised P&L in USD
    notes            TEXT                       -- free-text (errors, dry output, etc.)
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades (timestamp);
"""


# ─── Ledger ───────────────────────────────────────────────────────────────────

class TradeLedger:
    """
    Persistent trade ledger backed by SQLite.

    Thread-safety: each public method opens and closes its own connection so
    the ledger can be used safely from a single-threaded async loop or from
    a simple synchronous script.
    """

    def __init__(self, config: Config) -> None:
        self._db_path = config.DB_PATH
        self._init_db()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TRADES_TABLE)
            conn.execute(_CREATE_INDEX)
            conn.commit()
        logger.debug("TradeLedger: DB initialised at %s", self._db_path)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ── Write ──────────────────────────────────────────────────────────────────

    def record_trade(
        self,
        *,
        mode: str,
        symbol: str,
        direction: str,
        signal_score: int,
        spread_pct: float,
        in_denom: str,
        out_denom: str,
        in_amount: float,
        out_amount: Optional[float] = None,
        tx_hash: Optional[str] = None,
        status: str,
        gas_fee: Optional[float] = None,
        pnl_usd: Optional[float] = None,
        notes: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """
        Insert a trade record and return its auto-generated row id.

        Parameters
        ----------
        timestamp:
            ISO-8601 UTC string.  Defaults to *now* if not provided.
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()

        sql = """
            INSERT INTO trades (
                timestamp, mode, symbol, direction, signal_score,
                spread_pct, in_denom, out_denom, in_amount, out_amount,
                tx_hash, status, gas_fee, pnl_usd, notes
            ) VALUES (
                :timestamp, :mode, :symbol, :direction, :signal_score,
                :spread_pct, :in_denom, :out_denom, :in_amount, :out_amount,
                :tx_hash, :status, :gas_fee, :pnl_usd, :notes
            )
        """
        params: dict[str, Any] = dict(
            timestamp=ts,
            mode=mode,
            symbol=symbol,
            direction=direction,
            signal_score=signal_score,
            spread_pct=spread_pct,
            in_denom=in_denom,
            out_denom=out_denom,
            in_amount=in_amount,
            out_amount=out_amount,
            tx_hash=tx_hash,
            status=status,
            gas_fee=gas_fee,
            pnl_usd=pnl_usd,
            notes=notes,
        )

        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            row_id: int = cursor.lastrowid  # type: ignore[assignment]

        logger.info(
            "Ledger: recorded trade #%d [%s %s %s score=%d pnl=%s]",
            row_id, mode.upper(), direction, symbol, signal_score,
            f"${pnl_usd:.4f}" if pnl_usd is not None else "N/A",
        )
        return row_id

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_daily_pnl(self, date_utc: Optional[str] = None) -> float:
        """
        Sum of today's (or the specified date's) pnl_usd.

        Parameters
        ----------
        date_utc:
            ISO date string e.g. ``"2026-03-18"``.  Defaults to today UTC.

        Returns
        -------
        float
            Total P&L for the day (negative = net loss).
        """
        date_str = date_utc or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sql = """
            SELECT COALESCE(SUM(pnl_usd), 0.0) AS total
            FROM trades
            WHERE timestamp LIKE :prefix
              AND pnl_usd IS NOT NULL
        """
        with self._connect() as conn:
            row = conn.execute(sql, {"prefix": f"{date_str}%"}).fetchone()
        return float(row["total"])

    def get_stats(self, days: int = 7) -> dict:
        """
        Aggregate statistics over the last *days* days.

        Returns
        -------
        dict with keys:
            num_trades, wins, losses, win_rate (0-1),
            total_pnl, avg_pnl, avg_spread, best_trade, worst_trade
        """
        sql = """
            SELECT
                COUNT(*)                        AS num_trades,
                SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END)   AS wins,
                SUM(CASE WHEN pnl_usd <= 0 THEN 1 ELSE 0 END)  AS losses,
                COALESCE(SUM(pnl_usd), 0.0)    AS total_pnl,
                COALESCE(AVG(pnl_usd), 0.0)    AS avg_pnl,
                COALESCE(AVG(ABS(spread_pct)), 0.0) AS avg_spread,
                COALESCE(MAX(pnl_usd), 0.0)    AS best_trade,
                COALESCE(MIN(pnl_usd), 0.0)    AS worst_trade
            FROM trades
            WHERE timestamp >= datetime('now', :offset)
              AND pnl_usd IS NOT NULL
        """
        offset = f"-{days} days"
        with self._connect() as conn:
            row = conn.execute(sql, {"offset": offset}).fetchone()

        num = int(row["num_trades"])
        wins = int(row["wins"] or 0)
        win_rate = wins / num if num > 0 else 0.0

        return {
            "num_trades": num,
            "wins": wins,
            "losses": int(row["losses"] or 0),
            "win_rate": round(win_rate, 4),
            "total_pnl": round(float(row["total_pnl"]), 4),
            "avg_pnl": round(float(row["avg_pnl"]), 4),
            "avg_spread": round(float(row["avg_spread"]), 6),
            "best_trade": round(float(row["best_trade"]), 4),
            "worst_trade": round(float(row["worst_trade"]), 4),
        }

    def get_consecutive_fails(self) -> int:
        """
        Count the number of consecutive 'failed' status rows at the tail of
        the trades table (most recent first).

        Returns 0 if the most recent trade was a success.
        """
        sql = """
            SELECT status
            FROM trades
            ORDER BY id DESC
            LIMIT 20
        """
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()

        count = 0
        for row in rows:
            if row["status"] == "failed":
                count += 1
            else:
                break
        return count

    def get_recent_trades(self, limit: int = 10) -> list[dict]:
        """Return the most recent *limit* trade rows as dicts."""
        sql = """
            SELECT *
            FROM trades
            ORDER BY id DESC
            LIMIT :limit
        """
        with self._connect() as conn:
            rows = conn.execute(sql, {"limit": limit}).fetchall()
        return [dict(row) for row in rows]

    def get_all_for_date(self, date_utc: str) -> list[dict]:
        """Return all trades for a given UTC date string (YYYY-MM-DD)."""
        sql = """
            SELECT *
            FROM trades
            WHERE timestamp LIKE :prefix
            ORDER BY id ASC
        """
        with self._connect() as conn:
            rows = conn.execute(sql, {"prefix": f"{date_utc}%"}).fetchall()
        return [dict(row) for row in rows]
