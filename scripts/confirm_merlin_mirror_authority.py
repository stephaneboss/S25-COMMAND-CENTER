#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


DEFAULT_ENDPOINT = "https://merlin.smajor.org/mcp"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Confirm mirror fleet authority to MERLIN via the live MCP bridge")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--mission-file", required=True)
    parser.add_argument("--authority", choices=["pending", "established"], default="pending")
    parser.add_argument("--summary", default="")
    return parser


async def run(args: argparse.Namespace) -> int:
    mission = json.loads(Path(args.mission_file).read_text(encoding="utf-8"))
    checked_at = datetime.now(timezone.utc).isoformat()
    summary = args.summary or (
        f"Mirror authority {args.authority} for {mission['fleet_name']} with {len(mission['containers'])} containers. "
        f"Workspace admin={mission.get('workspace_admin_email', 'admin@merlin.ai')}."
    )
    feedback = {
        "authority": args.authority,
        "fleet_name": mission["fleet_name"],
        "mirror_count": len(mission["containers"]),
        "google_cloud_project": mission.get("google_cloud_project"),
        "workspace_admin_email": mission.get("workspace_admin_email"),
        "google_service_account_email": mission.get("google_service_account_email"),
        "checked_at": checked_at,
        "mission_file": str(Path(args.mission_file)),
    }

    async with streamablehttp_client(args.endpoint) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await session.call_tool("heartbeat", {"note": f"mirror_authority_{args.authority}"})
            result = await session.call_tool(
                "write_feedback",
                {
                    "summary": summary,
                    "level": "INFO" if args.authority == "established" else "WARN",
                    "source": "CODEX_MIRROR_FLEET",
                    "feedback_json": json.dumps(feedback),
                },
            )
            chunks = []
            for item in result.content:
                text = getattr(item, "text", None)
                if text:
                    chunks.append(text)
            print(json.dumps({"ok": True, "authority": args.authority, "endpoint": args.endpoint, "result": chunks}, indent=2))
    return 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
