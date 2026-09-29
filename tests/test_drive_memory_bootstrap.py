"""Memory content must be bounded, verified, and never become authorization."""
import hashlib
import json

import pytest

from agents.drive_memory_bootstrap import MemoryUnavailable, load_private_memory


def test_verified_memory_and_tamper_rejection(tmp_path):
    name = "Reprise.md"
    (tmp_path / name).write_text("État vérifié", encoding="utf-8")
    digest = hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
    (tmp_path / "INDEX.json").write_text(json.dumps({
        "schema": "s25.memory.index.v1",
        "documents": [{"name": name, "sha256": digest}]}), encoding="utf-8")
    context, receipts = load_private_memory(tmp_path)
    assert "État vérifié" in context
    assert receipts == [{"name": name, "sha256": digest}]
    (tmp_path / name).write_text("modifié", encoding="utf-8")
    with pytest.raises(MemoryUnavailable, match="checksum"):
        load_private_memory(tmp_path)


def test_path_traversal_rejected(tmp_path):
    (tmp_path / "INDEX.json").write_text(json.dumps({
        "schema": "s25.memory.index.v1",
        "documents": [{"name": "../private.md", "sha256": "a" * 64}]}), encoding="utf-8")
    with pytest.raises(MemoryUnavailable, match="entry"):
        load_private_memory(tmp_path)
