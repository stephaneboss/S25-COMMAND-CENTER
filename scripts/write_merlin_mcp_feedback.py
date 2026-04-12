#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


DEFAULT_ENDPOINT = os.getenv("GEMINI_MCP_ENDPOINT", "https://merlin.smajor.org/mcp")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a feedback note into the live MERLIN MCP bridge")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--level", default="INFO")
    parser.add_argument("--source", default="CODEX_MCP")
    parser.add_argument("--mission-id", default="")
    parser.add_argument("--feedback-json", default="{}")
    return parser


async def run(args: argparse.Namespace) -> int:
    async with streamablehttp_client(args.endpoint) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "write_feedback",
                {
                    "summary": args.summary,
                    "level": args.level,
                    "source": args.source,
                    "mission_id": args.mission_id,
                    "feedback_json": args.feedback_json,
                },
            )
            chunks = []
            for item in result.content:
                text = getattr(item, "text", None)
                if text:
                    chunks.append(text)
            print(json.dumps({"ok": True, "endpoint": args.endpoint, "result": chunks}, indent=2))
            return 0


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
