"""
S25 Lumière — Human Layer (Sheet 8)
=====================================
Couche pré-humanoïde — pont entre système S25 et actions physiques.

Phase 1: Perception + Decision locale (avant RTX4090)
Phase 2: Vision (Gemini Pro Vision) + Audio (Whisper)
Phase 3: Humanoïde complet sur Akash GPU

Pour l'instant: framework de base, interfaces définies.
Les modules GPU seront activés quand Akash RTX4090 sera live.

Architecture:
  ┌────────────────────────────────────────────┐
  │              HUMAN LAYER                   │
  │  Perception → Memory → Decision → Action   │
  └────────────────────────────────────────────┘
       ↑                              ↓
  Camera/Mic                    HA automations
  Gemini Vision                 TRINITY TTS
  Whisper STT                   Commander signals
"""

import os
import json
import time
import logging
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("s25.human_layer")

# ─── Config ──────────────────────────────────────────────────────────
HA_URL          = os.getenv("HA_URL",          "http://homeassistant.local:8123")
HA_TOKEN        = os.getenv("HA_TOKEN",        "")
COCKPIT_URL     = os.getenv("COCKPIT_URL",     "http://localhost:7777")
COMET_KEY       = os.getenv("COMET_BRIDGE_KEY", "s25-comet-bridge-key")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY",  "")

# GPU endpoint (Akash RTX4090 quand disponible)
GPU_ENDPOINT    = os.getenv("GPU_ENDPOINT",    "")

# Activation flags
VISION_ENABLED  = bool(os.getenv("VISION_ENABLED", ""))
AUDIO_ENABLED   = bool(os.getenv("AUDIO_ENABLED",  ""))
GPU_ENABLED     = bool(GPU_ENDPOINT)


# ─── Data structures ─────────────────────────────────────────────────
@dataclass
class Perception:
    """Une perception entrante (visuelle, audio, textuelle)."""
    ts:       str = field(default_factory=lambda: datetime.utcnow().isoformat())
    type:     str = "TEXT"           # TEXT | VISION | AUDIO
    source:   str = "unknown"
    content:  str = ""
    raw_data: Any = None
    confidence: float = 1.0


@dataclass
class Memory:
    """Mémoire courte/longue terme du système."""
    perceptions:  List[Dict] = field(default_factory=list)
    decisions:    List[Dict] = field(default_factory=list)
    context:      Dict       = field(default_factory=dict)
    created_at:   str        = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Decision:
    """Une décision prise par le système."""
    ts:          str   = field(default_factory=lambda: datetime.utcnow().isoformat())
    input_type:  str   = "TEXT"
    input_summary: str = ""
    action:      str   = "NONE"       # NONE | SPEAK | ALERT | TRADE | HA_COMMAND
    params:      Dict  = field(default_factory=dict)
    confidence:  float = 0.0
    reasoning:   str   = ""


# ─── Global state ────────────────────────────────────────────────────
_memory = Memory()
_memory_lock = threading.Lock()


# ─── Perception Layer ─────────────────────────────────────────────────
def perceive_text(text: str, source: str = "api") -> Perception:
    """Percevoir un signal texte."""
    p = Perception(
        type="TEXT",
        source=source,
        content=text,
        confidence=1.0,
    )
    _store_perception(p)
    return p


