#!/usr/bin/env python3

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import requests

from agents.cockpit_client import CockpitClient
from security.vault import vault_get


log = logging.getLogger("s25.gemini_ops")

GEMINI_API_KEY = vault_get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")) or ""
GEMINI_MODEL = os.getenv("GEMINI_INTERACTION_MODEL", "gemini-2.5-flash")
GEMINI_MCP_ENDPOINT = os.getenv(
    "GEMINI_MCP_ENDPOINT",
    os.getenv("MERLIN_MCP_PUBLIC_URL", "https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp"),
)
POLL_SECONDS = int(os.getenv("GEMINI_OPS_POLL_SECONDS", "600"))
ENABLE_MEMORY_REBUILD = os.getenv("RUN_GEMINI_MEMORY_REBUILD", "false").lower() in {"1", "true", "yes", "on"}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> tuple[int, Dict[str, Any] | str]:
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
        body: Dict[str, Any] | str = response.json()
    except Exception:
        body = response.text
    return response.status_code, body


def _basic_generate_check() -> dict[str, Any]:
    status, body = _post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        {"contents": [{"parts": [{"text": "Reply with OK."}]}]},
        timeout=60,
    )
    return {"name": "generate_content_basic", "status_code": status, "body": body}


def _interactions_basic_check() -> dict[str, Any]:
    status, body = _post_json(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        {
            "model": GEMINI_MODEL,
            "input": "Reply with OK.",
            "system_instruction": "Today is 2026-03-10.",
        },
        timeout=120,
    )
    return {"name": "interactions_basic", "status_code": status, "body": body}


def _interactions_mcp_check() -> dict[str, Any]:
    status, body = _post_json(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        {
            "model": GEMINI_MODEL,
            "input": "Use MCP tools to inspect the system and return a short status.",
            "tools": [
                {
                    "type": "mcp_server",
                    "name": "merlin_mesh",
                    "url": GEMINI_MCP_ENDPOINT,
                }
            ],
            "system_instruction": "Today is 2026-03-10.",
        },
        timeout=180,
    )
    return {"name": "interactions_mcp", "status_code": status, "body": body}


def _error_code(check: dict[str, Any]) -> str:
    body = check.get("body") or {}
    if isinstance(body, dict):
        error = body.get("error") or {}
        return str(error.get("code") or "")
    return ""


def _summarize_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
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

    basic_code = _error_code(basic or {})
    mcp_code = _error_code(mcp or {})

    if summary["interactions_mcp_ok"]:
        summary["likely_issue"] = "none"
        summary["next_action"] = "use_live_mcp"
    elif basic_code == "too_many_requests" or mcp_code == "too_many_requests":
        summary["likely_issue"] = "quota_or_billing"
        summary["next_action"] = "enable_billing_and_verify_project_tier"
    elif summary["core_generate_content_ok"] and summary["interactions_basic_ok"] and mcp and mcp["status_code"] >= 500:
        summary["likely_issue"] = "interactions_mcp_backend"
        summary["next_action"] = "retry_later_and_validate_google_project_support"
    elif summary["core_generate_content_ok"] and basic and basic["status_code"] >= 500:
        summary["likely_issue"] = "interactions_backend"
        summary["next_action"] = "retry_later_or_change_google_project"
    elif text and text["status_code"] >= 400:
        summary["likely_issue"] = "base_api_key_or_project"
        summary["next_action"] = "validate_api_key_project_and_region"

    return summary


def _run_memory_rebuild() -> dict[str, Any]:
    if not ENABLE_MEMORY_REBUILD:
        return {"enabled": False}
    try:
        from agents.gemini_memory import rebuild_index

        index = rebuild_index()
        return {
            "enabled": True,
            "ok": True,
            "documents": len(index.get("documents", [])),
            "model": index.get("model"),
        }
    except Exception as exc:
        return {"enabled": True, "ok": False, "error": str(exc)}


def _report_to_cockpit(client: CockpitClient, checks: list[dict[str, Any]], summary: dict[str, Any], memory_rebuild: dict[str, Any]) -> None:
    ts = _utcnow_iso()
    status = "online" if summary.get("core_generate_content_ok") else "degraded"
    note = (
        f"GeminiOps tick. interactions_mcp={summary.get('interactions_mcp_ok')} "
        f"issue={summary.get('likely_issue')}"
    )
    client.heartbeat("MERLIN", note=note)
    client.update_state(
        "MERLIN",
        updates={
            "status": status,
            "last_query": "gemini_ops_daemon",
            "last_feedback_at": ts,
        },
        intel={
            "merlin_feedback": {
                "ts": ts,
                "summary": note,
                "source": "GEMINI_OPS_DAEMON",
                "summary_status": summary,
                "checks": checks,
                "mcp_endpoint": GEMINI_MCP_ENDPOINT,
                "memory_rebuild": memory_rebuild,
            },
            "gemini_ops": {
                "ts": ts,
                "model": GEMINI_MODEL,
                "endpoint": GEMINI_MCP_ENDPOINT,
                "summary": summary,
                "checks": checks,
                "memory_rebuild": memory_rebuild,
            },
        },
    )


def main() -> None:
    logging.basicConfig(level=os.getenv("GEMINI_OPS_LOG_LEVEL", "INFO"))
    client = CockpitClient()
    log.info("Starting Gemini Ops daemon every %ss against %s", POLL_SECONDS, GEMINI_MCP_ENDPOINT)

    while True:
        try:
            if not GEMINI_API_KEY:
                raise RuntimeError("GEMINI_API_KEY missing")

            checks = [
                _basic_generate_check(),
                _interactions_basic_check(),
                _interactions_mcp_check(),
            ]
            summary = _summarize_checks(checks)
            memory_rebuild = _run_memory_rebuild()
            _report_to_cockpit(client, checks, summary, memory_rebuild)
        except Exception as exc:
            log.warning("Gemini Ops tick failed: %s", exc)
            client.update_state(
                "MERLIN",
                updates={
                    "status": "degraded",
                    "last_query": "gemini_ops_daemon_failed",
                    "last_feedback_at": _utcnow_iso(),
                },
                intel={
                    "gemini_ops": {
                        "ts": _utcnow_iso(),
                        "model": GEMINI_MODEL,
                        "endpoint": GEMINI_MCP_ENDPOINT,
                        "error": str(exc),
                    }
                },
            )
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
