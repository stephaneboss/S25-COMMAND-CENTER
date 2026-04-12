#!/usr/bin/env python3
# ============================================================
# S25 LUMIÈRE — Watchdog Self-Healing v1.0
# CentOS Akash — Auto-repair engine
# Ping Merlin/HA/Tunnel — Relance auto en cas de crash
# ============================================================

import os, sys, time, json, subprocess, requests, logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [WATCHDOG] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/s25_watchdog.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("s25_watchdog")

# ─────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────
HA_URL         = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN       = os.getenv("HA_TOKEN", "")
TUNNEL_SCRIPT  = os.getenv("TUNNEL_SCRIPT", "/config/scripts/start_s25_tunnel.sh")
PROXY_SCRIPT   = os.getenv("PROXY_SCRIPT", "/config/python_scripts/kimi_proxy.py")
AKASH_ENDPOINT = os.getenv("AKASH_ENDPOINT", "http://localhost:5050")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))   # secondes
MAX_RETRIES    = int(os.getenv("MAX_RETRIES", "3"))

# Nouveaux endpoints a surveiller
AKASH_COCKPIT_URL = os.getenv("AKASH_COCKPIT_URL", "https://api.smajor.org")
ALIENSTEF_URL     = os.getenv("ALIENSTEF_URL", "http://10.0.0.97:11434")
MERLIN_URL        = os.getenv("MERLIN_URL", "https://merlin.smajor.org")

STATUS_FILE   = "/tmp/s25_watchdog_status.json"
FAILOVER_FILE = "/tmp/s25_failover_state.json"