def perceive_vision(image_url: str, source: str = "camera") -> Optional[Perception]:
    """
    Analyser une image avec Gemini Vision.
    Retourne une perception avec description textuelle.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — vision disabled")
        return None

    if not VISION_ENABLED:
        logger.info("Vision disabled (VISION_ENABLED not set)")
        return None

    try:
        # Gemini Vision API
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GEMINI_API_KEY}",
            json={
                "contents": [{
                    "parts": [
                        {"text": "Décris ce que tu vois. Contexte: système S25 de surveillance trading crypto. Sois bref et factuel."},
                        {"inlineData": {"mimeType": "image/jpeg", "data": _fetch_image_b64(image_url)}},
                    ]
                }]
            },
            timeout=30,
        )
        if r.status_code == 200:
            content = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            p = Perception(
                type="VISION",
                source=source,
                content=content,
                confidence=0.85,
            )
            _store_perception(p)
            logger.info(f"Vision: {content[:100]}")
            return p
    except Exception as e:
        logger.error(f"Vision perception failed: {e}")
    return None


def _fetch_image_b64(url: str) -> str:
    """Télécharger image et encoder en base64."""
    import base64
    r = requests.get(url, timeout=10)
    return base64.b64encode(r.content).decode()


def _store_perception(p: Perception):
    """Stocker perception en mémoire courte terme."""
    with _memory_lock:
        _memory.perceptions.insert(0, asdict(p))
        # Garder 200 perceptions max
        _memory.perceptions = _memory.perceptions[:200]


# ─── Decision Engine ─────────────────────────────────────────────────
def make_decision(perception: Perception) -> Decision:
    """
    Prendre une décision basée sur une perception.
    Phase 1: Règles simples
    Phase 2: Gemini Pro reasoning (si GPU dispo)
    """
    decision = Decision(
        input_type=perception.type,
        input_summary=perception.content[:200],
    )

    # Règles de base Phase 1
    content = perception.content.upper()

    if any(kw in content for kw in ["ALERTE", "ALERT", "CRITIQUE", "CRITICAL", "T3"]):
        decision.action    = "ALERT"
        decision.confidence = 0.9
        decision.reasoning  = "Mot-clé critique détecté"
        decision.params = {"message": perception.content, "urgent": True}

    elif any(kw in content for kw in ["BUY", "ACHAT", "ACHETER"]):
        decision.action    = "SPEAK"
        decision.confidence = 0.8
        decision.reasoning  = "Signal d'achat détecté"
        decision.params = {"message": f"Signal d'achat détecté. {perception.content[:100]}"}

    elif any(kw in content for kw in ["SELL", "VENTE", "VENDRE"]):
        decision.action    = "SPEAK"
        decision.confidence = 0.8
        decision.reasoning  = "Signal de vente détecté"
        decision.params = {"message": f"Signal de vente détecté. {perception.content[:100]}"}

    elif any(kw in content for kw in ["HA:", "HOMEASSISTANT:", "AUTOMATION:"]):
        decision.action    = "HA_COMMAND"
        decision.confidence = 0.75
        decision.reasoning  = "Commande HA détectée"
        decision.params = {"command": perception.content}

    else:
        decision.action    = "NONE"
        decision.confidence = 0.5
        decision.reasoning  = "Aucune règle déclenchée"

    # Store decision
    with _memory_lock:
        _memory.decisions.insert(0, asdict(decision))
        _memory.decisions = _memory.decisions[:100]

    logger.info(f"Decision: {decision.action} (conf={decision.confidence:.0%}) — {decision.reasoning}")
    return decision


def make_decision_gemini(perception: Perception) -> Optional[Decision]:
    """
    Phase 2: Décision via Gemini Pro (raisonnement avancé).
    Utilise le contexte mémoire pour meilleure décision.
    """
    if not GEMINI_API_KEY:
        return None

    # Build context from memory
    recent_perceptions = _memory.perceptions[:5]
    recent_decisions   = _memory.decisions[:3]
    context = {
        "current_signal":   perception.content,
        "recent_history":   recent_perceptions,
        "recent_decisions": recent_decisions,
        "system_state":     _memory.context,
    }

    prompt = f"""Tu es l'agent de décision du système S25 Lumière — trading crypto automatisé.

Contexte actuel:
{json.dumps(context, indent=2, ensure_ascii=False)[:3000]}

Signal entrant (type={perception.type}):
"{perception.content}"

Réponds en JSON avec ce format EXACT:
{{
  "action": "NONE|SPEAK|ALERT|TRADE|HA_COMMAND",
  "confidence": 0.0-1.0,
  "reasoning": "Explication courte",
  "params": {{}}
}}

