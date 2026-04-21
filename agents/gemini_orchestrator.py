#!/usr/bin/env python3
"""
S25 Gemini Orchestrator — daily trading brief via Gemini 2.5 Pro
=================================================================
Cron every 2h. Collects full trading context (portfolio, trades, strategies,
market, quant_brain decisions) and asks Gemini 2.5 Pro to write a concise
Québec-French analyst brief with warnings + actionable suggestions.

Output:
  memory/gemini_brief.json   (latest brief + history)
  HA: sensor.s25_gemini_brief (summary 250 chars)
  HA: sensor.s25_gemini_mood  (bullish|bearish|neutral|caution)
  Cockpit: /api/trading/brief exposes full JSON

Uses Google AI Studio API directly (no Cloud Console needed) — just
the GEMINI_API_KEY already in vault.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

logger = logging.getLogger("s25.gemini_orchestrator")

REPO = Path(__file__).resolve().parent.parent
BRIEF_PATH = REPO / "memory" / "gemini_brief.json"
HISTORY_PATH = REPO / "memory" / "gemini_brief_history.jsonl"
COCKPIT = os.getenv("S25_COCKPIT_URL", "http://localhost:7777")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


def _env_get(key: str) -> str:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


def _cockpit_get(path: str) -> Dict[str, Any]:
    try:
        r = requests.get(f"{COCKPIT}{path}", timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.warning("cockpit %s failed: %s", path, e)
    return {}


def collect_context() -> Dict[str, Any]:
    """Gather everything Gemini needs to analyse the system."""
    ctx = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "portfolio": _cockpit_get("/api/coinbase/portfolio"),
        "pnl": _cockpit_get("/api/trading/pnl"),
        "spot": _cockpit_get("/api/coinbase/spot-prices"),
        "strategies": _cockpit_get("/api/trading/strategies"),
        "executor_status": _cockpit_get("/api/trading/coinbase/status"),
        "risk_config": _cockpit_get("/api/trading/risk-config"),
    }
    # Last 24h trades
    log = REPO / "memory" / "trades_log.jsonl"
    cutoff = time.time() - 24 * 3600
    recent_trades: List[Dict] = []
    if log.exists():
        for line in log.read_text().splitlines():
            if not line.strip():
                continue
            try:
                t = json.loads(line)
            except Exception:
                continue
            ts = t.get("ts", 0)
            if isinstance(ts, (int, float)) and ts >= cutoff and t.get("mode") == "live":
                recent_trades.append({
                    "ts": ts,
                    "side": t.get("side"),
                    "symbol": t.get("symbol"),
                    "usd": t.get("usd_amount"),
                    "price": t.get("avg_price"),
                    "source": t.get("source"),
                    "success": t.get("success"),
                })
    ctx["trades_last_24h"] = recent_trades[-20:]

    # Last quant_brain decisions
    qb = REPO / "memory" / "quant_brain_log.jsonl"
    qb_decisions: List[Dict] = []
    if qb.exists():
        for line in qb.read_text().splitlines()[-5:]:
            if line.strip():
                try:
                    qb_decisions.append(json.loads(line))
                except Exception:
                    pass
    ctx["recent_quant_brain"] = qb_decisions
    return ctx


PROMPT = """Tu es l'analyste quant du système de trading S25 Lumière (perso, automatisé, Coinbase).

Parle direct en français québécois, sans broderie. Pas plus de 150 mots dans le summary.

Voici l'état actuel :

PORTFOLIO: {portfolio}
P&L: {pnl}
PRIX SPOT: {spot}
STRATEGIES ACTIVES: {strategies}
EXECUTOR: {executor_status}
TRADES LAST 24H: {trades_last_24h}
DÉCISIONS QUANT_BRAIN RÉCENTES: {recent_quant_brain}
RISK CONFIG: {risk_config}

Tâche — réponds en JSON STRICT (pas de markdown, juste JSON) :

