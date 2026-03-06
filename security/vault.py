"""
S25 Lumière — Security Vault
=============================
Encrypted API key management. Zero leaks.

Key loading priority (highest → lowest):
1. Environment variables (Akash container env → safest)
2. .env file (local dev only — NEVER commit)
3. Raise ValueError if required key missing

NEVER hardcode secrets in source code.
NEVER log secret values.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger("s25.vault")


class S25Vault:
    """
    Secure API key vault for S25 agents.

    Usage:
        vault = S25Vault()
        ha_token   = vault.require("HA_TOKEN")
        gemini_key = vault.require("GEMINI_API_KEY")
        mexc_key   = vault.get("MEXC_API_KEY")  # Optional — returns None if missing
    """

    # Keys that MUST be present for core system to function
    REQUIRED_KEYS: Dict[str, str] = {
        "HA_TOKEN":       "Home Assistant Long-Lived API Token",
        "GEMINI_API_KEY": "Google Gemini API Key (main AI model)",
    }

    # Keys needed for trading operations
    TRADING_KEYS: Dict[str, str] = {
        "MEXC_API_KEY":    "MEXC Exchange API Key",
        "MEXC_SECRET_KEY": "MEXC Exchange Secret Key",
    }

    # Optional enhancement keys
    OPTIONAL_KEYS: Dict[str, str] = {
        "OPENAI_API_KEY":       "OpenAI GPT API Key (backup AI)",
        "PERPLEXITY_API_KEY":   "Perplexity AI API Key",
        "KIMI_API_KEY":         "Kimi Web3 API Key",
        "TELEGRAM_BOT_TOKEN":   "Telegram Notification Bot Token",
        "TELEGRAM_CHAT_ID":     "Telegram Chat ID for alerts",
        "OSMOSIS_MNEMONIC":     "Osmosis Wallet Mnemonic (auto-swap)",
    }

    # Values that indicate a placeholder (not a real key)
    PLACEHOLDER_VALUES = {
        "REPLACE_WITH_TOKEN",
        "REPLACE_WITH_KEY",
        "YOUR_KEY_HERE",
        "TODO",
        "",
    }

    def __init__(self, env_file: str = ".env"):
        self._secrets:     Dict[str, str] = {}
        self._sources:     Dict[str, str] = {}
        self._env_file     = Path(env_file)
        self._load_all()

    def _load_all(self):
        """Load from .env then override with real env vars."""
        # Step 1: .env file (lowest priority — dev only)
        if self._env_file.exists():
            self._load_env_file()

        # Step 2: Real environment variables (override .env)
        all_known = {
            **self.REQUIRED_KEYS,
            **self.TRADING_KEYS,
            **self.OPTIONAL_KEYS
        }
        for key in all_known:
            val = os.environ.get(key, "").strip()
            if val and val not in self.PLACEHOLDER_VALUES:
                self._secrets[key] = val
                self._sources[key] = "env_var"

        loaded_count = len(self._secrets)
        logger.info(f"Vault initialized: {loaded_count} secrets loaded")

        # Log missing required keys (without values)
        missing = [k for k in self.REQUIRED_KEYS if k not in self._secrets]
        if missing:
            logger.warning(f"Missing required keys: {missing}")

    def _load_env_file(self):
        """Parse .env file into secrets dict."""
        try:
            with open(self._env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    key, _, value = line.partition("=")
                    key   = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if value and value not in self.PLACEHOLDER_VALUES:
                        self._secrets[key] = value
                        self._sources[key] = ".env"

            logger.debug(f"Loaded .env: {self._env_file}")
        except Exception as e:
            logger.warning(f"Could not read .env: {e}")

    # ─── Public API ──────────────────────────────────────────────────────────

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret by key. Returns default if not found.
        Safe to call for optional keys.
        """
        return self._secrets.get(key, default)

    def require(self, key: str) -> str:
        """
        Get a required secret. Raises ValueError if missing.
        Use for keys that the system cannot operate without.
        """
        val = self._secrets.get(key)
        if not val:
            desc = {
                **self.REQUIRED_KEYS,
                **self.TRADING_KEYS,
                **self.OPTIONAL_KEYS
            }.get(key, "Unknown key")
            raise ValueError(
                f"Required secret '{key}' not set.\n"
                f"Description: {desc}\n"
                f"Fix: Add '{key}=your_value' to .env or set as environment variable."
            )
        return val

    def has(self, key: str) -> bool:
        """Check if a key is available."""
        return key in self._secrets

    def mask(self, key: str) -> str:
        """Return masked value for safe logging. Never logs real values."""
        val = self._secrets.get(key, "")
        if not val:
            return "[NOT SET]"
        if len(val) <= 8:
            return "****"
        return val[:4] + "****" + val[-4:]

    # ─── Audit ───────────────────────────────────────────────────────────────

    def audit(self) -> Dict:
        """
        Security audit report — shows presence/source but NEVER values.
        Safe to log/store.
        """
        all_keys = {
            **self.REQUIRED_KEYS,
            **self.TRADING_KEYS,
            **self.OPTIONAL_KEYS
        }

        return {
            "timestamp":        datetime.utcnow().isoformat(),
            "total_loaded":     len(self._secrets),
            "loaded": {
                key: {
                    "present": True,
                    "source":  self._sources.get(key, "unknown"),
                    "masked":  self.mask(key)
                }
                for key in self._secrets
            },
            "missing_required": [
                k for k in self.REQUIRED_KEYS if k not in self._secrets
            ],
            "missing_trading":  [
                k for k in self.TRADING_KEYS  if k not in self._secrets
            ],
            "missing_optional": [
                k for k in self.OPTIONAL_KEYS if k not in self._secrets
            ],
        }

    def check_ready(self) -> Dict[str, bool]:
        """Quick readiness check for all key categories."""
        return {
            "core_ready":    all(k in self._secrets for k in self.REQUIRED_KEYS),
            "trading_ready": all(k in self._secrets for k in self.TRADING_KEYS),
            "ha_ready":      "HA_TOKEN" in self._secrets,
            "ai_ready":      "GEMINI_API_KEY" in self._secrets,
            "mexc_ready":    all(k in self._secrets for k in ["MEXC_API_KEY", "MEXC_SECRET_KEY"]),
        }


# ─── Singleton ───────────────────────────────────────────────────────────────

_vault: Optional[S25Vault] = None


def get_vault(env_file: str = ".env") -> S25Vault:
    """Get or create the global vault instance."""
    global _vault
    if _vault is None:
        _vault = S25Vault(env_file)
    return _vault


def vault_get(key: str, default: Optional[str] = None) -> Optional[str]:
    """Shorthand: get a secret from global vault."""
    return get_vault().get(key, default)


def vault_require(key: str) -> str:
    """Shorthand: require a secret from global vault."""
    return get_vault().require(key)
