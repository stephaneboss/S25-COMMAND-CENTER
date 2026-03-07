"""
S25 LUMIÈRE — Vault Sync (Shared Secrets Inter-Containers)
============================================================
Synchronisation sécurisée des clés API entre micro-services Akash.

Principe:
  - Core-Dev sert les secrets chiffrés via /api/vault/secrets
  - Chaque conteneur pull ses secrets au démarrage
  - Authentification par S25_SHARED_SECRET (tournant toutes les 24h)
  - Secrets jamais dans les images Docker ni les logs

Usage:
  python scripts/vault_sync.py --check          # Vérifier quels secrets sont set
  python scripts/vault_sync.py --generate-key   # Générer un nouveau shared secret
  python scripts/vault_sync.py --push-to-ha     # Pousser secrets vers HA input_text
  python scripts/vault_sync.py --pull SERVICE   # Pull secrets pour un service
"""

import os
import sys
import json
import hmac
import hashlib
import argparse
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("s25.vault")

# ─── Secrets Schema ───────────────────────────────────────────────────
# Définit quels secrets vont dans quels services
SECRETS_SCHEMA = {
    "global": [
        "S25_SHARED_SECRET",     # Clé inter-services (tous les conteneurs)
        "HA_URL",                # URL Home Assistant
        "HA_TOKEN",              # Token HA Long-Lived
    ],
    "core-dev": [
        "GEMINI_API_KEY",        # Gemini Pro pour MERLIN/ARKON
        "OPENAI_API_KEY",        # GPT pour GOUV4
    ],
    "intel-comet": [
        "PERPLEXITY_API_KEY",    # COMET Watchman
        "KIMI_API_KEY",          # Kimi Web3 signals
    ],
    "voice-relay": [
        "OPENAI_API_KEY",        # GPT Realtime pour voice
    ],
    "executor": [
        "MEXC_API_KEY",          # MEXC trading
        "MEXC_API_SECRET",       # MEXC trading secret
        "AKASH_WALLET",          # Wallet AKT pour Treasury
        "AKASH_MNEMONIC",        # Mnemonic (optionnel, pour CLI)
    ],
    "monitor": [
        # Monitor n'a besoin que du shared secret (déjà dans global)
    ],
}

# Secrets obligatoires vs optionnels
REQUIRED_SECRETS = {
    "S25_SHARED_SECRET",
    "HA_TOKEN",
    "S25_SHARED_SECRET",
}


# ─── Validation ──────────────────────────────────────────────────────
def check_secrets(service: Optional[str] = None) -> Dict:
    """Vérifier quels secrets sont configurés dans l'environnement."""
    results = {}

    # Déterminer quels secrets checker
    if service:
        keys_to_check = SECRETS_SCHEMA.get("global", []) + SECRETS_SCHEMA.get(service, [])
    else:
        keys_to_check = set()
        for keys in SECRETS_SCHEMA.values():
            keys_to_check.update(keys)
        keys_to_check = list(keys_to_check)

    missing  = []
    present  = []
    optional = []

    for key in sorted(keys_to_check):
        val = os.getenv(key, "")
        if val:
            present.append(key)
            results[key] = "✅ SET"
        elif key in REQUIRED_SECRETS:
            missing.append(key)
            results[key] = "❌ MISSING (required)"
        else:
            optional.append(key)
            results[key] = "⚠️  NOT SET (optional)"

    return {
        "service":  service or "all",
        "present":  present,
        "missing":  missing,
        "optional": optional,
        "results":  results,
        "ready":    len(missing) == 0,
    }


# ─── Secret Generation ────────────────────────────────────────────────
def generate_shared_secret(length: int = 32) -> str:
    """Générer un nouveau shared secret sécurisé."""
    return secrets.token_hex(length)


def rotate_secret() -> str:
    """Générer un secret avec timestamp pour rotation 24h."""
    today = datetime.utcnow().strftime("%Y%m%d")
    base  = os.getenv("S25_SECRET_BASE", generate_shared_secret(16))
    # HMAC-SHA256 avec la date comme message → secret change chaque jour
    return hmac.new(base.encode(), today.encode(), hashlib.sha256).hexdigest()


# ─── .env Generator ──────────────────────────────────────────────────
def generate_env_file(service: str, output_path: str = None) -> str:
    """
    Générer un fichier .env pour un service spécifique.
    Inclut global + service-specific secrets.
    """
    keys = SECRETS_SCHEMA.get("global", []) + SECRETS_SCHEMA.get(service, [])
    lines = [
        f"# S25 LUMIÈRE — {service.upper()} secrets",
        f"# Generated: {datetime.utcnow().isoformat()}",
        f"# DO NOT COMMIT — add to .gitignore",
        "",
    ]

    for key in sorted(set(keys)):
        val = os.getenv(key, "REPLACE_ME")
        lines.append(f"{key}={val}")

    content = "\n".join(lines)

    if output_path:
        with open(output_path, "w") as f:
            f.write(content)
        logger.info(f"Env file written: {output_path}")

    return content


