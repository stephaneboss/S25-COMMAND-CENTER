#!/usr/bin/env python3
# ============================================================
# S25 LUMIÈRE — AI Router v2.0
# Multi-model: Gemini (principal) + Ollama + OpenAI + Claude
# Lit signal Kimi → Analyse Gemini → Décision MEXC → HA update
# ============================================================

import json
import os
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [S25] %(levelname)s: %(message)s'
)
log = logging.getLogger("ai_router_s25")

# ─────────────────────────────────────────────────────
# CONFIG — À personnaliser dans secrets.yaml HA
# ─────────────────────────────────────────────────────
HA_URL        = os.getenv("HA_URL", "http://172.30.32.1:8123")
HA_TOKEN      = os.getenv("HA_TOKEN", "")          # Long-Lived Token HA
GEMINI_KEY    = os.getenv("GEMINI_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")
CLAUDE_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
MEXC_KEY      = os.getenv("MEXC_API_KEY", "")
MEXC_SECRET   = os.getenv("MEXC_SECRET", "")

# Output path pour sensors HA REST
AI_ANALYSIS_PATH = "/config/www/ai_analysis.json"

# Modèles disponibles
MODELS = {
    "gemini":    "gemini-2.0-flash-exp",
    "ollama":    "mistral",
    "openai":    "gpt-4o",
    "claude":    "claude-3-5-sonnet-20241022",
    "perplexity":"llama-3.1-sonar-large-128k-online",
    "kimi":      "moonshot-v1-8k",
}

# ─────────────────────────────────────────────────────
# HA API HELPERS
# ─────────────────────────────────────────────────────
def ha_headers():
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }

def ha_get_state(entity_id):
    """Lire l'état d'une entité HA"""
    try:
        r = requests.get(
            f"{HA_URL}/api/states/{entity_id}",
            headers=ha_headers(),
            timeout=5
        )
        if r.status_code == 200:
            return r.json().get("state", "")
    except Exception as e:
        log.error(f"HA get_state error {entity_id}: {e}")
    return ""

def ha_set_state(entity_id, value):
    """Mettre à jour une entité HA"""
    try:
        r = requests.post(
            f"{HA_URL}/api/states/{entity_id}",
            headers=ha_headers(),
            json={"state": value},
            timeout=5
        )
        log.info(f"HA set {entity_id} = {value} [{r.status_code}]")
        return r.status_code == 200 or r.status_code == 201
    except Exception as e:
        log.error(f"HA set_state error: {e}")
        return False

def ha_set_input_text(entity_id, value):
    """Mettre à jour un input_text HA"""
    try:
        r = requests.post(
            f"{HA_URL}/api/services/input_text/set_value",
            headers=ha_headers(),
            json={"entity_id": entity_id, "value": str(value)[:255]},
            timeout=5
        )
        return r.status_code in [200, 201]
    except Exception as e:
        log.error(f"HA input_text error: {e}")
        return False

def ha_fire_event(event_type, data=None):
    """Déclencher un événement HA"""
    try:
        r = requests.post(
            f"{HA_URL}/api/events/{event_type}",
            headers=ha_headers(),
            json=data or {},
            timeout=5
        )
        return r.status_code in [200, 201]
    except Exception as e:
        log.error(f"HA fire_event error: {e}")
        return False