# ─────────────────────────────────────────────────────
# CHECKS
# ─────────────────────────────────────────────────────
def check_ha():
    try:
        r = requests.get(f"{HA_URL}/api/", headers={"Authorization": f"Bearer {HA_TOKEN}"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.error(f"HA check failed: {e}")
        return False

def check_tunnel():
    """Vérifie si le tunnel Cloudflare est actif"""
    try:
        result = subprocess.run(["pgrep", "-f", "cloudflared"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_proxy():
    """Vérifie si le proxy Kimi est actif"""
    try:
        r = requests.get("http://localhost:9191/health", timeout=5)
        return r.status_code == 200
    except:
        try:
            result = subprocess.run(["pgrep", "-f", "kimi_proxy"], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

def check_akash_api():
    """Vérifie si l'API MEXC Strike est accessible"""
    try:
        r = requests.get(f"{AKASH_ENDPOINT}/health", timeout=5)
        return r.status_code == 200
    except:
        return False

def check_akash_cockpit():
    """Vérifie si le cockpit Akash répond via Cloudflare"""
    try:
        r = requests.get(f"{AKASH_COCKPIT_URL}/health", timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.error(f"Akash cockpit check failed: {e}")
        return False

def check_alienstef():
    """Vérifie si le node local AlienStef Ollama est actif"""
    try:
        r = requests.get(f"{ALIENSTEF_URL}/api/tags", timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.error(f"AlienStef check failed: {e}")
        return False

def check_merlin():
    """Vérifie si Merlin MCP bridge répond"""
    try:
        r = requests.get(f"{MERLIN_URL}/health", timeout=15)
        return r.status_code == 200
    except Exception as e:
        log.error(f"Merlin check failed: {e}")
        return False

def update_failover_state(akash_ok, alien_ok):
    """Met à jour l'état de failover Akash → AlienStef"""
    state = {
        "timestamp": datetime.utcnow().isoformat(),
        "akash_cockpit": akash_ok,
        "alienstef": alien_ok,
        "failover_active": not akash_ok and alien_ok,
        "primary_endpoint": AKASH_COCKPIT_URL if akash_ok else "http://10.0.0.97:7777"
    }
    try:
        with open(FAILOVER_FILE, "w") as f:
            json.dump(state, f, indent=2)
        if state["failover_active"]:
            log.warning("⚠️ FAILOVER ACTIF: Akash down, AlienStef primaire")
            notify_ha("FAILOVER: Cockpit Akash down, AlienStef est le primaire", "🔄 S25 Failover")
    except:
        pass

def check_disk():
    """Vérifie l'espace disque"""
    result = subprocess.run(["df", "-h", "/config"], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    if len(lines) >= 2:
        parts = lines[1].split()
        usage = int(parts[4].replace('%', ''))
        return usage < 90, usage
    return True, 0

# ─────────────────────────────────────────────────────
# REPAIRS
# ─────────────────────────────────────────────────────
def repair_tunnel():
    log.warning("⚠️ Tunnel DOWN — tentative de relance...")
    try:
        subprocess.Popen(
            ["bash", TUNNEL_SCRIPT],
            stdout=open("/tmp/tunnel_repair.log", "w"),
            stderr=subprocess.STDOUT
        )
        time.sleep(10)
        if check_tunnel():
            log.info("✅ Tunnel relancé avec succès")
            notify_ha("Tunnel S25 relancé automatiquement par Watchdog")
            return True
        else:
            log.error("❌ Tunnel toujours DOWN après réparation")
            return False
    except Exception as e:
        log.error(f"Repair tunnel error: {e}")
        return False

def repair_proxy():
    log.warning("⚠️ Proxy Kimi DOWN — tentative de relance...")
    try:
        subprocess.Popen(
            ["python3", PROXY_SCRIPT],
            stdout=open("/tmp/proxy_repair.log", "w"),
            stderr=subprocess.STDOUT
        )
        time.sleep(5)
        if check_proxy():
            log.info("✅ Proxy Kimi relancé")
            notify_ha("Proxy Kimi relancé automatiquement par Watchdog")
            return True
        return False
    except Exception as e:
        log.error(f"Repair proxy error: {e}")
        return False

# ─────────────────────────────────────────────────────
# NOTIFICATION HA
# ─────────────────────────────────────────────────────
def notify_ha(message: str, title: str = "🔧 S25 Watchdog"):
    if not HA_TOKEN:
        return
    try:
        requests.post(
            f"{HA_URL}/api/services/persistent_notification/create",
            headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
            json={"title": title, "message": message, "notification_id": "s25_watchdog"},
            timeout=5
        )
        # Update comet intel
        requests.post(
            f"{HA_URL}/api/services/input_text/set_value",
            headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
            json={"entity_id": "input_text.s25_comet_intel", "value": f"🔧 WATCHDOG: {message[:200]}"},
            timeout=5
        )
    except:
        pass

# ─────────────────────────────────────────────────────
# SAVE STATUS
# ─────────────────────────────────────────────────────
def save_status(status: dict):
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except:
        pass

# ─────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────
def run():
    log.info("⚡ S25 LUMIÈRE Watchdog démarré")
    log.info(f"Vérification toutes les {CHECK_INTERVAL}s")

    failures = {"ha": 0, "tunnel": 0, "proxy": 0}

    while True:
        ts = datetime.utcnow().isoformat()
        status = {"timestamp": ts, "checks": {}, "repairs": []}

        # CHECK HA
        ha_ok = check_ha()
        status["checks"]["ha"] = ha_ok
        if ha_ok:
            failures["ha"] = 0
            log.info("✅ HA: OK")
        else:
            failures["ha"] += 1
            log.warning(f"⚠️ HA DOWN ({failures['ha']}/{MAX_RETRIES})")
            if failures["ha"] >= MAX_RETRIES:
                log.error("🚨 HA inaccessible depuis trop longtemps!")
                notify_ha("HA inaccessible — vérification manuelle requise", "🚨 S25 ALERTE CRITIQUE")

        # CHECK TUNNEL
        tunnel_ok = check_tunnel()
        status["checks"]["tunnel"] = tunnel_ok
        if tunnel_ok:
            failures["tunnel"] = 0
            log.info("✅ Tunnel: OK")
        else:
            failures["tunnel"] += 1
            log.warning(f"⚠️ Tunnel DOWN ({failures['tunnel']})")
            if failures["tunnel"] <= MAX_RETRIES:
                repaired = repair_tunnel()
                if repaired:
                    status["repairs"].append("tunnel")

        # CHECK PROXY
        proxy_ok = check_proxy()
        status["checks"]["proxy"] = proxy_ok
        if proxy_ok:
            failures["proxy"] = 0
            log.info("✅ Proxy Kimi: OK")
        else:
            failures["proxy"] += 1
            log.warning(f"⚠️ Proxy DOWN ({failures['proxy']})")
            if failures["proxy"] <= MAX_RETRIES:
                repaired = repair_proxy()
                if repaired:
                    status["repairs"].append("proxy")

        # CHECK AKASH COCKPIT
        akash_ok = check_akash_cockpit()
        status["checks"]["akash_cockpit"] = akash_ok
        if akash_ok:
            log.info("✅ Akash Cockpit: OK")
        else:
            log.warning("⚠️ Akash Cockpit DOWN")

        # CHECK ALIENSTEF
        alien_ok = check_alienstef()
        status["checks"]["alienstef"] = alien_ok
        if alien_ok:
            log.info("✅ AlienStef: OK")
        else:
            log.warning("⚠️ AlienStef DOWN")

        # CHECK MERLIN
        merlin_ok = check_merlin()
        status["checks"]["merlin"] = merlin_ok
        if merlin_ok:
            log.info("✅ Merlin MCP: OK")
        else:
            log.warning("⚠️ Merlin MCP DOWN")

        # FAILOVER STATE
        update_failover_state(akash_ok, alien_ok)

        # CHECK DISK
        disk_ok, disk_pct = check_disk()
        status["checks"]["disk_pct"] = disk_pct
        if not disk_ok:
            log.error(f"🚨 DISQUE PLEIN: {disk_pct}%")
            notify_ha(f"⚠️ Disque à {disk_pct}% — nettoyage requis!", "🚨 S25 Disque")

        # SAVE STATUS
        save_status(status)

        log.info(f"Status: HA={ha_ok} Tunnel={tunnel_ok} Proxy={proxy_ok} Akash={akash_ok} Alien={alien_ok} Merlin={merlin_ok} Disk={disk_pct}%")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
