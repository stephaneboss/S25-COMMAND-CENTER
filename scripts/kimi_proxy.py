"""
S25 Lumiere -- Kimi Proxy v2.0 avec queue SQLite persistante
=============================================================
Proxy HTTP port 9191 : recoit les signaux Kimi Web3 via tunnel CloudFlare
et les forward au webhook HA interne.

FIX #3 (Issue pipeline S25):
  - File d'attente SQLite persistante : aucun signal perdu meme si HA redémarre
  - Retry automatique toutes les 30s pour les signaux non-livres
  - Compteur de signaux manques dans /status
  - Auto-reconnect si webhook HA repond 4xx/5xx

Deploy: copier ce fichier dans /config/python_scripts/kimi_proxy.py sur HA
puis lancer avec: python3 /config/python_scripts/kimi_proxy.py

Variables d'environnement:
  KIMI_PROXY_PORT     Port d'ecoute (defaut: 9191)
  HA_WEBHOOK_URL      URL webhook HA interne (defaut: http://homeassistant:8123/...)
  HA_WEBHOOK_ID       ID du webhook HA
  QUEUE_DB_PATH       Chemin SQLite (defaut: /data/kimi_signal_queue.db)
"""

import os
import time
import json
import sqlite3
import logging
import threading
import requests
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [KIMI-PROXY] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/proxy.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

# --- Config ---
PROXY_PORT    = int(os.getenv("KIMI_PROXY_PORT", "9191"))
HA_BASE       = os.getenv("HA_BASE_URL", "http://homeassistant:8123")
WEBHOOK_ID    = os.getenv("HA_WEBHOOK_ID", "s25_kimi_scan_secret_xyz")
HA_WEBHOOK    = f"{HA_BASE}/api/webhook/{WEBHOOK_ID}"
QUEUE_DB      = os.getenv("QUEUE_DB_PATH", "/data/kimi_signal_queue.db")
RETRY_INTERVAL = 30   # secondes entre chaque retry des signaux en attente
MAX_RETRIES    = 10   # apres 10 echecs, marquer comme dead-letter (pas supprime)

# --- SQLite Queue ---

