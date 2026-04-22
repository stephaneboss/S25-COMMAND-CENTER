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

    ALLOWED_PRODUCTS = {"BTC-USD", "ETH-USD", "AKT-USD", "SOL-USD", "ATOM-USD", "DOGE-USD", "PAXG-USD"}
    MAX_USD_PER_TRADE_DEFAULT = 50.0
    MAX_OPEN_ORDERS = 5
    # Auto bracket: after every successful BUY, place an OCO with SL+TP.
    DEFAULT_SL_PCT = 3.0   # stop-loss  -3% below entry
    DEFAULT_TP_PCT = 6.0   # take-profit +6% above entry (1:2 R/R)

    def __init__(self, config: Dict = None, commander=None):
        super().__init__("coinbase_executor", "1.0.0", config)
        self.commander = commander

        cfg = (config or {}).get("coinbase_executor", {})
        self.dry_run = bool(cfg.get("dry_run", True))
        self.enabled = bool(cfg.get("enabled", False))
        self.max_usd_per_trade = float(cfg.get("max_usd_per_trade", self.MAX_USD_PER_TRADE_DEFAULT))
        self.default_order_type = cfg.get("default_order_type", "MARKET").upper()
        self.allowed_products = set(cfg.get("allowed_products", self.ALLOWED_PRODUCTS))
        self.auto_bracket = bool(cfg.get("auto_bracket", True))
        self.sl_pct = float(cfg.get("sl_pct", self.DEFAULT_SL_PCT))
        self.tp_pct = float(cfg.get("tp_pct", self.DEFAULT_TP_PCT))

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

    _GRAN_SECONDS = {
        "ONE_MINUTE": 60, "FIVE_MINUTE": 300, "FIFTEEN_MINUTE": 900,
        "THIRTY_MINUTE": 1800, "ONE_HOUR": 3600, "TWO_HOUR": 7200,
        "SIX_HOUR": 21600, "ONE_DAY": 86400,
    }

    def get_candles(self, product_id: str, granularity: str = "ONE_HOUR", limit: int = 50):
        """Return a list of Candle objects (most recent last)."""
        from strategies.base import Candle
        c = self._get_client()
        if c is None:
            return []
        secs = self._GRAN_SECONDS.get(granularity, 3600)
        now = int(time.time())
        start = now - (limit * secs)
        try:
            resp = c.get_public_candles(
                product_id=product_id,
                start=str(start),
                end=str(now),
                granularity=granularity,
            )
            d = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
            rows = d.get("candles") or []
            candles = []
            for row in rows:
                r = row if isinstance(row, dict) else getattr(row, "__dict__", {})
                candles.append(Candle(
                    start=int(r.get("start", 0)) if r.get("start") else 0,
                    open=float(r.get("open", 0)), high=float(r.get("high", 0)),
                    low=float(r.get("low", 0)), close=float(r.get("close", 0)),
                    volume=float(r.get("volume", 0)),
                ))
            candles.sort(key=lambda x: x.start)
            return candles
        except Exception as e:
            logger.warning("candles fetch %s %s failed: %s", product_id, granularity, e)
            return []

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
        """Aggregate every account into a single portfolio snapshot with USD totals.

        Counts both `available_balance` and `hold` (funds reserved by open
        orders) so the total matches what the Coinbase app displays.
        """
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
            total_hold_usd = 0.0
            total_cad = 0.0
            for acc in accounts or []:
                def _g(o, k):
                    return o.get(k) if isinstance(o, dict) else getattr(o, k, None)
                cur = _g(acc, "currency")
                bal_avail = _g(acc, "available_balance") or {}
                bal_hold = _g(acc, "hold") or {}
                try:
                    avail = float(_g(bal_avail, "value") or 0)
                    hold = float(_g(bal_hold, "value") or 0)
                except Exception:
                    avail = hold = 0.0
                total_amt = avail + hold
                if not cur or total_amt <= 0:
                    continue
                if cur in ("USD", "USDC", "USDT"):
                    usd = total_amt
                elif cur == "CAD":
                    total_cad += total_amt
                    usd = total_amt * 0.73
                else:
                    spot = self.get_product_price(f"{cur}-USD")
                    usd = (total_amt * spot) if spot else 0.0
                total_usd += usd
                if hold > 0:
                    total_hold_usd += (hold / total_amt) * usd if total_amt else 0
                coins.append({
                    "currency": cur,
                    "amount": total_amt,
                    "available": avail,
                    "hold": hold,
                    "usd_value": round(usd, 2),
                })
            coins.sort(key=lambda x: x["usd_value"], reverse=True)
            return {
                "ok": True,
                "total_usd": round(total_usd, 2),
                "available_usd": round(total_usd - total_hold_usd, 2),
                "reserved_in_open_orders_usd": round(total_hold_usd, 2),
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

    def place_bracket_sell(
        self, product_id: str, base_size: float, entry_price: float,
        source: str = "auto_bracket",
        sl_pct: Optional[float] = None,
        tp_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place an OCO bracket SELL: stop-loss + take-profit after a successful BUY.

        Uses Coinbase trigger_bracket_order_gtc_sell which is a native OCO.
        Never fires in dry_run. Never called unless auto_bracket is on.
        SL/TP % can be overridden per-trade (used by adaptive ATR sizing).
        """
        from uuid import uuid4
        if self.dry_run:
            return {"ok": True, "skipped": "dry_run"}
        c = self._get_client()
        if c is None:
            return {"ok": False, "error": "client_unavailable"}
        effective_sl = sl_pct if sl_pct is not None else self.sl_pct
        effective_tp = tp_pct if tp_pct is not None else self.tp_pct
        try:
            sl_price = round(entry_price * (1 - effective_sl / 100.0), 8)
            tp_price = round(entry_price * (1 + effective_tp / 100.0), 8)
            qty_str = self._quantize_base_size(product_id, float(base_size))
            client_order_id = f"s25-br-{uuid4().hex[:12]}"
            resp = c.trigger_bracket_order_gtc_sell(
                client_order_id=client_order_id,
                product_id=product_id,
                base_size=qty_str,
                limit_price=f"{tp_price:.8f}",
                stop_trigger_price=f"{sl_price:.8f}",
            )
            raw = resp if isinstance(resp, dict) else getattr(resp, "__dict__", {})
            success = raw.get("success", False)
            logger.info("bracket placed %s qty=%s TP=%.6f SL=%.6f (sl_pct=%.2f tp_pct=%.2f) ok=%s",
                        product_id, qty_str, tp_price, sl_price, effective_sl, effective_tp, success)
            return {
                "ok": bool(success),
                "client_order_id": client_order_id,
                "order_id": (raw.get("success_response") or {}).get("order_id") if isinstance(raw.get("success_response"), dict) else None,
                "qty": qty_str,
                "entry_price": entry_price,
                "tp_price": tp_price,
                "sl_price": sl_price,
                "sl_pct": effective_sl,
                "tp_pct": effective_tp,
            }
        except Exception as e:
            logger.error("bracket failed: %s", e)
            return {"ok": False, "error": str(e)}

    def get_portfolio_usd(self) -> float:
        """Total portfolio value in USD. Used for risk sizing."""
        p = self.get_portfolio()
        if isinstance(p, dict) and p.get("ok"):
            return float(p.get("total_usd", 0))
        return 0.0

    # Executor-level cooldown: the single choke-point all signal paths traverse.
    # Key = (source, normalized_symbol) WITHOUT action, so flip-flop BUY→SELL
    # from the same source on the same coin is blocked as a single family.
    EXECUTOR_COOLDOWN_SEC = 600  # 10 minutes default
    MAX_TRADES_PER_HOUR = 10      # global rate limit

    @classmethod
    def _coolfile(cls) -> "Path":
        from pathlib import Path
        return Path(__file__).resolve().parent.parent / "memory" / "executor_cooldown.json"

    def _cooldown_check(self, signal: Dict) -> Optional[Dict]:
        """Return a skip-dict if cooldown or rate limit blocks, else None."""
        import json as _cdjson
        cdp = self._coolfile()
        cdp.parent.mkdir(parents=True, exist_ok=True)
        try:
            state = _cdjson.loads(cdp.read_text()) if cdp.exists() else {}
        except Exception:
            state = {}
        now = time.time()
        source = str(signal.get("source", "") or "UNKNOWN").upper()
        sym = str(signal.get("symbol", "")).upper().replace("/", "").replace("-", "")
        for q in ("USDT", "USDC"):
            if sym.endswith(q):
                sym = sym[:-len(q)] + "USD"
                break
        key = f"{source}|{sym}"
        # Per-key cooldown
        last = float(state.get(key, 0))
        if now - last < self.EXECUTOR_COOLDOWN_SEC:
            return {
                "ok": False,
                "skipped": "executor_cooldown",
                "key": key,
                "age_sec": int(now - last),
                "cooldown_sec": self.EXECUTOR_COOLDOWN_SEC,
            }
        # Global rate limit
        recent = state.get("_recent_trades", [])
        recent = [t for t in recent if now - float(t) < 3600]
        if len(recent) >= self.MAX_TRADES_PER_HOUR:
            return {
                "ok": False,
                "skipped": "hourly_rate_limit",
                "count_last_hour": len(recent),
                "limit": self.MAX_TRADES_PER_HOUR,
            }
        # Passes. Record pre-emptively so concurrent calls in flight also block.
        state[key] = now
        recent.append(now)
        state["_recent_trades"] = recent[-20:]  # keep last 20
        try:
            cdp.write_text(_cdjson.dumps(state))
        except Exception:
            pass
        return None

    def _check_blocklist_and_kill(self, signal):
        """Return skip-dict if source is blocklisted or kill-switch active, else None."""
        from pathlib import Path as _P
        import json as _j
        # Kill-switch (all trades blocked)
        kill = _P(__file__).resolve().parent.parent / "memory" / "emergency_stop.flag"
        if kill.exists():
            return {"ok": False, "skipped": "kill_switch_active",
                    "source": str(signal.get("source", ""))}
        # Source blocklist
        bl_path = _P(__file__).resolve().parent.parent / "memory" / "signal_source_blocklist.json"
        if bl_path.exists():
            try:
                data = _j.loads(bl_path.read_text())
                blocked = [str(s).upper() for s in data.get("blocked_sources", [])]
                src_name = str(signal.get("source", "")).upper()
                if src_name in blocked:
                    return {"ok": False, "skipped": "source_blocked",
                            "source": src_name, "blocklist": blocked}
            except Exception:
                pass
        return None

    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        # Source blocklist + emergency kill-switch (highest priority gate)
        gate = self._check_blocklist_and_kill(signal)
        if gate is not None:
            return gate
        # Executor cooldown — gates EVERY path (webhook_tradingview, api_signal,
        # api_tv_pine, mesh_bridge, auto_scanner, DCA).
        action = str(signal.get("action", "")).upper()
        if action in ("BUY", "SELL"):
            skip = self._cooldown_check(signal)
            if skip is not None:
                return skip
        symbol = str(signal.get("symbol", "")).upper()
        if "/" in symbol:
            base, quote = symbol.split("/", 1)
            if quote in ("USDT", "USDC"):
                quote = "USD"
            symbol = f"{base}-{quote}"

        if action not in ("BUY", "SELL"):
            return {"ok": False, "error": f"non_actionable: {action}"}

        # === Pro capital allocation: risk-based sizing + adaptive SL ===
        adaptive_sl_pct = self.sl_pct
        adaptive_tp_pct = self.tp_pct
        usd_amount = float(signal.get("usd_amount", self.max_usd_per_trade))
        try:
            from agents import risk_engine
            cfg = risk_engine.get_config()
            # Adaptive SL based on ATR of 1h candles for this symbol
            if cfg.get("use_volatility_sl", True):
                candles = self.get_candles(symbol, "ONE_HOUR", limit=30)
                if candles:
                    adaptive_sl_pct = risk_engine.compute_adaptive_sl_pct(candles, cfg)
                    rr = cfg.get("default_tp_pct", 6.0) / cfg.get("default_sl_pct", 3.0)
                    adaptive_tp_pct = adaptive_sl_pct * rr
            # Risk-based sizing only if signal didn't hardcode usd_amount
            if "usd_amount" not in signal or signal.get("usd_amount") is None:
                portfolio = self.get_portfolio_usd()
                usd_amount = risk_engine.compute_notional(portfolio, adaptive_sl_pct, cfg)
                logger.info("risk-based sizing: portfolio=%.2f sl=%.2f -> notional=%.2f",
                            portfolio, adaptive_sl_pct, usd_amount)
        except Exception as _e:
            logger.warning("risk engine fallback (keeping fixed sizing): %s", _e)

        # === Cap to available balance per side (prevents INSUFFICIENT_FUND spam) ===
        try:
            port = self.get_portfolio()
            if port.get("ok"):
                coins = port.get("coins", []) or []
                if action == "BUY":
                    # cap to available USD - $0.50 buffer
                    usd_row = next((c for c in coins if c.get("currency") == "USD"), None)
                    available = float(usd_row.get("available", 0)) if usd_row else 0.0
                    max_spend = max(0.0, available - 0.50)
                    if max_spend < 1.0:
                        return {
                            "ok": False,
                            "error": f"insufficient_usd_for_buy: available=${available:.2f}",
                            "available_usd": available,
                            "requested_usd": usd_amount,
                        }
                    if usd_amount > max_spend:
                        logger.info("capping BUY notional $%.2f -> $%.2f (USD cap)",
                                    usd_amount, max_spend)
                        usd_amount = round(max_spend, 2)
                elif action == "SELL":
                    # cap to coin held * spot, leaving a tiny buffer
                    base = symbol.split("-")[0]
                    coin_row = next((c for c in coins if c.get("currency") == base), None)
                    available_coin = float(coin_row.get("available", 0)) if coin_row else 0.0
                    spot = self.get_product_price(symbol)
                    max_usd = (available_coin * spot * 0.99) if spot else 0.0
                    if max_usd < 1.0:
                        return {
                            "ok": False,
                            "error": f"insufficient_{base}_for_sell: available={available_coin} (~${max_usd:.2f})",
                            "available_coin": available_coin,
                            "requested_usd": usd_amount,
                        }
                    if usd_amount > max_usd:
                        logger.info("capping SELL notional $%.2f -> $%.2f (coin cap %s=%.8f)",
                                    usd_amount, max_usd, base, available_coin)
                        usd_amount = round(max_usd, 2)
        except Exception as _ce:
            logger.warning("balance cap check failed: %s", _ce)

        result = self.place_market_order(
            product_id=symbol,
            side=action,
            usd_amount=usd_amount,
            reason=signal.get("reason", ""),
            source=signal.get("source", "webhook"),
        )
        # Expose risk context
        if isinstance(result, dict):
            result["risk"] = {"sl_pct": adaptive_sl_pct, "tp_pct": adaptive_tp_pct, "notional": usd_amount}

        # For LIVE orders: give Coinbase ~1s then enrich with fill info so
        # the tracker + bracket have correct base_size / avg_price / fees.
        if (result.get("ok") and not self.dry_run
                and (result.get("order") or {}).get("success")):
            order = result["order"]
            oid = order.get("order_id")
            if oid:
                time.sleep(1.2)
                info = self._get_order_info(oid)
                if info:
                    try:
                        filled_size = float(info.get("filled_size") or 0)
                        filled_value = float(info.get("filled_value") or 0)
                        fees = float(info.get("total_fees") or 0)
                        if filled_size > 0:
                            order["base_size"] = filled_size
                            order["base_size_submitted"] = filled_size
                            order["filled_value"] = filled_value
                            order["avg_price"] = filled_value / filled_size
                            order["fee"] = fees
                            order["filled_status"] = info.get("status")
                    except Exception as _fe:
                        logger.warning("fill enrichment failed: %s", _fe)

        # Record in position tracker (append JSONL)
        try:
            from agents.position_tracker import record_from_order_result, TradeEntry, record_trade
            order = result.get("order") or {}
            # If we already have enriched fill info, record a complete entry
            if order.get("avg_price") is not None and order.get("base_size") is not None:
                entry = TradeEntry(
                    ts=time.time(),
                    trade_id=order.get("client_order_id", f"s25-{int(time.time())}"),
                    order_id=order.get("order_id"),
                    symbol=order.get("product_id", ""),
                    side=order.get("side", ""),
                    usd_amount=float(order.get("usd_amount", 0) or 0),
                    base_size=float(order.get("base_size") or 0),
                    avg_price=float(order.get("avg_price") or 0),
                    fee=float(order.get("fee") or 0),
                    mode=order.get("mode", "dry_run"),
                    strategy=signal.get("strategy", signal.get("source", "")),
                    source=signal.get("source", ""),
                    success=bool(order.get("success", False)),
                    notes=signal.get("reason", ""),
                )
                record_trade(entry)
            else:
                record_from_order_result(result, signal)
        except Exception as _te:
            logger.warning("position_tracker record failed: %s", _te)

        # Auto bracket (SL + TP) after a successful live BUY
        if (
            self.auto_bracket
            and result.get("ok")
            and not self.dry_run
            and action == "BUY"
            and (result.get("order") or {}).get("success")
        ):
            order = result["order"]
            qty = None
            try:
                if order.get("base_size"):
                    qty = float(order["base_size"])
                elif order.get("base_size_submitted"):
                    qty = float(order["base_size_submitted"])
            except Exception:
                qty = None

            if qty and qty > 0:
                # Prefer actual fill price; fallback to current spot
                entry_price = order.get("avg_price") or self.get_product_price(symbol)
                if entry_price:
                    bracket = self.place_bracket_sell(
                        symbol, qty, float(entry_price), source="auto_bracket",
                        sl_pct=adaptive_sl_pct, tp_pct=adaptive_tp_pct,
                    )
                    result["bracket"] = bracket
            else:
                result["bracket"] = {"ok": False, "error": "no_base_size_resolved"}

        return result

    def _get_order_info(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Look up an order's filled state on Coinbase. Used by bracket + backfill."""
        c = self._get_client()
        if c is None:
            return None
        try:
            r = c.get_order(order_id)
            d = r if isinstance(r, dict) else getattr(r, "__dict__", {})
            order = d.get("order")
            if order is None:
                return None
            od = order if isinstance(order, dict) else getattr(order, "__dict__", {})
            return {
                "status": od.get("status"),
                "filled_size": od.get("filled_size"),
                "filled_value": od.get("filled_value"),
                "total_fees": od.get("total_fees"),
                "avg_filled_price": od.get("average_filled_price"),
                "raw": od,
            }
        except Exception as e:
            logger.warning("get_order %s failed: %s", order_id, e)
            return None

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
