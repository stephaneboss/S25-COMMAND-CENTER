"""
S25-KIMI-v2 Telegram Reporter
==============================
Sends formatted alerts and reports via the Telegram Bot API.

Design principles
-----------------
- NEVER raise an exception.  Any Telegram failure is logged and swallowed so
  the main bot loop is never interrupted by a notification issue.
- MODE is displayed prominently in every message (DRY / PAPER / LIVE).
- Messages use a consistent emoji language:
    ✅ success  ❌ fail  ⚠️ warning  🔴 circuit breaker  📊 report  🚀 startup
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _mode_badge(mode: str) -> str:
    badges = {"dry": "🧪 DRY", "paper": "📄 PAPER", "live": "🔴 LIVE"}
    return badges.get(mode.lower(), mode.upper())


class TelegramReporter:
    """
    Sends pre-formatted messages to a Telegram chat.

    If TELEGRAM_TOKEN or TELEGRAM_CHAT_ID are empty strings the reporter
    operates in silent mode (logs only, no HTTP calls).
    """

    def __init__(self, config: Config) -> None:
        self._cfg = config
        self._token = config.TELEGRAM_TOKEN
        self._chat_id = config.TELEGRAM_CHAT_ID
        self._silent = not (self._token and self._chat_id)
        if self._silent:
            logger.info("TelegramReporter: no credentials — silent mode")

    # ── Public methods ─────────────────────────────────────────────────────────

    def send_startup_report(self, mode: str, balance_usd: float) -> None:
        """
        Send on bot startup.
        """
        badge = _mode_badge(mode)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        text = (
            f"🚀 *S25-KIMI-v2 STARTED*\n"
            f"Mode: *{badge}*\n"
            f"Balance: *${balance_usd:.2f} USD*\n"
            f"Scan interval: {self._cfg.SCAN_INTERVAL}s\n"
            f"Spread threshold: {self._cfg.SPREAD_THRESHOLD:.2%}\n"
            f"Min score: {self._cfg.MIN_SIGNAL_SCORE}\n"
            f"Daily loss cap: ${self._cfg.MAX_DAILY_LOSS_USD:.2f}\n"
            f"⏰ {ts}"
        )
        self._send(text)

    def send_trade_alert(
        self,
        signal: dict,
        result: dict,
        pnl: Optional[float],
    ) -> None:
        """
        Send an alert on every trade attempt (success or failure).
        """
        badge = _mode_badge(self._cfg.MODE)
        symbol = signal.get("symbol", "?")
        direction = signal.get("direction", "?")
        score = signal.get("score", 0)
        spread = signal.get("spread_pct", 0.0)
        osm_p = signal.get("osm_price", 0.0)
        cex_p = signal.get("cex_price", 0.0)

        success = result.get("success", False)
        tx_hash = result.get("tx_hash", "")
        error = result.get("error", "")

        status_icon = "✅" if success else "❌"
        direction_arrow = "⬆️ BUY" if direction == "BUY" else "⬇️ SELL"

        lines = [
            f"{status_icon} *Trade Alert* [{badge}]",
            f"Symbol: *{symbol}*  {direction_arrow}",
            f"OSM: ${osm_p:.4f}  |  CEX: ${cex_p:.4f}",
            f"Spread: *{spread:.3%}*  Score: *{score}*",
        ]

        if pnl is not None:
            pnl_icon = "📈" if pnl >= 0 else "📉"
            lines.append(f"P&L: {pnl_icon} *${pnl:.4f}*")

        if tx_hash:
            lines.append(f"TX: `{tx_hash[:20]}...`")

        if not success and error:
            lines.append(f"Error: _{error[:120]}_")

        self._send("\n".join(lines))

    def send_circuit_breaker_alert(self, reason: str) -> None:
        """
        Send an urgent alert when the circuit breaker trips.
        """
        badge = _mode_badge(self._cfg.MODE)
        ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
        text = (
            f"🔴 *CIRCUIT BREAKER TRIPPED* [{badge}]\n"
            f"Reason: _{reason}_\n"
            f"Cooldown: {self._cfg.CIRCUIT_BREAKER_COOLDOWN_MIN} min\n"
            f"⏰ {ts}"
        )
        self._send(text)

    def send_daily_report(
        self,
        stats: dict,
        balance_usd: float,
        daily_pnl: float,
    ) -> None:
        """
        Send a comprehensive end-of-day (or on-demand) summary.
        """
        badge = _mode_badge(self._cfg.MODE)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        pnl_icon = "📈" if daily_pnl >= 0 else "📉"
        win_rate_pct = stats.get("win_rate", 0.0) * 100

        text = (
            f"📊 *Daily Report* [{badge}]\n"
            f"{pnl_icon} Daily P&L: *${daily_pnl:.4f}*\n"
            f"Balance: *${balance_usd:.2f}*\n"
            f"─────────────────\n"
            f"Trades (7d): *{stats.get('num_trades', 0)}*\n"
            f"Wins / Losses: {stats.get('wins', 0)} / {stats.get('losses', 0)}\n"
            f"Win rate: *{win_rate_pct:.1f}%*\n"
            f"Total P&L (7d): *${stats.get('total_pnl', 0):.4f}*\n"
            f"Avg spread: {stats.get('avg_spread', 0):.4%}\n"
            f"Best trade: ${stats.get('best_trade', 0):.4f}\n"
            f"Worst trade: ${stats.get('worst_trade', 0):.4f}\n"
            f"─────────────────\n"
            f"⏰ {ts}"
        )
        self._send(text)

    def send_heartbeat(
        self,
        scan_count: int,
        balance_usd: float,
        daily_pnl: float,
    ) -> None:
        """
        Lightweight heartbeat — sent every HEARTBEAT_INTERVAL scans.
        """
        badge = _mode_badge(self._cfg.MODE)
        pnl_icon = "📈" if daily_pnl >= 0 else "📉"
        ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
        text = (
            f"💓 *Heartbeat* [{badge}]\n"
            f"Scan #{scan_count}  |  Balance: ${balance_usd:.2f}\n"
            f"{pnl_icon} Daily P&L: ${daily_pnl:.4f}\n"
            f"⏰ {ts}"
        )
        self._send(text)

    def send_warning(self, message: str) -> None:
        """Generic ⚠️ warning message."""
        badge = _mode_badge(self._cfg.MODE)
        ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
        text = f"⚠️ *Warning* [{badge}]\n{message}\n⏰ {ts}"
        self._send(text)

    def send_shutdown_report(
        self,
        scan_count: int,
        daily_pnl: float,
        stats: dict,
    ) -> None:
        """Final report on graceful shutdown (CTRL+C)."""
        badge = _mode_badge(self._cfg.MODE)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        pnl_icon = "📈" if daily_pnl >= 0 else "📉"
        text = (
            f"🛑 *S25-KIMI-v2 STOPPED* [{badge}]\n"
            f"Total scans: {scan_count}\n"
            f"{pnl_icon} Daily P&L: *${daily_pnl:.4f}*\n"
            f"Trades (7d): {stats.get('num_trades', 0)} "
            f"(win rate {stats.get('win_rate', 0)*100:.1f}%)\n"
            f"⏰ {ts}"
        )
        self._send(text)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _send(self, text: str) -> None:
        """
        Send a Markdown-formatted message to the configured Telegram chat.

        Failures are caught and logged — never propagated.
        """
        if self._silent:
            logger.info("[Telegram silent] %s", text.replace("\n", " | "))
            return

        url = _TELEGRAM_API.format(token=self._token)
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            if not resp.ok:
                logger.warning(
                    "Telegram send failed: %d %s", resp.status_code, resp.text[:200]
                )
            else:
                logger.debug("Telegram: message sent (chat_id=%s)", self._chat_id)
        except requests.exceptions.RequestException as exc:
            logger.warning("Telegram send exception: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Telegram unexpected error: %s", exc)
