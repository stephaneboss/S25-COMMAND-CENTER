#!/usr/bin/env python3
"""
S25 Treasury auto-refuel orchestrator.

Goal: keep akash1 funded with real uakt so container cleanup + redeploys
never get blocked by gas. Chains:

  1. check akash1 uakt balance
  2. if < MIN_UAKT -> swap ATOM (cosmos1) -> AKT (akash1) via atom_to_akt.py
  3. once funded -> close ghost DSEQs via akash_cleanup_ghosts.py

Reads WALLET_MNEMONIC from env or ../.env.

Usage:
  DRY_RUN=1 python3 tools/treasury_autorefuel.py
  python3 tools/treasury_autorefuel.py
  NO_CLEANUP=1 python3 tools/treasury_autorefuel.py  # swap only
  NO_SWAP=1 python3 tools/treasury_autorefuel.py     # cleanup only

Env:
  WALLET_MNEMONIC   BIP39 phrase (required)
  MIN_UAKT          threshold below which we refuel (default 1_500_000 = 1.5 AKT)
  REFUEL_ATOM       ATOM to swap if below threshold (default 1.0)
  DRY_RUN           1 = no broadcast, just plan
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SWAP_SCRIPT = os.path.join(HERE, "atom_to_akt.py")
CLEANUP_SCRIPT = os.path.join(HERE, "akash_cleanup_ghosts.py")

AKASH_LCD = "https://akash-rest.publicnode.com"
HUB_LCD = "https://cosmos-rest.publicnode.com"


def load_mnemonic() -> str:
    mnemonic = os.environ.get("WALLET_MNEMONIC", "").strip()
    if mnemonic:
        return mnemonic
    env_path = os.path.join(REPO, ".env")
    if os.path.isfile(env_path):
        for line in open(env_path):
            line = line.strip()
            if line.startswith("WALLET_MNEMONIC="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    return ""


def http_json(url: str) -> dict:
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "curl/8"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def get_balance(lcd: str, addr: str, denom: str) -> int:
    try:
        data = http_json(
            f"{lcd}/cosmos/bank/v1beta1/balances/{addr}?pagination.limit=200"
        )
        for entry in data.get("balances", []):
            if entry.get("denom") == denom:
                return int(entry.get("amount", "0"))
        return 0
    except Exception as e:
        print(f"   balance query failed ({denom[:12]}): {e}")
        return 0


def derive_addresses(mnemonic: str) -> tuple[str, str, str]:
    from cosmpy.aerial.wallet import LocalWallet

    w_cosmos = LocalWallet.from_mnemonic(mnemonic, prefix="cosmos")
    w_osmo = LocalWallet.from_mnemonic(mnemonic, prefix="osmo")
    w_akash = LocalWallet.from_mnemonic(mnemonic, prefix="akash")
    return str(w_cosmos.address()), str(w_osmo.address()), str(w_akash.address())


def run(cmd: list, env: dict) -> int:
    print(f"\n>>> {' '.join(cmd)}")
    return subprocess.call(cmd, env=env)


def main() -> int:
    mnemonic = load_mnemonic()
    if not mnemonic:
        print("ERROR: WALLET_MNEMONIC not set in env or .env", file=sys.stderr)
        return 2

    min_uakt = int(os.environ.get("MIN_UAKT", "1500000"))
    refuel_atom = float(os.environ.get("REFUEL_ATOM", "1.0"))
    dry_run = os.environ.get("DRY_RUN", "0") == "1"
    no_swap = os.environ.get("NO_SWAP", "0") == "1"
    no_cleanup = os.environ.get("NO_CLEANUP", "0") == "1"

    try:
        addr_cosmos, addr_osmo, addr_akash = derive_addresses(mnemonic)
    except Exception as e:
        print(f"ERROR: mnemonic invalid or cosmpy missing: {e}", file=sys.stderr)
        return 2

    print("=" * 60)
    print("S25 Treasury auto-refuel")
    print("=" * 60)
    print(f"cosmos   : {addr_cosmos}")
    print(f"osmo     : {addr_osmo}")
    print(f"akash    : {addr_akash}")
    print(f"min_uakt : {min_uakt} ({min_uakt/1e6:.3f} AKT)")
    print(f"refuel   : {refuel_atom} ATOM")
    print(f"dry_run  : {dry_run}")

    uakt_before = get_balance(AKASH_LCD, addr_akash, "uakt")
    atom_before = get_balance(HUB_LCD, addr_cosmos, "uatom")
    print(f"\nakash1 uakt  : {uakt_before} ({uakt_before/1e6:.6f} AKT)")
    print(f"cosmos1 uatom: {atom_before} ({atom_before/1e6:.6f} ATOM)")

    # ---- step 1: swap if under threshold ----------------------------------
    if no_swap:
        print("\n[swap] NO_SWAP=1 -> skipped")
    elif uakt_before >= min_uakt:
        print(f"\n[swap] uakt >= min_uakt, no swap needed")
    else:
        need_uatom = int(refuel_atom * 1_000_000) + 5000
        if atom_before < need_uatom:
            print(
                f"\nERROR: cosmos1 has {atom_before} uatom, need >= {need_uatom}",
                file=sys.stderr,
            )
            return 3
        env = {
            **os.environ,
            "WALLET_MNEMONIC": mnemonic,
            "ATOM_AMOUNT": str(refuel_atom),
            "DRY_RUN": "1" if dry_run else "0",
        }
        rc = run(["python3", SWAP_SCRIPT], env)
        if rc != 0:
            print(f"\nERROR: swap script exited {rc}", file=sys.stderr)
            return rc

    # ---- step 2: cleanup ghost DSEQs --------------------------------------
    if no_cleanup:
        print("\n[cleanup] NO_CLEANUP=1 -> skipped")
        return 0

    uakt_after = get_balance(AKASH_LCD, addr_akash, "uakt")
    print(f"\nakash1 uakt after swap: {uakt_after}")

    if not dry_run and uakt_after < 30000:
        print(
            "WARN: uakt still under 30000, skipping cleanup (not enough for 6 closures)",
            file=sys.stderr,
        )
        return 0

    env = {
        **os.environ,
        "WALLET_MNEMONIC": mnemonic,
        "DRY_RUN": "1" if dry_run else "0",
    }
    rc = run(["python3", CLEANUP_SCRIPT], env)
    if rc != 0:
        print(f"\nWARN: cleanup exited {rc}", file=sys.stderr)

    # ---- summary ----------------------------------------------------------
    uakt_final = get_balance(AKASH_LCD, addr_akash, "uakt")
    atom_final = get_balance(HUB_LCD, addr_cosmos, "uatom")
    print("\n" + "=" * 60)
    print("Auto-refuel done")
    print(f"  uakt : {uakt_before} -> {uakt_final}")
    print(f"  uatom: {atom_before} -> {atom_final}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
