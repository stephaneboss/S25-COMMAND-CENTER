"""Build a provider intelligence snapshot from official sources."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
MEMORY_DIR = ROOT / "memory"
SNAPSHOT_JSON = MEMORY_DIR / "provider_watch_snapshot.json"
SNAPSHOT_MD = MEMORY_DIR / "PROVIDER_WATCH.md"


@dataclass
class SourceCheck:
    provider: str
    category: str
    url: str
    title: str
    status: str
    checked_at: str
    note: str


SOURCES = [
    {
        "provider": "OpenAI",
        "category": "changelog",
        "url": "https://platform.openai.com/docs/changelog",
        "note": "Track Responses API, tools, MCP, background mode, and GPT-compatible patterns.",
    },
    {
        "provider": "OpenAI",
        "category": "responses_news",
        "url": "https://openai.com/index/new-tools-and-features-in-the-responses-api/",
        "note": "Use as product direction for agent tooling and future TRINITY upgrades.",
    },
    {
        "provider": "Google",
        "category": "gemini_changelog",
        "url": "https://ai.google.dev/gemini-api/docs/changelog",
        "note": "Gemini remains the long-term memory and retrieval pillar for S25.",
    },
    {
        "provider": "Google",
        "category": "embedding_ga",
        "url": "https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/",
        "note": "Watch embedding updates and retirement windows for legacy embedding models.",
    },
    {
        "provider": "Anthropic",
        "category": "release_notes",
        "url": "https://docs.anthropic.com/en/release-notes/api",
        "note": "Watch compatibility features, model lifecycle, and code/backend primitives.",
    },
    {
        "provider": "Perplexity",
        "category": "comet_shortcuts",
        "url": "https://www.perplexity.ai/help-center/en/articles/11897890-comet-shortcuts",
        "note": "Shortcuts are the best current lever for repeatable provider-watch workflows in Comet.",
    },
    {
        "provider": "Perplexity",
        "category": "assistant_permissions",
        "url": "https://comet-help.perplexity.ai/en/articles/12658082-control-what-comet-assistant-can-use",
        "note": "Use to keep Comet useful but constrained when it touches account surfaces.",
    },
    {
        "provider": "Perplexity",
        "category": "work_guide",
        "url": "https://r2cdn.perplexity.ai/pdf/pplx-at-work.pdf",
        "note": "Use Work patterns to turn provider watch into a repeatable operating routine.",
    },
]


def _fetch(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "S25-Provider-Watch/1.0 (+https://trinity-s25-proxy.trinitys25steph.workers.dev)"
        },
    )
    with urlopen(request, timeout=30) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def _strip_tags(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()
    return cleaned.replace("\xa0", " ")


def _extract_title(body: str) -> str:
    patterns = [
        r"<meta[^>]+property=[\"']og:title[\"'][^>]+content=[\"']([^\"']+)",
        r"<title[^>]*>(.*?)</title>",
        r"<h1[^>]*>(.*?)</h1>",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return unescape(_strip_tags(match.group(1)))[:200]
    return "title_not_found"


def _fallback_title(url: str, category: str) -> str:
    if url.lower().endswith(".pdf"):
        return f"{category}_pdf"
    return category


def build_snapshot() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()
    checks: list[SourceCheck] = []
    for source in SOURCES:
        try:
            body = _fetch(source["url"])
            title = _extract_title(body)
            if title == "title_not_found":
                title = _fallback_title(source["url"], source["category"])
            status = "ok"
        except HTTPError as exc:
            title = _fallback_title(source["url"], source["category"])
            status = "restricted" if exc.code == 403 else "error"
        except URLError:
            title = _fallback_title(source["url"], source["category"])
            status = "error"
        except Exception:  # pragma: no cover - defensive snapshotting
            title = _fallback_title(source["url"], source["category"])
            status = "error"
        checks.append(
            SourceCheck(
                provider=source["provider"],
                category=source["category"],
                url=source["url"],
                title=title,
                status=status,
                checked_at=checked_at,
                note=source["note"],
            )
        )
    snapshot = {
        "generated_at": checked_at,
        "status": "ok" if all(item.status == "ok" for item in checks) else "partial",
        "checks": [asdict(item) for item in checks],
    }
    return snapshot


def render_markdown(snapshot: dict) -> str:
    lines = [
        "# Provider Watch Snapshot",
        "",
        f"- Generated at: `{snapshot['generated_at']}`",
        f"- Global status: `{snapshot['status']}`",
        "",
        "## Current official-source checks",
        "",
    ]
    grouped: dict[str, list[dict]] = {}
    for item in snapshot["checks"]:
        grouped.setdefault(item["provider"], []).append(item)
    for provider in ("OpenAI", "Google", "Anthropic", "Perplexity"):
        provider_checks = grouped.get(provider, [])
        if not provider_checks:
            continue
        lines.extend([f"### {provider}", ""])
        for item in provider_checks:
            lines.append(f"- `{item['category']}` [{item['title']}]({item['url']}) [{item['status']}]")
            lines.append(f"  S25 note: {item['note']}")
        lines.append("")
    lines.extend(
        [
            "## Use in S25",
            "",
            "- Feed this snapshot to TRINITY, MERLIN, or COMET when reviewing provider changes.",
            "- Treat Google/Gemini as the long-term memory and retrieval base.",
            "- Treat OpenAI/TRINITY as the orchestration surface for voice and action flows.",
            "- Treat Claude/Codex as the backend implementation force.",
            "- Treat Comet as the browser-native watchtower for product, work, and workflow updates.",
            "",
        ]
    )
    return "\n".join(lines)


def write_snapshot(snapshot: dict) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_JSON.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    SNAPSHOT_MD.write_text(render_markdown(snapshot), encoding="utf-8")


def main() -> None:
    snapshot = build_snapshot()
    write_snapshot(snapshot)
    print(f"[provider-watch] wrote {SNAPSHOT_JSON}")
    print(f"[provider-watch] wrote {SNAPSHOT_MD}")
    print(f"[provider-watch] status={snapshot['status']} checks={len(snapshot['checks'])}")


if __name__ == "__main__":
    main()
