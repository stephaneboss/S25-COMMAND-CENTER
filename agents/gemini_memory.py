#!/usr/bin/env python3

import json
import logging
import math
import os
from pathlib import Path
from typing import Dict, List

import requests
from security.vault import vault_get


log = logging.getLogger("s25.gemini_memory")

GEMINI_API_KEY = vault_get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")) or ""
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
DEFAULT_ROOT_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = Path(os.getenv("MEMORY_DIR", str(DEFAULT_ROOT_DIR / "memory")))
ROOT_DIR = Path(os.getenv("S25_ROOT_DIR", str(DEFAULT_ROOT_DIR)))
DOCS_DIR = ROOT_DIR / "docs"
MEMORY_INDEX_FILE = MEMORY_DIR / "gemini_memory_index.json"

INDEX_TARGETS = [
    ("shared_memory", MEMORY_DIR / "SHARED_MEMORY.md"),
    ("agents_state", MEMORY_DIR / "agents_state.json"),
    ("provider_watch", MEMORY_DIR / "PROVIDER_WATCH.md"),
    ("provider_watch_snapshot", MEMORY_DIR / "provider_watch_snapshot.json"),
    ("provider_intelligence", DOCS_DIR / "PROVIDER_INTELLIGENCE.md"),
    ("comet_work_system", DOCS_DIR / "COMET_WORK_SYSTEM.md"),
    ("gemini_foundation", DOCS_DIR / "GEMINI_FOUNDATION.md"),
    ("agent_registry", DOCS_DIR / "AGENT_REGISTRY.md"),
    ("workstream_board", DOCS_DIR / "WORKSTREAM_BOARD.md"),
]


def _embed_text(text: str) -> List[float]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing")

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_EMBED_MODEL}:embedContent",
        params={"key": GEMINI_API_KEY},
        json={"model": f"models/{GEMINI_EMBED_MODEL}", "content": {"parts": [{"text": text[:8000]}]}},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["embedding"]["values"]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _load_documents() -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    for doc_id, path in INDEX_TARGETS:
        if path.exists():
            docs.append({"id": doc_id, "path": str(path), "text": path.read_text(encoding="utf-8")})

    return docs


def rebuild_index() -> Dict[str, object]:
    documents = _load_documents()
    embeddings = []
    for doc in documents:
        try:
            embeddings.append({
                "id": doc["id"],
                "path": doc.get("path", ""),
                "embedding": _embed_text(doc["text"]),
                "preview": doc["text"][:500],
            })
        except Exception as exc:
            log.warning("embedding failed for %s: %s", doc["id"], exc)

    index = {
        "model": GEMINI_EMBED_MODEL,
        "documents": embeddings,
    }
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def search(query: str, top_k: int = 3) -> List[Dict[str, object]]:
    if not MEMORY_INDEX_FILE.exists():
        rebuild_index()
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing")
    index = json.loads(MEMORY_INDEX_FILE.read_text(encoding="utf-8"))
    query_embedding = _embed_text(query)
    scored = []
    for doc in index.get("documents", []):
        score = _cosine_similarity(query_embedding, doc.get("embedding", []))
        scored.append({
            "id": doc["id"],
            "path": doc.get("path", ""),
            "score": round(score, 4),
            "preview": doc.get("preview", ""),
        })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def search_to_markdown(query: str, top_k: int = 5) -> str:
    if not GEMINI_API_KEY:
        return "\n".join(
            [
                "# Gemini Memory Search",
                "",
                f"- Query: `{query}`",
                "- Error: `GEMINI_API_KEY missing`",
                "- Action: set `GEMINI_API_KEY` before semantic search.",
            ]
        )

    results = search(query, top_k=top_k)
    lines = [
        "# Gemini Memory Search",
        "",
        f"- Query: `{query}`",
        f"- Model: `{GEMINI_EMBED_MODEL}`",
        "",
    ]
    if not results:
        lines.append("- No results")
        return "\n".join(lines)

    for item in results:
        lines.append(f"- `{item['id']}` score=`{item['score']}`")
        if item.get("path"):
            lines.append(f"  path: {item['path']}")
        preview = item["preview"].replace("\n", " ")[:260]
        lines.append(f"  preview: {preview}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="S25 Gemini semantic memory")
    parser.add_argument("--query", help="Semantic search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [GEMINI_MEMORY] %(levelname)s %(message)s")
    if args.query:
        print(search_to_markdown(args.query, top_k=args.top_k))
    else:
        index = rebuild_index()
        print(json.dumps({"ok": True, "model": index["model"], "documents": len(index["documents"])}, indent=2))