Actions disponibles:
- NONE: Ne rien faire
- SPEAK: Jouer message TTS (params: message)
- ALERT: Alerte urgente (params: message, level)
- TRADE: Signal trading (params: action, symbol, confidence)
- HA_COMMAND: Commande HA (params: service, entity_id, data)
"""

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        if r.status_code == 200:
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Extract JSON from response
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return Decision(
                    input_type=perception.type,
                    input_summary=perception.content[:200],
                    action=data.get("action", "NONE"),
                    confidence=float(data.get("confidence", 0)),
                    reasoning=data.get("reasoning", ""),
                    params=data.get("params", {}),
                )
    except Exception as e:
        logger.error(f"Gemini decision failed: {e}")
    return None


# ─── Action Layer ─────────────────────────────────────────────────────
def execute_decision(decision: Decision) -> bool:
    """Exécuter une décision."""
    if decision.action == "NONE":
        return True

    elif decision.action in ("SPEAK", "ALERT"):
        return _action_speak(
            decision.params.get("message", ""),
            urgent=(decision.action == "ALERT")
        )

    elif decision.action == "HA_COMMAND":
        return _action_ha_command(decision.params)

    elif decision.action == "TRADE":
        return _action_trade_signal(decision.params)

    else:
        logger.warning(f"Action inconnue: {decision.action}")
        return False


def _action_speak(message: str, urgent: bool = False) -> bool:
    """Exécuter action vocale via TRINITY."""
    try:
        endpoint = "/api/vocal/alert" if urgent else "/api/vocal/say"
        r = requests.post(
            f"{COCKPIT_URL}{endpoint}",
            json={"message": message, "urgent": urgent},
            headers={"X-S25-Key": COMET_KEY},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"TRINITY speak failed: {e}")
        return False


def _action_ha_command(params: Dict) -> bool:
    """Exécuter une commande HA."""
    if not HA_TOKEN:
        logger.warning("HA_TOKEN not set")
        return False
    try:
        service = params.get("service", "")
        entity_id = params.get("entity_id", "")
        data = params.get("data", {})
        data["entity_id"] = entity_id

        domain, svc = service.split(".", 1) if "." in service else (service, "turn_on")
        r = requests.post(
            f"{HA_URL}/api/services/{domain}/{svc}",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json",
            },
            json=data,
            timeout=5,
        )
        return r.status_code in (200, 201)
    except Exception as e:
        logger.error(f"HA command failed: {e}")
        return False


def _action_trade_signal(params: Dict) -> bool:
    """Envoyer signal de trade vers le cockpit."""
    try:
        r = requests.post(
            f"{COCKPIT_URL}/api/signal",
            json={
                "action":     params.get("action", "HOLD"),
                "symbol":     params.get("symbol", "BTC/USDT"),
                "confidence": params.get("confidence", 0.5),
                "source":     "human_layer",
                "ts":         datetime.utcnow().isoformat(),
            },
            headers={"X-S25-Key": COMET_KEY},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Trade signal failed: {e}")
        return False


# ─── Pipeline complet ─────────────────────────────────────────────────
def process(text: str, source: str = "api") -> Decision:
    """
    Pipeline complet: Texte → Perception → Decision → Action.

    Exemple:
        from agents.human_layer import process
        decision = process("BUY BTC/USDT signal from ARKON-5")
    """
    perception = perceive_text(text, source=source)

    # Phase 2 si Gemini dispo, sinon Phase 1
    if GEMINI_API_KEY:
        decision = make_decision_gemini(perception) or make_decision(perception)
    else:
        decision = make_decision(perception)

    execute_decision(decision)
    return decision


# ─── Flask routes ────────────────────────────────────────────────────
def register_human_routes(app, state: Dict):
    """Injecter routes Human Layer dans le cockpit Flask."""
    from flask import request, jsonify

    def _check_key():
        return request.headers.get("X-S25-Key", "") == COMET_KEY

    @app.route("/api/human/perceive", methods=["POST"])
    def api_human_perceive():
        """Traiter un signal via le Human Layer."""
        if not _check_key():
            return jsonify({"error": "unauthorized"}), 401
        data = request.json or {}
        text   = data.get("text", "")
        source = data.get("source", "api")
        if not text:
            return jsonify({"error": "text requis"}), 400
        decision = process(text, source=source)
        return jsonify({"ok": True, "decision": asdict(decision)})

    @app.route("/api/human/memory", methods=["GET"])
    def api_human_memory():
        """Lire la mémoire courante."""
        n = int(request.args.get("n", 10))
        with _memory_lock:
            return jsonify({
                "ok":          True,
                "perceptions": _memory.perceptions[:n],
                "decisions":   _memory.decisions[:n],
                "context":     _memory.context,
            })

    @app.route("/api/human/status", methods=["GET"])
    def api_human_status():
        """Statut Human Layer."""
        return jsonify({
            "ok":             True,
            "phase":          2 if GEMINI_API_KEY else 1,
            "vision_enabled": VISION_ENABLED,
            "audio_enabled":  AUDIO_ENABLED,
            "gpu_enabled":    GPU_ENABLED,
            "gpu_endpoint":   GPU_ENDPOINT or None,
            "perceptions":    len(_memory.perceptions),
            "decisions":      len(_memory.decisions),
            "ts":             datetime.utcnow().isoformat(),
        })

    logger.info("Human Layer routes registered: /api/human/perceive|memory|status")


# ─── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="S25 Human Layer")
    parser.add_argument("--process", type=str, help="Traiter un signal texte")
    parser.add_argument("--test",    action="store_true", help="Test avec signaux mock")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║   S25 Human Layer (Sheet 8)         ║
║   Phase: {'2 (Gemini)' if GEMINI_API_KEY else '1 (règles)'}                    ║
║   Vision: {'ON' if VISION_ENABLED else 'OFF'} | Audio: {'ON' if AUDIO_ENABLED else 'OFF'} | GPU: {'ON' if GPU_ENABLED else 'OFF'}  ║
╚══════════════════════════════════════╝
""")

    if args.test:
        test_signals = [
            ("BUY BTC/USDT signal — confidence 0.87", "arkon5"),
            ("ALERTE T2 — hashrate Antminer critique!", "monitoring"),
            ("HOLD — marché consolidation", "gemini"),
            ("HA: automation.s25_backup à activer", "commander"),
        ]
        for text, source in test_signals:
            print(f"\n📡 Signal [{source}]: {text}")
            decision = process(text, source=source)
            print(f"   → Action: {decision.action} (conf={decision.confidence:.0%})")
            print(f"   → {decision.reasoning}")

    elif args.process:
        decision = process(args.process, source="cli")
        print(f"\nDécision: {decision.action}")
        print(f"Confiance: {decision.confidence:.0%}")
        print(f"Raisonnement: {decision.reasoning}")
        if decision.params:
            print(f"Params: {json.dumps(decision.params, ensure_ascii=False)}")
    else:
        parser.print_help()
