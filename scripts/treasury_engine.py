"""
S25 Lumière — Treasury Engine (Sheet 6)
=========================================
Surveillance balance AKT + auto-fuel.

Monitore le solde AKT du wallet Akash.
Si < seuil → alerte COMET + signal swap ATOM→AKT.

Usage:
  python scripts/treasury_engine.py              # Check une fois
  python scripts/treasury_engine.py --watch      # Watch mode (300s loop)
  python scripts/treasury_engine.py --test       # Test avec données mock
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TREASURY] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("treasury_engine")

# ─── Config ──────────────────────────────────────────────────────────
COCKPIT_URL     = os.getenv("COCKPIT_URL",     "http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com")
COMET_KEY       = os.getenv("COMET_BRIDGE_KEY", "s25-comet-bridge-key")
WATCH_INTERVAL  = int(os.getenv("TREASURY_INTERVAL", "300"))   # 5 min par défaut

# Wallet Akash à surveiller (set via env)
AKASH_WALLET    = os.getenv("AKASH_WALLET", "")

# Seuils AKT
AKT_LOW_ALERT   = float(os.getenv("AKT_LOW_ALERT",  "3.0"))   # Alerte si < 3 AKT
AKT_CRITICAL    = float(os.getenv("AKT_CRITICAL",   "1.0"))   # Critique si < 1 AKT
AKT_REFUEL_TARGET = float(os.getenv("AKT_REFUEL",  "10.0"))   # Target après refuel

# APIs
AKASH_LCD       = os.getenv("AKASH_LCD",  "https://akash-api.polkachu.com")
COSMOS_LCD      = os.getenv("COSMOS_LCD", "https://cosmos-api.polkachu.com")
COINGECKO_URL   = "https://api.coingecko.com/api/v3/simple/price"

# Déploiements à surveiller
DSEQS = [
    {"dseq": "25822281", "name": "S25 Cockpit",  "cost_akt_day": 0.013},  # ~$0.38/mois
    {"dseq": "25708774", "name": "GPU RTX4090",  "cost_akt_day": 0.26},   # ~$8/mois
]


# ─── Akash Balance ───────────────────────────────────────────────────
def get_akt_balance(wallet: str) -> Optional[float]:
    """Fetch AKT balance from Akash LCD node."""
    if not wallet:
        logger.warning("AKASH_WALLET not set")
        return None
    try:
        r = requests.get(
            f"{AKASH_LCD}/cosmos/bank/v1beta1/balances/{wallet}",
            timeout=10
        )
        if r.status_code != 200:
            logger.error(f"Akash LCD error: {r.status_code}")
            return None
        balances = r.json().get("balances", [])
        for b in balances:
            if b["denom"] == "uakt":
                return int(b["amount"]) / 1_000_000  # uAKT → AKT
        return 0.0
    except Exception as e:
        logger.error(f"AKT balance fetch failed: {e}")
        return None


def get_atom_balance(wallet: str) -> Optional[float]:
    """Fetch ATOM balance (for potential swap source)."""
    if not wallet:
        return None
    # Convert Akash wallet to Cosmos wallet (same key, different prefix)
    # This is a simplification — actual conversion needs bech32
    try:
        r = requests.get(
            f"{COSMOS_LCD}/cosmos/bank/v1beta1/balances/{wallet}",
            timeout=10
        )
        if r.status_code != 200:
            return None
        balances = r.json().get("balances", [])
        for b in balances:
            if b["denom"] == "uatom":
                return int(b["amount"]) / 1_000_000
        return 0.0
    except Exception as e:
        logger.error(f"ATOM balance fetch failed: {e}")
        return None


# ─── Prix AKT/USD ─────────────────────────────────────────────────────
def get_akt_price_usd() -> Optional[float]:
    """Fetch AKT price from CoinGecko."""
    try:
        r = requests.get(
            COINGECKO_URL,
            params={"ids": "akash-network", "vs_currencies": "usd"},
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get("akash-network", {}).get("usd")
        return None
    except Exception:
        return None


# ─── Escrow Check ────────────────────────────────────────────────────
def get_deployment_escrow(dseq: str) -> Optional[Dict]:
    """Check escrow balance for a specific deployment."""
    try:
        r = requests.get(
            f"{AKASH_LCD}/akash/deployment/v1beta3/deployments/info",
            params={"id.dseq": dseq, "id.owner": AKASH_WALLET},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            escrow = data.get("escrow_account", {})
            balance = escrow.get("balance", {})
            return {
                "dseq":   dseq,
                "amount": int(balance.get("amount", 0)) / 1_000_000,
                "denom":  balance.get("denom", "uakt"),
            }
        return None
    except Exception as e:
        logger.error(f"Escrow check failed for DSEQ {dseq}: {e}")
        return None


# ─── Mock data ────────────────────────────────────────────────────────
def _mock_treasury() -> Dict:
    """Mock data for testing."""
    return {
        "akt_balance": 4.2,
        "atom_balance": 12.5,
        "akt_price_usd": 1.85,
        "deployments": [
            {"dseq": "25822281", "name": "S25 Cockpit", "escrow_akt": 2.1, "days_left": 161},
            {"dseq": "25708774", "name": "GPU RTX4090",  "escrow_akt": 1.8, "days_left": 6},
        ],
        "status": "LOW",
        "alerts": ["AKT balance faible: 4.2 AKT (seuil: 3.0)"],
    }


# ─── Treasury Analysis ───────────────────────────────────────────────
def analyze_treasury(
    akt_balance: float,
    akt_price: Optional[float],
    deployments: list,
) -> Tuple[str, list]:
    """
    Analyze treasury state.
    Returns (status, alerts).
    Status: OK | LOW | CRITICAL
    """
    alerts = []
    status = "OK"

    # Balance check
    if akt_balance < AKT_CRITICAL:
        status = "CRITICAL"
        alerts.append({
            "type":    "AKT_CRITICAL",
            "level":   "CRITICAL",
            "message": f"AKT balance CRITIQUE: {akt_balance:.2f} AKT (seuil: {AKT_CRITICAL})",
            "action":  f"REFUEL_URGENT — acheter {AKT_REFUEL_TARGET - akt_balance:.1f} AKT",
        })
    elif akt_balance < AKT_LOW_ALERT:
        status = "LOW"
        alerts.append({
            "type":    "AKT_LOW",
            "level":   "WARNING",
            "message": f"AKT balance faible: {akt_balance:.2f} AKT (seuil: {AKT_LOW_ALERT})",
            "action":  f"Planifier achat {AKT_REFUEL_TARGET - akt_balance:.1f} AKT",
        })

    # Escrow check per deployment
    for dep in deployments:
        days = dep.get("days_left", 999)
        if days < 3:
            alerts.append({
                "type":    "ESCROW_CRITICAL",
                "level":   "CRITICAL",
                "message": f"DSEQ {dep['dseq']} ({dep['name']}): escrow expire dans {days:.1f} jours!",
                "action":  f"Refuel escrow DSEQ {dep['dseq']} immédiatement",
            })
            if status != "CRITICAL":
                status = "LOW"
        elif days < 7:
            alerts.append({
                "type":    "ESCROW_LOW",
                "level":   "WARNING",
                "message": f"DSEQ {dep['dseq']} ({dep['name']}): escrow expire dans {days:.1f} jours",
                "action":  f"Planifier refuel escrow DSEQ {dep['dseq']}",
            })

    if akt_price:
        usd_val = akt_balance * akt_price
        logger.info(f"Wallet AKT: {akt_balance:.2f} AKT (${usd_val:.2f} USD @ ${akt_price:.3f})")

    return status, alerts


# ─── Push to Cockpit / COMET ─────────────────────────────────────────
def push_treasury_to_cockpit(report: Dict) -> bool:
    """Send treasury report to cockpit intel feed."""
    try:
        level = {
            "OK":       "INFO",
            "LOW":      "WARNING",
            "CRITICAL": "CRITICAL",
        }.get(report["status"], "INFO")

        r = requests.post(
            f"{COCKPIT_URL}/api/intel",
            json={
                "source":  "treasury_engine",
                "level":   level,
                "summary": f"Treasury {report['status']}: {report['akt_balance']:.2f} AKT",
                "data":    report,
            },
            headers={"X-S25-Key": COMET_KEY},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Cockpit push failed: {e}")
        return False


# ─── Write log JSON ──────────────────────────────────────────────────
def write_treasury_log(report: Dict) -> str:
    """Write treasury report to JSON log."""
    log_path = "/tmp/treasury_last.json"
    try:
        with open(log_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Treasury log: {log_path}")
    except Exception as e:
        logger.warning(f"Could not write log: {e}")
    return json.dumps(report, indent=2)


# ─── Main ─────────────────────────────────────────────────────────────
def run_treasury(test_mode: bool = False) -> Dict:
    """Single treasury check run."""
    logger.info(f"{'[TEST MODE] ' if test_mode else ''}Treasury check started")

    if test_mode:
        report = _mock_treasury()
        print("\n=== Treasury Engine Output ===")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return report

    # Fetch balances
    akt = get_akt_balance(AKASH_WALLET) or 0.0
    atom = get_atom_balance(AKASH_WALLET)
    price = get_akt_price_usd()

    # Fetch escrow per deployment
    deployments = []
    for dep in DSEQS:
        escrow = get_deployment_escrow(dep["dseq"])
        if escrow:
            akt_amount = escrow["amount"]
            days_left = akt_amount / dep["cost_akt_day"] if dep["cost_akt_day"] > 0 else 999
            deployments.append({
                "dseq":       dep["dseq"],
                "name":       dep["name"],
                "escrow_akt": akt_amount,
                "days_left":  round(days_left, 1),
            })
        else:
            deployments.append({
                "dseq":       dep["dseq"],
                "name":       dep["name"],
                "escrow_akt": None,
                "days_left":  None,
            })

    # Analyze
    status, alerts = analyze_treasury(akt, price, deployments)

    report = {
        "ts":            datetime.utcnow().isoformat(),
        "akt_balance":   akt,
        "atom_balance":  atom,
        "akt_price_usd": price,
        "akt_value_usd": round(akt * price, 2) if price else None,
        "deployments":   deployments,
        "status":        status,
        "alerts":        alerts,
        "source":        "treasury_engine",
    }

    # Log alerts
    for alert in alerts:
        lvl = alert.get("level", "INFO")
        if lvl == "CRITICAL":
            logger.error(f"🚨 {alert['message']}")
            logger.error(f"   ACTION: {alert.get('action', '')}")
        else:
            logger.warning(f"⚠️  {alert['message']}")

    # Write log
    write_treasury_log(report)

    # Push to cockpit (if not OK, always push; if OK, push every 10th run)
    if status != "OK" or not alerts:
        ok = push_treasury_to_cockpit(report)
        logger.info(f"Cockpit push: {'✅' if ok else '❌'}")

    logger.info(f"Treasury check complete — Status: {status}")
    return report


# ─── Entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="S25 Treasury Engine")
    parser.add_argument("--watch", action="store_true",
                        help=f"Watch mode — runs every {WATCH_INTERVAL}s")
    parser.add_argument("--test",  action="store_true",
                        help="Test mode — mock data, no network calls")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║   S25 Treasury Engine (Sheet 6)     ║
║   Wallet: {AKASH_WALLET[:20] or 'NOT SET':<20}  ║
║   Alert seuil: {AKT_LOW_ALERT} AKT              ║
╚══════════════════════════════════════╝
""")

    if args.test:
        run_treasury(test_mode=True)
    elif args.watch:
        logger.info(f"Watch mode — interval: {WATCH_INTERVAL}s")
        while True:
            try:
                run_treasury()
            except Exception as e:
                logger.error(f"Treasury error: {e}")
            time.sleep(WATCH_INTERVAL)
    else:
        run_treasury()
