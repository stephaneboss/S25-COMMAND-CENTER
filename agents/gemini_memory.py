#!/usr/bin/env python3

import json
import logging
import math
import os
from pathlib import Path
from typing import Dict, List

import requests


log = logging.getLogger("s25.gemini_memory")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
MEMORY_DIR = Path(os.getenv("MEMORY_DIR", "/app/memory"))
MEMORY_INDEX_FILE = MEMORY_DIR / "gemini_memory_index.json"


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
    shared_memory = MEMORY_DIR / "SHARED_MEMORY.md"
    agents_state = MEMORY_DIR / "agents_state.json"

    if shared_memory.exists():
        docs.append({"id": "shared_memory", "text": shared_memory.read_text(encoding="utf-8")})
    if agents_state.exists():
        docs.append({"id": "agents_state", "text": agents_state.read_text(encoding="utf-8")})

    return docs


def rebuild_index() -> Dict[str, object]:
    documents = _load_documents()
    embeddings = []
    for doc in documents:
        try:
            embeddings.append({
                "id": doc["id"],
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
    index = json.loads(MEMORY_INDEX_FILE.read_text(encoding="utf-8"))
    query_embedding = _embed_text(query)
    scored = []
    for doc in index.get("documents", []):
        score = _cosine_similarity(query_embedding, doc.get("embedding", []))
        scored.append({
            "id": doc["id"],
            "score": round(score, 4),
            "preview": doc.get("preview", ""),
        })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [GEMINI_MEMORY] %(levelname)s %(message)s")
    index = rebuild_index()
    print(json.dumps({"ok": True, "model": index["model"], "documents": len(index["documents"])}, indent=2))