{{
  "summary": "résumé 150 mots max de l'état du système + marché",
  "warnings": ["max 3 red flags visibles maintenant (patterns dangereux, over-exposure, etc.)"],
  "suggestions": ["max 3 actions concrètes pour les 24h à venir (disable/enable strategy, ajuster param, etc.)"],
  "mood": "bullish|bearish|neutral|caution",
  "portfolio_health_score": 0-100
}}
"""


def ask_gemini(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import google.generativeai as genai
    except Exception as e:
        return {"error": f"google-generativeai import: {e}"}

    api_key = _env_get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY absent"}

    genai.configure(api_key=api_key)
    # Trim context to reasonable size
    ctx_trim = {
        "portfolio_total": context.get("portfolio", {}).get("total_usd"),
        "portfolio_avail": context.get("portfolio", {}).get("available_usd"),
        "coins": context.get("portfolio", {}).get("coins", []),
        "pnl": context.get("pnl"),
        "spot_prices": context.get("spot", {}).get("prices"),
        "strategies": [
            {k: v for k, v in s.items()
             if k in ("name", "enabled", "symbols", "usd_size", "total_signals")}
            for s in context.get("strategies", {}).get("strategies", [])
        ],
        "executor": {k: v for k, v in context.get("executor_status", {}).items()
                     if k in ("dry_run", "orders_placed", "max_usd_per_trade")},
        "trades_last_24h_count": len(context.get("trades_last_24h", [])),
        "trades_last_24h": context.get("trades_last_24h", [])[-10:],
        "quant_brain_decisions": context.get("recent_quant_brain", []),
    }

    prompt = PROMPT.format(
        portfolio=json.dumps(ctx_trim.get("coins", []), default=str)[:500],
        pnl=json.dumps(ctx_trim.get("pnl"), default=str)[:500],
        spot=json.dumps(ctx_trim.get("spot_prices"), default=str)[:400],
        strategies=json.dumps(ctx_trim.get("strategies"), default=str)[:800],
        executor_status=json.dumps(ctx_trim.get("executor"), default=str),
        trades_last_24h=json.dumps(ctx_trim.get("trades_last_24h"), default=str)[:1500],
        recent_quant_brain=json.dumps(ctx_trim.get("quant_brain_decisions"), default=str)[:800],
        risk_config="default conservative",
    )

    model = genai.GenerativeModel(MODEL)
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )
        raw = response.text.strip()
        # Strip any code fence
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        return json.loads(raw)
    except Exception as e:
        logger.error("Gemini call failed: %s", e)
        return {"error": str(e), "raw_response": getattr(response, "text", "") if 'response' in dir() else ""}


def push_ha(summary: str, mood: str, score: int, warnings: List[str], suggestions: List[str]):
    url = _env_get("HA_URL") or "http://10.0.0.136:8123"
    token = _env_get("HA_TOKEN")
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        requests.post(
            f"{url.rstrip('/')}/api/states/sensor.s25_gemini_brief",
            headers=headers,
            json={
                "state": summary[:250],
                "attributes": {
                    "full_summary": summary,
                    "warnings": warnings,
                    "suggestions": suggestions,
                    "mood": mood,
                    "health_score": score,
                    "friendly_name": "S25 Gemini Brief",
                    "icon": "mdi:brain",
                },
            },
            timeout=6,
        )
        requests.post(
            f"{url.rstrip('/')}/api/states/sensor.s25_gemini_mood",
            headers=headers,
            json={
                "state": mood,
                "attributes": {
                    "friendly_name": "S25 Gemini Mood",
                    "health_score": score,
                    "icon": {
                        "bullish": "mdi:trending-up",
                        "bearish": "mdi:trending-down",
                        "neutral": "mdi:minus",
                        "caution": "mdi:alert",
                    }.get(mood, "mdi:brain"),
                },
            },
            timeout=6,
        )
        # Persistent notification if caution or warnings
        if mood == "caution" or len(warnings) > 0:
            requests.post(
                f"{url.rstrip('/')}/api/services/persistent_notification/create",
                headers=headers,
                json={
                    "title": f"🧠 Gemini brief [{mood}] score {score}",
                    "message": summary + "\n\n" + "\n".join(f"⚠️ {w}" for w in warnings),
                },
                timeout=6,
            )
    except Exception as e:
        logger.warning("HA push failed: %s", e)


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    logger.info("=== gemini_orchestrator tick ===")

    context = collect_context()
    logger.info("context built: portfolio=$%s trades24h=%d",
                (context.get("portfolio", {}) or {}).get("total_usd"),
                len(context.get("trades_last_24h", [])))

    brief = ask_gemini(context)
    brief["generated_at"] = datetime.now(timezone.utc).isoformat()
    brief["model"] = MODEL

    if "error" in brief:
        logger.error("Gemini error: %s", brief["error"])
    else:
        logger.info("Gemini mood=%s score=%s",
                    brief.get("mood"), brief.get("portfolio_health_score"))

    # Persist latest
    BRIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    BRIEF_PATH.write_text(json.dumps(brief, indent=2, ensure_ascii=False))
    with HISTORY_PATH.open("a") as f:
        f.write(json.dumps(brief, default=str, ensure_ascii=False) + "\n")

    # Push HA
    if "error" not in brief:
        push_ha(
            summary=brief.get("summary", ""),
            mood=brief.get("mood", "neutral"),
            score=int(brief.get("portfolio_health_score", 50)),
            warnings=brief.get("warnings", []),
            suggestions=brief.get("suggestions", []),
        )

    print(json.dumps(brief, indent=2, ensure_ascii=False))
    return 0 if "error" not in brief else 1


if __name__ == "__main__":
    sys.exit(main())
