"""
S25 Lumière — ARKON Signal Processor
=====================================
Processes trading signals from ARKON-5 AI model via Kimi Web3.

Signal flow:
  Kimi Web3 → HA Webhook → Commander.dispatch() → ArkonSignal
  ArkonSignal validates → enriches with market data → routes to RiskGuardian + MexcExecutor

Signal format (from Kimi):
{
    "scan_data": {
        "symbol":     "BTC/USDT",
        "action":     "BUY" | "SELL" | "HOLD",
        "confidence": 0.87,      # 0-1
        "price":      65000.0,
        "targets":    [66000, 68000],
        "stop_loss":  63000,
        "timeframe":  "4H",
        "model":      "ARKON-5",
        "reason":     "Breakout confirmed..."
    }
}
"""

import asyncio
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

from .base import BaseAgent

logger = logging.getLogger("s25.arkon")


class ArkonSignal(BaseAgent):
    """
    ARKON Signal Processor — AI Trading Signal Handler.

    Validates and enriches signals from ARKON-5.
    Routes approved signals to MexcExecutor.
    """

    VALID_ACTIONS   = {"BUY", "SELL", "HOLD"}
    MIN_CONFIDENCE  = 0.75

    def __init__(self, config: Dict = None, commander=None):
        super().__init__("arkon_signal", "1.0.0", config)
        self.commander = commander

        arkon_cfg = config.get("arkon_signal", {}) if config else {}
        self.min_confidence = arkon_cfg.get("min_confidence", self.MIN_CONFIDENCE)
        self.symbols        = arkon_cfg.get("symbols", ["BTC/USDT", "ETH/USDT"])

        # State
        self.signals_received  = 0
        self.signals_approved  = 0
        self.signals_rejected  = 0
        self.last_signal:      Optional[Dict] = None

    async def run(self):
        """Idle loop — signals come via handle_signal."""
        await asyncio.sleep(30)

    async def handle_signal(self, signal: Dict[str, Any]):
        """Process incoming signals."""
        stype = signal.get("type")

        if stype == "ARKON_SIGNAL":
            await self._process_arkon(signal)

        elif stype == "KIMI_WEBHOOK":
            # Raw Kimi webhook — parse and re-dispatch as ARKON_SIGNAL
            await self._parse_kimi(signal)

    async def _parse_kimi(self, signal: Dict):
        """Parse raw Kimi webhook payload."""
        try:
            scan_data = signal.get("data", {}).get("scan_data", {})
            if not scan_data:
                self.logger.warning("Empty Kimi webhook payload")
                return

            arkon_signal = {
                "type":   "ARKON_SIGNAL",
                "source": "kimi_web3",
                "target": "all",
                "ts":     datetime.utcnow().isoformat(),
                "data":   scan_data
            }

            # Update HA input_text with signal data
            self._update_ha_entity(scan_data)

            # Dispatch as ARKON_SIGNAL
            if self.commander:
                await self.commander.dispatch(arkon_signal)

        except Exception as e:
            self.logger.error(f"Kimi parse error: {e}")

    async def _process_arkon(self, signal: Dict):
        """Validate and process an ARKON trading signal."""
        self.signals_received += 1
        data = signal.get("data", {})

        # Validate signal
        validation = self._validate(data)
        if not validation["valid"]:
            self.signals_rejected += 1
            self.logger.warning(
                f"Signal rejected: {validation['reason']} "
                f"| {data.get('symbol')} {data.get('action')}"
            )
            self._update_ha_status("REJECTED", data, validation["reason"])
            return

        # Enrich with metadata
        enriched = {
            **data,
            "validated_at": datetime.utcnow().isoformat(),
            "approved":     True,
        }

        self.signals_approved += 1
        self.last_signal = enriched

        action = data.get("action", "HOLD")
        symbol = data.get("symbol", "?")
        conf   = data.get("confidence", 0)

        self.logger.info(
            f"✓ ARKON SIGNAL: {action} {symbol} "
            f"(conf: {conf:.0%}) @ {data.get('price', '?')}"
        )

        # Update HA
        self._update_ha_status("APPROVED", enriched)

        # Route to executor (only non-HOLD signals with sufficient confidence)
        if action != "HOLD" and self.commander:
            exec_signal = {
                "type":   "EXECUTE_ORDER",
                "target": "mexc_executor",
                "source": "arkon_signal",
                "data":   enriched
            }
            await self.commander.dispatch(exec_signal)

    def _validate(self, data: Dict) -> Dict:
        """Validate signal data. Returns {valid, reason}."""
        if not data:
            return {"valid": False, "reason": "Empty signal"}

        action = data.get("action", "").upper()
        if action not in self.VALID_ACTIONS:
            return {"valid": False, "reason": f"Invalid action: {action}"}

        confidence = data.get("confidence", 0)
        if confidence < self.min_confidence:
            return {
                "valid": False,
                "reason": f"Low confidence: {confidence:.0%} < {self.min_confidence:.0%}"
            }

        symbol = data.get("symbol", "")
        if self.symbols and symbol not in self.symbols:
            return {"valid": False, "reason": f"Symbol not in whitelist: {symbol}"}

        return {"valid": True, "reason": ""}

    def _update_ha_status(self, status: str, data: Dict, reason: str = ""):
        """Update HA entities with signal status."""
        ha_url   = self.config.get("ha_url", "")
        ha_token = self.config.get("ha_token", "")
        if not ha_url or not ha_token:
            return

        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type":  "application/json"
        }

        try:
            # Update sensor
            requests.post(
                f"{ha_url}/api/states/sensor.s25_arkon_signal",
                headers=headers,
                json={
                    "state": status,
                    "attributes": {
                        "action":           data.get("action", "HOLD"),
                        "symbol":           data.get("symbol", ""),
                        "confidence":       data.get("confidence", 0),
                        "price":            data.get("price", 0),
                        "received_total":   self.signals_received,
                        "approved_total":   self.signals_approved,
                        "rejected_total":   self.signals_rejected,
                        "reject_reason":    reason,
                        "friendly_name":    "S25 ARKON-5 Signal"
                    }
                },
                timeout=5
            )

            # Update input_text for ai_router
            if data:
                requests.post(
                    f"{ha_url}/api/services/input_text/set_value",
                    headers=headers,
                    json={
                        "entity_id": "input_text.ai_model_actif",
                        "value": f"ARKON_{data.get('action', 'HOLD')}"
                    },
                    timeout=5
                )
        except Exception:
            pass

    def _update_ha_entity(self, scan_data: Dict):
        """Push Kimi scan data into HA input_text.ai_prompt."""
        ha_url   = self.config.get("ha_url", "")
        ha_token = self.config.get("ha_token", "")
        if not ha_url or not ha_token:
            return

        try:
            requests.post(
                f"{ha_url}/api/services/input_text/set_value",
                headers={
                    "Authorization": f"Bearer {ha_token}",
                    "Content-Type":  "application/json"
                },
                json={
                    "entity_id": "input_text.ai_prompt",
                    "value":     json.dumps(scan_data)[:255]
                },
                timeout=5
            )
        except Exception:
            pass
