#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from google import genai

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.vault import vault_get


DEFAULT_ENDPOINT = "https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp"
DEFAULT_MODEL = os.getenv("GEMINI_INTERACTION_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = vault_get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")) or ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a live Gemini interaction against the MERLIN MCP bridge")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Remote MCP endpoint")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model for Interactions API")
    parser.add_argument("--no-writeback", action="store_true", help="Skip write_feedback instruction")
    parser.add_argument("--dump-json", action="store_true", help="Print the full raw API response")
    return parser


def build_prompt(writeback: bool, checked_at: str, endpoint: str) -> str:
    prompt = (
        "You are MERLIN validating the S25 mesh. "
        "Use the remote MCP tools to inspect the live system. "
        "Call get_system_status, get_mesh_status, and get_missions before answering. "
        "Return a short operator verdict with status, key risks, and next action. "
        f"Checked at {checked_at}. MCP endpoint: {endpoint}."
    )
    if writeback:
        prompt += (
            " Then call write_feedback with a concise summary in English, "
            "level=INFO, source=GEMINI_REMOTE, and feedback_json containing "
            "a JSON object with keys verdict, next_action, checked_at, and endpoint."
        )
    return prompt


def main() -> int:
    args = build_parser().parse_args()
    if not GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY missing")

    checked_at = datetime.now(timezone.utc).isoformat()
    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        interaction = client.interactions.create(
            model=args.model,
            input=build_prompt(
                writeback=not args.no_writeback,
                checked_at=checked_at,
                endpoint=args.endpoint,
            ),
            tools=[
                {
                    "type": "mcp_server",
                    "name": "merlin_mesh",
                    "url": args.endpoint,
                }
            ],
            system_instruction=(
                "Today is "
                + checked_at
                + ". Use MCP tools when facts are needed. Keep the final answer concise and operational."
            ),
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "model": args.model,
                    "endpoint": args.endpoint,
                    "error": str(exc),
                    "hint": "Gemini Interactions is still unstable here; check project quota and retry with the same MCP endpoint.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    if args.dump_json:
        print(json.dumps(interaction.to_json_dict(), indent=2))
        return 0

    text_outputs = [item.text for item in interaction.outputs if getattr(item, "text", None)]
    print(json.dumps({"ok": True, "model": args.model, "endpoint": args.endpoint}, indent=2))
    if text_outputs:
        print("")
        print("\n".join(text_outputs).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
