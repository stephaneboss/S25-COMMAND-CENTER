"""
S25 Lumiere security vault.

Priority order:
1. Runtime environment variables
2. OS keyring / credential manager
3. Encrypted sync bundle
4. Local .env fallback
"""

from __future__ import annotations

import base64
import hashlib
import json
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

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover - optional dependency
    Fernet = None
    InvalidToken = Exception


class S25Vault:
    REQUIRED_KEYS: Dict[str, str] = {
        "HA_TOKEN": "Home Assistant long-lived API token",
        "GEMINI_API_KEY": "Google Gemini API key",
        "S25_SHARED_SECRET": "Shared secret for cockpit public actions",
    }

    TRADING_KEYS: Dict[str, str] = {
        "MEXC_API_KEY": "MEXC exchange API key",
        "MEXC_SECRET_KEY": "MEXC exchange secret key",
        "CBA_API_KEY": "Coinbase Advanced API key (View + Trade, no Transfer)",
        "CBA_API_SECRET": "Coinbase Advanced API secret / EC private key",
        "CDC_API_KEY": "Crypto.com exchange API key",
        "CDC_API_SECRET": "Crypto.com exchange API secret",
    }

    OPTIONAL_KEYS: Dict[str, str] = {
        "OPENAI_API_KEY": "OpenAI API key",
        "ANTHROPIC_API_KEY": "Anthropic API key",
        "PERPLEXITY_API_KEY": "Perplexity API key",
        "KIMI_API_KEY": "Kimi API key",
        "S25_MASTER_SEED": "Wallet creator master seed phrase",
        "WALLET_MNEMONIC": "BIP39 mnemonic for cosmos1/osmo1/akash1 signer (creator-route)",
        "AKASH_MNEMONIC": "Alias for WALLET_MNEMONIC used by Akash tools",
        "TELEGRAM_BOT_TOKEN": "Telegram bot token",
        "TELEGRAM_CHAT_ID": "Telegram chat id",
        "OSMOSIS_MNEMONIC": "Osmosis wallet mnemonic",
        "S25_SECRETS_BUNDLE_KEY": "Master key for encrypted sync bundle",
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
        self._bundle_path = Path(
            os.getenv(
                "S25_SECRETS_BUNDLE_PATH",
                str(Path.home() / "Google Drive" / "S25" / "secrets.bundle"),
            )
        )
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
        self._load_bundle()
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

    def _bundle_master_secret(self) -> Optional[str]:
        raw = os.getenv("S25_SECRETS_BUNDLE_KEY")
        if self._is_real(raw):
            return raw.strip()
        if keyring:
            try:
                raw = keyring.get_password(self._service_name, "S25_SECRETS_BUNDLE_KEY")
            except Exception:
                raw = None
            if self._is_real(raw):
                return raw.strip()
        return self._secrets.get("S25_SECRETS_BUNDLE_KEY")

    def _bundle_fernet_key(self) -> Optional[bytes]:
        if not Fernet:
            return None
        secret = self._bundle_master_secret()
        if not self._is_real(secret):
            return None
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def _load_bundle(self) -> None:
        if not self._bundle_path.exists():
            return
        if not Fernet:
            logger.warning("cryptography missing; cannot load encrypted bundle")
            return

        fernet_key = self._bundle_fernet_key()
        if not fernet_key:
            logger.debug("No bundle key available; skipping encrypted bundle")
            return

        try:
            payload = self._bundle_path.read_bytes()
            decrypted = Fernet(fernet_key).decrypt(payload)
            data = json.loads(decrypted.decode("utf-8"))
        except InvalidToken:
            logger.warning("Encrypted bundle exists but key is invalid")
            return
        except Exception as exc:
            logger.warning("Could not read encrypted bundle %s: %s", self._bundle_path, exc)
            return

        for key_name, value in data.items():
            if self._is_real(value):
                self._secrets[key_name] = value.strip()
                self._sources[key_name] = "bundle"

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._secrets.get(key, default)

    def require(self, key: str) -> str:
        value = self._secrets.get(key)
        if value:
            return value
        desc = self.all_known_keys.get(key, "Unknown key")
        raise ValueError(
            f"Required secret '{key}' not set. Description: {desc}. "
            f"Add it to runtime env, OS keyring, encrypted bundle, or {self._env_file}."
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

    def set_bundle_key(self, value: str, prefer_keyring: bool = True) -> str:
        return self.set_local("S25_SECRETS_BUNDLE_KEY", value, prefer_keyring=prefer_keyring)

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

    def bundle_status(self) -> Dict[str, object]:
        return {
            "path": str(self._bundle_path),
            "exists": self._bundle_path.exists(),
            "crypto_ready": Fernet is not None,
            "master_key_ready": self._bundle_fernet_key() is not None,
        }

    def write_bundle(self, include_optional: bool = True) -> str:
        if not Fernet:
            raise RuntimeError("cryptography is required for encrypted bundle support")
        fernet_key = self._bundle_fernet_key()
        if not fernet_key:
            raise RuntimeError("Missing S25_SECRETS_BUNDLE_KEY in keyring, env, or .env")

        payload = self.export_env_map(include_optional=include_optional)
        payload.pop("S25_SECRETS_BUNDLE_KEY", None)
        self._bundle_path.parent.mkdir(parents=True, exist_ok=True)
        token = Fernet(fernet_key).encrypt(json.dumps(payload, indent=2).encode("utf-8"))
        self._bundle_path.write_bytes(token)
        return str(self._bundle_path)

    def audit(self) -> Dict[str, object]:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_loaded": len(self._secrets),
            "bundle": self.bundle_status(),
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
            "bundle_ready": self.bundle_status()["exists"] and self.bundle_status()["master_key_ready"],
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
