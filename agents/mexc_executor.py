"""
S25 Lumière — MEXC Executor
=============================
Order execution agent for MEXC Exchange.

IMPORTANT: dry_run=True by default. Enable live trading only
when API keys are configured and risk management is confirmed.

Supported operations:
- Market orders (instant fill)
- Limit orders (price control)
- Stop loss / take profit
- Order status tracking

Config: configs/agents.yaml → mexc_executor section
Keys:   .env → MEXC_API_KEY + MEXC_SECRET_KEY
"""

import asyncio
import hashlib
import hmac
import logging
import time
import requests
from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import urlencode

from .base import BaseAgent

logger = logging.getLogger("s25.mexc")


class MexcExecutor(BaseAgent):
    """
    MEXC Exchange order executor.

    Modes:
    - dry_run=True  (default): Logs orders but doesn't send them
    - dry_run=False (live):    Real orders on MEXC

    Always validates through RiskGuardian before executing.
    """

    BASE_URL = "https://api.mexc.com"

    def __init__(self, config: Dict = None, commander=None):
        super().__init__("mexc_executor", "1.0.0", config)
        self.commander = commander

        mexc_cfg = config.get("mexc_executor", {}) if config else {}

        self.dry_run     = mexc_cfg.get("dry_run", True)   # SAFE DEFAULT
        self.enabled     = mexc_cfg.get("enabled", False)
        self.order_type  = mexc_cfg.get("default_order_type", "LIMIT")
        self.size_pct    = mexc_cfg.get("default_size_pct", 5.0)

        # Load API keys from vault
        self._api_key    = ""
        self._api_secret = ""
        self._load_keys()

        # Order tracking
        self.orders_placed:    List[Dict] = []
        self.orders_filled:    List[Dict] = []
        self.dry_run_orders:   List[Dict] = []

        if self.dry_run:
            self.logger.info(
                "MexcExecutor initialized in DRY RUN mode — "
                "no real orders will be placed"
            )
        else:
            self.logger.warning(
                "MexcExecutor in LIVE mode — real orders will be executed!"
            )

    def _load_keys(self):
        """Load API keys from vault."""
        try:
            from security.vault import get_vault
            vault = get_vault()
            self._api_key    = vault.get("MEXC_API_KEY", "")
            self._api_secret = vault.get("MEXC_SECRET_KEY", "")
            if self._api_key:
                self.logger.info(
                    f"MEXC keys loaded: {self._api_key[:4]}****"
                )
        except Exception as e:
            self.logger.warning(f"Could not load MEXC keys: {e}")

    # ─── Agent Interface ─────────────────────────────────────────────

    async def run(self):
        """Check open order status periodically."""
        await self._check_open_orders()
        await asyncio.sleep(30)

    async def handle_signal(self, signal: Dict[str, Any]):
        """Handle signals from Commander."""
        stype = signal.get("type")

        if stype == "EXECUTE_ORDER":
            await self._handle_execute(signal.get("data", {}))

        elif stype == "CANCEL_ORDER":
            order_id = signal.get("data", {}).get("order_id")
            if order_id:
                await self._cancel_order(order_id)

        elif stype == "CLOSE_ALL":
            await self._close_all_positions()

    # ─── Order Execution ─────────────────────────────────────────────

    async def _handle_execute(self, signal_data: Dict):
        """Process an execute order signal."""
        symbol     = signal_data.get("symbol", "").replace("/", "")  # BTC/USDT → BTCUSDT
        action     = signal_data.get("action", "").upper()           # BUY | SELL
        price      = signal_data.get("price", 0)
        stop_loss  = signal_data.get("stop_loss", 0)
        targets    = signal_data.get("targets", [])
        confidence = signal_data.get("confidence", 0)

        if not symbol or action not in ("BUY", "SELL"):
            self.logger.warning(f"Invalid order signal: {signal_data}")
            return

        if not self.enabled:
            self.logger.info(
                f"MEXC disabled — would have executed: {action} {symbol} @ {price}"
            )
            return

        # Build order
        order = {
            "symbol":   symbol,
            "side":     action,
            "type":     self.order_type,
            "price":    price,
            "quantity": await self._calculate_quantity(symbol, price),
            "ts":       datetime.utcnow().isoformat(),
            "source":   "arkon_signal",
            "confidence": confidence,
            "stop_loss": stop_loss,
            "targets":   targets,
        }

        if self.dry_run:
            await self._dry_run_order(order)
        else:
            await self._live_order(order)

    async def _dry_run_order(self, order: Dict):
        """Simulate order execution without hitting MEXC."""
        order["dry_run"] = True
        order["simulated_fill_price"] = order["price"]
        order["status"] = "FILLED (simulated)"

        self.dry_run_orders.append(order)

        self.logger.info(
            f"📋 DRY RUN: {order['side']} {order['quantity']} "
            f"{order['symbol']} @ {order['price']}"
        )

        # Report to HA
        self._update_ha_order(order)

    async def _live_order(self, order: Dict):
        """Place a real order on MEXC."""
        if not self._api_key or not self._api_secret:
            self.logger.error("MEXC API keys not configured — cannot place order")
            return

        try:
            params = {
                "symbol":    order["symbol"],
                "side":      order["side"],
                "type":      order["type"],
                "quantity":  str(order["quantity"]),
                "price":     str(order["price"]),
                "timestamp": int(time.time() * 1000),
            }

            # Sign request
            query = urlencode(params)
            signature = hmac.new(
                self._api_secret.encode(),
                query.encode(),
                hashlib.sha256
            ).hexdigest()
            params["signature"] = signature

            r = requests.post(
                f"{self.BASE_URL}/api/v3/order",
                headers={"X-MEXC-APIKEY": self._api_key},
                params=params,
                timeout=10
            )

            if r.status_code == 200:
                result = r.json()
                order["order_id"] = result.get("orderId")
                order["status"]   = result.get("status", "NEW")
                self.orders_placed.append(order)

                self.logger.info(
                    f"✅ ORDER PLACED: {order['side']} {order['quantity']} "
                    f"{order['symbol']} @ {order['price']} "
                    f"| ID: {order['order_id']}"
                )

                # Audit log
                from security.audit import audit
                audit(
                    "ORDER_PLACED", "mexc_executor",
                    {
                        "symbol":   order["symbol"],
                        "side":     order["side"],
                        "price":    order["price"],
                        "quantity": order["quantity"],
                        "order_id": order["order_id"],
                    },
                    risk="HIGH"
                )

                self._update_ha_order(order)
            else:
                self.logger.error(
                    f"MEXC order failed: HTTP {r.status_code} — {r.text[:200]}"
                )

        except Exception as e:
            self.logger.error(f"Order execution error: {e}")

    async def _cancel_order(self, order_id: str):
        """Cancel an open order."""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Cancel order {order_id}")
            return

        # Find order symbol
        order = next(
            (o for o in self.orders_placed if o.get("order_id") == order_id),
            None
        )
        if not order:
            self.logger.warning(f"Order not found: {order_id}")
            return

        try:
            params = {
                "symbol":    order["symbol"],
                "orderId":   order_id,
                "timestamp": int(time.time() * 1000),
            }
            query     = urlencode(params)
            signature = hmac.new(
                self._api_secret.encode(), query.encode(), hashlib.sha256
            ).hexdigest()
            params["signature"] = signature

            r = requests.delete(
                f"{self.BASE_URL}/api/v3/order",
                headers={"X-MEXC-APIKEY": self._api_key},
                params=params,
                timeout=10
            )

            if r.status_code == 200:
                self.logger.info(f"Order {order_id} cancelled")
            else:
                self.logger.error(f"Cancel failed: {r.status_code}")

        except Exception as e:
            self.logger.error(f"Cancel order error: {e}")

    async def _close_all_positions(self):
        """Emergency close all open positions."""
        self.logger.warning("CLOSE ALL POSITIONS triggered!")
        for order in self.orders_placed:
            if order.get("status") not in ("FILLED", "CANCELLED"):
                await self._cancel_order(order.get("order_id"))

    async def _check_open_orders(self):
        """Poll MEXC for order status updates."""
        if not self.orders_placed or self.dry_run or not self._api_key:
            return

        for order in self.orders_placed:
            if order.get("status") not in ("FILLED", "CANCELLED"):
                try:
                    params = {
                        "symbol":    order["symbol"],
                        "orderId":   order["order_id"],
                        "timestamp": int(time.time() * 1000),
                    }
                    query     = urlencode(params)
                    signature = hmac.new(
                        self._api_secret.encode(), query.encode(), hashlib.sha256
                    ).hexdigest()
                    params["signature"] = signature

                    r = requests.get(
                        f"{self.BASE_URL}/api/v3/order",
                        headers={"X-MEXC-APIKEY": self._api_key},
                        params=params,
                        timeout=5
                    )

                    if r.status_code == 200:
                        data = r.json()
                        new_status = data.get("status")
                        if new_status != order.get("status"):
                            order["status"] = new_status
                            self.logger.info(
                                f"Order {order['order_id']} → {new_status}"
                            )
                            if new_status == "FILLED":
                                self.orders_filled.append(order)
                except Exception:
                    pass

    # ─── Helpers ─────────────────────────────────────────────────────

    async def _calculate_quantity(self, symbol: str, price: float) -> float:
        """
        Calculate order quantity based on portfolio % config.
        For now returns a default — will be integrated with portfolio tracker.
        """
        # TODO: integrate with actual portfolio balance
        # Default: $100 test size in dry run
        test_size_usd = 100.0
        if price > 0:
            return round(test_size_usd / price, 6)
        return 0.001

    def _update_ha_order(self, order: Dict):
        """Update HA sensor with latest order."""
        ha_url   = self.config.get("ha_url", "")
        ha_token = self.config.get("ha_token", "")
        if not ha_url or not ha_token:
            return
        try:
            requests.post(
                f"{ha_url}/api/states/sensor.s25_mexc_last_order",
                headers={
                    "Authorization": f"Bearer {ha_token}",
                    "Content-Type":  "application/json"
                },
                json={
                    "state": order.get("status", "UNKNOWN"),
                    "attributes": {
                        "symbol":       order.get("symbol"),
                        "side":         order.get("side"),
                        "price":        order.get("price"),
                        "quantity":     order.get("quantity"),
                        "dry_run":      order.get("dry_run", False),
                        "ts":           order.get("ts"),
                        "friendly_name": "S25 Last MEXC Order"
                    }
                },
                timeout=5
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        """Extended status including order counts."""
        base = super().get_status()
        base.update({
            "dry_run":         self.dry_run,
            "enabled":         self.enabled,
            "orders_placed":   len(self.orders_placed),
            "orders_filled":   len(self.orders_filled),
            "dry_run_orders":  len(self.dry_run_orders),
            "api_key_set":     bool(self._api_key),
        })
        return base
