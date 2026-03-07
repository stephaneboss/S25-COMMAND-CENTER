"""
S25 Lumière — ARKON-5 Bridge (Sheet 5)
=======================================
Pont entre Home Assistant (capteurs) et le système ARKON-5.

Récupère les états HA → mappe en signaux trading/survie →
envoie vers cockpit Akash + Commander.

Usage:
  python scripts/arkon5_bridge.py              # Run once
  python scripts/arkon5_bridge.py --watch      # Watch mode (60s loop)
  python scripts/arkon5_bridge.py --test       # Test avec données mock
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime
from typing import Dict, Optional, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ARKON5] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("arkon5_bridge")

# ─── Config ──────────────────────────────────────────────────────────
HA_URL          = os.getenv("HA_URL",          "http://homeassistant.local:8123")
HA_TOKEN        = os.getenv("HA_TOKEN",        "")
COCKPIT_URL     = os.getenv("COCKPIT_URL",     "http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com")
COMET_KEY       = os.getenv("COMET_BRIDGE_KEY", "s25-comet-bridge-key")
WATCH_INTERVAL  = int(os.getenv("CHECK_INTERVAL", "60"))

# ─── HA Entity Map → ARKON Signal ────────────────────────────────────
#
# Mappe tes capteurs HA sur des signaux ARKON-5.
# Format: "entity_id": { "signal": ..., "threshold": ..., "action": ... }
#
ENTITY_MAP = {
    # Trading signals (depuis Kimi/Gemini via HA)
    "input_text.arkon5_signal": {
        "type": "TRADING_SIGNAL",
        "parse_json": True,
    },
    "input_select.s25_threat_level": {
        "type": "THREAT_LEVEL",
        "map": {"T0": 0, "T1": 1, "T2": 2, "T3": 3},
    },
    "input_boolean.ai_auto_mode": {
        "type": "AUTO_MODE",
        "map": {"on": True, "off": False},
    },

    # Antminer monitoring
    "sensor.antminer_hashrate": {
        "type": "HASHRATE",
        "unit": "TH/s",
        "alert_below": 90.0,    # Alert si < 90 TH/s
    },
    "sensor.antminer_temperature": {
        "type": "TEMP",
        "unit": "°C",
        "alert_above": 80.0,    # Alert si > 80°C
    },

    # Système
    "sensor.s25_mexc_last_order": {
        "type": "MEXC_ORDER",
    },
}


# ─── Fetch HA states ─────────────────────────────────────────────────
def fetch_ha_states(entity_ids: List[str] = None) -> Dict:
    """Fetch entity states from Home Assistant API."""
    if not HA_TOKEN:
        logger.warning("HA_TOKEN not set — using mock data")
        return _mock_states()

    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type":  "application/json",
    }

    try:
        if entity_ids:
            # Fetch specific entities
            states = {}
            for eid in entity_ids:
                r = requests.get(
                    f"{HA_URL}/api/states/{eid}",
                    headers=headers, timeout=5
                )
                if r.status_code == 200:
                    states[eid] = r.json()
        else:
            # Fetch all states
            r = requests.get(
                f"{HA_URL}/api/states",
                headers=headers, timeout=10
            )
            if r.status_code != 200:
                logger.error(f"HA API error: {r.status_code}")
                return {}
            states = {e["entity_id"]: e for e in r.json()}

        logger.info(f"Fetched {len(states)} HA states")
        return states

    except Exception as e:
        logger.error(f"HA fetch failed: {e}")
        return {}


def _mock_states() -> Dict:
    """Mock states for testing without HA."""
    return {
        "input_text.arkon5_signal": {
            "entity_id": "input_text.arkon5_signal",
            "state": json.dumps({
                "action": "BUY",
                "symbol": "BTC/USDT",
                "confidence": 0.87,
                "price": 65000,
                "source": "gemini_arkon5",
            }),
            "last_updated": datetime.utcnow().isoformat(),
        },
        "input_select.s25_threat_level": {
            "entity_id": "input_select.s25_threat_level",
            "state": "T0",
        },
        "input_boolean.ai_auto_mode": {
            "entity_id": "input_boolean.ai_auto_mode",
            "state": "on",
        },
    }


# ─── Parse & map signals ─────────────────────────────────────────────
def parse_arkon_signal(states: Dict) -> Optional[Dict]:
    """
    Parse HA states and extract ARKON-5 trading signal.
    Returns signal dict or None.
    """
    signal_ent = states.get("input_text.arkon5_signal")
    if not signal_ent:
        return None

    raw_state = signal_ent.get("state", "")
    if not raw_state or raw_state in ("unknown", "unavailable", ""):
        return None

    # Try JSON parse
    try:
        signal = json.loads(raw_state)
        signal["ts"] = signal_ent.get("last_updated", datetime.utcnow().isoformat())
        signal["source_entity"] = "input_text.arkon5_signal"
        return signal
    except json.JSONDecodeError:
        # Plain text signal (eg: "BUY BTC/USDT 0.87")
        parts = raw_state.split()
        if parts and parts[0] in ("BUY", "SELL", "HOLD"):
            return {
                "action":     parts[0],
                "symbol":     parts[1] if len(parts) > 1 else "BTC/USDT",
                "confidence": float(parts[2]) if len(parts) > 2 else 0.75,
                "price":      0,
                "ts":         datetime.utcnow().isoformat(),
                "source":     "ha_text",
            }
    return None


def parse_threat_level(states: Dict) -> int:
    """Extract threat level from HA."""
    ent = states.get("input_select.s25_threat_level")
    if not ent:
        return 0
    state = ent.get("state", "T0").upper()
    return {"T0": 0, "T1": 1, "T2": 2, "T3": 3}.get(state, 0)


def parse_system_alerts(states: Dict) -> List[Dict]:
    """Check for system alerts (Antminer, etc.)."""
    alerts = []

    # Antminer hashrate
    hr_ent = states.get("sensor.antminer_hashrate")
    if hr_ent:
        try:
            hr = float(hr_ent.get("state", 0))
            if hr < 90.0:
                alerts.append({
                    "type":    "HASHRATE_LOW",
                    "value":   hr,
                    "message": f"Antminer hashrate faible: {hr} TH/s (seuil: 90)",
                    "level":   "WARNING",
                })
        except (ValueError, TypeError):
            pass

    # Antminer temperature
    temp_ent = states.get("sensor.antminer_temperature")
    if temp_ent:
        try:
            temp = float(temp_ent.get("state", 0))
            if temp > 80.0:
                alerts.append({
                    "type":    "TEMP_HIGH",
                    "value":   temp,
                    "message": f"Antminer temp élevée: {temp}°C (seuil: 80)",
                    "level":   "ALERT",
                })
        except (ValueError, TypeError):
            pass

    return alerts


# ─── Push to Cockpit ─────────────────────────────────────────────────
def push_signal_to_cockpit(signal: Dict) -> bool:
    """Send ARKON-5 signal to cockpit."""
    try:
        r = requests.post(
            f"{COCKPIT_URL}/api/signal",
            json=signal,
            headers={"X-S25-Key": COMET_KEY},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Cockpit push failed: {e}")
        return False


def push_threat_to_cockpit(level: int) -> bool:
    """Update threat level in cockpit."""
    try:
        r = requests.post(
            f"{COCKPIT_URL}/api/threat",
            json={"level": level},
            headers={"X-S25-Key": COMET_KEY},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Threat push failed: {e}")
        return False


def push_alert_to_cockpit(alert: Dict) -> bool:
    """Send system alert via COMET bridge."""
    try:
        r = requests.post(
            f"{COCKPIT_URL}/api/intel",
            json={
                "source":  "arkon5_bridge",
                "level":   alert.get("level", "WARNING"),
                "summary": alert.get("message", ""),
                "data":    alert,
            },
            headers={"X-S25-Key": COMET_KEY},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Alert push failed: {e}")
        return False


# ─── Write JSON log for Akash CentOS ─────────────────────────────────
def write_log_json(signal: Optional[Dict], threat: int, alerts: List) -> str:
    """Write structured JSON log — readable by CentOS watchdog."""
    log_entry = {
        "ts":           datetime.utcnow().isoformat(),
        "threat_level": threat,
        "signal":       signal,
        "alerts":       alerts,
        "status":       "OK" if not alerts else "ALERT",
        "source":       "arkon5_bridge",
    }

    log_path = "/tmp/arkon5_last.json"
    try:
        with open(log_path, "w") as f:
            json.dump(log_entry, f, indent=2)
        logger.info(f"Log written: {log_path}")
    except Exception as e:
        logger.warning(f"Could not write log: {e}")

    return json.dumps(log_entry, indent=2)


# ─── Main bridge loop ─────────────────────────────────────────────────
def run_bridge(test_mode: bool = False):
    """Single bridge run — fetch HA → parse → push to cockpit."""
    logger.info(f"{'[TEST MODE] ' if test_mode else ''}ARKON-5 bridge run started")

    # Fetch
    states = fetch_ha_states(list(ENTITY_MAP.keys()))
    if not states:
        logger.warning("No HA states — cockpit update skipped")
        return

    # Parse
    signal  = parse_arkon_signal(states)
    threat  = parse_threat_level(states)
    alerts  = parse_system_alerts(states)

    # Log
    log_json = write_log_json(signal, threat, alerts)

    if signal:
        logger.info(f"Signal: {signal.get('action')} {signal.get('symbol')} "
                    f"conf={signal.get('confidence', 0):.0%}")
    if alerts:
        for a in alerts:
            logger.warning(f"Alert: {a['message']}")

    if test_mode:
        print("\n=== ARKON-5 Bridge Output ===")
        print(log_json)
        return

    # Push to cockpit
    if signal:
        ok = push_signal_to_cockpit(signal)
        logger.info(f"Signal pushed: {'✅' if ok else '❌'}")

    ok = push_threat_to_cockpit(threat)
    logger.info(f"Threat T{threat} pushed: {'✅' if ok else '❌'}")

    for alert in alerts:
        ok = push_alert_to_cockpit(alert)
        logger.info(f"Alert pushed: {'✅' if ok else '❌'}")

    logger.info("Bridge run complete")


# ─── Entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="S25 ARKON-5 Bridge")
    parser.add_argument("--watch", action="store_true",
                        help=f"Watch mode — runs every {WATCH_INTERVAL}s")
    parser.add_argument("--test",  action="store_true",
                        help="Test mode — uses mock data, no cockpit push")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║   S25 ARKON-5 Bridge (Sheet 5)      ║
║   HA: {HA_URL[:28]}  ║
║   Cockpit: {COCKPIT_URL[:24]}  ║
╚══════════════════════════════════════╝
""")

    if args.test:
        run_bridge(test_mode=True)
    elif args.watch:
        logger.info(f"Watch mode — interval: {WATCH_INTERVAL}s")
        while True:
            try:
                run_bridge()
            except Exception as e:
                logger.error(f"Bridge error: {e}")
            time.sleep(WATCH_INTERVAL)
    else:
        run_bridge()