def init_db():
    con = sqlite3.connect(QUEUE_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at TEXT NOT NULL,
            payload    TEXT NOT NULL,
            status     TEXT NOT NULL DEFAULT 'pending',
            attempts   INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            delivered_at TEXT
        )
    """)
    con.commit()
    con.close()
    log.info(f"Queue SQLite initialisee: {QUEUE_DB}")


def enqueue_signal(payload: dict) -> int:
    con = sqlite3.connect(QUEUE_DB)
    cur = con.execute(
        "INSERT INTO signals (received_at, payload, status) VALUES (?, ?, 'pending')",
        (datetime.now(timezone.utc).isoformat(), json.dumps(payload))
    )
    sig_id = cur.lastrowid
    con.commit()
    con.close()
    log.info(f"Signal #{sig_id} enqueued: {str(payload)[:80]}")
    return sig_id


def mark_delivered(sig_id: int):
    con = sqlite3.connect(QUEUE_DB)
    con.execute(
        "UPDATE signals SET status='delivered', delivered_at=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(), sig_id)
    )
    con.commit()
    con.close()



def _notify_ha_dead_letter(sig_id: int, attempts: int, error: str):
    """Envoie une notification HA quand un signal atteint dead-letter."""
    ha_token = os.getenv("HA_TOKEN", "")
    if not ha_token:
        log.debug("HA_TOKEN non set -- notification dead-letter ignoree")
        return
    try:
        requests.post(
            f"{HA_BASE}/api/services/persistent_notification/create",
            headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
            json={
                "title": "[S25] Kimi Signal Dead-Letter",
                "message": f"Signal #{sig_id} abandonne apres {attempts} tentatives. Erreur: {error[:200]}",
                "notification_id": f"s25_dead_letter_{sig_id}",
            },
            timeout=5,
        )
        log.info(f"Notification HA dead-letter envoyee pour signal #{sig_id}")
    except Exception as e:
        log.warning(f"Notification HA dead-letter failed: {e}")

def mark_failed(sig_id: int, attempts: int, error: str):
    status = "dead_letter" if attempts >= MAX_RETRIES else "pending"
    con = sqlite3.connect(QUEUE_DB)
    con.execute(
        "UPDATE signals SET status=?, attempts=?, last_error=? WHERE id=?",
        (status, attempts, error[:500], sig_id)
    )
    con.commit()
    con.close()
    if status == "dead_letter":
        log.error(f"Signal #{sig_id} dead-letter apres {attempts} tentatives: {error[:100]}")
        _notify_ha_dead_letter(sig_id, attempts, error)


def get_pending_signals():
    con = sqlite3.connect(QUEUE_DB)
    rows = con.execute(
        "SELECT id, payload, attempts FROM signals WHERE status='pending' ORDER BY id"
    ).fetchall()
    con.close()
    return rows


def get_queue_stats() -> dict:
    con = sqlite3.connect(QUEUE_DB)
    stats = {}
    for status in ("pending", "delivered", "dead_letter"):
        row = con.execute(
            "SELECT COUNT(*) FROM signals WHERE status=?", (status,)
        ).fetchone()
        stats[status] = row[0] if row else 0
    con.close()
    return stats


# --- HA Webhook delivery ---

def deliver_to_ha(payload: dict) -> tuple[bool, str]:
    """Envoie le signal au webhook HA. Retourne (success, error_msg)."""
    try:
        r = requests.post(HA_WEBHOOK, json=payload, timeout=10)
        if r.status_code in (200, 201, 204):
            return True, ""
        return False, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, str(e)


# --- Retry worker ---

class RetryWorker(threading.Thread):
    """Thread de fond qui retente les signaux pending toutes les RETRY_INTERVAL sec."""

    def __init__(self):
        super().__init__(daemon=True, name="kimi-retry")
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        log.info("RetryWorker demarre")
        while not self._stop.is_set():
            self._stop.wait(RETRY_INTERVAL)
            if self._stop.is_set():
                break
            pending = get_pending_signals()
            if pending:
                log.info(f"RetryWorker: {len(pending)} signal(s) en attente -- tentative delivery")
            for sig_id, payload_json, attempts in pending:
                try:
                    payload = json.loads(payload_json)
                except Exception:
                    mark_failed(sig_id, attempts + 1, "JSON decode error")
                    continue
                ok, err = deliver_to_ha(payload)
                if ok:
                    mark_delivered(sig_id)
                    log.info(f"RetryWorker: signal #{sig_id} livre avec succes (tentative {attempts+1})")
                else:
                    mark_failed(sig_id, attempts + 1, err)
                    log.warning(f"RetryWorker: signal #{sig_id} echec tentative {attempts+1}: {err}")


# --- HTTP Request Handler ---

class KimiProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        log.debug(fmt % args)

    def send_json(self, code: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            stats = get_queue_stats()
            self.send_json(200, {
                "ok": True,
                "queue": stats,
                "ha_webhook": HA_WEBHOOK,
                "proxy_port": PROXY_PORT,
            })
        elif self.path == "/health":
            self.send_json(200, {"ok": True})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body)
        except Exception:
            self.send_json(400, {"error": "invalid JSON"})
            return

        # Enqueue immediatement (persistance garantie)
        sig_id = enqueue_signal(payload)

        # Tentative directe (optimiste)
        ok, err = deliver_to_ha(payload)
        if ok:
            mark_delivered(sig_id)
            log.info(f"Signal #{sig_id} livre directement a HA")
            self.send_json(200, {"ok": True, "signal_id": sig_id, "delivered": True})
        else:
            log.warning(f"Signal #{sig_id} queued (HA indisponible: {err}) -- retry dans {RETRY_INTERVAL}s")
            self.send_json(202, {
                "ok": True,
                "signal_id": sig_id,
                "delivered": False,
                "queued": True,
                "retry_in": RETRY_INTERVAL,
                "ha_error": err,
            })


# --- Main ---

if __name__ == "__main__":
    import signal as _signal

    init_db()

    # Verifier si des signaux pending existent deja (reprise apres crash)
    pending = get_pending_signals()
    if pending:
        log.warning(f"Reprise: {len(pending)} signaux en attente dans la queue")

    retry_worker = RetryWorker()
    retry_worker.start()

    server = HTTPServer(("0.0.0.0", PROXY_PORT), KimiProxyHandler)

    def handle_signal(sig, frame):
        log.info("Arret demande -- shutdown propre")
        retry_worker.stop()
        server.shutdown()

    _signal.signal(_signal.SIGINT,  handle_signal)
    _signal.signal(_signal.SIGTERM, handle_signal)

    log.info(f"""
+=========================================+
|  S25 LUMIERE -- Kimi Proxy v2.0          |
|  Port: {PROXY_PORT:<5}                         |
|  HA Webhook: {WEBHOOK_ID[:20]:<20}  |
|  Queue: {QUEUE_DB:<32} |
|  Retry: toutes les {RETRY_INTERVAL}s               |
+=========================================+
""")
    log.info(f"Kimi Proxy demarre sur 0.0.0.0:{PROXY_PORT}")
    server.serve_forever()
