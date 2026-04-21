#!/usr/bin/env python3
"""
S25 Gemini News Scanner — live web news via Gemini 2.5 Pro + Google Search grounding
======================================================================================
Same role as a Perplexity scanner would have, but FREE via Google AI Studio tier.
No separate API key needed — reuses GEMINI_API_KEY.

Cron every 1h. Three queries:
  1. Crypto market + BTC price action + news last 24h
  2. Whale movements + exchange flows + on-chain anomalies
  3. Upcoming macro events (Fed, CPI) that move crypto

Returns structured sentiment, top headlines, risk factors, with citations
to source web pages (grounding chunks from Google Search).

HA sensors:
  sensor.s25_news_sentiment   (bullish|bearish|neutral|uncertain)
  sensor.s25_news_headline    (top headline, 250 chars)
Cockpit: /api/trading/news

Replaces the dormant perplexity_scanner (Perplexity refused prepaid crypto
cards for credits). Uses the new `google-genai` SDK (replaces deprecated
google-generativeai).
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

logger = logging.getLogger("s25.gemini_news")

REPO = Path(__file__).resolve().parent.parent
LATEST_PATH = REPO / "memory" / "news_scan.json"
HISTORY_PATH = REPO / "memory" / "news_scan_history.jsonl"
MODEL = os.getenv("GEMINI_NEWS_MODEL", "gemini-2.5-pro")

QUERIES = [
    "Crypto market Bitcoin Ethereum last 24 hours: price action, major news, regulatory events, key headlines. Respond in French.",
    "Bitcoin last 24h: any major whale movements, exchange inflows/outflows, unusual on-chain activity, short/long liquidations?",
    "Upcoming 7 days macro events (Fed, CPI, FOMC, major earnings) that could move crypto market? Include specific dates.",
]

STRUCTURE_PROMPT = """
Répond en JSON STRICT (pas de markdown):
{{
  "summary": "résumé 200 mots max en français québécois",
  "sentiment": "bullish|bearish|neutral|uncertain",
  "confidence": 0.0-1.0,
  "top_headlines": ["max 3 courtes headlines"],
  "risk_factors": ["max 2 risques concrets"]
}}

QUERY: {query}
"""


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def _get_api_key() -> str:
    try:
        from security.vault import vault_get
        k = vault_get("GEMINI_API_KEY", "") or ""
        if k:
            return k
    except Exception:
        pass
    return _env_get("GEMINI_API_KEY")


def query_gemini(client, query: str) -> Dict[str, Any]:
    """One grounded query → structured + citations."""
    from google.genai import types
    try:
        r = client.models.generate_content(
            model=MODEL,
            contents=STRUCTURE_PROMPT.format(query=query),
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3,
            ),
        )
        raw = (r.text or "").strip()
        # Strip fences if present
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw_text": raw[:800]}

        # Extract grounding citations
        citations = []
        try:
            if r.candidates and r.candidates[0].grounding_metadata:
                gm = r.candidates[0].grounding_metadata
                for c in (gm.grounding_chunks or [])[:5]:
                    if c.web:
                        citations.append({
                            "title": c.web.title,
                            "uri": c.web.uri,
                        })
        except Exception:
            pass
        parsed["citations"] = citations
        return parsed
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def push_ha(results: List[Dict]):
    url = _env_get("HA_URL") or "http://10.0.0.136:8123"
    token = _env_get("HA_TOKEN")
    if not token:
        return
    from collections import Counter
    sents = [r.get("sentiment", "neutral") for r in results if "sentiment" in r]
    agg = Counter(sents).most_common(1)[0][0] if sents else "neutral"
    headlines = []
    for r in results:
        headlines.extend(r.get("top_headlines", []) or [])
    top_headline = (headlines[0][:250] if headlines else "no headlines")
    risks = []
    for r in results:
        risks.extend(r.get("risk_factors", []) or [])
    all_citations = []
    for r in results:
        all_citations.extend(r.get("citations", []) or [])

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        requests.post(
            f"{url.rstrip('/')}/api/states/sensor.s25_news_sentiment",
            headers=headers,
            json={
                "state": agg,
                "attributes": {
                    "friendly_name": "S25 News Sentiment",
                    "icon": {
                        "bullish": "mdi:trending-up",
                        "bearish": "mdi:trending-down",
                        "neutral": "mdi:minus",
                        "uncertain": "mdi:help-circle",
                    }.get(agg, "mdi:newspaper-variant"),
                    "risks": risks[:5],
                    "source_count": len(all_citations),
                    "model": MODEL,
                },
            },
            timeout=6,
        )
        requests.post(
            f"{url.rstrip('/')}/api/states/sensor.s25_news_headline",
            headers=headers,
            json={
                "state": top_headline,
                "attributes": {
                    "friendly_name": "S25 News Headline",
                    "icon": "mdi:newspaper",
                    "all_headlines": headlines[:8],
                    "citations": all_citations[:5],
                },
            },
            timeout=6,
        )
    except Exception as e:
        logger.warning("HA push failed: %s", e)


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    api_key = _get_api_key()
    if not api_key:
        logger.error("GEMINI_API_KEY missing — cannot scan")
        return 1

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error("google.genai import failed: %s — pip install google-genai", e)
        return 1

    logger.info("=== news scanner tick (%s) ===", MODEL)
    results = []
    for q in QUERIES:
        logger.info("querying: %s", q[:80])
        r = query_gemini(client, q)
        r["query"] = q
        r["ts"] = datetime.now(timezone.utc).isoformat()
        if "error" in r:
            logger.warning("query failed: %s", r["error"])
        else:
            logger.info("sentiment=%s conf=%s citations=%d",
                        r.get("sentiment"), r.get("confidence"),
                        len(r.get("citations", [])))
        results.append(r)

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "results": results,
    }
    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    with HISTORY_PATH.open("a") as f:
        f.write(json.dumps(snapshot, default=str, ensure_ascii=False) + "\n")

    push_ha(results)
    # Show first 2000 chars of output for visibility
    print(json.dumps(snapshot, indent=2, ensure_ascii=False)[:2500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
