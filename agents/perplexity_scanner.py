#!/usr/bin/env python3
"""
S25 Perplexity Scanner — live news + sentiment feed
====================================================
Cron every 1h. Queries Perplexity Sonar API (model llama-3.1-sonar-small-128k-online)
with crypto market / BTC / Fed / regulatory queries. Returns:
  - Structured sentiment (bullish/bearish/neutral/uncertain)
  - Top 3 news items with citations
  - Major risk factors detected

Publishes to HA sensors:
  sensor.s25_perplexity_sentiment   (bullish|bearish|neutral|uncertain)
  sensor.s25_perplexity_headline    (top news, 250 chars)
Persists to memory/perplexity_scan.json + history JSONL.

Activates automatically when PERPLEXITY_API_KEY is in vault/env.
Silent no-op if key missing (doesn't block startup, doesn't crash cron).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

logger = logging.getLogger("s25.perplexity_scanner")

REPO = Path(__file__).resolve().parent.parent
LATEST_PATH = REPO / "memory" / "perplexity_scan.json"
HISTORY_PATH = REPO / "memory" / "perplexity_scan_history.jsonl"
API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")

QUERIES = [
    "Crypto market BTC ETH last 24 hours: price action, major news, regulatory events. Summarize in 200 words.",
    "Any major whale movements, exchange outflows/inflows, or on-chain anomalies in Bitcoin last 24h?",
    "Upcoming macro events (Fed, CPI, earnings) that could move crypto prices this week?",
]

PROMPT_TEMPLATE = """You are a crypto market intelligence analyst for an automated trading system.
Be concise and factual. Only report verifiable news from the last 24 hours.

QUERY: {query}

Respond in JSON ONLY (no markdown):
{{
  "summary": "3-5 sentence summary",
  "sentiment": "bullish|bearish|neutral|uncertain",
  "confidence": 0.0-1.0,
  "top_headlines": ["max 3 short headlines"],
  "risk_factors": ["max 2 concrete risks you see"]
}}"""


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def _get_api_key() -> str:
    # vault first (keyring), then env, then .env file
    try:
        from security.vault import vault_get
        k = vault_get("PERPLEXITY_API_KEY", "") or ""
        if k:
            return k
    except Exception:
        pass
    return _env_get("PERPLEXITY_API_KEY")


def query_sonar(api_key: str, query: str) -> Dict[str, Any]:
    prompt = PROMPT_TEMPLATE.format(query=query)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        data = r.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        citations = data.get("citations", []) or []
        # Strip optional fences
        if content.startswith("```"):
            content = content.split("```")[1].lstrip("json").strip()
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"raw": content[:500]}
        parsed["citations"] = citations[:5]
        parsed["model"] = MODEL
        return parsed
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def push_ha(results: List[Dict]):
    url = _env_get("HA_URL") or "http://10.0.0.136:8123"
    token = _env_get("HA_TOKEN")
    if not token:
        return
    # Aggregate sentiment = mode of confidence-weighted sentiments
    sentiments = [r.get("sentiment", "neutral") for r in results if "sentiment" in r]
    from collections import Counter
    agg_sentiment = Counter(sentiments).most_common(1)[0][0] if sentiments else "neutral"
    # Top headline = first from first result
    top_headlines = (results[0].get("top_headlines") or [""]) if results else [""]
    headline = top_headlines[0][:250] if top_headlines else "no headlines"
    # All risk factors
    risks = []
    for r in results:
        risks.extend(r.get("risk_factors", []) or [])
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        requests.post(
            f"{url.rstrip('/')}/api/states/sensor.s25_perplexity_sentiment",
            headers=headers,
            json={
                "state": agg_sentiment,
                "attributes": {
                    "friendly_name": "S25 Perplexity Sentiment",
                    "icon": {
                        "bullish": "mdi:trending-up",
                        "bearish": "mdi:trending-down",
                        "neutral": "mdi:minus",
                        "uncertain": "mdi:help-circle",
                    }.get(agg_sentiment, "mdi:eye"),
                    "risks": risks[:5],
                    "full_results_count": len(results),
                },
            },
            timeout=6,
        )
        requests.post(
            f"{url.rstrip('/')}/api/states/sensor.s25_perplexity_headline",
            headers=headers,
            json={
                "state": headline,
                "attributes": {
                    "friendly_name": "S25 Perplexity Top Headline",
                    "icon": "mdi:newspaper",
                    "all_headlines": [h for r in results for h in (r.get("top_headlines") or [])][:8],
                    "citations_count": sum(len(r.get("citations", [])) for r in results),
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
        logger.warning("PERPLEXITY_API_KEY absent — scanner dormant. "
                       "Set via: keyring.set_password('S25-LUMIERE', 'PERPLEXITY_API_KEY', 'pplx-...')")
        return 0  # Dormant, not error

    logger.info("Perplexity scanner running with model=%s (%d queries)", MODEL, len(QUERIES))
    results = []
    for q in QUERIES:
        logger.info("querying: %s", q[:80])
        out = query_sonar(api_key, q)
        if "error" in out:
            logger.warning("query failed: %s", out["error"])
        else:
            logger.info("got sentiment=%s confidence=%s",
                        out.get("sentiment"), out.get("confidence"))
        results.append({"query": q, **out, "ts": datetime.now(timezone.utc).isoformat()})

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
    print(json.dumps(snapshot, indent=2, ensure_ascii=False)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
