#!/usr/bin/env python3
"""
Close dead/ghost Akash DSEQs using the S25 wallet mnemonic.

Reads WALLET_MNEMONIC from env or ../.env, signs MsgCloseDeployment via
cosmpy raw protobuf (bypasses akash CLI keyring entirely), and broadcasts
to akashnet-2. Skips DSEQs already closed.

Usage:
  DRY_RUN=1 python3 tools/akash_cleanup_ghosts.py
  python3 tools/akash_cleanup_ghosts.py            # real broadcast
  python3 tools/akash_cleanup_ghosts.py 25822281 26028154 ...  # override list
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

from cosmpy.aerial.client import LedgerClient, NetworkConfig
from cosmpy.aerial.tx import SigningCfg, Transaction
from cosmpy.aerial.wallet import LocalWallet

AKASH_LCD = "https://akash-rest.publicnode.com"
CHAIN_ID = "akashnet-2"

# Ghost DSEQs from docs/WORKSTREAM_BOARD.md (2026-04-14 audit)
DEFAULT_GHOSTS = [
    25878071,  # merlin-mesh (provider 404)
    25822281,  # provider akash1v4m...yykk dead
    26028154,  # jjozzietech ghost (HA nabu.casa expired)
    26034859,  # jjozzietech doublon
    26128127,  # antonaccimattia 502
    26129577,  # lease CLOSED but deployment still active
]

# ---------------------------------------------------------------------------
# Raw protobuf encoder for akash.deployment.v1beta3.MsgCloseDeployment
#   message MsgCloseDeployment { DeploymentID id = 1; }
#   message DeploymentID { string owner = 1; uint64 dseq = 2; }
# ---------------------------------------------------------------------------
def _varint(n: int) -> bytes:
    out = bytearray()
    while n > 0x7F:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n & 0x7F)
    return bytes(out)


def _tag(field: int, wire: int) -> bytes:
    return _varint((field << 3) | wire)


def _enc_string(field: int, s: str) -> bytes:
    b = s.encode("utf-8")
    return _tag(field, 2) + _varint(len(b)) + b


def _enc_uint64(field: int, n: int) -> bytes:
    return _tag(field, 0) + _varint(n)


def _enc_msg(field: int, body: bytes) -> bytes:
    return _tag(field, 2) + _varint(len(body)) + body


def _encode_msg_close_deployment(owner: str, dseq: int) -> bytes:
    deployment_id = _enc_string(1, owner) + _enc_uint64(2, dseq)
    return _enc_msg(1, deployment_id)


class _RawProtoMsg:
    def __init__(self, type_url_no_slash: str, body: bytes):
        self._body = body
        self.DESCRIPTOR = type("D", (), {"full_name": type_url_no_slash})()

    def SerializeToString(self) -> bytes:  # noqa: N802
        return self._body


# ---------------------------------------------------------------------------
def load_mnemonic() -> str:
    # --- creator-route: unified mnemonic lookup ---
    try:
        from security.wallet_creator import get_mnemonic as _s25_get_mnemonic
        mnemonic = _s25_get_mnemonic(required=False) or ''
    except Exception:
        mnemonic = ''
    # legacy fallback (keeps .env + ../.env scan) if creator returned empty
    if not mnemonic:
        mnemonic = os.environ.get("WALLET_MNEMONIC", "").strip()
        if mnemonic:
            return mnemonic
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env",
        )
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


def get_deployment_state(owner: str, dseq: int) -> str:
    """Return 'active', 'closed', or 'not_found'."""
    try:
        url = (
            f"{AKASH_LCD}/akash/deployment/v1beta3/deployments/info"
            f"?id.owner={owner}&id.dseq={dseq}"
        )
        data = http_json(url)
        state = data.get("deployment", {}).get("deployment", {}).get("state", "")
        if state == "active":
            return "active"
        if state in ("closed", "closed_insufficient_funds"):
            return "closed"
        return state or "not_found"
    except Exception as e:
        return f"err:{e}"


def get_uakt_balance(addr: str) -> int:
    try:
        data = http_json(
            f"{AKASH_LCD}/cosmos/bank/v1beta1/balances/{addr}?pagination.limit=50"
        )
        for entry in data.get("balances", []):
            if entry.get("denom") == "uakt":
                return int(entry.get("amount", "0"))
        return 0
    except Exception:
        return 0


def main() -> int:
    mnemonic = load_mnemonic()
    if not mnemonic:
        print("ERROR: WALLET_MNEMONIC not set in env or .env", file=sys.stderr)
        return 2

    dry_run = os.environ.get("DRY_RUN", "0") == "1"
    targets = [int(x) for x in sys.argv[1:]] or DEFAULT_GHOSTS

    wallet = LocalWallet.from_mnemonic(mnemonic, prefix="akash")
    owner = str(wallet.address())

    print("=" * 60)
    print("S25 Akash ghost DSEQ cleanup")
    print("=" * 60)
    print(f"owner : {owner}")
    print(f"dry   : {dry_run}")

    uakt = get_uakt_balance(owner)
    print(f"uakt  : {uakt} ({uakt/1e6:.6f} AKT)")

    need_per_tx = 5000  # fee per close
    need_total = need_per_tx * len(targets) + 10000  # + margin
    if not dry_run and uakt < need_total:
        print(
            f"ERROR: need >= {need_total} uakt for {len(targets)} closures, "
            f"have {uakt}. Run treasury_autorefuel.py first.",
            file=sys.stderr,
        )
        return 3

    # Prefilter: skip already-closed
    print("\nPrefilter DSEQ states:")
    active_targets = []
    for dseq in targets:
        state = get_deployment_state(owner, dseq)
        marker = "OK" if state == "active" else "--"
        print(f"  [{marker}] {dseq}: {state}")
        if state == "active":
            active_targets.append(dseq)

    if not active_targets:
        print("\nNothing to close.")
        return 0

    if dry_run:
        print(f"\nDRY_RUN=1 -> would close {len(active_targets)} DSEQ(s): {active_targets}")
        return 0

    cfg = NetworkConfig(
        chain_id=CHAIN_ID,
        url=f"rest+{AKASH_LCD}",
        fee_minimum_gas_price=0.025,
        fee_denomination="uakt",
        staking_denomination="uakt",
    )
    client = LedgerClient(cfg)
    acct = client.query_account(owner)
    seq = acct.sequence

    results = []
    for dseq in active_targets:
        print(f"\n[close] DSEQ={dseq}")
        body = _encode_msg_close_deployment(owner, dseq)
        msg = _RawProtoMsg("akash.deployment.v1beta3.MsgCloseDeployment", body)
        tx = Transaction()
        tx.add_message(msg)
        tx.seal(
            SigningCfg.direct(wallet.public_key(), seq),
            fee=f"{need_per_tx}uakt",
            gas_limit=200_000,
        )
        tx.sign(wallet.signer(), CHAIN_ID, acct.number)
        tx.complete()
        try:
            resp = client.broadcast_tx(tx)
            print(f"   tx: {resp.tx_hash}")
            resp.wait_to_complete()
            print("   OK closed")
            results.append((dseq, "ok", resp.tx_hash))
        except Exception as e:
            print(f"   FAIL: {e}")
            results.append((dseq, "fail", str(e)))
        seq += 1
        time.sleep(2)

    print("\n" + "=" * 60)
    print("Cleanup summary:")
    for dseq, status, info in results:
        print(f"  {dseq}: {status}  {info[:50]}")
    print("=" * 60)
    ok = sum(1 for _, s, _ in results if s == "ok")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
