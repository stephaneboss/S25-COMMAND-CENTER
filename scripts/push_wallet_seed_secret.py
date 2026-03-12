#!/usr/bin/env python3

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import List

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import secretmanager
from google.iam.v1 import iam_policy_pb2, policy_pb2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.vault import vault_get


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Push the S25 wallet creator seed into Google Secret Manager")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--secret-id", default="s25-master-seed")
    parser.add_argument(
        "--service-account",
        action="append",
        default=[],
        help="Service account email allowed to access this secret. Repeatable.",
    )
    parser.add_argument("--seed")
    parser.add_argument("--from-vault-key", default="S25_MASTER_SEED")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def resolve_seed(args: argparse.Namespace) -> str:
    if args.seed:
        return args.seed.strip()
    from_vault = vault_get(args.from_vault_key, "") or ""
    if from_vault.strip():
        return from_vault.strip()
    return getpass.getpass("Wallet creator seed phrase: ").strip()


def ensure_secret(client: secretmanager.SecretManagerServiceClient, project_id: str, secret_id: str) -> str:
    parent = f"projects/{project_id}"
    secret_name = f"{parent}/secrets/{secret_id}"
    try:
        client.get_secret(request={"name": secret_name})
        return secret_name
    except NotFound:
        pass
    try:
        secret = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        return secret.name
    except AlreadyExists:
        return secret_name


def add_version(client: secretmanager.SecretManagerServiceClient, secret_name: str, seed: str) -> str:
    version = client.add_secret_version(
        request={
            "parent": secret_name,
            "payload": {"data": seed.encode("utf-8")},
        }
    )
    return version.name


def normalize_member(raw: str) -> str:
    value = raw.strip()
    if ":" in value:
      return value
    if value.endswith(".gserviceaccount.com"):
        return f"serviceAccount:{value}"
    return f"user:{value}"


def bind_accessors(client: secretmanager.SecretManagerServiceClient, secret_name: str, service_accounts: List[str]) -> List[str]:
    if not service_accounts:
        return []
    policy = client.get_iam_policy(request=iam_policy_pb2.GetIamPolicyRequest(resource=secret_name))
    members = [normalize_member(email) for email in service_accounts]
    existing_binding = None
    for binding in policy.bindings:
        if binding.role == "roles/secretmanager.secretAccessor":
            existing_binding = binding
            break
    if existing_binding is None:
        existing_binding = policy.bindings.add(role="roles/secretmanager.secretAccessor")
    for member in members:
        if member not in existing_binding.members:
            existing_binding.members.append(member)
    client.set_iam_policy(
        request=iam_policy_pb2.SetIamPolicyRequest(
            resource=secret_name,
            policy=policy_pb2.Policy(bindings=policy.bindings, etag=policy.etag, version=policy.version),
        )
    )
    return members


def main() -> int:
    args = build_parser().parse_args()
    seed = resolve_seed(args)
    if not seed:
        print(json.dumps({"ok": False, "error": "seed_missing"}, indent=2))
        return 1

    summary = {
        "ok": True,
        "project_id": args.project_id,
        "secret_id": args.secret_id,
        "service_accounts": args.service_account,
        "seed_chars": len(seed),
        "from_vault_key": args.from_vault_key,
    }
    if args.dry_run:
        summary["mode"] = "dry_run"
        print(json.dumps(summary, indent=2))
        return 0

    client = secretmanager.SecretManagerServiceClient()
    secret_name = ensure_secret(client, args.project_id, args.secret_id)
    version_name = add_version(client, secret_name, seed)
    bound_members = bind_accessors(client, secret_name, args.service_account)

    summary.update(
        {
            "mode": "applied",
            "secret_name": secret_name,
            "version_name": version_name,
            "bound_members": bound_members,
        }
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
