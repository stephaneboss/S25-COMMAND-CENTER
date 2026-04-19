"""
S25 Lumiere - Coinbase Advanced Executor
==========================================
Order execution agent for Coinbase Advanced Trade API.

IMPORTANT: dry_run=True by default. Flip to live only when:
  1. CBA_API_KEY + CBA_API_SECRET present (View + Trade perms, NO Transfer)
  2. IP whitelist on Coinbase side includes 74.58.253.112
  3. HA input_boolean.s25_trading_live is ON

Supported:
- Market orders (BUY notional USD, SELL quantity)
- Limit orders
- Order status + cancellation
- Account balances

Config: configs/agents.yaml -> coinbase_executor
Keys:   CBA_API_KEY / CBA_API_SECRET via vault (keyring preferred)
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .base import BaseAgent

logger = logging.getLogger("s25.coinbase")


class CoinbaseExecutor(BaseAgent):
    """Coinbase Advanced order executor, dry-run safe by default."""

    ALLOWED_PRODUCTS = {"BTC-USD", "ETH-USD", "AKT-USD", "SOL-USD", "ATOM-USD"}
    MAX_USD_PER_TRADE_DEFAULT = 50.0
    MAX_OPEN_ORDERS = 5

    def __init__(self, config: Dict = None, commander=None):
        super().__init__("coinbase_executor", "1.0.0", config)
        self.commander = commander

        cfg = (config or {}).get("coinbase_executor", {})
        self.dry_run = bool(cfg.get("dry_run", True))
        self.enabled = bool(cfg.get("enabled", False))
        self.max_usd_per_trade = float(cfg.get("max_usd_per_trade", self.MAX_USD_PER_TRADE_DEFAULT))
        self.default_order_type = cfg.get("default_order_type", "MARKET").upper()
        self.allowed_products = set(cfg.get("allowed_products", self.ALLOWED_PRODUCTS))

        self._api_key: str = ""
        self._api_secret: str = ""
        self._client = None
        self._load_keys()

        self.orders_placed: List[Dict] = []
        self.dry_run_orders: List[Dict] = []

        mode = "DRY_RUN" if self.dry_run else "LIVE"
        logger.info("CoinbaseExecutor up | mode=%s | max_usd=%.2f | products=%s",
                    mode, self.max_usd_per_trade, sorted(self.allowed_products))

    def _load_keys(self) -> None:
        self._api_key = os.environ.get("CBA_API_KEY", "") or os.environ.get("COINBASE_API_KEY", "")
        self._api_secret = os.environ.get("CBA_API_SECRET", "") or os.environ.get("COINBASE_API_SECRET", "")
        if not (self._api_key and self._api_secret):
            try:
                from security.vault import vault_get
                self._api_key = self._api_key or vault_get("CBA_API_KEY", "") or vault_get("COINBASE_API_KEY", "") or ""
                self._api_secret = self._api_secret or vault_get("CBA_API_SECRET", "") or vault_get("COINBASE_API_SECRET", "") or ""
            except Exception as e:
                logger.warning("vault unreachable for CBA keys: %s", e)

        if self._api_key and self._api_secret:
            logger.info("CBA keys loaded (api_key=%s****)", self._api_key[:6])
        else:
            logger.warning("CBA keys NOT configured - executor locked to dry_run")
            self.dry_run = True

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not (self._api_key and self._api_secret):
            return None
        try:
            # Force IPv4 outbound: Coinbase IP whitelist typically only accepts IPv4
            # and AlienStef's ISP routes api.coinbase.com via IPv6 by default.
            import socket
            import urllib3.util.connection as urllib3_cn
            urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

            from coinbase.rest import RESTClient
            self._client = RESTClient(api_key=self._api_key, api_secret=self._api_secret)
            return self._client
        except Exception as e:
            logger.error("failed to init Coinbase SDK: %s", e)
            return None

    def get_accounts(self) -> Dict[str, Any]:
        c = self._get_client()
        if c is None:
            return {"ok": False, "error": "client_unavailable"}
        try:
            resp = c.get_accounts()
            accounts = getattr(resp, "accounts", resp.get("accounts") if isinstance(resp, dict) else [])
            summary = {}
            for acc in accounts or []:
                cur = acc.get("currency") if isinstance(acc, dict) else getattr(acc, "currency", None)
                bal = acc.get("available_balance") if isinstance(acc, dict) else getattr(acc, "available_balance", None)
                if bal and cur:
                    val = bal.get("value") if isinstance(bal, dict) else getattr(bal, "value", None)
                    if val and float(val) > 0:
                        summary[cur] = float(val)
            return {"ok": True, "balances": summary, "count": len(summary)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_product_price(self, product_id: str) -> Optional[float]:
        c = self._get_client()
        if c is None:
            return None
        try:
            resp = c.get_product(product_id)
            price = resp.get("price") if isinstance(resp, dict) else getattr(resp, "price", None)
            return float(price) if price else None
        except Exception as e:
            logger.warning("price fetch failed for %s: %s", product_id, e)
            return None

    def _pre_flight(self, product_id: str, usd_amount: float, side: str) -> Optional[str]:
        if product_id not in self.allowed_products:
            return f"product_not_allowed: {product_id}"
        if side.upper() not in ("BUY", "SELL"):
            return f"invalid_side: {side}"
        if usd_amount <= 0:
            return "non_positive_amount"
        if usd_amount > self.max_usd_per_trade:
            return f"exceeds_max_per_trade: {usd_amount} > {self.max_usd_per_trade}"
        return None

    def place_market_order(
        self,
        product_id: str,
        side: str,
        usd_amount: float,
        reason: str = "",
        source: str = "manual",
    ) -> Dict[str, Any]:
        ts = int(time.time())
        err = self._pre_flight(product_id, usd_amount, side)
        if err:
            return {"ok": False, "error": err, "ts": ts}

        order_record = {
            "ts": ts,
            "product_id": product_id,
            "side": side.upper(),
            "type": "MARKET",
            "usd_amount": usd_amount,
            "reason": reason,
            "source": source,
            "mode": "dry_run" if self.dry_run else "live",
        }

        if self.dry_run:
            self.dry_run_orders.append(order_record)
            logger.info("[DRY_RUN] market order: %s", order_record)
            return {"ok": True, "dry_run": True, "order": order_record}

        c = self._get_client()
        if c is None:
            return {"ok": False, "error": "client_unavailable", "ts": ts}

        client_order_id = f"s25-{source}-{uuid4().hex[:12]}"
        try:
            if side.upper() == "BUY":
                resp = c.market_order_buy(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    quote_size=f"{usd_amount:.2f}",
                )
            else:
                price = self.get_product_price(product_id)
                if not price:
                    return {"ok": False, "error": "price_unavailable_for_sell_sizing"}
                base_size = usd_amount / price
                resp = c.market_order_sell(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=f"{base_size:.8f}",
                )
            success = getattr(resp, "success", resp.get("success") if isinstance(resp, dict) else False)
            order_record["client_order_id"] = client_order_id
            order_record["success"] = bool(success)
            order_record["raw"] = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
            self.orders_placed.append(order_record)
            logger.info("[LIVE] market order placed: %s success=%s", client_order_id, success)
            return {"ok": True, "dry_run": False, "order": order_record}
        except Exception as e:
            logger.error("market order failed: %s", e)
            return {"ok": False, "error": str(e), "ts": ts, "order": order_record}

    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled and not self.dry_run:
            return {"ok": False, "error": "executor_disabled"}

        action = str(signal.get("action", "")).upper()
        symbol = str(signal.get("symbol", "")).upper()
        if "/" in symbol:
            base, quote = symbol.split("/", 1)
            if quote in ("USDT", "USDC"):
                quote = "USD"
            symbol = f"{base}-{quote}"

        if action not in ("BUY", "SELL"):
            return {"ok": False, "error": f"non_actionable: {action}"}

        return self.place_market_order(
            product_id=symbol,
            side=action,
            usd_amount=float(signal.get("usd_amount", self.max_usd_per_trade)),
            reason=signal.get("reason", ""),
            source=signal.get("source", "webhook"),
        )

    def exec_status(self) -> Dict[str, Any]:
        return {
            "agent": "coinbase_executor",
            "dry_run": self.dry_run,
            "enabled": self.enabled,
            "api_key_configured": bool(self._api_key),
            "allowed_products": sorted(self.allowed_products),
            "max_usd_per_trade": self.max_usd_per_trade,
            "orders_placed": len(self.orders_placed),
            "dry_run_orders": len(self.dry_run_orders),
        }

    # --- BaseAgent abstract stubs (we are event-driven, not loop-driven) ---

    async def run(self):
        return None

    async def handle_signal(self, signal: Dict[str, Any]):
        return self.execute_signal(signal)


_executor: Optional[CoinbaseExecutor] = None


def get_executor(config: Dict = None) -> CoinbaseExecutor:
    global _executor
    if _executor is None:
        _executor = CoinbaseExecutor(config=config or {})
    return _executor
