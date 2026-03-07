"""
S25 Lumière — TRINITY Vocal Pipeline (Sheet 7)
================================================
Pont entre GPT/GOUV4 et Home Assistant TTS.

TRINITY = Text-to-Speech pipeline pour cockpit vocal.
Reçoit texte → joue via HA media_player (TTS).

Intégration:
  GPT (GOUV4) → POST /api/vocal/say → HA TTS service → Speaker

Routes Flask (à injecter dans cockpit_lumiere.py):
  POST /api/vocal/say     → Joue un message vocal immédiatement
  POST /api/vocal/alert   → Alerte prioritaire (interrompt)
  GET  /api/vocal/status  → Statut du pipeline vocal
  GET  /api/vocal/history → Derniers messages joués

Usage direct:
  python agents/trinity_vocal.py --say "S25 en ligne, tous les systèmes nominaux"
  python agents/trinity_vocal.py --test
"""

import os
import json
import time
import logging
import requests
import argparse
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("s25.trinity")

# ─── Config ──────────────────────────────────────────────────────────
HA_URL          = os.getenv("HA_URL",          "http://homeassistant.local:8123")
HA_TOKEN        = os.getenv("HA_TOKEN",        "")
COCKPIT_URL     = os.getenv("COCKPIT_URL",     "http://localhost:7777")
COMET_KEY       = os.getenv("COMET_BRIDGE_KEY", "s25-comet-bridge-key")

# HA TTS config
TTS_SERVICE     = os.getenv("TTS_SERVICE",     "tts.cloud_say")         # cloud_say ou google_translate
TTS_LANGUAGE    = os.getenv("TTS_LANGUAGE",    "fr-CA")                 # Québécois!
TTS_MEDIA_PLAYER = os.getenv("TTS_MEDIA_PLAYER", "media_player.s25_speaker")

# Limites
MAX_HISTORY     = 50
MIN_INTERVAL    = 3.0   # Secondes entre messages (anti-spam)

# État local
_vocal_history: List[Dict] = []
_last_spoken_ts: float = 0.0


# ─── HA TTS ──────────────────────────────────────────────────────────
def speak_via_ha(message: str, language: str = None, urgent: bool = False) -> bool:
    """
    Send TTS message to Home Assistant.
    Plays on TTS_MEDIA_PLAYER via TTS_SERVICE.
    """
    global _last_spoken_ts

    if not HA_TOKEN:
        logger.warning("HA_TOKEN not set — TTS disabled")
        return False

    # Rate limiting (sauf urgent)
    now = time.time()
    if not urgent and (now - _last_spoken_ts) < MIN_INTERVAL:
        logger.warning(f"TTS rate limit — attendez {MIN_INTERVAL}s")
        return False

    lang = language or TTS_LANGUAGE
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type":  "application/json",
    }

    try:
        # Use HA TTS service
        r = requests.post(
            f"{HA_URL}/api/services/tts/speak",
            headers=headers,
            json={
                "entity_id": TTS_MEDIA_PLAYER,
                "message":   message,
                "language":  lang,
                "options":   {"voice": "fr-CA-AntoineNeural"} if "cloud" in TTS_SERVICE else {},
            },
            timeout=10,
        )

        if r.status_code in (200, 201):
            _last_spoken_ts = now
            logger.info(f"TRINITY 🎙️: {message[:80]}")
            _log_vocal(message, lang, success=True)
            return True
        else:
            logger.error(f"HA TTS error: {r.status_code} — {r.text[:200]}")
            _log_vocal(message, lang, success=False, error=str(r.status_code))
            return False

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        _log_vocal(message, lang, success=False, error=str(e))
        return False


def speak_alert(message: str) -> bool:
    """Alerte prioritaire — ignore rate limit."""
    # Optionnel: jouer un son d'alerte avant le message
    try:
        if HA_TOKEN:
            requests.post(
                f"{HA_URL}/api/services/media_player/play_media",
                headers={
                    "Authorization": f"Bearer {HA_TOKEN}",
                    "Content-Type":  "application/json",
                },
                json={
                    "entity_id":  TTS_MEDIA_PLAYER,
                    "media_content_id": "https://www.soundjay.com/button/beep-07.wav",
                    "media_content_type": "music",
                },
                timeout=5,
            )
            time.sleep(0.8)
    except Exception:
        pass  # Son optionnel, on continue

    return speak_via_ha(message, urgent=True)


# ─── Log ─────────────────────────────────────────────────────────────
def _log_vocal(message: str, language: str, success: bool, error: str = None):
    """Ajoute à l'historique vocal."""
    entry = {
        "ts":       datetime.utcnow().isoformat(),
        "message":  message,
        "language": language,
        "success":  success,
        "error":    error,
    }
    _vocal_history.insert(0, entry)
    # Garder seulement les derniers MAX_HISTORY
    while len(_vocal_history) > MAX_HISTORY:
        _vocal_history.pop()


