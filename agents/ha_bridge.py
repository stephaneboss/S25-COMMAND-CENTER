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
import time
import requests
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("s25.ha_bridge")

try:
    from security.vault import vault_get
except ImportError:
    def vault_get(key, default=None):
        return os.environ.get(key, default)


class HABridge:
    """Single point of contact for Home Assistant API."""

    def __init__(self):
        self.url = os.getenv("HA_URL", "http://10.0.0.136:8123").rstrip("/")
        self.token = vault_get("HA_TOKEN", os.getenv("HA_TOKEN", "")) or ""
        self._timeout = 8
        # Circuit breaker: after a network failure, HA is considered unreachable for
        # _down_ttl seconds so callers (e.g. /api/status, 6 entities) fail fast instead
        # of waiting 8 s per call (2026-10-01: /api/status took 16 s, cockpit heartbeat lost).
        self._down_ttl = int(os.getenv("HA_DOWN_TTL_SEC", "60"))
        self._down_until = 0.0
        self.last_error = ""

    @property
    def connected(self) -> bool:
        return bool(self.url and self.token)

    @property
    def reachable(self) -> bool:
        return self.connected and time.time() >= self._down_until

    def _mark_down(self, e: Exception) -> None:
        self._down_until = time.time() + self._down_ttl
        self.last_error = f"{type(e).__name__}: {e}"[:200]

    def _mark_up(self) -> None:
        self._down_until = 0.0
        self.last_error = ""

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
            self._mark_up()
            return {"ok": r.status_code == 200, "status_code": r.status_code}
        except (requests.ConnectionError, requests.Timeout) as e:
            self._mark_down(e)
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_state(self, entity_id: str) -> Optional[Dict]:
        """Read a single entity state from HA."""
        if not self.reachable:
            return None
        try:
            r = requests.get(
                f"{self.url}/api/states/{entity_id}",
                headers=self._headers,
                timeout=self._timeout,
            )
            self._mark_up()
            if r.status_code == 200:
                return r.json()
        except (requests.ConnectionError, requests.Timeout) as e:
            self._mark_down(e)
            logger.warning("HA get_state(%s) failed, HA marked unreachable %ss: %s",
                           entity_id, self._down_ttl, e)
        except Exception as e:
            logger.warning("HA get_state(%s) failed: %s", entity_id, e)
        return None

    def push_sensor(self, entity_id: str, state: Any, attributes: Dict = None) -> bool:
        """Push/update a sensor value in HA."""
        if not self.reachable:
            return False
        payload = {"state": str(state), "attributes": attributes or {}}
        try:
            r = requests.post(
                f"{self.url}/api/states/{entity_id}",
                headers=self._headers,
                json=payload,
                timeout=self._timeout,
            )
            self._mark_up()
            ok = r.status_code in (200, 201)
            if not ok:
                logger.warning("HA push_sensor(%s) -> %s", entity_id, r.status_code)
            return ok
        except (requests.ConnectionError, requests.Timeout) as e:
            self._mark_down(e)
            logger.error("HA push_sensor(%s) failed, HA marked unreachable %ss: %s",
                         entity_id, self._down_ttl, e)
            return False
        except Exception as e:
            logger.error("HA push_sensor(%s) error: %s", entity_id, e)
            return False

    def call_service(self, domain: str, service: str, data: Dict = None) -> bool:
        """Call a HA service (shell_command, automation, input_boolean, etc.)."""
        if not self.reachable:
            return False
        try:
            r = requests.post(
                f"{self.url}/api/services/{domain}/{service}",
                headers=self._headers,
                json=data or {},
                timeout=12,
            )
            self._mark_up()
            ok = r.status_code == 200
            if not ok:
                logger.warning("HA call_service(%s.%s) -> %s", domain, service, r.status_code)
            return ok
        except (requests.ConnectionError, requests.Timeout) as e:
            self._mark_down(e)
            logger.error("HA call_service(%s.%s) failed, HA marked unreachable %ss: %s",
                         domain, service, self._down_ttl, e)
            return False
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
        sensor_results = []

        def record_sensor(entity_id, state, attributes):
            ok = self.push_sensor(entity_id, state, attributes)
            sensor_results.append(ok)
            return ok

        # 1. ARKON-5 action sensor
        record_sensor("sensor.s25_arkon5_action", action, {
            "friendly_name": "S25 ARKON-5 Action",
            "symbol": symbol, "source": source, "verdict": verdict,
            "icon": "mdi:robot",
        })
        results["arkon5_action"] = action

        # 2. Confidence sensor
        conf_pct = int(effective_confidence * 100)
        record_sensor("sensor.s25_arkon5_conf", str(conf_pct), {
            "friendly_name": "S25 ARKON-5 Confidence",
            "unit_of_measurement": "%",
            "raw_confidence": confidence,
            "effective_confidence": effective_confidence,
            "icon": "mdi:gauge",
        })
        results["arkon5_conf"] = conf_pct

        # 3. Price sensors
        record_sensor("sensor.s25_arkon5_tp", str(price), {
            "friendly_name": "S25 ARKON-5 Target Price",
            "unit_of_measurement": "USD",
        })
        record_sensor("sensor.s25_arkon5_sl", str(round(price * 0.97, 2)), {
            "friendly_name": "S25 ARKON-5 Stop Loss",
            "unit_of_measurement": "USD",
        })

        # 4. Reason sensor
        record_sensor("sensor.s25_arkon5_reason", reason[:255], {
            "friendly_name": "S25 ARKON-5 Reason", "source": source,
        })

        # 5. Pipeline status
        record_sensor("sensor.s25_pipeline_status", verdict, {
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
        record_sensor("sensor.s25_trinity_signal", action, {
            "friendly_name": "S25 Trinity Signal",
            "intent": f"{action} {symbol} -- eff={effective_confidence:.2f} via {source}",
            "source": source,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        # 7. EXECUTE -> request MEXC service via HA shell_commands
        service_ok = True
        if verdict == "EXECUTE":
            base_asset = symbol.split("/")[0] if "/" in symbol else symbol
            base_lower = base_asset.lower()
            service_name = None

            if action == "BUY" and base_lower in ("btc", "doge", "xrp"):
                service_name = f"spot_buy_{base_lower}"
            elif action == "SELL" and base_lower in ("btc", "doge", "xrp"):
                service_name = f"spot_sell_{base_lower}"
            elif action == "BUY":
                service_name = "trade_spot_buy"
            elif action == "SELL":
                service_name = "trade_spot_sell"

            service_ok = bool(service_name) and self.call_service("shell_command", service_name)
            results["mexc_service_requested"] = service_name
            results["mexc_service_accepted"] = service_ok
            # HA accepting a service request does not confirm an exchange order.
            if service_ok:
                self.call_service("shell_command", "notify_trade")
                self.call_service("input_text", "set_value", {
                    "entity_id": "input_text.agent_trading_status",
                    "value": f"REQUESTED_{action}_{base_asset}",
                })
                results["trading_status"] = f"REQUESTED_{action}_{base_asset}"

        # 8. Mobile notification
        emoji = {"BUY": "\U0001f4c8", "SELL": "\U0001f4c9", "HOLD": "\u23f8\ufe0f"}.get(action, "\U0001f514")
        notif_ok = self.notify(
            message=f"Conf: {conf_pct}% | {verdict} | {source}\n{reason[:100]}",
            title=f"{emoji} S25 {action} {symbol}",
            importance="high" if verdict == "EXECUTE" else "default",
        )
        results["notification"] = "sent" if notif_ok else "failed"
        results["sensors_ok"] = all(sensor_results)
        # An accepted trade request must not look failed solely because telemetry failed:
        # callers could otherwise retry and submit a duplicate order.
        results["ok"] = service_ok if verdict == "EXECUTE" else (results["sensors_ok"] and notif_ok)
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
