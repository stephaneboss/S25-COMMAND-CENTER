#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
from typing import Dict, Tuple

try:
    from google.cloud import secretmanager
except Exception:  # pragma: no cover
    secretmanager = None


DEFAULT_SECRET_MAP = {
    "S25_SHARED_SECRET": "s25-shared-secret",
    "GEMINI_API_KEY": "gemini-api-key",
    "MEXC_API_KEY": "mexc-api-key",
    "MEXC_SECRET_KEY": "mexc-secret-key",
}


def materialize_adc_file(path: Path) -> Tuple[bool, str]:
    if path.exists():
        return True, str(path)
    payload_b64 = os.getenv("GOOGLE_ADC_JSON_B64", "").strip()
    if not payload_b64:
        return False, "adc_missing"
    raw = base64.b64decode(payload_b64.encode("utf-8"))
    path.write_bytes(raw)
    return True, str(path)


def build_client() -> "secretmanager.SecretManagerServiceClient":
    if secretmanager is None:
        raise RuntimeError("google-cloud-secret-manager dependency missing")
    return secretmanager.SecretManagerServiceClient()


def access_secret(
    client: "secretmanager.SecretManagerServiceClient",
    project_id: str,
    secret_name: str,
    version: str = "latest",
) -> str:
    resource = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
    response = client.access_secret_version(request={"name": resource})
    return response.payload.data.decode("utf-8")


def load_secret_bundle(project_id: str, secret_map: Dict[str, str]) -> Dict[str, str]:
    client = build_client()
    bundle: Dict[str, str] = {}
    for env_name, secret_name in secret_map.items():
        bundle[env_name] = access_secret(client, project_id, secret_name)
    return bundle


def parse_secret_map(raw: str | None) -> Dict[str, str]:
    if not raw:
        return dict(DEFAULT_SECRET_MAP)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("secret map must be a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def render_env(bundle: Dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in sorted(bundle.items())) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap secrets from Google Secret Manager for S25 mirror containers")
    parser.add_argument("--project-id", default=os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    parser.add_argument("--secret-map-json", default=os.getenv("S25_GSM_SECRET_MAP_JSON", ""))
    parser.add_argument("--output", default="")
    parser.add_argument("--adc-path", default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/google-adc.json"))
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.project_id:
        print(json.dumps({"ok": False, "error": "google_cloud_project_missing"}, indent=2))
        return 1

    adc_path = Path(args.adc_path)
    adc_ready, adc_detail = materialize_adc_file(adc_path)
    if adc_ready:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = adc_detail

    secret_map = parse_secret_map(args.secret_map_json)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "dry_run",
                    "project_id": args.project_id,
                    "adc_ready": adc_ready,
                    "adc_detail": adc_detail,
                    "secret_map": secret_map,
                },
                indent=2,
            )
        )
        return 0

    bundle = load_secret_bundle(args.project_id, secret_map)
    rendered = render_env(bundle)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "project_id": args.project_id,
                "adc_ready": adc_ready,
                "adc_detail": adc_detail,
                "keys_loaded": sorted(bundle.keys()),
                "output": args.output or None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
