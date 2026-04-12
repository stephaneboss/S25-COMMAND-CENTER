#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from typing import Any

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from security.vault import vault_get


DEFAULT_MODEL = os.getenv("GEMINI_INTERACTION_MODEL", "gemini-2.5-flash")
DEFAULT_MCP_ENDPOINT = os.getenv("GEMINI_MCP_ENDPOINT", "https://merlin.smajor.org/mcp")
GEMINI_API_KEY = vault_get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")) or ""


def post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> tuple[int, dict[str, Any] | str]:
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        json=payload,
        timeout=timeout,
    )
    try:
        body: dict[str, Any] | str = response.json()
    except Exception:
        body = response.text
    return response.status_code, body


def run_check(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    status, body = post_json("https://generativelanguage.googleapis.com/v1beta/interactions", payload)
    result: dict[str, Any] = {"name": name, "status_code": status}
    if isinstance(body, dict):
        result["body"] = body
    else:
        result["body_text"] = str(body)[:1200]
    return result


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "core_generate_content_ok": False,
        "interactions_basic_ok": False,
        "interactions_mcp_ok": False,
        "likely_issue": "unknown",
        "next_action": "inspect_checks",
    }

    basic = next((item for item in checks if item["name"] == "interactions_basic"), None)
    mcp = next((item for item in checks if item["name"] == "interactions_mcp"), None)
    text = next((item for item in checks if item["name"] == "generate_content_basic"), None)

    if text and text["status_code"] == 200:
        summary["core_generate_content_ok"] = True
    if basic and basic["status_code"] == 200:
        summary["interactions_basic_ok"] = True
    if mcp and mcp["status_code"] == 200:
        summary["interactions_mcp_ok"] = True

    def error_code(item: dict[str, Any] | None) -> str:
        if not item:
            return ""
        body = item.get("body") or {}
        if isinstance(body, dict):
            error = body.get("error") or {}
            return str(error.get("code") or "")
        return ""

    basic_code = error_code(basic)
    mcp_code = error_code(mcp)

    if summary["interactions_mcp_ok"]:
        summary["likely_issue"] = "none"
        summary["next_action"] = "use_live_mcp"
    elif basic_code == "too_many_requests" or mcp_code == "too_many_requests":
        summary["likely_issue"] = "quota_or_billing"
        summary["next_action"] = "enable_billing_and_verify_project_tier"
    elif summary["core_generate_content_ok"] and basic and basic["status_code"] == 200 and mcp and mcp["status_code"] >= 500:
        summary["likely_issue"] = "interactions_mcp_backend"
        summary["next_action"] = "retry_later_and_validate_google_project_support"
    elif summary["core_generate_content_ok"] and basic and basic["status_code"] >= 500:
        summary["likely_issue"] = "interactions_backend"
        summary["next_action"] = "retry_later_or_change_google_project"
    elif text and text["status_code"] >= 400:
        summary["likely_issue"] = "base_api_key_or_project"
        summary["next_action"] = "validate_api_key_project_and_region"

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Gemini project readiness for Interactions + MCP")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--endpoint", default=DEFAULT_MCP_ENDPOINT)
    args = parser.parse_args()

    if not GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY missing")

    checks: list[dict[str, Any]] = []

    gen_status, gen_body = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{args.model}:generateContent",
        {"contents": [{"parts": [{"text": "Reply with OK."}]}]},
        timeout=60,
    )
    checks.append(
        {
            "name": "generate_content_basic",
            "status_code": gen_status,
            "body": gen_body if isinstance(gen_body, dict) else {"text": str(gen_body)[:1200]},
        }
    )

    checks.append(
        run_check(
            "interactions_basic",
            {
                "model": args.model,
                "input": "Reply with OK.",
                "system_instruction": "Today is 2026-03-10.",
            },
        )
    )

    checks.append(
        run_check(
            "interactions_mcp",
            {
                "model": args.model,
                "input": "Use MCP tools to inspect the system and return a short status.",
                "tools": [
                    {
                        "type": "mcp_server",
                        "name": "merlin_mesh",
                        "url": args.endpoint,
                    }
                ],
                "system_instruction": "Today is 2026-03-10.",
            },
        )
    )

    report = {
        "ok": True,
        "model": args.model,
        "endpoint": args.endpoint,
        "summary": summarize(checks),
        "checks": checks,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
