#!/usr/bin/env python3

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Dict, Tuple

try:
    from google.cloud import secretmanager
except Exception:  # pragma: no cover
    secretmanager = None


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
