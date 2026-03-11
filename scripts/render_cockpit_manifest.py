#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.vault import S25Vault


REQUIRED_KEYS = ("HA_TOKEN", "S25_SHARED_SECRET")
OPTIONAL_KEYS = ("GEMINI_API_KEY",)


def normalize_secret(key: str, value: str) -> str:
    cleaned = value.strip()
    if "\r" in cleaned or "\n" in cleaned:
        raise ValueError(f"{key} contains line breaks; re-store it cleanly in the vault")
    return cleaned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Akash cockpit manifest with secrets from the S25 vault")
    parser.add_argument(
        "--template",
        default=str(ROOT / "akash" / "deploy_cockpit.yaml"),
        help="Source YAML manifest template",
    )
    parser.add_argument(
        "--output",
        help="Output YAML path. Defaults to a temp file outside the repo.",
    )
    parser.add_argument("--env-file", default=".env", help="Fallback env file path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    vault = S25Vault(env_file=args.env_file)

    missing = [key for key in REQUIRED_KEYS if not vault.has(key)]
    if missing:
        print(f"Missing required secrets: {', '.join(missing)}", file=sys.stderr)
        return 1

    template_path = Path(args.template)
    payload = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    env_items = payload["services"]["s25-cockpit"]["env"]

    env_map: dict[str, str] = {}
    for item in env_items:
        key, _, value = item.partition("=")
        env_map[key] = value

    for key in REQUIRED_KEYS:
        env_map[key] = normalize_secret(key, vault.require(key))

    for key in OPTIONAL_KEYS:
        if vault.has(key):
            env_map[key] = normalize_secret(key, vault.require(key))

    payload["services"]["s25-cockpit"]["env"] = [f"{key}={value}" for key, value in env_map.items()]

    output_path = Path(args.output) if args.output else Path(tempfile.gettempdir()) / "s25-cockpit.rendered.yaml"
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
