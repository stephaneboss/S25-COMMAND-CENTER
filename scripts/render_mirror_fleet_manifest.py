#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.vault import vault_get


def parse_cpu_units(value: str) -> float:
    return float(str(value).strip())


def build_service(name: str, image: str, env_map: Dict[str, str], cpu: str, memory: str, storage: str, price_uakt: int) -> Dict[str, Any]:
    return {
        "image": image,
        "env": [f"{key}={value}" for key, value in env_map.items()],
        "profiles": {
            "compute": {
                name: {
                    "resources": {
                        "cpu": {"units": parse_cpu_units(cpu)},
                        "memory": {"size": memory},
                        "storage": {"size": storage},
                    }
                }
            },
            "placement": {
                "akash": {
                    "pricing": {
                        name: {
                            "denom": "uakt",
                            "amount": price_uakt,
                        }
                    }
                }
            },
        },
        "deployment": {
            name: {
                "akash": {
                    "profile": name,
                    "count": 1,
                }
            }
        },
    }


def merge_sections(payload: Dict[str, Any], section: str, value: Dict[str, Any]) -> None:
    payload.setdefault(section, {})
    payload[section].update(value)


def build_manifest(config: Dict[str, Any], use_live_shared_secret: bool = False) -> Dict[str, Any]:
    fleet_name = config["fleet_name"]
    image = config["image"]
    cockpit_url = config["cockpit_url"]
    public_mcp_url = config["public_mcp_url"]
    project_id = config["google_cloud_project"]
    workspace_admin_email = config.get("workspace_admin_email", "admin@merlin.ai")
    google_service_account_email = config.get("google_service_account_email", "")
    default_resources = config.get("default_resources", {})
    default_secret_profile = config.get("secret_profiles", {}).get("mirror_default", {})
    shared_secret = (
        vault_get("S25_SHARED_SECRET", "") if use_live_shared_secret else ""
    ) or "REPLACE_WITH_S25_SHARED_SECRET"

    payload: Dict[str, Any] = {"version": "2.0", "services": {}, "profiles": {"compute": {}, "placement": {"akash": {"pricing": {}}}}, "deployment": {}}

    for container in config["containers"]:
        container_id = container["id"]
        service_name = f"{fleet_name}-{container_id}"
        secret_profile_name = container.get("google_secret_profile", "mirror_default")
        secret_profile = config.get("secret_profiles", {}).get(secret_profile_name, default_secret_profile)
        env_map = {
            "COCKPIT_URL": cockpit_url,
            "S25_SHARED_SECRET": shared_secret,
            "MIRROR_FLEET_NAME": fleet_name,
            "MIRROR_CONTAINER_ID": container_id,
            "MIRROR_MODE": container.get("mode", "observer"),
            "MIRROR_ASSIGNED_LANE": container.get("assigned_lane", "default_lane"),
            "MIRROR_TOTAL_CONTAINERS": str(config["mirror_count"]),
            "PUBLIC_MERLIN_MCP_URL": public_mcp_url,
            "GOOGLE_CLOUD_PROJECT": project_id,
            "MERLIN_WORKSPACE_ADMIN_EMAIL": workspace_admin_email,
            "GOOGLE_SERVICE_ACCOUNT_EMAIL": google_service_account_email,
            "S25_BOOTSTRAP_GOOGLE_SECRETS": "true",
            "S25_SECRET_PROFILE": secret_profile_name,
            "S25_GSM_SECRET_MAP_JSON": json.dumps(secret_profile, separators=(",", ":")),
            "RUN_MERLIN_MCP_BRIDGE": "false",
            "RUN_MERLIN_FEEDBACK_LOOP": "false",
            "RUN_GEMINI_OPS_DAEMON": "false",
            "RUN_ORACLE_AGENT": "false",
            "RUN_ONCHAIN_GUARDIAN": "false",
            "RUN_TREASURY_AUTOPILOT": "true" if container.get("run_treasury_autopilot") else "false",
            "ENABLE_TRADING_STACK": "true" if container.get("inject_trading_stack") else "false",
        }
        service = build_service(
            service_name,
            image,
            env_map,
            str(container.get("cpu", default_resources.get("cpu", "0.25"))),
            container.get("memory", default_resources.get("memory", "256Mi")),
            container.get("storage", default_resources.get("storage", "1Gi")),
            int(container.get("price_uakt", default_resources.get("price_uakt", 100))),
        )
        payload["services"][service_name] = {"image": service["image"], "env": service["env"]}
        merge_sections(payload["profiles"], "compute", service["profiles"]["compute"])
        payload["profiles"]["placement"]["akash"]["pricing"].update(service["profiles"]["placement"]["akash"]["pricing"])
        payload["deployment"].update(service["deployment"])

    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render the S25 MERLIN mirror fleet Akash manifest")
    parser.add_argument("--mission-file", default=str(ROOT / "configs" / "mission_mirror_akash.example.json"))
    parser.add_argument("--output", default="")
    parser.add_argument("--use-live-shared-secret", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = json.loads(Path(args.mission_file).read_text(encoding="utf-8"))
    payload = build_manifest(config, use_live_shared_secret=args.use_live_shared_secret)
    output_path = Path(args.output) if args.output else Path(tempfile.gettempdir()) / "s25-merlin-mirror-fleet.rendered.yaml"
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output_path), "fleet_name": config["fleet_name"], "containers": len(config["containers"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
