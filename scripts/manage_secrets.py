#!/usr/bin/env python3

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.vault import S25Vault


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage S25 secrets")
    parser.add_argument("--env-file", default=".env", help="Env file fallback path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audit", help="Show masked audit report")
    sub.add_parser("doctor", help="Show missing keys and operator guidance")

    status_cmd = sub.add_parser("status", help="Show one key status")
    status_cmd.add_argument("key")

    set_cmd = sub.add_parser("set", help="Store a secret locally")
    set_cmd.add_argument("key")
    set_cmd.add_argument("--value")
    set_cmd.add_argument("--no-keyring", action="store_true")

    bundle_key_cmd = sub.add_parser("set-bundle-key", help="Store bundle master key")
    bundle_key_cmd.add_argument("--value")
    bundle_key_cmd.add_argument("--no-keyring", action="store_true")

    delete_cmd = sub.add_parser("delete", help="Delete a secret from local stores")
    delete_cmd.add_argument("key")

    export_cmd = sub.add_parser("export", help="Export env lines for runtime injection")
    export_cmd.add_argument("--include-optional", action="store_true")

    sub.add_parser("bundle-status", help="Show encrypted bundle readiness")
    write_bundle_cmd = sub.add_parser("write-bundle", help="Write encrypted sync bundle")
    write_bundle_cmd.add_argument("--include-optional", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    vault = S25Vault(env_file=args.env_file)

    if args.command == "audit":
        print(json.dumps(vault.audit(), indent=2))
        return 0

    if args.command == "doctor":
        audit = vault.audit()
        print("# S25 Secret Doctor")
        print("")
        print("Missing required:")
        for key in audit["missing_required"]:
            print(f"- {key}")
        print("")
        print("Missing trading:")
        for key in audit["missing_trading"]:
            print(f"- {key}")
        print("")
        print("Recommended order:")
        print("1. Store local operator secrets in OS keyring")
        print("2. Inject runtime secrets into Akash and GitHub as env vars")
        print("3. Keep .env only as local fallback")
        return 0

    if args.command == "status":
        print(
            json.dumps(
                {
                    "key": args.key,
                    "present": vault.has(args.key),
                    "source": vault.source(args.key),
                    "masked": vault.mask(args.key),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "set":
        value = args.value or getpass.getpass(f"Value for {args.key}: ")
        source = vault.set_local(args.key, value, prefer_keyring=not args.no_keyring)
        print(json.dumps({"ok": True, "key": args.key, "stored_in": source}, indent=2))
        return 0

    if args.command == "set-bundle-key":
        value = args.value or getpass.getpass("Bundle master key: ")
        source = vault.set_bundle_key(value, prefer_keyring=not args.no_keyring)
        print(json.dumps({"ok": True, "stored_in": source}, indent=2))
        return 0

    if args.command == "delete":
        removed = vault.delete_local(args.key)
        print(json.dumps({"ok": True, "key": args.key, "removed_from": removed}, indent=2))
        return 0

    if args.command == "export":
        for key, value in vault.export_env_map(include_optional=args.include_optional).items():
            print(f"{key}={value}")
        return 0

    if args.command == "bundle-status":
        print(json.dumps(vault.bundle_status(), indent=2))
        return 0

    if args.command == "write-bundle":
        path = vault.write_bundle(include_optional=args.include_optional)
        print(json.dumps({"ok": True, "path": path}, indent=2))
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