# ─── Flask routes ────────────────────────────────────────────────────
def register_trinity_routes(app, state: Dict):
    """
    Injecter les routes TRINITY dans le cockpit Flask.
    Appeler depuis cockpit_lumiere.py:
        from agents.trinity_vocal import register_trinity_routes
        register_trinity_routes(app, state)
    """
    from flask import request, jsonify

    def _check_key():
        key = request.headers.get("X-S25-Key", "")
        return key == COMET_KEY

    @app.route("/api/vocal/say", methods=["POST"])
    def api_vocal_say():
        """Joue un message TTS."""
        if not _check_key():
            return jsonify({"error": "unauthorized"}), 401

        data = request.json or {}
        message  = data.get("message", "").strip()
        language = data.get("language", TTS_LANGUAGE)
        urgent   = data.get("urgent", False)

        if not message:
            return jsonify({"error": "message requis"}), 400

        ok = speak_via_ha(message, language=language, urgent=urgent)
        return jsonify({
            "ok":      ok,
            "message": message,
            "ts":      datetime.utcnow().isoformat(),
        })

    @app.route("/api/vocal/alert", methods=["POST"])
    def api_vocal_alert():
        """Alerte prioritaire — son + message."""
        if not _check_key():
            return jsonify({"error": "unauthorized"}), 401

        data = request.json or {}
        message = data.get("message", "ALERTE système S25!").strip()

        ok = speak_alert(message)

        # Aussi envoyer au COMET feed
        state.setdefault("comet_feed", []).insert(0, {
            "ts":      datetime.utcnow().isoformat(),
            "source":  "trinity",
            "level":   "ALERT",
            "summary": f"🎙️ Alerte vocale: {message[:100]}",
            "data":    {"message": message},
        })

        return jsonify({"ok": ok, "message": message})

    @app.route("/api/vocal/status", methods=["GET"])
    def api_vocal_status():
        """Statut pipeline TRINITY."""
        return jsonify({
            "ok":           True,
            "trinity":      "ONLINE",
            "ha_token":     bool(HA_TOKEN),
            "tts_service":  TTS_SERVICE,
            "media_player": TTS_MEDIA_PLAYER,
            "language":     TTS_LANGUAGE,
            "history_count": len(_vocal_history),
            "ts":           datetime.utcnow().isoformat(),
        })

    @app.route("/api/vocal/history", methods=["GET"])
    def api_vocal_history():
        """Derniers messages joués."""
        n = int(request.args.get("n", 10))
        return jsonify({
            "ok":      True,
            "history": _vocal_history[:n],
            "count":   len(_vocal_history),
        })

    logger.info("TRINITY routes registered: /api/vocal/say|alert|status|history")


# ─── Convenience helper ───────────────────────────────────────────────
def trinity_say(message: str, urgent: bool = False) -> bool:
    """
    One-liner pour tout agent S25.

    Exemple:
        from agents.trinity_vocal import trinity_say
        trinity_say("Signal BUY confirmé — BTC/USDT 65k")
        trinity_say("ALERTE: hashrate Antminer critique!", urgent=True)
    """
    if urgent:
        return speak_alert(message)
    return speak_via_ha(message)


# ─── GOUV4/GPT Vocal Templates ────────────────────────────────────────
VOCAL_TEMPLATES = {
    "startup":   "S25 Lumière en ligne. Tous les systèmes nominaux. Niveau de menace: {threat}.",
    "buy":       "Signal d'achat détecté. {symbol} à {price} dollars. Confiance: {confidence} pourcent.",
    "sell":      "Signal de vente. {symbol}. Action recommandée: vendre.",
    "hold":      "Signal de maintien pour {symbol}. On garde la position.",
    "alert_t1":  "Attention. Niveau de menace un activé. Surveillance renforcée.",
    "alert_t2":  "Alerte niveau deux. Réduire l'exposition. Rester vigilant.",
    "alert_t3":  "ALERTE CRITIQUE. Niveau trois. Kill switch disponible. Intervention requise.",
    "akt_low":   "Attention. Solde AKT faible: {balance} tokens. Recharger le wallet.",
    "hashrate":  "Alerte Antminer. Hash rate insuffisant: {value} tera hash par seconde.",
    "cockpit":   "Tableau de bord S25 opérationnel. Akash en ligne.",
    "kill":      "Kill switch activé. Arrêt d'urgence. Aucun trade ne sera exécuté.",
}


def say_template(template_key: str, urgent: bool = False, **kwargs) -> bool:
    """Joue un message vocal depuis un template."""
    template = VOCAL_TEMPLATES.get(template_key, "")
    if not template:
        logger.warning(f"Template inconnu: {template_key}")
        return False
    message = template.format(**kwargs)
    return trinity_say(message, urgent=urgent)


# ─── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="S25 TRINITY Vocal Pipeline")
    parser.add_argument("--say",  type=str, help="Message à jouer via TTS")
    parser.add_argument("--alert", type=str, help="Alerte prioritaire")
    parser.add_argument("--test",  action="store_true", help="Test avec mock")
    parser.add_argument("--template", type=str, help="Jouer un template (ex: startup)")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║   S25 TRINITY — Vocal Pipeline      ║
║   TTS: {TTS_SERVICE[:28]}  ║
║   Lang: {TTS_LANGUAGE:<28}  ║
╚══════════════════════════════════════╝
""")

    if args.test:
        print("Templates disponibles:")
        for k, v in VOCAL_TEMPLATES.items():
            print(f"  {k:15} → {v[:60]}...")
        print("\n[TEST] HA_TOKEN:", "SET ✅" if HA_TOKEN else "NOT SET ❌")
        print("[TEST] HA_URL:", HA_URL)
        if HA_TOKEN:
            ok = trinity_say("Test TRINITY. Système vocal S25 opérationnel. Tabarnak, ça marche!")
            print(f"TTS test: {'✅ OK' if ok else '❌ Échec'}")

    elif args.say:
        ok = trinity_say(args.say)
        print(f"{'✅ Joué' if ok else '❌ Échec'}: {args.say}")

    elif args.alert:
        ok = trinity_say(args.alert, urgent=True)
        print(f"{'✅ Alerte jouée' if ok else '❌ Échec'}: {args.alert}")

    elif args.template:
        ok = say_template(args.template)
        print(f"{'✅ Template joué' if ok else '❌ Échec'}: {args.template}")

    else:
        parser.print_help()
