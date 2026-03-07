"""
S25 LUMIÈRE — Monitor Service (Container 5/5)
==============================================
Watchdog + Health checks pour tous les micro-services.

Surveille:
  - core-dev     :7777  /health
  - intel-comet  :7778  /health
  - voice-relay  :7779  (WebSocket ping)
  - executor     :7780  /health

Alertes via:
  - POST /api/intel cockpit (COMET feed)
  - HA webhook si configuré

Usage:
  python scripts/monitor_service.py           # HTTP API mode (port 7781)
  python scripts/monitor_service.py --watch   # Watch mode (30s loop, no HTTP)
  python scripts/monitor_service.py --once    # Check une fois et quitte
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MONITOR] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("s25.monitor")

# ─── Config ──────────────────────────────────────────────────────────
PORT            = int(os.getenv("PORT", "7781"))
S25_SECRET      = os.getenv("S25_SHARED_SECRET", "s25-inter-service-key-2026")
COCKPIT_URL     = os.getenv("COCKPIT_URL", "http://core-dev:7777")
WATCH_INTERVAL  = int(os.getenv("MONITOR_INTERVAL", "30"))
ALERT_WEBHOOK   = os.getenv("ALERT_WEBHOOK", "")

# Cibles à surveiller (depuis env ou défauts)
_raw_targets = os.getenv(
    "WATCH_TARGETS",
    "http://core-dev:7777/health,http://intel-comet:7778/health,http://executor:7780/health"
)
WATCH_TARGETS = [t.strip() for t in _raw_targets.split(",") if t.strip()]

# ─── État global ─────────────────────────────────────────────────────
_monitor_state: Dict = {
    "started_at": datetime.utcnow().isoformat(),
    "checks_total": 0,
    "alerts_sent": 0,
    "services": {},
    "last_check": None,
}
_alert_history: List[Dict] = []
_prev_states: Dict = {}


# ─── Health Check ─────────────────────────────────────────────────────
def check_service(url: str, timeout: int = 5) -> Dict:
    """Checker le health d'un service."""
    name = _url_to_name(url)
    try:
        r = requests.get(url, timeout=timeout)
        ok = r.status_code in (200, 201)
        latency_ms = int(r.elapsed.total_seconds() * 1000)
        return {
            "name":       name,
            "url":        url,
            "ok":         ok,
            "status":     r.status_code,
            "latency_ms": latency_ms,
            "ts":         datetime.utcnow().isoformat(),
        }
    except requests.exceptions.ConnectionError:
        return {"name": name, "url": url, "ok": False, "error": "CONNECTION_REFUSED", "ts": datetime.utcnow().isoformat()}
    except requests.exceptions.Timeout:
        return {"name": name, "url": url, "ok": False, "error": "TIMEOUT",            "ts": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"name": name, "url": url, "ok": False, "error": str(e),               "ts": datetime.utcnow().isoformat()}


def _url_to_name(url: str) -> str:
    """Extraire un nom lisible depuis une URL."""
    for name in ["core-dev", "intel-comet", "voice-relay", "executor", "monitor"]:
        if name in url:
            return name
    return url.split("//")[-1].split("/")[0]


# ─── Full Sweep ───────────────────────────────────────────────────────
def run_checks() -> Dict:
    """Checker tous les services configurés."""
    _monitor_state["checks_total"] += 1
    _monitor_state["last_check"] = datetime.utcnow().isoformat()

    results = {}
    alerts  = []

    for target_url in WATCH_TARGETS:
        result = check_service(target_url)
        name   = result["name"]
        results[name] = result

        was_ok = _prev_states.get(name, True)  # Première fois = OK par défaut
        is_ok  = result["ok"]

        # Détecter les transitions d'état
        if was_ok and not is_ok:
            # Service qui vient de tomber
            alert = {
                "type":    "SERVICE_DOWN",
                "level":   "CRITICAL",
                "service": name,
                "url":     target_url,
                "error":   result.get("error", f"HTTP {result.get('status', '?')}"),
                "ts":      datetime.utcnow().isoformat(),
            }
            alerts.append(alert)
            logger.error(f"🚨 SERVICE DOWN: {name} ({target_url})")

        elif not was_ok and is_ok:
            # Service qui revient en ligne
            alert = {
                "type":    "SERVICE_RECOVERED",
                "level":   "INFO",
                "service": name,
                "url":     target_url,
                "ts":      datetime.utcnow().isoformat(),
            }
            alerts.append(alert)
            logger.info(f"✅ SERVICE RECOVERED: {name}")

        elif is_ok:
            logger.debug(f"  ✓ {name} ({result.get('latency_ms', '?')}ms)")
        else:
            logger.warning(f"  ✗ {name} — {result.get('error', 'unknown')}")

        _prev_states[name] = is_ok

    # Mettre à jour l'état global
    _monitor_state["services"] = results

    # Envoyer les alertes
    for alert in alerts:
        _send_alert(alert)
        _alert_history.insert(0, alert)

    # Garder historique
    while len(_alert_history) > 100:
        _alert_history.pop()

    # Résumé
    n_ok  = sum(1 for r in results.values() if r.get("ok"))
    n_tot = len(results)
    status = "ALL_OK" if n_ok == n_tot else ("DEGRADED" if n_ok > 0 else "ALL_DOWN")

    return {
        "status":   status,
        "ok":       n_ok,
        "total":    n_tot,
        "results":  results,
        "alerts":   alerts,
        "ts":       _monitor_state["last_check"],
    }


