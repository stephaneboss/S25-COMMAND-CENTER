"""Private, draft-only invoice lane for S25 voice commands.

No Invoice Simple scraping, mail delivery, or payment operations live here.
The runtime stores customer data in a private SQLite file, never in Git memory.
"""
from __future__ import annotations

import hmac
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request


invoice_drafts = Blueprint("invoice_drafts", __name__)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _db():
    path = Path(os.environ["S25_INVOICE_DB"])
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=10000")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY, source TEXT NOT NULL, source_ref TEXT NOT NULL,
            client_ref TEXT NOT NULL, payload TEXT NOT NULL, version INTEGER NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            UNIQUE(source, source_ref)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, draft_id TEXT NOT NULL,
            version INTEGER NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
            request_id TEXT NOT NULL UNIQUE, detail TEXT NOT NULL, at TEXT NOT NULL
        );
    """)
    return connection


def _snapshot(row):
    return {"id": row["id"], "source": row["source"],
            "source_ref": row["source_ref"], "client_ref": row["client_ref"],
            "data": json.loads(row["payload"]), "version": row["version"],
            "status": row["status"], "created_at": row["created_at"],
            "updated_at": row["updated_at"]}


def _error(message, status):
    return jsonify({"ok": False, "error": message}), status


@invoice_drafts.before_request
def _guard():
    # This lane is disabled until a private DB and runtime secret are provisioned.
    secret = os.getenv("S25_INVOICE_API_SECRET", "")
    if (os.getenv("S25_INVOICE_API_ENABLED") != "true" or not secret
            or not os.getenv("S25_INVOICE_DB")):
        return _error("invoice_lane_disabled", 503)
    supplied = request.headers.get("X-Invoice-Secret", "")
    if not hmac.compare_digest(supplied, secret):
        return _error("unauthorized", 401)


def _body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def _text(value, limit=300):
    return isinstance(value, str) and 0 < len(value.strip()) <= limit


def _data(value):
    if not isinstance(value, dict):
        return False
    if not _text(value.get("currency"), 3) or value["currency"] != "CAD":
        return False
    lines = value.get("lines")
    return (isinstance(lines, list) and 0 < len(lines) <= 100 and all(
        isinstance(line, dict) and _text(line.get("description"))
        and isinstance(line.get("quantity"), int) and not isinstance(line.get("quantity"), bool)
        and 0 < line["quantity"] <= 100000
        and isinstance(line.get("unit_cents"), int) and not isinstance(line.get("unit_cents"), bool)
        and 0 <= line["unit_cents"] <= 100000000 for line in lines))


def _totals(data):
    # Taxes are deliberately not inferred from an unverified registration number.
    return sum(line["quantity"] * line["unit_cents"] for line in data["lines"])


@invoice_drafts.post("/api/business/invoice-drafts")
def create_draft():
    body = _body()
    if not (body.get("source") in ("invoice_simple_export", "manual_verified")
            and _text(body.get("source_ref"), 120)
            and _text(body.get("client_ref"), 120)
            and _text(body.get("actor"), 120)
            and _text(body.get("request_id"), 120)
            and _data(body.get("data"))):
        return _error("invalid_draft", 400)
    data = {"currency": "CAD", "lines": body["data"]["lines"],
            "subtotal_cents": _totals(body["data"]),
            "taxes": "unverified", "recipient": "unverified"}
    now, draft_id = _now(), str(uuid.uuid4())
    with _db() as db:
        try:
            db.execute("INSERT INTO drafts VALUES (?,?,?,?,?,?,?,?,?)",
                       (draft_id, body["source"], body["source_ref"],
                        body["client_ref"], json.dumps(data), 1, "draft", now, now))
            db.execute("INSERT INTO events (draft_id,version,actor,action,request_id,detail,at) "
                       "VALUES (?,?,?,?,?,?,?)", (draft_id, 1, body["actor"], "created",
                       body["request_id"], json.dumps({"source_ref": body["source_ref"]}), now))
        except sqlite3.IntegrityError:
            db.rollback()
            return _error("duplicate_source_or_request", 409)
        return jsonify({"ok": True, "draft": _snapshot(db.execute(
            "SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone())}), 201


@invoice_drafts.get("/api/business/invoice-drafts/<draft_id>")
def get_draft(draft_id):
    with _db() as db:
        row = db.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
        if row is None:
            return _error("not_found", 404)
        events = [dict(e) for e in db.execute(
            "SELECT version,actor,action,request_id,detail,at FROM events "
            "WHERE draft_id=? ORDER BY id", (draft_id,))]
        return jsonify({"ok": True, "draft": _snapshot(row), "events": events})


@invoice_drafts.post("/api/business/invoice-drafts/<draft_id>/revise")
def revise_draft(draft_id):
    body = _body()
    if not (type(body.get("expected_version")) is int
            and _text(body.get("actor"), 120)
            and _text(body.get("request_id"), 120)
            and _data(body.get("data"))):
        return _error("invalid_revision", 400)
    with _db() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
        if row is None:
            return _error("not_found", 404)
        if row["version"] != body["expected_version"]:
            return _error("version_conflict", 409)
        new_version, now = row["version"] + 1, _now()
        data = {"currency": "CAD", "lines": body["data"]["lines"],
                "subtotal_cents": _totals(body["data"]),
                "taxes": "unverified", "recipient": "unverified"}
        detail = {"old_subtotal_cents": json.loads(row["payload"])["subtotal_cents"],
                  "new_subtotal_cents": data["subtotal_cents"]}
        if "voice_transcript" in body:
            if not _text(body["voice_transcript"], 2000):
                return _error("invalid_voice_transcript", 400)
            detail["voice_transcript"] = body["voice_transcript"]
        try:
            db.execute("INSERT INTO events (draft_id,version,actor,action,request_id,detail,at) "
                       "VALUES (?,?,?,?,?,?,?)", (draft_id, new_version, body["actor"],
                       "revised", body["request_id"], json.dumps(detail), now))
        except sqlite3.IntegrityError:
            db.rollback()
            return _error("duplicate_request", 409)
        db.execute("UPDATE drafts SET payload=?,version=?,updated_at=? WHERE id=?",
                   (json.dumps(data), new_version, now, draft_id))
        return jsonify({"ok": True, "draft": _snapshot(db.execute(
            "SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone())})
