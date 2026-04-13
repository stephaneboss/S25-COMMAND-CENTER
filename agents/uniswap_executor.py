#!/usr/bin/env python3
"""
S25 LUMIERE - Uniswap V3 DEX Executor (Arbitrum)
Modes: dry_run | paper | live
"""

import os, json, logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("s25.uniswap_executor")

TOKENS = {
    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    "ARB":  "0x912CE59144191C1204E64559FE8253a0e49E6548",
    "WBTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
    "DAI":  "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
    "LINK": "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
}

FEE_TIERS = {"lowest": 100, "low": 500, "medium": 3000, "high": 10000}
TRADE_LEDGER = Path(os.getenv("MEMORY_DIR", "/app/memory")) / "uniswap_trades.json"


class UniswapExecutor:
    def __init__(self):
        self.mode = os.getenv("UNISWAP_MODE", "dry_run")
        self.rpc_url = os.getenv("ARB_RPC_URL", "https://arb1.arbitrum.io/rpc")
        self.private_key = os.getenv("ARB_PRIVATE_KEY", "")
        self.wallet_address = os.getenv("ARB_WALLET_ADDRESS", "")
        self.max_trade_usd = float(os.getenv("UNISWAP_MAX_TRADE_USD", "50"))
        self.slippage_pct = float(os.getenv("UNISWAP_SLIPPAGE_PCT", "0.5"))
        self.default_fee = FEE_TIERS["low"]
        self._web3 = None
        self._uniswap = None

    def _init_web3(self):
        if self._web3 is not None:
            return True
        try:
            from web3 import Web3
            self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self._web3.is_connected():
                log.error("Cannot connect to Arbitrum RPC")
                return False
            if self.private_key and self.mode == "live":
                from uniswap import Uniswap
                self._uniswap = Uniswap(
                    address=self.wallet_address,
                    private_key=self.private_key,
                    version=3, provider=self.rpc_url,
                )
            log.info("Web3 connected. Chain ID: %s", self._web3.eth.chain_id)
            return True
        except Exception as e:
            log.error("Web3 init failed: %s", e)
            return False

    def get_status(self):
        s = {
            "mode": self.mode, "chain": "arbitrum", "rpc": self.rpc_url,
            "wallet": self.wallet_address or "NOT_SET",
            "max_trade_usd": self.max_trade_usd,
            "web3_connected": False, "eth_balance": "0", "trades_count": 0,
        }
        try:
            if self._init_web3():
                s["web3_connected"] = True
                if self.wallet_address:
                    bal = self._web3.eth.get_balance(self._web3.to_checksum_address(self.wallet_address))
                    s["eth_balance"] = str(self._web3.from_wei(bal, "ether"))
            s["trades_count"] = len(self._load_ledger())
        except Exception as e:
            s["error"] = str(e)
        return s

    def get_price(self, token_in, token_out, amount_in_wei=10**18):
        if not self._init_web3():
            return {"error": "web3 not connected"}
        try:
            from uniswap import Uniswap
            uni = Uniswap(address=None, private_key=None, version=3, provider=self.rpc_url)
            addr_in = self._resolve_token(token_in)
            addr_out = self._resolve_token(token_out)
            if not addr_in or not addr_out:
                return {"error": f"Unknown token: {token_in} or {token_out}"}
            price = uni.get_price_input(
                self._web3.to_checksum_address(addr_in),
                self._web3.to_checksum_address(addr_out),
                amount_in_wei, fee=self.default_fee,
            )
            return {"token_in": token_in, "token_out": token_out,
                    "amount_in_wei": str(amount_in_wei), "amount_out_wei": str(price)}
        except Exception as e:
            return {"error": str(e)}

    def execute_swap(self, token_in, token_out, amount_usd, reason="", source="PIPELINE"):
        ts = datetime.now(timezone.utc).isoformat()
        rec = {"ts": ts, "token_in": token_in, "token_out": token_out,
               "amount_usd": amount_usd, "reason": reason, "source": source,
               "mode": self.mode, "chain": "arbitrum"}

        if amount_usd > self.max_trade_usd:
            rec["status"] = "REJECTED"
            rec["error"] = f"Exceeds max ${self.max_trade_usd}"
            self._save_trade(rec); return rec

        if self.mode == "dry_run":
            rec["status"] = "DRY_RUN"
            rec["message"] = f"Would swap ${amount_usd} {token_in} -> {token_out}"
            log.info("[DRY_RUN] %s", rec["message"])
            self._save_trade(rec); return rec

        if not self._init_web3():
            rec["status"] = "ERROR"; rec["error"] = "Web3 not connected"
            self._save_trade(rec); return rec

        if self.mode == "paper":
            quote = self.get_price(token_in, token_out)
            rec["status"] = "PAPER_TRADE"; rec["quote"] = quote
            log.info("[PAPER] ${amount_usd} %s -> %s", token_in, token_out)
            self._save_trade(rec); return rec

        if self.mode == "live":
            if not self.private_key:
                rec["status"] = "ERROR"; rec["error"] = "No private key"
                self._save_trade(rec); return rec
            try:
                addr_in = self._resolve_token(token_in)
                addr_out = self._resolve_token(token_out)
                amount_wei = self._web3.to_wei(amount_usd / 3000, "ether")
                tx = self._uniswap.make_trade(
                    self._web3.to_checksum_address(addr_in),
                    self._web3.to_checksum_address(addr_out),
                    amount_wei, fee=self.default_fee,
                )
                rec["status"] = "EXECUTED"
                rec["tx_hash"] = tx.hex() if hasattr(tx, "hex") else str(tx)
                log.info("[LIVE] TX: %s", rec["tx_hash"])
            except Exception as e:
                rec["status"] = "FAILED"; rec["error"] = str(e)
                log.error("[LIVE] Failed: %s", e)
            self._save_trade(rec); return rec

        rec["status"] = "UNKNOWN_MODE"; self._save_trade(rec); return rec

    def _resolve_token(self, symbol):
        if symbol.startswith("0x") and len(symbol) == 42:
            return symbol
        return TOKENS.get(symbol.upper())

    def _load_ledger(self):
        try:
            return json.loads(TRADE_LEDGER.read_text()) if TRADE_LEDGER.exists() else []
        except Exception:
            return []

    def _save_trade(self, record):
        ledger = self._load_ledger()
        ledger.append(record)
        TRADE_LEDGER.write_text(json.dumps(ledger[-200:], indent=2))


_executor = None
def get_executor():
    global _executor
    if _executor is None:
        _executor = UniswapExecutor()
    return _executor
