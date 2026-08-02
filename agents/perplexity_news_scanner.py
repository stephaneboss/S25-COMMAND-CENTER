#!/usr/bin/env python3
"""
S25 Perplexity News Scanner — live web news via Perplexity Sonar (search-grounded)
====================================================================================
Restores real Perplexity-backed news/sentiment scanning (the previous
perplexity_scanner was removed after Perplexity rejected the prepaid crypto
card for billing - fixed 2026-08-02, card now accepted, see PERPLEXITY_API_KEY).

Writes the SAME output files/schema as gemini_news_scanner.py so cockpit's
/api/trading/news and the HA sensors (sensor.s25_news_sentiment,
sensor.s25_news_headline) work unchanged regardless of which scanner ran last:
  memory/news_scan.json          (latest snapshot)
  memory/news_scan_history.jsonl (append-only history)

Cron: same cadence as gemini_news_scanner (hourly), NOT both at once - see
docs note in cockpit_lumiere.py / crontab about which one is actually scheduled.

Three queries (same as gemini_news_scanner, kept identical for comparability):
  1. Crypto market + BTC price action + news last 24h
  2. Whale movements + exchange flows + on-chain anomalies
  3. Upcoming macro events (Fed, CPI) that move crypto
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

logger = logging.getLogger("s25.perplexity_news")

REPO = Path(__file__).resolve().parent.parent
LATEST_PATH = REPO / "memory" / "news_scan.json"
HISTORY_PATH = REPO / "memory" / "news_scan_history.jsonl"
MODEL = os.getenv("PERPLEXITY_NEWS_MODEL", "sonar")
API_URL = "https://api.perplexity.ai/chat/completions"

QUERIES = [
    "Crypto market Bitcoin Ethereum last 24 hours: price action, major news, regulatory events, key headlines. Respond in French.",
    "Bitcoin last 24h: any major whale movements, exchange inflows/outflows, unusual on-chain activity, short/long liquidations?",
    "Upcoming 7 days macro events (Fed, CPI, FOMC, major earnings) that could move crypto market? Include specific dates.",
]

STRUCTURE_PROMPT = """Répond en JSON STRICT (pas de markdown, pas de texte hors du JSON):
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
        k = vault_get("PERPLEXITY_API_KEY", "") or ""
        if k:
            return k
    except Exception:
        pass
    return _env_get("PERPLEXITY_API_KEY")


def query_perplexity(api_key: str, query: str) -> Dict[str, Any]:
    """One search-grounded query -> structured + citations."""
    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": STRUCTURE_PROMPT.format(query=query)}],
                "temperature": 0.3,
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        try:
            parsed = json.loads(raw)
        except (ValueError, IndexError):
            parsed = {"raw_text": raw[:800]}

        # Perplexity returns citations as a flat list of URLs (unlike Gemini's
        # title+uri grounding chunks) - normalize to the same {title, uri} shape
        # so downstream consumers (push_ha, cockpit) don't need to branch on scanner.
        citations = [{"title": None, "uri": u} for u in (data.get("citations") or [])[:5]]
        parsed["citations"] = citations
        return parsed
    except requests.RequestException as e:
        return {"error": f"{type(e).__name__}: {e}"}
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
    except requests.RequestException as e:
        logger.warning("HA push failed: %s", e)


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    api_key = _get_api_key()
    if not api_key:
        logger.error("PERPLEXITY_API_KEY missing - cannot scan")
        return 1

    logger.info("=== perplexity news scanner tick (%s) ===", MODEL)
    results = []
    for q in QUERIES:
        logger.info("querying: %s", q[:80])
        r = query_perplexity(api_key, q)
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
        "source": "perplexity",
        "results": results,
    }
    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    with HISTORY_PATH.open("a") as f:
        f.write(json.dumps(snapshot, default=str, ensure_ascii=False) + "\n")

    push_ha(results)
    print(json.dumps(snapshot, indent=2, ensure_ascii=False)[:2500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
