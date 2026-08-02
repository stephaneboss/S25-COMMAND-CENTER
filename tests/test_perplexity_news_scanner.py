"""
S25 Lumière — Perplexity news scanner tests (mocked HTTP, no real API calls/credits used)
=============================================================================================
Run: python3 -m pytest tests/test_perplexity_news_scanner.py -v
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import perplexity_news_scanner as pns  # noqa: E402


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise pns.requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload


def test_query_perplexity_parses_structured_json(monkeypatch):
    payload = {
        "choices": [{"message": {"content": json.dumps({
            "summary": "test resume",
            "sentiment": "bullish",
            "confidence": 0.8,
            "top_headlines": ["h1", "h2"],
            "risk_factors": ["r1"],
        })}}],
        "citations": ["https://example.com/a", "https://example.com/b"],
    }
    monkeypatch.setattr(pns.requests, "post", lambda *a, **kw: FakeResponse(payload))
    result = pns.query_perplexity("fake-key", "test query")
    assert result["sentiment"] == "bullish"
    assert result["confidence"] == 0.8
    assert len(result["citations"]) == 2
    assert result["citations"][0] == {"title": None, "uri": "https://example.com/a"}


def test_query_perplexity_handles_markdown_fenced_json(monkeypatch):
    fenced = "```json\n" + json.dumps({"summary": "x", "sentiment": "neutral", "confidence": 0.5,
                                        "top_headlines": [], "risk_factors": []}) + "\n```"
    payload = {"choices": [{"message": {"content": fenced}}], "citations": []}
    monkeypatch.setattr(pns.requests, "post", lambda *a, **kw: FakeResponse(payload))
    result = pns.query_perplexity("fake-key", "test query")
    assert result["sentiment"] == "neutral"


def test_query_perplexity_handles_malformed_json_gracefully(monkeypatch):
    payload = {"choices": [{"message": {"content": "not json at all"}}], "citations": []}
    monkeypatch.setattr(pns.requests, "post", lambda *a, **kw: FakeResponse(payload))
    result = pns.query_perplexity("fake-key", "test query")
    assert "raw_text" in result
    assert result["citations"] == []


def test_query_perplexity_handles_http_error(monkeypatch):
    def raise_err(*a, **kw):
        raise pns.requests.RequestException("connection failed")
    monkeypatch.setattr(pns.requests, "post", raise_err)
    result = pns.query_perplexity("fake-key", "test query")
    assert "error" in result


def test_main_writes_same_schema_as_gemini_scanner(tmp_path, monkeypatch):
    """Output schema must stay compatible with cockpit's /api/trading/news and
    the existing HA sensors regardless of which scanner produced it."""
    monkeypatch.setattr(pns, "LATEST_PATH", tmp_path / "news_scan.json")
    monkeypatch.setattr(pns, "HISTORY_PATH", tmp_path / "news_scan_history.jsonl")
    monkeypatch.setattr(pns, "_get_api_key", lambda: "fake-key")
    monkeypatch.setattr(pns, "push_ha", lambda results: None)  # no HA in test env

    payload = {
        "choices": [{"message": {"content": json.dumps({
            "summary": "s", "sentiment": "bullish", "confidence": 0.7,
            "top_headlines": ["h"], "risk_factors": [],
        })}}],
        "citations": [],
    }
    monkeypatch.setattr(pns.requests, "post", lambda *a, **kw: FakeResponse(payload))

    rc = pns.main()
    assert rc == 0
    snapshot = json.loads((tmp_path / "news_scan.json").read_text())
    assert "generated_at" in snapshot
    assert "model" in snapshot
    assert "results" in snapshot
    assert len(snapshot["results"]) == len(pns.QUERIES)
    assert snapshot["source"] == "perplexity"


def test_main_fails_cleanly_without_api_key(monkeypatch):
    monkeypatch.setattr(pns, "_get_api_key", lambda: "")
    assert pns.main() == 1
