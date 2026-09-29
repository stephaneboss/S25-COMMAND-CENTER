"""The voice draft lane must preserve edits and reject stale commands."""
import json

from flask import Flask

from agents.invoice_drafts import invoice_drafts


def test_private_draft_lifecycle(tmp_path, monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(invoice_drafts)
    client = app.test_client()
    body = {"source": "manual_verified", "source_ref": "demo-1",
            "client_ref": "customer-1", "actor": "STEF",
            "request_id": "create-1", "data": {"currency": "CAD", "lines": [
                {"description": "Déneigement", "quantity": 1, "unit_cents": 10000}]}}

    assert client.post("/api/business/invoice-drafts", json=body).status_code == 503
    monkeypatch.setenv("S25_INVOICE_API_ENABLED", "true")
    monkeypatch.setenv("S25_INVOICE_API_SECRET", "test-secret")
    monkeypatch.setenv("S25_INVOICE_DB", str(tmp_path / "private" / "invoices.sqlite"))
    assert client.post("/api/business/invoice-drafts", json=body).status_code == 401
    headers = {"X-Invoice-Secret": "test-secret"}
    created = client.post("/api/business/invoice-drafts", json=body, headers=headers)
    assert created.status_code == 201
    draft = created.json["draft"]
    assert draft["data"]["subtotal_cents"] == 10000
    assert draft["data"]["taxes"] == "unverified"
    draft_url = "/api/business/invoice-drafts/" + draft["id"]

    revision = {"expected_version": 1, "actor": "TRINITY",
                "request_id": "voice-1", "voice_transcript": "Change le montant à 120 dollars",
                "data": {"currency": "CAD", "lines": [
                    {"description": "Déneigement", "quantity": 1, "unit_cents": 12000}]}}
    changed = client.post(draft_url + "/revise", json=revision, headers=headers)
    assert changed.status_code == 200
    assert changed.json["draft"]["version"] == 2
    assert changed.json["draft"]["data"]["subtotal_cents"] == 12000
    assert client.post(draft_url + "/revise", json=revision, headers=headers).status_code == 409
    assert client.post("/api/business/invoice-drafts", json=body, headers=headers).status_code == 409
    reused_request = dict(body, source_ref="demo-2")
    assert client.post("/api/business/invoice-drafts", json=reused_request, headers=headers).status_code == 409

    read = client.get(draft_url, headers=headers)
    assert read.status_code == 200
    assert read.json["draft"]["status"] == "draft"
    assert len(read.json["events"]) == 2
    assert json.loads(read.json["events"][1]["detail"])["voice_transcript"] == revision["voice_transcript"]
