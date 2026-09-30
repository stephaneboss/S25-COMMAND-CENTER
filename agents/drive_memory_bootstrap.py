"""Load a verified, private Drive memory mirror as reference context.

The operator syncs a private Drive folder to S25_MEMORY_DIR outside the repo.
This module grants no permissions and never treats document text as commands.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


MAX_DOCUMENTS = 12
MAX_BYTES = 64 * 1024
MAX_TOTAL_BYTES = 96 * 1024
_SAFE_NAME = re.compile(r"[A-Za-z0-9_À-ÿ().-]+\.md\Z")


class MemoryUnavailable(Exception):
    """The private mirror is absent or cannot be verified."""


def load_private_memory(directory: str | Path) -> tuple[str, list[dict]]:
    """Return bounded reference text and file receipts; fail closed on mismatch."""
    root = Path(directory)
    if not root.is_dir() or root.is_symlink():
        raise MemoryUnavailable("memory_directory_missing")
    index_path = root / "INDEX.json"
    if index_path.is_symlink() or not index_path.is_file() or index_path.stat().st_size > 16_384:
        raise MemoryUnavailable("memory_index_missing_or_oversized")
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MemoryUnavailable("memory_index_invalid") from exc
    documents = index.get("documents")
    if (index.get("schema") != "s25.memory.index.v1"
            or not isinstance(documents, list)
            or not 1 <= len(documents) <= MAX_DOCUMENTS):
        raise MemoryUnavailable("memory_index_schema_invalid")

    parts, receipts, names, total_bytes = [], [], set(), 0
    for entry in documents:
        if not isinstance(entry, dict):
            raise MemoryUnavailable("memory_entry_invalid")
        name, expected = entry.get("name"), entry.get("sha256")
        if (not isinstance(name, str) or not _SAFE_NAME.fullmatch(name)
                or name in names or not isinstance(expected, str)
                or not re.fullmatch(r"[0-9a-f]{64}", expected)):
            raise MemoryUnavailable("memory_entry_invalid")
        names.add(name)
        target = root / name
        if target.is_symlink() or not target.is_file() or target.stat().st_size > MAX_BYTES:
            raise MemoryUnavailable("memory_file_missing_or_oversized")
        raw = target.read_bytes()
        total_bytes += len(raw)
        if total_bytes > MAX_TOTAL_BYTES:
            raise MemoryUnavailable("memory_total_oversized")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            raise MemoryUnavailable("memory_checksum_mismatch")
        try:
            content = raw.decode("utf-8")
        except UnicodeError as exc:
            raise MemoryUnavailable("memory_encoding_invalid") from exc
        receipts.append({"name": name, "sha256": digest})
        parts.append(f"[REFERENCE {name} sha256={digest}]\n{content}\n[/REFERENCE]")
    return "\n\n".join(parts), receipts


def append_receipt(receipts: list[dict], agent: str) -> None:
    """Only metadata goes to the private audit log, never document content."""
    log_path = os.getenv("S25_MEMORY_AUDIT_LOG")
    if not log_path:
        return
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log:
        log.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(),
                              "agent": agent, "documents": receipts}) + "\n")
