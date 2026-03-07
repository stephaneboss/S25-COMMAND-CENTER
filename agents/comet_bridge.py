"""
S25 Lumière — COMET Bridge
============================
Point de connexion entre COMET (Perplexity Watchman) et le système S25.

COMET peut envoyer de l'intel via:
  POST /api/intel          → cockpit_lumiere.py (port 7777)
  POST /api/threat         → mise à jour niveau T0-T3
  GET  /api/status         → état du système complet

Le bridge expose aussi une API locale pour que les autres
agents puissent interroger COMET via HA ou directement.

Usage Perplexity / COMET:
  curl -X POST http://<cockpit-url>/api/intel \\
    -H "Content-Type: application/json" \\
    -H "X-S25-Key: <COMET_BRIDGE_KEY>" \\
    -d '{"source":"comet","level":"INFO","summary":"BTC breakout détecté","data":{}}'
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("s25.comet")

# ─── Config ──────────────────────────────────────────────────────────
COCKPIT_URL     = os.getenv("COCKPIT_URL",     "http://localhost:7777")
HA_URL          = os.getenv("HA_URL",          "http://homeassistant.local:8123")
HA_TOKEN        = os.getenv("HA_TOKEN",        "")
COMET_BRIDGE_KEY = os.getenv("COMET_BRIDGE_KEY", "s25-comet-bridge-key")

# HA entity pour stocker l'intel COMET
HA_ENTITY_INTEL   = "input_text.comet_intel"
HA_ENTITY_STATUS  = "input_text.comet_status"
HA_ENTITY_THREAT  = "input_select.s25_threat_level"


# ─── Intel payload structure ──────────────────────────────────────────
def build_intel_payload(
    source: str,
    summary: str,
    level: str = "INFO",       # INFO | WARNING | ALERT | CRITICAL
    data: Dict = None,
    threat_level: Optional[int] = None,
) -> Dict:
    """Build standardized intel payload for COMET → S25."""
    return {
        "source":       source,
        "summary":      summary,
        "level":        level,
        "data":         data or {},
        "threat_level": threat_level,
        "ts":           datetime.utcnow().isoformat(),
        "version":      "1.0",
    }


# ─── Send to Cockpit ─────────────────────────────────────────────────
def push_intel_to_cockpit(payload: Dict) -> bool:
    """Push intel from COMET to S25 Cockpit."""
    try:
        r = requests.post(
            f"{COCKPIT_URL}/api/intel",
            json=payload,
            headers={"X-S25-Key": COMET_BRIDGE_KEY},
            timeout=5,
        )
        if r.status_code == 200:
            logger.info(f"COMET intel pushed: [{payload['level']}] {payload['summary']}")
            return True
        else:
            logger.warning(f"Cockpit push failed: {r.status_code}")
            return False
    except Exception as e:
        logger.error(f"Cockpit unreachable: {e}")
        return False


def push_threat_to_cockpit(level: int, reason: str = "") -> bool:
    """Update threat level from COMET."""
    try:
        r = requests.post(
            f"{COCKPIT_URL}/api/threat",
            json={"level": level, "reason": reason, "source": "comet"},
            headers={"X-S25-Key": COMET_BRIDGE_KEY},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Threat update failed: {e}")
        return False


# ─── Send to Home Assistant ──────────────────────────────────────────
def push_intel_to_ha(payload: Dict) -> bool:
    """Mirror COMET intel to HA entity for automations."""
    if not HA_TOKEN:
        return False
    try:
        summary = f"[{payload['level']}] {payload['summary']}"[:255]  # HA limit
        r = requests.post(
            f"{HA_URL}/api/states/{HA_ENTITY_INTEL}",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type":  "application/json",
            },
            json={
                "state":      summary,
                "attributes": {
                    "source":       payload.get("source", "comet"),
                    "level":        payload.get("level", "INFO"),
                    "data":         json.dumps(payload.get("data", {}))[:255],
                    "ts":           payload.get("ts", ""),
                    "friendly_name": "COMET Intel Feed",
                },
            },
            timeout=5,
        )
        return r.status_code in (200, 201)
    except Exception as e:
        logger.error(f"HA push failed: {e}")
        return False


def push_threat_to_ha(level: int) -> bool:
    """Update HA threat level entity."""
    if not HA_TOKEN:
        return False
    level_map = {0: "T0", 1: "T1", 2: "T2", 3: "T3"}
    try:
        r = requests.post(
            f"{HA_URL}/api/services/input_select/select_option",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type":  "application/json",
            },
            json={
                "entity_id": HA_ENTITY_THREAT,
                "option":    level_map.get(level, "T0"),
            },
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"HA threat update failed: {e}")
        return False


# ─── Read from Cockpit (COMET queries system status) ─────────────────
def get_system_status() -> Optional[Dict]:
    """
    COMET queries the cockpit for full system status.
    Returns dict with threat_level, signal, ha_online, etc.
    """
    try:
        r = requests.get(f"{COCKPIT_URL}/api/status", timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def get_current_signal() -> Optional[Dict]:
    """Get latest ARKON-5 signal for COMET context."""
    status = get_system_status()
    if status:
        return status.get("signal")
    return None


# ─── Flask routes to add to cockpit ──────────────────────────────────
def register_comet_routes(app, state: Dict):
    """
    Register COMET bridge routes on the cockpit Flask app.
    Call this from cockpit_lumiere.py:
        from agents.comet_bridge import register_comet_routes
        register_comet_routes(app, state)
    """
    from flask import request, jsonify

    def _check_key():
        key = request.headers.get("X-S25-Key", "")
        return key == COMET_BRIDGE_KEY

    @app.route("/api/intel", methods=["POST"])
    def api_intel():
        """Receive intel from COMET or any S25 agent."""
        if not _check_key():
            return jsonify({"error": "unauthorized"}), 401

        data = request.json or {}
        entry = {
            "ts":      datetime.utcnow().isoformat(),
            "source":  data.get("source", "unknown"),
            "level":   data.get("level", "INFO"),
            "summary": data.get("summary", ""),
            "data":    data.get("data", {}),
        }

        # Append to state logs
        state.setdefault("comet_feed", []).insert(0, entry)
        state["comet_feed"] = state["comet_feed"][:100]  # Keep last 100

        # Auto-escalate threat if COMET sends ALERT/CRITICAL
        if entry["level"] == "CRITICAL" and state.get("threat_level", 0) < 3:
            state["threat_level"] = 3
        elif entry["level"] == "ALERT" and state.get("threat_level", 0) < 2:
            state["threat_level"] = 2

        logger.info(f"[COMET] [{entry['level']}] {entry['summary']}")
        return jsonify({"ok": True, "ts": entry["ts"]})

    @app.route("/api/comet/feed", methods=["GET"])
    def api_comet_feed():
        """COMET or UI reads the intel feed."""
        n = int(request.args.get("n", 20))
        return jsonify({
            "ok":    True,
            "feed":  state.get("comet_feed", [])[:n],
            "count": len(state.get("comet_feed", [])),
        })

    @app.route("/api/comet/ping", methods=["GET", "POST"])
    def api_comet_ping():
        """COMET health check — confirms bridge is alive."""
        return jsonify({
            "ok":           True,
            "bridge":       "comet",
            "ts":           datetime.utcnow().isoformat(),
            "threat_level": state.get("threat_level", 0),
            "ha_online":    state.get("ha_online", False),
        })

    @app.route("/api/comet/status-check", methods=["GET"])
    def api_comet_status_check():
        """COMET full system status check — Québécois edition."""
        threat = state.get("threat_level", 0)
        ha_ok  = state.get("ha_online", False)
        sig    = state.get("signal", {})

        if threat == 0 and ha_ok:
            vibe = "TABARNAK — ça roule en crisse ! 🚀"
            status = "OPTIMAL"
        elif threat == 1:
            vibe = "Câline, on surveille... T1 actif."
            status = "SURVEILLANCE"
        elif threat == 2:
            vibe = "Ostie, alerte T2 — on reste sharp !"
            status = "ALERTE"
        elif threat == 3:
            vibe = "CRISSE — T3 CRITIQUE, KILL SWITCH !"
            status = "CRITIQUE"
        else:
            vibe = "En attente boss..."
            status = "STANDBY"

        return jsonify({
            "ok":           True,
            "vibe":         vibe,
            "status":       status,
            "threat_level": threat,
            "ha_online":    ha_ok,
            "signal":       sig.get("action", "STANDBY"),
            "ts":           datetime.utcnow().isoformat(),
        })

    logger.info("COMET bridge routes registered: /api/intel, /api/comet/feed, /api/comet/ping, /api/comet/status-check")


# ─── Convenience: send from any agent ────────────────────────────────
def comet_send(summary: str, level: str = "INFO", data: Dict = None,
               threat: int = None) -> bool:
    """
    One-liner for any S25 agent to send intel to COMET bridge.

    Example:
        from agents.comet_bridge import comet_send
        comet_send("BTC/USDT BUY signal confirmed", level="INFO", data={"price": 65000})
        comet_send("RISK: daily loss limit 80%", level="ALERT", threat=2)
    """
    payload = build_intel_payload(
        source="s25_agent",
        summary=summary,
        level=level,
        data=data,
        threat_level=threat,
    )
    ok_cockpit = push_intel_to_cockpit(payload)
    ok_ha      = push_intel_to_ha(payload)

    if threat is not None:
        push_threat_to_cockpit(threat, summary)
        push_threat_to_ha(threat)

    return ok_cockpit or ok_ha


# ─── CLI test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== COMET Bridge — Test ===")
    print(f"Cockpit: {COCKPIT_URL}")
    print(f"HA:      {HA_URL}")

    # Test status
    status = get_system_status()
    if status:
        print(f"✅ Cockpit status: T{status.get('threat_level',0)} | "
              f"Signal: {status.get('signal',{}).get('action','---')}")
    else:
        print("❌ Cockpit not reachable (normal if not running)")

    # Test intel send
    ok = comet_send(
        "COMET bridge test — connexion OK",
        level="INFO",
        data={"test": True, "ts": datetime.utcnow().isoformat()},
    )
    print(f"Intel push: {'✅ OK' if ok else '❌ Failed (cockpit offline?)'}")
