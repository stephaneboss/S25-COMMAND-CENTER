"""
S25 Lumiere security vault.

Priority order:
1. Runtime environment variables
2. OS keyring / credential manager
3. Local .env fallback
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("s25.vault")

try:
    import keyring
    from keyring.errors import KeyringError
except Exception:  # pragma: no cover - optional dependency
    keyring = None

    class KeyringError(Exception):
        pass


class S25Vault:
    REQUIRED_KEYS: Dict[str, str] = {
        "HA_TOKEN": "Home Assistant long-lived API token",
        "GEMINI_API_KEY": "Google Gemini API key",
        "S25_SHARED_SECRET": "Shared secret for cockpit public actions",
    }

    TRADING_KEYS: Dict[str, str] = {
        "MEXC_API_KEY": "MEXC exchange API key",
        "MEXC_SECRET_KEY": "MEXC exchange secret key",
    }

    OPTIONAL_KEYS: Dict[str, str] = {
        "OPENAI_API_KEY": "OpenAI API key",
        "ANTHROPIC_API_KEY": "Anthropic API key",
        "PERPLEXITY_API_KEY": "Perplexity API key",
        "KIMI_API_KEY": "Kimi API key",
        "TELEGRAM_BOT_TOKEN": "Telegram bot token",
        "TELEGRAM_CHAT_ID": "Telegram chat id",
        "OSMOSIS_MNEMONIC": "Osmosis wallet mnemonic",
    }

    PLACEHOLDER_VALUES = {
        "",
        "TODO",
        "YOUR_KEY_HERE",
        "REPLACE_WITH_KEY",
        "REPLACE_WITH_TOKEN",
        "change_me_x100",
        "change_me_s25_secret",
    }

    def __init__(self, env_file: str = ".env"):
        self._env_file = Path(env_file)
        self._service_name = os.getenv("S25_VAULT_SERVICE", "S25-LUMIERE")
        self._secrets: Dict[str, str] = {}
        self._sources: Dict[str, str] = {}
        self._load_all()

    @property
    def all_known_keys(self) -> Dict[str, str]:
        return {
            **self.REQUIRED_KEYS,
            **self.TRADING_KEYS,
            **self.OPTIONAL_KEYS,
        }

    def _is_real(self, value: Optional[str]) -> bool:
        if value is None:
            return False
        return value.strip() not in self.PLACEHOLDER_VALUES

    def _load_all(self) -> None:
        if self._env_file.exists():
            self._load_env_file()
        self._load_keyring()
        self._load_environment()

        logger.info("Vault initialized with %s secrets", len(self._secrets))
        missing = [key for key in self.REQUIRED_KEYS if key not in self._secrets]
        if missing:
            logger.warning("Missing required keys: %s", missing)

    def _load_env_file(self) -> None:
        try:
            for raw in self._env_file.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if self._is_real(value):
                    self._secrets[key] = value
                    self._sources[key] = ".env"
        except Exception as exc:
            logger.warning("Could not read %s: %s", self._env_file, exc)

    def _load_keyring(self) -> None:
        if not keyring:
            return
        for key in self.all_known_keys:
            try:
                value = keyring.get_password(self._service_name, key)
            except KeyringError as exc:
                logger.warning("Keyring read failed for %s: %s", key, exc)
                return
            if self._is_real(value):
                self._secrets[key] = value.strip()
                self._sources[key] = "keyring"

    def _load_environment(self) -> None:
        for key in self.all_known_keys:
            value = os.getenv(key)
            if self._is_real(value):
                self._secrets[key] = value.strip()
                self._sources[key] = "env_var"

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._secrets.get(key, default)

    def require(self, key: str) -> str:
        value = self._secrets.get(key)
        if value:
            return value
        desc = self.all_known_keys.get(key, "Unknown key")
        raise ValueError(
            f"Required secret '{key}' not set. Description: {desc}. "
            f"Add it to runtime env, OS keyring, or {self._env_file}."
        )

    def has(self, key: str) -> bool:
        return key in self._secrets

    def source(self, key: str) -> str:
        return self._sources.get(key, "missing")

    def mask(self, key: str) -> str:
        value = self._secrets.get(key, "")
        if not value:
            return "[NOT SET]"
        if len(value) <= 8:
            return "****"
        return value[:4] + "****" + value[-4:]

    def set_local(self, key: str, value: str, prefer_keyring: bool = True) -> str:
        value = value.strip()
        if not self._is_real(value):
            raise ValueError(f"Secret '{key}' is empty or placeholder")

        if prefer_keyring and keyring:
            keyring.set_password(self._service_name, key, value)
            self._secrets[key] = value
            self._sources[key] = "keyring"
            return "keyring"

        current = {}
        if self._env_file.exists():
            for raw in self._env_file.read_text(encoding="utf-8").splitlines():
                if "=" not in raw or raw.strip().startswith("#"):
                    continue
                name, _, existing = raw.partition("=")
                current[name.strip()] = existing.strip()
        current[key] = value
        rendered = "\n".join(f"{name}={current[name]}" for name in sorted(current))
        self._env_file.write_text(rendered + "\n", encoding="utf-8")
        self._secrets[key] = value
        self._sources[key] = ".env"
        return ".env"

    def delete_local(self, key: str) -> list[str]:
        removed = []
        if keyring:
            try:
                keyring.delete_password(self._service_name, key)
                removed.append("keyring")
            except Exception:
                pass

        if self._env_file.exists():
            kept = []
            changed = False
            for raw in self._env_file.read_text(encoding="utf-8").splitlines():
                if raw.strip().startswith(f"{key}="):
                    changed = True
                    continue
                kept.append(raw)
            if changed:
                text = "\n".join(kept).strip()
                self._env_file.write_text((text + "\n") if text else "", encoding="utf-8")
                removed.append(".env")

        self._secrets.pop(key, None)
        self._sources.pop(key, None)
        return removed

    def export_env_map(self, include_optional: bool = False) -> Dict[str, str]:
        keys = {**self.REQUIRED_KEYS, **self.TRADING_KEYS}
        if include_optional:
            keys.update(self.OPTIONAL_KEYS)
        return {key: self._secrets[key] for key in keys if key in self._secrets}

    def audit(self) -> Dict[str, object]:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_loaded": len(self._secrets),
            "loaded": {
                key: {
                    "present": True,
                    "source": self._sources.get(key, "unknown"),
                    "masked": self.mask(key),
                }
                for key in sorted(self._secrets)
            },
            "missing_required": [key for key in self.REQUIRED_KEYS if key not in self._secrets],
            "missing_trading": [key for key in self.TRADING_KEYS if key not in self._secrets],
            "missing_optional": [key for key in self.OPTIONAL_KEYS if key not in self._secrets],
        }

    def check_ready(self) -> Dict[str, bool]:
        return {
            "core_ready": all(key in self._secrets for key in self.REQUIRED_KEYS),
            "trading_ready": all(key in self._secrets for key in self.TRADING_KEYS),
            "ha_ready": "HA_TOKEN" in self._secrets,
            "ai_ready": "GEMINI_API_KEY" in self._secrets,
            "mexc_ready": all(key in self._secrets for key in self.TRADING_KEYS),
        }


_vault: Optional[S25Vault] = None


def get_vault(env_file: str = ".env") -> S25Vault:
    global _vault
    if _vault is None:
        _vault = S25Vault(env_file)
    return _vault


def vault_get(key: str, default: Optional[str] = None) -> Optional[str]:
    return get_vault().get(key, default)


def vault_require(key: str) -> str:
    return get_vault().require(key)
