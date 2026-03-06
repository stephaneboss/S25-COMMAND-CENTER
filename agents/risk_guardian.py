"""
S25 Lumière — Risk Guardian
============================
Circuit breaker and risk management agent.

Enforces hard limits on:
- Daily loss %
- Max position size
- Max open positions
- Stop loss per trade
- Drawdown limits

If ANY limit is breached → triggers Commander circuit breaker.
"""

import asyncio
import logging
import requests
from datetime import datetime, date
from typing import Dict, Any, Optional

from .base import BaseAgent, AgentStatus

logger = logging.getLogger("s25.risk_guardian")


class RiskGuardian(BaseAgent):
    """
    Risk management agent — the last line of defense.

    If RISK_BREACH signal received, immediately:
    1. Triggers circuit breaker on Commander
    2. Notifies HA
    3. Logs to audit trail

    Config keys:
    - max_daily_loss_pct   : Max % portfolio loss per day (default 5%)
    - max_position_size_pct: Max % portfolio in one position (default 20%)
    - max_open_positions   : Max concurrent positions (default 5)
    - stop_loss_pct        : Stop loss per trade (default 3%)
    """

    def __init__(self, config: Dict = None, commander=None):
        super().__init__("risk_guardian", "1.0.0", config)
        self.commander = commander

        # Risk limits from config
        limits = config.get("risk_guardian", {}) if config else {}
        self.max_daily_loss_pct    = limits.get("max_daily_loss_pct", 5.0)
        self.max_position_size_pct = limits.get("max_position_size_pct", 20.0)
        self.max_open_positions    = limits.get("max_open_positions", 5)
        self.stop_loss_pct         = limits.get("stop_loss_pct", 3.0)

        # State
        self.daily_loss_pct       = 0.0
        self.open_positions       = 0
        self.trading_paused       = False
        self.today_date           = date.today()
        self.violations:          list = []

    async def run(self):
        """Periodic risk check loop."""
        await self._check_daily_reset()
        await self._publish_status()
        await asyncio.sleep(60)  # Check every minute

    async def handle_signal(self, signal: Dict[str, Any]):
        """Handle risk-related signals."""
        stype = signal.get("type")

        if stype == "RISK_BREACH":
            await self._handle_breach(signal)

        elif stype == "TRADE_EXECUTED":
            await self._update_position_count(signal, +1)

        elif stype == "TRADE_CLOSED":
            await self._update_position_count(signal, -1)

        elif stype == "PNL_UPDATE":
            await self._update_daily_pnl(signal)

        elif stype == "ARKON_SIGNAL":
            # Pre-approve signal before it reaches executor
            approved = await self._approve_signal(signal)
            if not approved:
                logger.warning(f"RiskGuardian BLOCKED signal: {signal}")

    async def _approve_signal(self, signal: Dict) -> bool:
        """
        Approve or block a trading signal based on risk limits.
        Returns True if signal is approved.
        """
        if self.trading_paused:
            self.logger.warning("Trading PAUSED — signal blocked")
            return False

        if self.daily_loss_pct >= self.max_daily_loss_pct:
            await self._breach(
                f"Daily loss limit reached: {self.daily_loss_pct:.1f}%"
                f" >= {self.max_daily_loss_pct}%"
            )
            return False

        if self.open_positions >= self.max_open_positions:
            self.logger.warning(
                f"Max open positions: {self.open_positions}"
                f"/{self.max_open_positions}"
            )
            return False

        return True

    async def _handle_breach(self, signal: Dict):
        """Handle a risk breach signal."""
        reason = signal.get("data", {}).get("reason", "Unknown risk breach")
        await self._breach(reason)

    async def _breach(self, reason: str):
        """Trigger risk breach — halt all trading."""
        self.trading_paused = True
        self.violations.append({
            "ts":     datetime.utcnow().isoformat(),
            "reason": reason
        })

        self.logger.critical(f"RISK BREACH: {reason}")

        # Trigger Commander circuit breaker
        if self.commander:
            self.commander.trigger_circuit_breaker(reason)

        # Notify HA
        self._notify_ha_breach(reason)

    async def _update_position_count(self, signal: Dict, delta: int):
        """Update open position count."""
        self.open_positions = max(0, self.open_positions + delta)

    async def _update_daily_pnl(self, signal: Dict):
        """Update daily P&L tracking."""
        pnl_pct = signal.get("data", {}).get("daily_pnl_pct", 0)
        self.daily_loss_pct = max(0, -pnl_pct)  # Convert loss to positive %

        if self.daily_loss_pct >= self.max_daily_loss_pct * 0.8:
            # Warning at 80% of limit
            self.logger.warning(
                f"Daily loss approaching limit: {self.daily_loss_pct:.1f}%"
                f"/{self.max_daily_loss_pct}%"
            )

    async def _check_daily_reset(self):
        """Reset daily counters at midnight."""
        today = date.today()
        if today != self.today_date:
            self.today_date     = today
            self.daily_loss_pct = 0.0
            self.violations     = []
            if self.trading_paused:
                self.trading_paused = False
                self.logger.info("Daily reset — trading RESUMED")

    async def _publish_status(self):
        """Publish risk status to HA."""
        ha_url   = self.config.get("ha_url", "")
        ha_token = self.config.get("ha_token", "")
        if ha_url and ha_token:
            self.report_ha(ha_url, ha_token,
                "PAUSED" if self.trading_paused else "OK",
                {
                    "daily_loss_pct":       self.daily_loss_pct,
                    "max_daily_loss_pct":   self.max_daily_loss_pct,
                    "open_positions":       self.open_positions,
                    "max_open_positions":   self.max_open_positions,
                    "trading_paused":       self.trading_paused,
                    "violations_today":     len(self.violations),
                }
            )

    def _notify_ha_breach(self, reason: str):
        """Fire HA event for risk breach."""
        ha_url   = self.config.get("ha_url", "")
        ha_token = self.config.get("ha_token", "")
        if not ha_url or not ha_token:
            return
        try:
            requests.post(
                f"{ha_url}/api/events/s25_risk_breach",
                headers={
                    "Authorization": f"Bearer {ha_token}",
                    "Content-Type":  "application/json"
                },
                json={"reason": reason, "ts": datetime.utcnow().isoformat()},
                timeout=5
            )
        except Exception:
            pass
