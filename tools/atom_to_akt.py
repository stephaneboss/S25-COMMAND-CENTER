#!/usr/bin/env python3
"""
ATOM (cosmos1) -> AKT (akash1) auto-pipeline.

Steps:
  1. IBC transfer N ATOM from cosmos1 -> osmo1  (Cosmos Hub channel-141)
  2. Wait for ATOM-IBC to land on osmo1
  3. Swap ATOM-IBC -> AKT-IBC on Osmosis (route from sqs.osmosis.zone)
  4. IBC transfer AKT-IBC from osmo1 -> akash1 (Osmosis channel-1)
  5. Wait for native uakt on akash1

Same HD priv key derives all 3 addresses (cosmos1 / osmo1 / akash1).

Usage:
  PK=<hex_secp256k1_priv> ATOM_AMOUNT=2.0 python3 tools/atom_to_akt.py
  DRY_RUN=1 ... -> only print quote, no broadcast
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

from cosmpy.aerial.client import LedgerClient, NetworkConfig
from cosmpy.aerial.tx import SigningCfg, Transaction
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin
from cosmpy.protos.ibc.applications.transfer.v1.tx_pb2 import MsgTransfer
from cosmpy.protos.ibc.core.client.v1.client_pb2 import Height


# ---------------------------------------------------------------------------
# Raw protobuf encoder for Osmosis MsgSwapExactAmountIn
# (avoids the descriptor-pool conflict that osmosis-protobuf causes when
#  imported alongside cosmpy's bundled cosmos protos).
#
# Schema (from osmosis poolmanager/v1beta1/tx.proto):
#   message MsgSwapExactAmountIn {
#     string sender                              = 1;
#     repeated SwapAmountInRoute routes          = 2;
#     cosmos.base.v1beta1.Coin token_in          = 3;
#     string token_out_min_amount                = 4;
#   }
#   message SwapAmountInRoute {
#     uint64 pool_id          = 1;
#     string token_out_denom  = 2;
#   }
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


def _encode_coin(denom: str, amount: str) -> bytes:
    return _enc_string(1, denom) + _enc_string(2, amount)


def _encode_route(pool_id: int, token_out_denom: str) -> bytes:
    return _enc_uint64(1, pool_id) + _enc_string(2, token_out_denom)


def _encode_msg_swap_exact_amount_in(
    sender: str,
    routes: list,           # list[(pool_id:int, token_out_denom:str)]
    token_in_denom: str,
    token_in_amount: str,
    token_out_min_amount: str,
) -> bytes:
    body = _enc_string(1, sender)
    for pool_id, denom in routes:
        body += _enc_msg(2, _encode_route(pool_id, denom))
    body += _enc_msg(3, _encode_coin(token_in_denom, token_in_amount))
    body += _enc_string(4, token_out_min_amount)
    return body


class _RawProtoMsg:
    """Stub object that quacks like a protobuf Message for cosmpy's
    Transaction.add_message: exposes DESCRIPTOR.full_name + SerializeToString."""

    def __init__(self, type_url_no_slash: str, body: bytes):
        self._body = body
        self.DESCRIPTOR = type("D", (), {"full_name": type_url_no_slash})()

    def SerializeToString(self) -> bytes:  # noqa: N802 (proto API)
        return self._body

# ---------------------------------------------------------------------------
# Constants (mainnet, well-known)
# ---------------------------------------------------------------------------
HUB_LCD = "https://rest.cosmos.directory/cosmoshub"
OSMO_LCD = "https://rest.cosmos.directory/osmosis"
AKASH_LCD = "https://rest.cosmos.directory/akash"

ATOM_TO_OSMO_CHANNEL = "channel-141"  # Cosmos Hub -> Osmosis
OSMO_TO_AKASH_CHANNEL = "channel-1"   # Osmosis    -> Akash

ATOM_DENOM_NATIVE = "uatom"
ATOM_DENOM_ON_OSMO = "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
AKT_DENOM_ON_OSMO = "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E00EB64743EF4"
AKT_DENOM_NATIVE = "uakt"


def http_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def get_balance(lcd: str, addr: str, denom: str) -> int:
    """Query full balances and filter for `denom` (the by_denom path is not
    proxied by rest.cosmos.directory)."""
    try:
        data = http_json(f"{lcd}/cosmos/bank/v1beta1/balances/{addr}?pagination.limit=200")
        for entry in data.get("balances", []):
            if entry.get("denom") == denom:
                return int(entry.get("amount", "0"))
        return 0
    except Exception as e:
        print(f"   balance query failed ({denom[:20]}): {e}")
        return 0


def wait_for_balance(lcd: str, addr: str, denom: str, min_amount: int, label: str, timeout: int = 300) -> int:
    print(f"   waiting for >= {min_amount} {label} on {addr[:14]}...")
    t0 = time.time()
    last = -1
    while time.time() - t0 < timeout:
        bal = get_balance(lcd, addr, denom)
        if bal != last:
            print(f"     [{int(time.time()-t0):3d}s] {label}: {bal}")
            last = bal
        if bal >= min_amount:
            print(f"   OK {label} arrived: {bal}")
            return bal
        time.sleep(8)
    raise TimeoutError(f"Timeout waiting for {label} on {addr}")


def get_quote(amount_uatom: int) -> dict:
    url = (
        "https://sqs.osmosis.zone/router/quote"
        f"?tokenIn={amount_uatom}{ATOM_DENOM_ON_OSMO}"
        f"&tokenOutDenom={AKT_DENOM_ON_OSMO}"
    )
    return http_json(url)


def main() -> int:
    pk_hex = os.environ.get("PK", "").strip()
    mnemonic = os.environ.get("WALLET_MNEMONIC", "").strip()

    # Autoload from repo .env if neither is set in environment
    if not pk_hex and not mnemonic:
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
                        mnemonic = val
                    break

    if not pk_hex and not mnemonic:
        print(
            "ERROR: set WALLET_MNEMONIC (BIP39) in .env or env, "
            "or PK (hex secp256k1) env var",
            file=sys.stderr,
        )
        return 2

    atom_amount = float(os.environ.get("ATOM_AMOUNT", "2.0"))
    slippage = float(os.environ.get("SLIPPAGE", "0.02"))
    dry_run = os.environ.get("DRY_RUN", "0") == "1"

    if mnemonic:
        w_cosmos = LocalWallet.from_mnemonic(mnemonic, prefix="cosmos")
        w_osmo = LocalWallet.from_mnemonic(mnemonic, prefix="osmo")
        w_akash = LocalWallet.from_mnemonic(mnemonic, prefix="akash")
    else:
        priv = PrivateKey(bytes.fromhex(pk_hex))
        w_cosmos = LocalWallet(priv, prefix="cosmos")
        w_osmo = LocalWallet(priv, prefix="osmo")
        w_akash = LocalWallet(priv, prefix="akash")

    addr_cosmos = str(w_cosmos.address())
    addr_osmo = str(w_osmo.address())
    addr_akash = str(w_akash.address())

    print("=" * 60)
    print("S25 ATOM -> AKT pipeline")
    print("=" * 60)
    print(f"cosmos: {addr_cosmos}")
    print(f"osmo  : {addr_osmo}")
    print(f"akash : {addr_akash}")
    print(f"amount: {atom_amount} ATOM")
    print(f"slip  : {slippage*100:.1f}%")
    print(f"dry   : {dry_run}")

    bal_atom = get_balance(HUB_LCD, addr_cosmos, ATOM_DENOM_NATIVE)
    bal_osmo_uosmo = get_balance(OSMO_LCD, addr_osmo, "uosmo")
    bal_akash_uakt = get_balance(AKASH_LCD, addr_akash, AKT_DENOM_NATIVE)
    print("\nBalances:")
    print(f"  cosmos1 uatom: {bal_atom}")
    print(f"  osmo1   uosmo: {bal_osmo_uosmo}")
    print(f"  akash1  uakt : {bal_akash_uakt}")

    amount_uatom = int(atom_amount * 1_000_000)
    if bal_atom < amount_uatom + 5000:
        print(f"ERROR: cosmos1 has only {bal_atom} uatom, need >= {amount_uatom+5000}")
        return 3
    if bal_osmo_uosmo < 13000:
        print(f"WARN: osmo1 has only {bal_osmo_uosmo} uosmo (~$0.01).")
        print("      Need >= ~13000 uosmo to cover swap+IBC fees.")
        print("      Will attempt anyway; may fail if insufficient.")

    quote = get_quote(amount_uatom)
    out_amount = int(quote["amount_out"])
    impact = quote.get("price_impact", "?")
    spot = quote.get("in_base_out_quote_spot_price", "?")
    print(f"\nQuote: {amount_uatom} uatom -> {out_amount} uakt-on-osmo")
    print(f"  price impact: {impact}")
    print(f"  spot 1 ATOM = {spot} AKT")
    routes_data = quote["route"][0]["pools"]
    print(f"  route: {[(p['id'], p['token_out_denom'][:24]) for p in routes_data]}")

    if dry_run:
        print("\nDRY_RUN=1 -> stopping here.")
        return 0

    # ── Step 1: IBC ATOM cosmos1 -> osmo1 ─────────────────────────────────
    print("\n[1/4] IBC transfer ATOM cosmos1 -> osmo1")
    hub_cfg = NetworkConfig(
        chain_id="cosmoshub-4",
        url=f"rest+{HUB_LCD}",
        fee_minimum_gas_price=0.005,
        fee_denomination="uatom",
        staking_denomination="uatom",
    )
    hub_client = LedgerClient(hub_cfg)

    timeout_ns_1 = int((time.time() + 600) * 1e9)
    msg_ibc1 = MsgTransfer(
        source_port="transfer",
        source_channel=ATOM_TO_OSMO_CHANNEL,
        token=Coin(denom=ATOM_DENOM_NATIVE, amount=str(amount_uatom)),
        sender=addr_cosmos,
        receiver=addr_osmo,
        timeout_height=Height(revision_number=0, revision_height=0),
        timeout_timestamp=timeout_ns_1,
        memo="S25-atom-to-akt",
    )

    acct = hub_client.query_account(addr_cosmos)
    print(f"   hub account number={acct.number} sequence={acct.sequence}")

    tx1 = Transaction()
    tx1.add_message(msg_ibc1)
    tx1.seal(SigningCfg.direct(w_cosmos.public_key(), acct.sequence), fee="5000uatom", gas_limit=200_000)
    tx1.sign(w_cosmos.signer(), "cosmoshub-4", acct.number)
    tx1.complete()

    resp1 = hub_client.broadcast_tx(tx1)
    print(f"   tx hash: {resp1.tx_hash}")
    resp1.wait_to_complete()
    print("   OK broadcast complete")

    # Wait for IBC arrival on osmo1
    pre_atom_osmo = get_balance(OSMO_LCD, addr_osmo, ATOM_DENOM_ON_OSMO)
    expected_atom_on_osmo = int(amount_uatom * 0.999)
    wait_for_balance(
        OSMO_LCD, addr_osmo, ATOM_DENOM_ON_OSMO,
        pre_atom_osmo + expected_atom_on_osmo, "ATOM-IBC", timeout=300,
    )

    # ── Step 2: Swap ATOM-IBC -> AKT-IBC on Osmosis ───────────────────────
    print("\n[2/4] Osmosis swap ATOM-IBC -> AKT-IBC")
    osmo_cfg = NetworkConfig(
        chain_id="osmosis-1",
        url=f"rest+{OSMO_LCD}",
        fee_minimum_gas_price=0.0025,
        fee_denomination="uosmo",
        staking_denomination="uosmo",
    )
    osmo_client = LedgerClient(osmo_cfg)

    quote2 = get_quote(amount_uatom)
    out_amount2 = int(quote2["amount_out"])
    pools2 = quote2["route"][0]["pools"]
    routes_tuples = [(int(p["id"]), p["token_out_denom"]) for p in pools2]
    min_out = int(out_amount2 * (1 - slippage))
    print(f"   route: {[(pid, d[:24]) for pid, d in routes_tuples]}")
    print(f"   expected: {out_amount2} uakt-on-osmo, min_out={min_out}")

    swap_body = _encode_msg_swap_exact_amount_in(
        sender=addr_osmo,
        routes=routes_tuples,
        token_in_denom=ATOM_DENOM_ON_OSMO,
        token_in_amount=str(amount_uatom),
        token_out_min_amount=str(min_out),
    )
    msg_swap = _RawProtoMsg(
        "osmosis.poolmanager.v1beta1.MsgSwapExactAmountIn", swap_body,
    )

    acct_o = osmo_client.query_account(addr_osmo)
    tx2 = Transaction()
    tx2.add_message(msg_swap)
    tx2.seal(SigningCfg.direct(w_osmo.public_key(), acct_o.sequence), fee="6250uosmo", gas_limit=500_000)
    tx2.sign(w_osmo.signer(), "osmosis-1", acct_o.number)
    tx2.complete()
    resp2 = osmo_client.broadcast_tx(tx2)
    print(f"   tx hash: {resp2.tx_hash}")
    resp2.wait_to_complete()
    print("   OK swap complete")

    # ── Step 3: IBC AKT-IBC -> akash1 ─────────────────────────────────────
    print("\n[3/4] IBC transfer AKT-IBC osmo1 -> akash1")
    akt_on_osmo = wait_for_balance(
        OSMO_LCD, addr_osmo, AKT_DENOM_ON_OSMO, min_out,
        "AKT-IBC on Osmosis", timeout=120,
    )

    timeout_ns_2 = int((time.time() + 600) * 1e9)
    msg_ibc2 = MsgTransfer(
        source_port="transfer",
        source_channel=OSMO_TO_AKASH_CHANNEL,
        token=Coin(denom=AKT_DENOM_ON_OSMO, amount=str(akt_on_osmo)),
        sender=addr_osmo,
        receiver=addr_akash,
        timeout_height=Height(revision_number=0, revision_height=0),
        timeout_timestamp=timeout_ns_2,
        memo="S25-atom-to-akt",
    )

    acct_o2 = osmo_client.query_account(addr_osmo)
    tx3 = Transaction()
    tx3.add_message(msg_ibc2)
    tx3.seal(SigningCfg.direct(w_osmo.public_key(), acct_o2.sequence), fee="6250uosmo", gas_limit=250_000)
    tx3.sign(w_osmo.signer(), "osmosis-1", acct_o2.number)
    tx3.complete()
    resp3 = osmo_client.broadcast_tx(tx3)
    print(f"   tx hash: {resp3.tx_hash}")
    resp3.wait_to_complete()
    print("   OK broadcast complete")

    # ── Step 4: Wait for native uakt on akash1 ────────────────────────────
    print("\n[4/4] Waiting for native uakt on akash1...")
    pre_uakt = bal_akash_uakt
    final = wait_for_balance(
        AKASH_LCD, addr_akash, AKT_DENOM_NATIVE,
        pre_uakt + int(akt_on_osmo * 0.99), "uakt on Akash", timeout=300,
    )

    print()
    print("=" * 60)
    print(f"DONE. akash1 balance: {final} uakt ({final/1e6:.4f} AKT)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