# ─── Alerting ─────────────────────────────────────────────────────────
def _send_alert(alert: Dict):
    """Envoyer une alerte au cockpit + HA webhook."""
    _monitor_state["alerts_sent"] += 1

    # 1. COMET feed via cockpit
    try:
        level = "CRITICAL" if alert.get("type") == "SERVICE_DOWN" else "INFO"
        svc   = alert.get("service", "?")
        msg   = (f"🚨 {svc} TOMBÉ — {alert.get('error', '')}"
                 if level == "CRITICAL"
                 else f"✅ {svc} revenu en ligne")
        requests.post(
            f"{COCKPIT_URL}/api/intel",
            json={"source": "monitor", "level": level, "summary": msg, "data": alert},
            headers={"X-S25-Key": S25_SECRET},
            timeout=3,
        )
    except Exception:
        pass

    # 2. HA Webhook (si configuré)
    if ALERT_WEBHOOK:
        try:
            requests.post(ALERT_WEBHOOK, json=alert, timeout=3)
        except Exception:
            pass


# ─── Flask API ────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "monitor", "ts": datetime.utcnow().isoformat()})

@app.route("/api/monitor/status", methods=["GET"])
def monitor_status():
    return jsonify({
        "ok":      True,
        "state":   _monitor_state,
        "targets": WATCH_TARGETS,
        "ts":      datetime.utcnow().isoformat(),
    })

@app.route("/api/monitor/check", methods=["GET"])
def monitor_check_now():
    """Forcer un check immédiat."""
    result = run_checks()
    return jsonify(result)

@app.route("/api/monitor/alerts", methods=["GET"])
def monitor_alerts():
    n = int(request.args.get("n", 20))
    return jsonify({
        "ok":      True,
        "alerts":  _alert_history[:n],
        "count":   len(_alert_history),
        "sent":    _monitor_state["alerts_sent"],
    })

@app.route("/api/monitor/services", methods=["GET"])
def monitor_services():
    return jsonify({
        "ok":       True,
        "services": _monitor_state.get("services", {}),
        "ts":       _monitor_state.get("last_check"),
    })


# ─── Background watch loop ────────────────────────────────────────────
def watch_loop():
    """Boucle de surveillance en background."""
    logger.info(f"Watch loop démarré — interval: {WATCH_INTERVAL}s")
    while True:
        try:
            summary = run_checks()
            n_ok  = summary["ok"]
            n_tot = summary["total"]
            logger.info(f"Check #{_monitor_state['checks_total']} — {n_ok}/{n_tot} OK — {summary['status']}")
        except Exception as e:
            logger.error(f"Watch loop error: {e}")
        time.sleep(WATCH_INTERVAL)


# ─── Main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="S25 Monitor Service")
    parser.add_argument("--watch", action="store_true", help="Watch mode seulement (sans HTTP)")
    parser.add_argument("--once",  action="store_true", help="Check une fois et quitte")
    parser.add_argument("--port",  type=int, default=PORT, help=f"Port HTTP (défaut: {PORT})")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║   S25 Monitor Service (5/5)         ║
║   Targets: {len(WATCH_TARGETS)} services                 ║
║   Interval: {WATCH_INTERVAL}s                        ║
╚══════════════════════════════════════╝
""")
    for t in WATCH_TARGETS:
        print(f"  → {t}")
    print()

    if args.once:
        result = run_checks()
        print(f"\nStatus: {result['status']} ({result['ok']}/{result['total']} OK)")
        for name, svc in result["results"].items():
            icon = "✅" if svc.get("ok") else "❌"
            err  = svc.get("error", f"{svc.get('latency_ms', '?')}ms")
            print(f"  {icon} {name:<20} {err}")

    elif args.watch:
        watch_loop()

    else:
        # HTTP API + background watch
        threading.Thread(target=watch_loop, daemon=True).start()
        app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
