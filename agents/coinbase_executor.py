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

    ALLOWED_PRODUCTS = {"BTC-USD", "ETH-USD", "AKT-USD", "SOL-USD", "ATOM-USD", "DOGE-USD"}
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

    _base_increment_cache: Dict[str, str] = {}

    def _get_base_increment(self, product_id: str) -> str:
        """Return Coinbase's base_increment for a product (e.g. '0.1' for DOGE).

        Required so SELL orders submit base_size at the right precision —
        otherwise we get PREVIEW_INVALID_SIZE_PRECISION.
        """
        if product_id in self._base_increment_cache:
            return self._base_increment_cache[product_id]
        c = self._get_client()
        if c is None:
            return "0.00000001"
        try:
            resp = c.get_product(product_id)
            d = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
            inc = d.get("base_increment") or "0.00000001"
            self._base_increment_cache[product_id] = str(inc)
            return str(inc)
        except Exception:
            return "0.00000001"

    def _quantize_base_size(self, product_id: str, raw_size: float) -> str:
        """Round `raw_size` DOWN to the product's base_increment, returned as a string
        formatted with the correct number of decimals."""
        from decimal import Decimal, ROUND_DOWN
        inc_s = self._get_base_increment(product_id)
        inc = Decimal(inc_s)
        q = (Decimal(str(raw_size)) / inc).to_integral_value(rounding=ROUND_DOWN) * inc
        # Format using the increment's own decimal count
        if "." in inc_s:
            decimals = len(inc_s.split(".")[1].rstrip("0")) or 1
        else:
            decimals = 0
        return f"{q:.{decimals}f}"

    # ─── Portfolio + fiat read side ─────────────────────────────────

    def get_portfolio(self) -> Dict[str, Any]:
        """Aggregate every account into a single portfolio snapshot with USD totals."""
        c = self._get_client()
        if c is None:
            return {"ok": False, "error": "client_unavailable"}
        try:
            resp = c.get_accounts()
            accounts = getattr(resp, "accounts", None)
            if accounts is None and isinstance(resp, dict):
                accounts = resp.get("accounts", [])
            coins = []
            total_usd = 0.0
            total_cad = 0.0
            for acc in accounts or []:
                def _g(o, k):
                    return o.get(k) if isinstance(o, dict) else getattr(o, k, None)
                cur = _g(acc, "currency")
                bal = _g(acc, "available_balance") or {}
                val_s = _g(bal, "value") if bal else None
                if not cur or not val_s:
                    continue
                val = float(val_s)
                if val <= 0:
                    continue
                usd = val
                if cur not in ("USD", "USDC", "USDT"):
                    spot = self.get_product_price(f"{cur}-USD")
                    usd = (val * spot) if spot else 0.0
                if cur == "CAD":
                    total_cad += val
                    usd = val * 0.73  # rough USD conv
                total_usd += usd
                coins.append({
                    "currency": cur,
                    "amount": val,
                    "usd_value": round(usd, 2),
                })
            coins.sort(key=lambda x: x["usd_value"], reverse=True)
            return {
                "ok": True,
                "total_usd": round(total_usd, 2),
                "total_cad_fiat": round(total_cad, 2),
                "coin_count": len(coins),
                "coins": coins,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_payment_methods(self) -> Dict[str, Any]:
        """List connected fiat payment methods (Interac, EFT, PayPal, cards)."""
        c = self._get_client()
        if c is None:
            return {"ok": False, "error": "client_unavailable"}
        try:
            resp = c.list_payment_methods()
            methods_raw = getattr(resp, "payment_methods", None)
            if methods_raw is None and isinstance(resp, dict):
                methods_raw = resp.get("payment_methods", [])
            methods = []
            for m in methods_raw or []:
                d = m if isinstance(m, dict) else getattr(m, "__dict__", {})
                methods.append({
                    "type": d.get("type"),
                    "name": d.get("name"),
                    "currency": d.get("currency"),
                    "allow_buy": d.get("allow_buy"),
                    "allow_sell": d.get("allow_sell"),
                    "allow_deposit": d.get("allow_deposit"),
                    "allow_withdraw": d.get("allow_withdraw"),
                    "verified": d.get("verified"),
                })
            return {"ok": True, "count": len(methods), "methods": methods}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_fee_tier(self) -> Dict[str, Any]:
        c = self._get_client()
        if c is None:
            return {"ok": False, "error": "client_unavailable"}
        try:
            resp = c.get_transaction_summary()
            d = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
            tier = d.get("fee_tier", {})
            return {
                "ok": True,
                "tier_name": tier.get("pricing_tier"),
                "maker_fee": tier.get("maker_fee_rate"),
                "taker_fee": tier.get("taker_fee_rate"),
                "total_volume_30d": d.get("total_volume"),
                "total_fees_30d": d.get("total_fees"),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def preview_order(
        self, product_id: str, side: str, usd_amount: float
    ) -> Dict[str, Any]:
        """Simulate a market order without placing it (SDK preview endpoint)."""
        err = self._pre_flight(product_id, usd_amount, side)
        if err:
            return {"ok": False, "error": err}
        c = self._get_client()
        if c is None:
            return {"ok": False, "error": "client_unavailable"}
        try:
            if side.upper() == "BUY":
                resp = c.preview_market_order_buy(product_id=product_id, quote_size=f"{usd_amount:.2f}")
            else:
                price = self.get_product_price(product_id)
                if not price:
                    return {"ok": False, "error": "price_unavailable"}
                raw_size = usd_amount / price
                base_size = self._quantize_base_size(product_id, raw_size)
                resp = c.preview_market_order_sell(product_id=product_id, base_size=base_size)
            d = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
            return {"ok": True, "preview": d}
        except Exception as e:
            return {"ok": False, "error": str(e)}

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

    LIVE_FLAG_PATH = os.path.expanduser("~/S25-COMMAND-CENTER/.coinbase_live.flag")

    def refresh_mode_from_ha(self, ttl: int = 30) -> bool:
        """Read the local live-mode flag to flip dry_run at runtime.

        A file at LIVE_FLAG_PATH acts as the single source of truth:
          file contains "on" (first line)  -> LIVE (if keys present)
          file absent OR content != "on"   -> DRY_RUN (safe)

        We use a file flag instead of an HA input_boolean because state
        pushed via /api/states/ is not persistent when an entity is not
        registered by its domain. Cockpit's POST /api/coinbase/live-mode
        toggles the file; HA can call that endpoint via a rest_command or
        automation.

        Cached for `ttl` seconds.
        """
        now = time.time()
        if hasattr(self, "_ha_mode_ts") and (now - self._ha_mode_ts) < ttl:
            return not self.dry_run
        self._ha_mode_ts = now
        try:
            import pathlib
            flag_path = pathlib.Path(self.LIVE_FLAG_PATH)
            flag_on = False
            if flag_path.exists():
                flag_on = flag_path.read_text().strip().lower() == "on"
            if flag_on and self._api_key and self._api_secret:
                if self.dry_run:
                    logger.warning("live-flag ON + keys present -> switching to LIVE mode")
                self.dry_run = False
            else:
                if not self.dry_run:
                    logger.info("live-flag OFF or keys missing -> back to DRY_RUN")
                self.dry_run = True
        except Exception as e:
            logger.warning("mode refresh failed, keeping current mode: %s", e)
        return not self.dry_run

    @classmethod
    def set_live_mode(cls, enabled: bool) -> Dict[str, Any]:
        """Write/remove the live-mode flag file. Used by /api/coinbase/live-mode."""
        import pathlib
        flag_path = pathlib.Path(cls.LIVE_FLAG_PATH)
        try:
            if enabled:
                flag_path.write_text("on\n")
                return {"ok": True, "enabled": True, "flag_path": str(flag_path)}
            else:
                if flag_path.exists():
                    flag_path.unlink()
                return {"ok": True, "enabled": False, "flag_path": str(flag_path)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def place_market_order(
        self,
        product_id: str,
        side: str,
        usd_amount: float,
        reason: str = "",
        source: str = "manual",
    ) -> Dict[str, Any]:
        self.refresh_mode_from_ha()
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
                raw_size = usd_amount / price
                base_size = self._quantize_base_size(product_id, raw_size)
                resp = c.market_order_sell(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=base_size,
                )
                order_record["base_size_submitted"] = base_size
            success = getattr(resp, "success", resp.get("success") if isinstance(resp, dict) else False)
            order_record["client_order_id"] = client_order_id
            order_record["success"] = bool(success)
            # Stringify the SDK response so Flask jsonify never fails on
            # non-serializable objects (proto messages, nested enums, etc.)
            try:
                raw_dict = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
                order_record["raw"] = {k: (str(v) if not isinstance(v, (str, int, float, bool, type(None), list, dict)) else v) for k, v in raw_dict.items()}
                # Extract key fields straight to top level for easier introspection
                if isinstance(raw_dict.get("success_response"), (dict,)):
                    order_record["order_id"] = raw_dict["success_response"].get("order_id")
                else:
                    sr = raw_dict.get("success_response")
                    oid = getattr(sr, "order_id", None) if sr else None
                    if oid:
                        order_record["order_id"] = oid
            except Exception as _se:
                order_record["raw"] = {"serialization_error": str(_se)}
            self.orders_placed.append(order_record)
            logger.info("[LIVE] market order placed: %s success=%s", client_order_id, success)
            return {"ok": True, "dry_run": False, "order": order_record}
        except Exception as e:
            logger.error("market order failed: %s", e)
            return {"ok": False, "error": str(e), "ts": ts, "order": order_record}

    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        # `self.enabled` was the legacy gate before the HA file-flag existed.
        # Now the single source of truth is `self.dry_run` (set by
        # refresh_mode_from_ha). place_market_order calls refresh itself
        # and handles both modes cleanly.
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
