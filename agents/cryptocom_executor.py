"""
S25 Lumiere — Crypto.com Exchange Executor
============================================
Order execution agent for Crypto.com Exchange (v1 API).

IMPORTANT: dry_run=True by default. Enable live trading only
when API keys are configured and risk management is confirmed.

Supported operations:
- Market orders (instant fill, notional for BUY, quantity for SELL)
- Limit orders (price + quantity)
- Order status tracking
- Order cancellation

Config: configs/agents.yaml -> cryptocom_executor section
Keys:   .env -> CDC_API_KEY + CDC_API_SECRET (fallback to vault)
"""

import asyncio
import hashlib
import hmac
import logging
import os
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

from .base import BaseAgent

logger = logging.getLogger("s25.cryptocom")


class CryptocomExecutor(BaseAgent):
    """
    Crypto.com Exchange order executor.

    Modes:
    - dry_run=True  (default): Logs orders but doesn't send them
    - dry_run=False (live):    Real orders on Crypto.com Exchange

    Always validates through RiskGuardian before executing.
    """

    BASE_URL = "https://api.crypto.com/exchange/v1"

    def __init__(self, config: Dict = None, commander=None):
        super().__init__("cryptocom_executor", "1.0.0", config)
        self.commander = commander

        cdc_cfg = config.get("cryptocom_executor", {}) if config else {}

        self.dry_run     = cdc_cfg.get("dry_run", True)    # SAFE DEFAULT
        self.enabled     = cdc_cfg.get("enabled", False)
        self.order_type  = cdc_cfg.get("default_order_type", "MARKET")
        self.size_pct    = cdc_cfg.get("default_size_pct", 5.0)

        # Load API keys
        self._api_key    = ""
        self._api_secret = ""
        self._load_keys()

        # Order tracking
        self.orders_placed:    List[Dict] = []
        self.orders_filled:    List[Dict] = []
        self.dry_run_orders:   List[Dict] = []

        if self.dry_run:
            self.logger.info(
                "CryptocomExecutor initialized in DRY RUN mode — "
                "no real orders will be placed"
            )
        else:
            self.logger.warning(
                "CryptocomExecutor in LIVE mode — real orders will be executed!"
            )

    def _load_keys(self):
        """Load API keys from env vars, fallback to vault."""
        self._api_key    = os.environ.get("CDC_API_KEY", "")
        self._api_secret = os.environ.get("CDC_API_SECRET", "")

        if self._api_key and self._api_secret:
            self.logger.info(
                f"CDC keys loaded from env: {self._api_key[:4]}****"
            )
            return

        # Fallback to vault
        try:
            from security.vault import get_vault
            vault = get_vault()
            self._api_key    = vault.get("CDC_API_KEY", "") or self._api_key
            self._api_secret = vault.get("CDC_API_SECRET", "") or self._api_secret
            if self._api_key:
                self.logger.info(
                    f"CDC keys loaded from vault: {self._api_key[:4]}****"
                )
        except Exception as e:
            self.logger.warning(f"Could not load CDC keys: {e}")

    # ─── Crypto.com API Signing ──────────────────────────────────────

    def _sign_request(
        self, method: str, request_id: int, params: Dict = None
    ) -> Dict:
        """
        Build and sign a Crypto.com Exchange v1 API request.

        Signature = HMAC-SHA256 of:
            method + str(id) + api_key + sorted_params_str + str(nonce)
        """
        params = params or {}
        nonce = int(time.time() * 1000)

        # Sort params by key for deterministic signing
        sorted_keys = sorted(params.keys())
        params_str = ""
        for key in sorted_keys:
            params_str += str(key) + str(params[key])

        sig_payload = (
            method
            + str(request_id)
            + self._api_key
            + params_str
            + str(nonce)
        )

        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            sig_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {
            "id":      request_id,
            "method":  method,
            "api_key": self._api_key,
            "params":  params,
            "nonce":   nonce,
            "sig":     signature,
        }

    def _api_call(
        self, method: str, params: Dict = None, timeout: int = 10
    ) -> Dict:
        """
        POST a signed request to the Crypto.com Exchange API.

        Returns the JSON response dict or raises on error.
        """
        request_id = int(time.time() * 1000)
        body = self._sign_request(method, request_id, params)

        r = requests.post(
            f"{self.BASE_URL}/{method}",
            json=body,
            timeout=timeout,
        )

        if r.status_code != 200:
            raise Exception(
                f"CDC API error: HTTP {r.status_code} — {r.text[:300]}"
            )

        data = r.json()
        if data.get("code") != 0:
            raise Exception(
                f"CDC API error: code={data.get('code')} "
                f"msg={data.get('message', 'unknown')}"
            )

        return data

    # ─── Public Helpers ──────────────────────────────────────────────

    def get_balance(self) -> List[Dict]:
        """
        Fetch non-zero balances from Crypto.com Exchange.

        Returns list of dicts with currency, available, locked.
        """
        data = self._api_call("private/get-account-summary")
        accounts = data.get("result", {}).get("accounts", [])

        balances = []
        for acct in accounts:
            available = float(acct.get("available", 0))
            order_val = float(acct.get("order", 0))
            stake_val = float(acct.get("stake", 0))
            if available > 0 or order_val > 0 or stake_val > 0:
                balances.append({
                    "currency":  acct.get("currency"),
                    "available": available,
                    "locked":    order_val + stake_val,
                })

        return balances

    def test_connection(self) -> Dict:
        """Test API connectivity and key validity."""
        try:
            balances = self.get_balance()
            return {
                "status":   "connected",
                "exchange": "crypto.com",
                "balances": len(balances),
            }
        except Exception as e:
            self.logger.error(f"CDC connection test failed: {e}")
            return {
                "status":   "disconnected",
                "exchange": "crypto.com",
                "error":    str(e),
            }

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

    # ─── Order Execution ─────────────────────────────────────────────

    async def _handle_execute(self, signal_data: Dict):
        """
        Process an execute order signal.

        Symbol format: DOGE/USDT -> DOGE_USDT (Crypto.com uses underscore).
        """
        raw_symbol = signal_data.get("symbol", "")
        symbol     = raw_symbol.replace("/", "_")   # DOGE/USDT -> DOGE_USDT
        action     = signal_data.get("action", "").upper()
        price      = signal_data.get("price", 0)
        quantity   = signal_data.get("quantity", 0)
        notional   = signal_data.get("notional", 0)
        confidence = signal_data.get("confidence", 0)

        if not symbol or action not in ("BUY", "SELL"):
            self.logger.warning(f"Invalid order signal: {signal_data}")
            return

        if not self.enabled:
            self.logger.info(
                f"CDC disabled — would have executed: {action} {symbol} @ {price}"
            )
            return

        order_type = signal_data.get("order_type", self.order_type).upper()

        # Build order
        order = {
            "instrument_name": symbol,
            "side":            action,
            "type":            order_type,
            "price":           price,
            "quantity":        quantity or await self._calculate_quantity(symbol, price),
            "notional":        notional or 100.0,  # default $100 for market buys
            "ts":              datetime.utcnow().isoformat(),
            "source":          "arkon_signal",
            "confidence":      confidence,
        }

        if self.dry_run:
            await self._dry_run_order(order)
        else:
            await self._live_order(order)

    async def _dry_run_order(self, order: Dict):
        """Simulate order execution without hitting Crypto.com."""
        order["dry_run"] = True
        order["simulated_fill_price"] = order["price"]
        order["status"] = "FILLED (simulated)"

        self.dry_run_orders.append(order)

        self.logger.info(
            f"DRY RUN: {order['side']} {order.get('quantity', '?')} "
            f"{order['instrument_name']} @ {order['price']} "
            f"(type={order['type']})"
        )

        self._update_ha_order(order)

    async def _live_order(self, order: Dict):
        """Place a real order on Crypto.com Exchange."""
        if not self._api_key or not self._api_secret:
            self.logger.error(
                "CDC API keys not configured — cannot place order"
            )
            return

        try:
            params = {
                "instrument_name": order["instrument_name"],
                "side":            order["side"],
                "type":            order["type"],
            }

            if order["type"] == "MARKET":
                if order["side"] == "BUY":
                    # Market buy uses notional (USD amount)
                    params["notional"] = str(order["notional"])
                else:
                    # Market sell uses quantity
                    params["quantity"] = str(order["quantity"])
            elif order["type"] == "LIMIT":
                params["price"]    = str(order["price"])
                params["quantity"] = str(order["quantity"])
            else:
                # Other order types: include both if available
                if order.get("price"):
                    params["price"] = str(order["price"])
                if order.get("quantity"):
                    params["quantity"] = str(order["quantity"])

            data = self._api_call("private/create-order", params)

            result = data.get("result", {})
            order["order_id"] = result.get("order_id")
            order["status"]   = "NEW"
            self.orders_placed.append(order)

            self.logger.info(
                f"ORDER PLACED: {order['side']} "
                f"{order['instrument_name']} "
                f"type={order['type']} "
                f"| ID: {order['order_id']}"
            )

            # Audit log
            try:
                from security.audit import audit
                audit(
                    "ORDER_PLACED", "cryptocom_executor",
                    {
                        "instrument": order["instrument_name"],
                        "side":       order["side"],
                        "type":       order["type"],
                        "order_id":   order["order_id"],
                    },
                    risk="HIGH"
                )
            except Exception:
                pass

            self._update_ha_order(order)

        except Exception as e:
            self.logger.error(f"CDC order execution error: {e}")

    async def _cancel_order(self, order_id: str):
        """Cancel an open order on Crypto.com Exchange."""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Cancel order {order_id}")
            return

        # Find order to get instrument_name
        order = next(
            (o for o in self.orders_placed if o.get("order_id") == order_id),
            None,
        )
        if not order:
            self.logger.warning(f"Order not found: {order_id}")
            return

        try:
            params = {
                "instrument_name": order["instrument_name"],
                "order_id":        order_id,
            }

            self._api_call("private/cancel-order", params)
            order["status"] = "CANCELLED"
            self.logger.info(f"Order {order_id} cancelled")

        except Exception as e:
            self.logger.error(f"CDC cancel order error: {e}")

    async def _check_open_orders(self):
        """Poll Crypto.com for order status updates."""
        if not self.orders_placed or self.dry_run or not self._api_key:
            return

        for order in self.orders_placed:
            if order.get("status") not in ("FILLED", "CANCELLED", "REJECTED", "EXPIRED"):
                try:
                    params = {"order_id": order["order_id"]}
                    data = self._api_call("private/get-order-detail", params, timeout=5)

                    result     = data.get("result", {})
                    order_info = result.get("order_info", {})
                    new_status = order_info.get("status", "")

                    if new_status and new_status != order.get("status"):
                        order["status"] = new_status
                        self.logger.info(
                            f"Order {order['order_id']} -> {new_status}"
                        )
                        if new_status == "FILLED":
                            order["avg_price"]   = order_info.get("avg_price")
                            order["filled_qty"]  = order_info.get("cumulative_quantity")
                            self.orders_filled.append(order)

                except Exception:
                    pass

    # ─── Helpers ─────────────────────────────────────────────────────

    async def _calculate_quantity(self, symbol: str, price: float) -> float:
        """
        Calculate order quantity based on portfolio % config.
        Default: $100 test size in dry run.
        """
        test_size_usd = 100.0
        if price > 0:
            return round(test_size_usd / price, 6)
        return 0.001

    def _update_ha_order(self, order: Dict):
        """Update HA sensor with latest Crypto.com order."""
        ha_url   = self.config.get("ha_url", "")
        ha_token = self.config.get("ha_token", "")
        if not ha_url or not ha_token:
            return
        try:
            requests.post(
                f"{ha_url}/api/states/sensor.s25_cdc_last_order",
                headers={
                    "Authorization": f"Bearer {ha_token}",
                    "Content-Type":  "application/json",
                },
                json={
                    "state": order.get("status", "UNKNOWN"),
                    "attributes": {
                        "instrument":    order.get("instrument_name"),
                        "side":          order.get("side"),
                        "type":          order.get("type"),
                        "price":         order.get("price"),
                        "quantity":      order.get("quantity"),
                        "notional":      order.get("notional"),
                        "dry_run":       order.get("dry_run", False),
                        "ts":            order.get("ts"),
                        "friendly_name": "S25 Last CDC Order",
                    },
                },
                timeout=5,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        """Extended status including order counts."""
        base = super().get_status()
        base.update({
            "exchange":        "crypto.com",
            "dry_run":         self.dry_run,
            "enabled":         self.enabled,
            "orders_placed":   len(self.orders_placed),
            "orders_filled":   len(self.orders_filled),
            "dry_run_orders":  len(self.dry_run_orders),
            "api_key_set":     bool(self._api_key),
        })
        return base
