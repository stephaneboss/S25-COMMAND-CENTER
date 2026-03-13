#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

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


def replace_env_line(text: str, key: str, value: str) -> str:
    marker = f"      - {key}="
    replacement = f"{marker}{value}"
    lines = text.splitlines()
    updated = []
    replaced = False
    for line in lines:
        if line.startswith(marker):
            updated.append(replacement)
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        raise ValueError(f"Could not find env line for {key} in template")
    return "\n".join(updated) + "\n"


def replace_image(text: str, image: str) -> str:
    marker = "    image: "
    lines = text.splitlines()
    updated = []
    replaced = False
    for line in lines:
        if line.startswith(marker):
            updated.append(f"{marker}{image}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        raise ValueError("Could not find image line in template")
    return "\n".join(updated) + "\n"


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
    parser.add_argument("--image", help="Override container image reference")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    vault = S25Vault(env_file=args.env_file)

    missing = [key for key in REQUIRED_KEYS if not vault.has(key)]
    if missing:
        print(f"Missing required secrets: {', '.join(missing)}", file=sys.stderr)
        return 1

    template_path = Path(args.template)
    rendered = template_path.read_text(encoding="utf-8").replace("\r\n", "\n")

    if args.image:
        rendered = replace_image(rendered, args.image.strip())

    for key in REQUIRED_KEYS:
        rendered = replace_env_line(rendered, key, normalize_secret(key, vault.require(key)))

    for key in OPTIONAL_KEYS:
        if vault.has(key):
            rendered = replace_env_line(rendered, key, normalize_secret(key, vault.require(key)))

    output_path = Path(args.output) if args.output else Path(tempfile.gettempdir()) / "s25-cockpit.rendered.yaml"
    output_path.write_text(rendered, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
