#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def run(endpoint: str) -> int:
    async with streamablehttp_client(endpoint) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            init = await session.initialize()
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            print(
                json.dumps(
                    {
                        "ok": True,
                        "endpoint": endpoint,
                        "server": init.serverInfo.name,
                        "version": init.serverInfo.version,
                        "tools": tool_names,
                    },
                    indent=2,
                )
            )
            return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a public or local MERLIN MCP handshake")
    parser.add_argument("endpoint", help="Full MCP endpoint, for example http://127.0.0.1:8000/mcp")
    args = parser.parse_args()

    try:
        return asyncio.run(run(args.endpoint))
    except Exception as exc:
        print(json.dumps({"ok": False, "endpoint": args.endpoint, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