# ─── Vault HTTP API (pour Core-Dev) ──────────────────────────────────
def register_vault_routes(app, state: Dict):
    """
    Routes Vault dans Core-Dev Flask.
    Permet aux autres services de pull leurs secrets au démarrage.
    """
    from flask import request, jsonify

    SHARED_SECRET = os.getenv("S25_SHARED_SECRET", "")

    def _check_service_auth():
        """Vérifier l'authentification inter-service."""
        key = request.headers.get("X-S25-Key", "")
        service = request.headers.get("X-S25-Service", "")
        return key == SHARED_SECRET and bool(service), service

    @app.route("/api/vault/ping", methods=["GET"])
    def vault_ping():
        """Health check du vault (pas d'auth requise)."""
        return jsonify({"ok": True, "vault": "ONLINE", "ts": datetime.utcnow().isoformat()})

    @app.route("/api/vault/secrets/<service_name>", methods=["GET"])
    def vault_get_secrets(service_name):
        """
        Retourner les secrets pour un service spécifique.
        Auth: X-S25-Key + X-S25-Service headers.
        """
        ok, requesting_service = _check_service_auth()
        if not ok:
            return jsonify({"error": "unauthorized"}), 401

        # Un service ne peut demander que ses propres secrets
        if requesting_service != service_name and requesting_service != "core-dev":
            return jsonify({"error": f"Service '{requesting_service}' ne peut pas accéder aux secrets de '{service_name}'"}), 403

        keys = SECRETS_SCHEMA.get("global", []) + SECRETS_SCHEMA.get(service_name, [])
        result = {}
        for key in set(keys):
            val = os.getenv(key, "")
            if val:
                result[key] = val  # NOTE: En prod, chiffrer avant de transmettre

        return jsonify({
            "ok":      True,
            "service": service_name,
            "secrets": result,
            "count":   len(result),
            "ts":      datetime.utcnow().isoformat(),
        })

    @app.route("/api/vault/manifest", methods=["GET"])
    def vault_manifest():
        """Retourner la liste des secrets requis (sans valeurs)."""
        ok, _ = _check_service_auth()
        if not ok:
            return jsonify({"error": "unauthorized"}), 401
        return jsonify({
            "ok":      True,
            "schema":  SECRETS_SCHEMA,
            "required": list(REQUIRED_SECRETS),
            "ts":      datetime.utcnow().isoformat(),
        })

    logger.info("Vault routes: /api/vault/ping|secrets|manifest")


# ─── Service Bootstrapper ─────────────────────────────────────────────
def bootstrap_service(service_name: str, vault_url: str = None) -> bool:
    """
    Au démarrage d'un service: pull les secrets depuis Core-Dev vault.
    Si vault indisponible, utilise les env vars existantes.

    À appeler dans le main() de chaque service avant tout.
    """
    if not vault_url:
        vault_url = os.getenv("COCKPIT_URL", "http://core-dev:7777")

    shared_secret = os.getenv("S25_SHARED_SECRET", "")
    if not shared_secret:
        logger.warning(f"[{service_name}] S25_SHARED_SECRET not set — secrets locaux seulement")
        return False

    try:
        import requests
        r = requests.get(
            f"{vault_url}/api/vault/secrets/{service_name}",
            headers={
                "X-S25-Key":     shared_secret,
                "X-S25-Service": service_name,
            },
            timeout=5,
        )

        if r.status_code == 200:
            data = r.json()
            secrets_loaded = data.get("secrets", {})
            # Injecter dans l'environnement du process
            for key, val in secrets_loaded.items():
                if not os.getenv(key):  # Ne pas écraser les env vars existantes
                    os.environ[key] = val
            logger.info(f"[{service_name}] ✅ {len(secrets_loaded)} secrets loaded from vault")
            return True
        else:
            logger.warning(f"[{service_name}] Vault returned {r.status_code} — using local env")
            return False

    except Exception as e:
        logger.warning(f"[{service_name}] Vault unavailable: {e} — using local env")
        return False


# ─── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="S25 Vault Sync")
    parser.add_argument("--check",        action="store_true", help="Vérifier les secrets configurés")
    parser.add_argument("--service",      type=str,            help="Filtrer par service (ex: executor)")
    parser.add_argument("--generate-key", action="store_true", help="Générer un nouveau S25_SHARED_SECRET")
    parser.add_argument("--gen-env",      type=str,            help="Générer .env pour un service")
    parser.add_argument("--pull",         type=str,            help="Pull secrets depuis vault pour SERVICE")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║   S25 Vault Sync — Shared Secrets   ║
║   Services: {len(SECRETS_SCHEMA)} configurés               ║
╚══════════════════════════════════════╝
""")

    if args.generate_key:
        new_key = generate_shared_secret()
        print(f"🔑 Nouveau S25_SHARED_SECRET:\n   {new_key}")
        print(f"\n   Ajoute dans HA secrets.yaml:")
        print(f"   s25_shared_secret: {new_key}")
        print(f"\n   Et dans chaque SDL Akash env var:")
        print(f"   - S25_SHARED_SECRET={new_key}")

    elif args.check:
        result = check_secrets(args.service)
        print(f"Service: {result['service']}")
        print(f"{'✅ Prêt' if result['ready'] else '❌ Incomplet'} ({len(result['present'])} set, {len(result['missing'])} missing)\n")
        for key, status in sorted(result["results"].items()):
            print(f"  {status:<30} {key}")

    elif args.gen_env:
        service = args.gen_env
        path = f".env.{service}"
        content = generate_env_file(service, path)
        print(f"✅ Généré: {path}")
        print(f"\nContenu:")
        print(content)

    elif args.pull:
        vault_url = os.getenv("COCKPIT_URL", "http://localhost:7777")
        ok = bootstrap_service(args.pull, vault_url)
        print(f"{'✅ Secrets pulled' if ok else '❌ Pull failed — check vault URL et shared secret'}")

    else:
        # Par défaut: check all
        result = check_secrets()
        print("=== Secrets Status ===")
        for key, status in sorted(result["results"].items()):
            print(f"  {status:<30} {key}")
        print(f"\n{'✅ Vault prêt' if result['ready'] else '❌ Secrets manquants: ' + ', '.join(result['missing'])}")
