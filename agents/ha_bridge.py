"""
S25 Lumiere - Home Assistant Bridge
=====================================
Centralized HA communication module for all agents.

All HA interactions (sensor push, service calls, notifications,
shell commands) go through this module. No agent should import
requests and hit HA directly.

Usage:
    from agents.ha_bridge import ha
    ha.push_sensor("sensor.s25_pipeline_status", "EXECUTE", {"action": "BUY"})
    ha.call_service("shell_command", "spot_buy_btc")
    ha.notify("Signal BUY BTC", title="S25 Alert")
"""

import logging
import os
import requests
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("s25.ha_bridge")

try:
    from security.vault import vault_get
except ImportError:
    vault_get = lambda key, default=None: os.environ.get(key, default)


class HABridge:
    """Single point of contact for Home Assistant API."""

    def __init__(self):
        self.url = os.getenv("HA_URL", "http://10.0.0.136:8123").rstrip("/")
        self.token = vault_get("HA_TOKEN", os.getenv("HA_TOKEN", "")) or ""
        self._timeout = 8

    @property
    def connected(self) -> bool:
        return bool(self.url and self.token)

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    # -- Core API ----------------------------------------------------------

    def ping(self) -> Dict[str, Any]:
        """Test HA connectivity and return status."""
        if not self.connected:
            return {"ok": False, "error": "HA not configured"}
        try:
            r = requests.get(
                f"{self.url}/api/",
                headers=self._headers,
                timeout=self._timeout,
            )
            return {"ok": r.status_code == 200, "status_code": r.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_state(self, entity_id: str) -> Optional[Dict]:
        """Read a single entity state from HA."""
        if not self.connected:
            return None
        try:
            r = requests.get(
                f"{self.url}/api/states/{entity_id}",
                headers=self._headers,
                timeout=self._timeout,
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.warning("HA get_state(%s) failed: %s", entity_id, e)
        return None

    def push_sensor(self, entity_id: str, state: Any, attributes: Dict = None) -> bool:
        """Push/update a sensor value in HA."""
        if not self.connected:
            return False
        payload = {"state": str(state), "attributes": attributes or {}}
        try:
            r = requests.post(
                f"{self.url}/api/states/{entity_id}",
                headers=self._headers,
                json=payload,
                timeout=self._timeout,
            )
            ok = r.status_code in (200, 201)
            if not ok:
                logger.warning("HA push_sensor(%s) -> %s", entity_id, r.status_code)
            return ok
        except Exception as e:
            logger.error("HA push_sensor(%s) error: %s", entity_id, e)
            return False

    def call_service(self, domain: str, service: str, data: Dict = None) -> bool:
        """Call a HA service (shell_command, automation, input_boolean, etc.)."""
        if not self.connected:
            return False
        try:
            r = requests.post(
                f"{self.url}/api/services/{domain}/{service}",
                headers=self._headers,
                json=data or {},
                timeout=12,
            )
            ok = r.status_code == 200
            if not ok:
                logger.warning("HA call_service(%s.%s) -> %s", domain, service, r.status_code)
            return ok
        except Exception as e:
            logger.error("HA call_service(%s.%s) error: %s", domain, service, e)
            return False

    def notify(self, message: str, title: str = "S25 Alert",
               target: str = "mobile_app_s_25", tag: str = "s25_signal",
               importance: str = "default") -> bool:
        """Send push notification via HA."""
        return self.call_service("notify", target, {
            "title": title,
            "message": message,
            "data": {"tag": tag, "importance": importance},
        })

    # -- Trading Pipeline --------------------------------------------------

    def push_signal(self, action: str, symbol: str, confidence: float,
                    effective_confidence: float, price: float,
                    reason: str, verdict: str, source: str) -> Dict[str, Any]:
        """Push a complete trading signal to HA sensors + trigger execution."""
        if not self.connected:
            return {"ok": False, "error": "HA not configured"}

        results = {}

        # 1. ARKON-5 action sensor
        self.push_sensor("sensor.s25_arkon5_action", action, {
            "friendly_name": "S25 ARKON-5 Action",
            "symbol": symbol, "source": source, "verdict": verdict,
            "icon": "mdi:robot",
        })
        results["arkon5_action"] = action

        # 2. Confidence sensor
        conf_pct = int(effective_confidence * 100)
        self.push_sensor("sensor.s25_arkon5_conf", str(conf_pct), {
            "friendly_name": "S25 ARKON-5 Confidence",
            "unit_of_measurement": "%",
            "raw_confidence": confidence,
            "effective_confidence": effective_confidence,
            "icon": "mdi:gauge",
        })
        results["arkon5_conf"] = conf_pct

        # 3. Price sensors
        self.push_sensor("sensor.s25_arkon5_tp", str(price), {
            "friendly_name": "S25 ARKON-5 Target Price",
            "unit_of_measurement": "USD",
        })
        self.push_sensor("sensor.s25_arkon5_sl", str(round(price * 0.97, 2)), {
            "friendly_name": "S25 ARKON-5 Stop Loss",
            "unit_of_measurement": "USD",
        })

        # 4. Reason sensor
        self.push_sensor("sensor.s25_arkon5_reason", reason[:255], {
            "friendly_name": "S25 ARKON-5 Reason", "source": source,
        })

        # 5. Pipeline status
        self.push_sensor("sensor.s25_pipeline_status", verdict, {
            "friendly_name": "S25 Pipeline Status",
            "action": action, "symbol": symbol,
            "confidence": confidence,
            "effective_confidence": effective_confidence,
            "source": source, "price": price,
            "mode": "authorized",
            "updated_by": "cockpit_pipeline",
        })
        results["pipeline_status"] = verdict

        # 6. Trinity signal
        self.push_sensor("sensor.s25_trinity_signal", action, {
            "friendly_name": "S25 Trinity Signal",
            "intent": f"{action} {symbol} -- eff={effective_confidence:.2f} via {source}",
            "source": source,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        # 7. EXECUTE -> trigger MEXC via HA shell_commands
        if verdict == "EXECUTE":
            base_asset = symbol.split("/")[0] if "/" in symbol else symbol
            base_lower = base_asset.lower()

            if action == "BUY" and base_lower in ("btc", "doge", "xrp"):
                self.call_service("shell_command", f"spot_buy_{base_lower}")
                results["mexc_executed"] = f"spot_buy_{base_lower}"
            elif action == "SELL" and base_lower in ("btc", "doge", "xrp"):
                self.call_service("shell_command", f"spot_sell_{base_lower}")
                results["mexc_executed"] = f"spot_sell_{base_lower}"
            elif action == "BUY":
                self.call_service("shell_command", "trade_spot_buy")
                results["mexc_executed"] = "trade_spot_buy"
            elif action == "SELL":
                self.call_service("shell_command", "trade_spot_sell")
                results["mexc_executed"] = "trade_spot_sell"

            self.call_service("shell_command", "notify_trade")
            self.call_service("input_text", "set_value", {
                "entity_id": "input_text.agent_trading_status",
                "value": f"EXECUTING_{action}_{base_asset}",
            })
            results["trading_status"] = f"EXECUTING_{action}_{base_asset}"

        # 8. Mobile notification
        emoji = {"BUY": "\U0001f4c8", "SELL": "\U0001f4c9", "HOLD": "\u23f8\ufe0f"}.get(action, "\U0001f514")
        notif_ok = self.notify(
            message=f"Conf: {conf_pct}% | {verdict} | {source}\n{reason[:100]}",
            title=f"{emoji} S25 {action} {symbol}",
            importance="high" if verdict == "EXECUTE" else "default",
        )
        results["notification"] = "sent" if notif_ok else "failed"
        results["ok"] = True
        return results

    # -- Wallet & Balance --------------------------------------------------

    def push_balance(self, entity_id: str, balance: float,
                     currency: str = "USD", extra: Dict = None) -> bool:
        """Push a wallet/balance sensor to HA."""
        attrs = {
            "friendly_name": f"S25 {entity_id.split('.')[-1].replace('_', ' ').title()}",
            "unit_of_measurement": currency,
            "icon": "mdi:wallet",
        }
        if extra:
            attrs.update(extra)
        return self.push_sensor(entity_id, str(round(balance, 2)), attrs)

    def get_wallet_status(self) -> Dict[str, Any]:
        """Read all S25 wallet sensors from HA."""
        wallets = {}
        entities = [
            "sensor.s25_mexc_spot_total",
            "sensor.s25_mexc_doge_qty",
            "sensor.s25_mexc_btc_qty",
            "sensor.s25_mexc_usdt_qty",
            "sensor.s25_wallet_total",
        ]
        for eid in entities:
            state = self.get_state(eid)
            if state:
                wallets[eid] = {
                    "state": state.get("state"),
                    "attributes": state.get("attributes", {}),
                }
        return wallets

    # -- Agent Status ------------------------------------------------------

    def push_agent_status(self, agent_name: str, status: str, extra: Dict = None) -> bool:
        """Push agent status to HA sensor."""
        entity_id = f"sensor.s25_agent_{agent_name.lower()}_status"
        attrs = {
            "friendly_name": f"S25 {agent_name} Status",
            "icon": "mdi:robot",
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            attrs.update(extra)
        return self.push_sensor(entity_id, status, attrs)

    # -- System ------------------------------------------------------------

    def push_system_health(self, metrics: Dict) -> bool:
        """Push system health metrics to HA."""
        return self.push_sensor("sensor.s25_system_health", "online", {
            "friendly_name": "S25 System Health",
            "icon": "mdi:server",
            **metrics,
        })


# -- Singleton -------------------------------------------------------------
ha = HABridge()