# ─────────────────────────────────────────────────────
# GEMINI — Analyse principale
# ─────────────────────────────────────────────────────
def analyze_with_gemini(kimi_signal: str, model: str = None) -> dict:
    """Analyse le signal Kimi avec Gemini et retourne une décision trading"""
    if not GEMINI_KEY:
        log.warning("GEMINI_API_KEY non configuré — fallback HOLD")
        return _fallback_decision("Gemini key manquante")

    gemini_model = model or MODELS["gemini"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={GEMINI_KEY}"

    prompt = f"""Tu es ARKON-5, le système d'analyse IA du projet S25 Lumière.
Tu analyses des signaux de marché crypto de Kimi Web3 et génères des décisions trading BTC/USDT pour MEXC.

Signal reçu de Kimi Web3:
{kimi_signal}

Timestamp: {datetime.utcnow().isoformat()}

Analyse ce signal et génère OBLIGATOIREMENT une réponse JSON avec cette structure exacte:
{{
  "decision": {{
    "action": "BUY" | "SELL" | "HOLD",
    "conf": 0.0 à 1.0 (float),
    "tp": prix en USDT (float ou null),
    "sl": prix en USDT (float ou null),
    "size": 0.0 à 1.0 (fraction du capital, float),
    "reason": "explication courte en français (max 200 chars)"
  }},
  "signal": {{
    "source": "kimi_web3",
    "strength": "strong|medium|weak",
    "trend": "bullish|bearish|neutral"
  }},
  "timestamp": "{datetime.utcnow().isoformat()}",
  "model": "ARKON-5/{gemini_model}",
  "version": "2.0"
}}

Règles:
- Action BUY si signal bullish fort (conf >= 0.65)
- Action SELL si signal bearish fort (conf >= 0.65)
- Action HOLD si signal faible ou ambigu (conf < 0.65)
- TP = prix actuel + 2-3% pour BUY, prix actuel - 2-3% pour SELL
- SL = prix actuel - 1.5% pour BUY, prix actuel + 1.5% pour SELL
- Size max = 0.25 (25% du capital par trade)
- RETOURNE UNIQUEMENT LE JSON, aucun texte avant ou après.
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json"
        }
    }

    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()

        # Extraire le texte de la réponse
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
        log.info(f"Gemini analyse OK: {result['decision']['action']} ({result['decision']['conf']:.0%})")
        return result

    except json.JSONDecodeError as e:
        log.error(f"Gemini JSON parse error: {e}")
        return _fallback_decision(f"Gemini parse error: {e}")
    except Exception as e:
        log.error(f"Gemini API error: {e}")
        return _fallback_decision(f"Gemini error: {e}")

# ─────────────────────────────────────────────────────
# FALLBACK DECISION
# ─────────────────────────────────────────────────────
def _fallback_decision(reason: str) -> dict:
    return {
        "decision": {
            "action": "HOLD",
            "conf": 0.0,
            "tp": None,
            "sl": None,
            "size": 0.0,
            "reason": f"FALLBACK: {reason}"
        },
        "signal": {"source": "fallback", "strength": "weak", "trend": "neutral"},
        "timestamp": datetime.utcnow().isoformat(),
        "model": "ARKON-5/fallback",
        "version": "2.0"
    }

# ─────────────────────────────────────────────────────
# ÉCRITURE ai_analysis.json (lu par sensors HA)
# ─────────────────────────────────────────────────────
def write_ai_analysis(result: dict):
    """Écrit le résultat dans /config/www/ pour que les sensors REST le lisent"""
    try:
        result["timestamp"] = time.time()
        with open(AI_ANALYSIS_PATH, "w") as f:
            json.dump(result, f, indent=2)
        log.info(f"ai_analysis.json écrit: {result['decision']['action']}")
        return True
    except Exception as e:
        log.error(f"Erreur écriture ai_analysis.json: {e}")
        return False

# ─────────────────────────────────────────────────────
# MISE À JOUR ENTITÉS HA
# ─────────────────────────────────────────────────────
def update_ha_entities(result: dict):
    """Met à jour les entités HA avec la décision ARKON-5"""
    decision = result.get("decision", {})
    action = decision.get("action", "HOLD")
    conf = decision.get("conf", 0)

    # Status pipeline
    status = f"ARKON5_{action}_CONF{int(conf*100)}"
    ha_set_input_text("input_text.ai_model_actif", status)

    # Déclencher événement HA pour notifications
    ha_fire_event("s25_arkon5_decision", {
        "action": action,
        "confidence": conf,
        "tp": decision.get("tp"),
        "sl": decision.get("sl"),
        "reason": decision.get("reason", "")
    })

    log.info(f"HA mis à jour: {status}")

# ─────────────────────────────────────────────────────
# MAIN — Pipeline S25
# ─────────────────────────────────────────────────────
def run_pipeline(kimi_signal: str = None):
    """Point d'entrée principal du pipeline S25"""
    log.info("=" * 50)
    log.info("⚡ S25 LUMIÈRE — Pipeline ARKON-5 démarré")

    # 1. Lire signal Kimi depuis HA si non fourni
    if not kimi_signal:
        kimi_signal = ha_get_state("input_text.ai_prompt")

    if not kimi_signal or len(kimi_signal) < 10:
        log.warning("Signal Kimi vide ou trop court — HOLD")
        return

    log.info(f"Signal reçu: {kimi_signal[:100]}...")

    # 2. Analyser avec Gemini
    result = analyze_with_gemini(kimi_signal)

    # 3. Écrire ai_analysis.json
    write_ai_analysis(result)

    # 4. Mettre à jour entités HA
    update_ha_entities(result)

    log.info(f"✅ Pipeline terminé: {result['decision']['action']} ({result['decision']['conf']:.0%})")
    return result

# ─────────────────────────────────────────────────────
# ENTRY POINT (pour HA python_scripts)
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test standalone
    test_signal = """
    BTC/USDT - Signal Kimi Web3 - 2026-03-03
    Prix actuel: 68,450 USDT
    RSI 1h: 58 (zone neutre)
    MACD: crossover haussier détecté
    Volume 24h: +35% au-dessus moyenne
    Sentiment: Bullish modéré
    Whales: Accumulation détectée (>100 BTC moves on-chain)
    Funding MEXC: 0.0012% (neutre)
    Signal: POSSIBLE BUY SETUP si BTC tient au-dessus 68k
    """
    result = run_pipeline(test_signal)
    print(json.dumps(result, indent=2, ensure_ascii=False))

# Pour appel depuis HA automation via python_script.run:
# data = hass.states.get('input_text.ai_prompt').state
# run_pipeline(data)
