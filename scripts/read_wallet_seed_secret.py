#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.google_secret_runtime import access_secret, build_client, materialize_adc_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read the S25 wallet creator seed from Google Secret Manager")
    parser.add_argument("--project-id", default=os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    parser.add_argument("--secret-id", default="s25-master-seed")
    parser.add_argument("--version", default="latest")
    parser.add_argument("--adc-path", default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/google-adc.json"))
    parser.add_argument("--format", choices=("summary", "env", "raw"), default="summary")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.project_id:
        print(json.dumps({"ok": False, "error": "google_cloud_project_missing"}, indent=2))
        return 1

    adc_ready, adc_detail = materialize_adc_file(Path(args.adc_path))
    if adc_ready:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = adc_detail

    client = build_client()
    value = access_secret(client, args.project_id, args.secret_id, version=args.version)

    if args.format == "raw":
        print(value)
        return 0
    if args.format == "env":
        print(f"S25_MASTER_SEED={value}")
        return 0

    masked = value[:4] + "..." + value[-4:] if len(value) >= 8 else "****"
    print(
        json.dumps(
            {
                "ok": True,
                "project_id": args.project_id,
                "secret_id": args.secret_id,
                "version": args.version,
                "adc_ready": adc_ready,
                "adc_detail": adc_detail,
                "chars": len(value),
                "masked": masked,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
