"""
S25 Wallet Creator — unified mnemonic access with secure fallback chain.

Read path (in order):
  1. OS keyring (gnome-keyring / Credential Manager / Keychain) via `keyring` lib
  2. GCP Secret Manager (if google_secret_runtime configured)
  3. .env WALLET_MNEMONIC (legacy — emits deprecation warning)

CLI:
    python3 -m security.wallet_creator status     # show source + mask
    python3 -m security.wallet_creator migrate    # .env -> keyring (destructive on .env)
    python3 -m security.wallet_creator addresses  # derive cosmos1/osmo1/akash1
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional, Tuple

from .vault import get_vault, vault_get

logger = logging.getLogger("s25.wallet_creator")

_ALIASES = ("WALLET_MNEMONIC", "AKASH_MNEMONIC", "OSMOSIS_MNEMONIC", "S25_MASTER_SEED")


def get_mnemonic(required: bool = True) -> Optional[str]:
    """Return the 12/24-word BIP39 mnemonic for the S25 creator wallet.

    Tries every alias in order so we stay compatible with existing tools
    that hardcoded one of the legacy names.
    """
    for key in _ALIASES:
        value = vault_get(key, "")
        if value and len(value.split()) >= 12:
            source = get_vault()._sources.get(key, "unknown")
            if source == ".env":
                logger.warning(
                    "mnemonic loaded from .env plaintext (key=%s). "
                    "Run `python3 -m security.wallet_creator migrate` to move it to the OS keyring.",
                    key,
                )
            return value.strip()
    if required:
        raise RuntimeError(
            "No mnemonic found. Set one of %s in keyring, env, or .env" % (_ALIASES,)
        )
    return None


def get_source() -> Tuple[Optional[str], Optional[str]]:
    """Return (alias_used, source_backend) without exposing the mnemonic."""
    v = get_vault()
    for key in _ALIASES:
        if key in v._secrets:
            return key, v._sources.get(key, "unknown")
    return None, None


def derive_addresses() -> dict:
    """Derive cosmos1 / osmo1 / akash1 addresses from the creator mnemonic.

    Requires cosmpy. Returns empty dict if dependency missing.
    """
    try:
        from cosmpy.crypto.keypairs import PrivateKey
        from cosmpy.crypto.address import Address
        from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins
    except Exception as exc:
        return {"error": f"dependency missing: {exc}"}

    mnemonic = get_mnemonic()
    seed = Bip39SeedGenerator(mnemonic).Generate()
    out = {}
    try:
        cosmos = Bip44.FromSeed(seed, Bip44Coins.COSMOS).DeriveDefaultPath()
        out["cosmos1"] = cosmos.PublicKey().ToAddress()
    except Exception as e:
        out["cosmos1_err"] = str(e)
    try:
        akash = Bip44.FromSeed(seed, Bip44Coins.AKASH_NETWORK).DeriveDefaultPath()
        out["akash1"] = akash.PublicKey().ToAddress()
    except Exception as e:
        out["akash1_err"] = str(e)
    try:
        osmo = Bip44.FromSeed(seed, Bip44Coins.OSMOSIS).DeriveDefaultPath()
        out["osmo1"] = osmo.PublicKey().ToAddress()
    except Exception as e:
        out["osmo1_err"] = str(e)
    return out


def status() -> dict:
    alias, source = get_source()
    present = alias is not None
    return {
        "present": present,
        "alias": alias,
        "source": source,
        "insecure": source == ".env",
    }


def migrate_env_to_keyring() -> dict:
    """Move the mnemonic from .env into the OS keyring, then delete the .env line."""
    import keyring  # lazy — require the lib only when actually migrating
    vault = get_vault()
    alias_found = None
    for alias in _ALIASES:
        if alias in vault._secrets and vault._sources.get(alias) == ".env":
            alias_found = alias
            break
    if not alias_found:
        return {"ok": False, "reason": "no mnemonic found in .env (already migrated or absent)"}

    mnemonic = vault._secrets[alias_found]
    keyring.set_password(vault._service_name, alias_found, mnemonic)
    removed = vault.delete_local(alias_found)
    # reload .env minus the key
    vault.delete_local(alias_found)
    return {"ok": True, "alias": alias_found, "removed_from": removed, "moved_to": "keyring"}


def _cli():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "status":
        import json
        print(json.dumps(status(), indent=2))
    elif cmd == "migrate":
        import json
        print(json.dumps(migrate_env_to_keyring(), indent=2))
    elif cmd == "addresses":
        import json
        print(json.dumps(derive_addresses(), indent=2))
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli()
