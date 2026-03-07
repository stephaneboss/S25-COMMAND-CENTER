"""
S25 LUMIÈRE — Central Télécom IA / Voice Relay
================================================
"L'Astérix de l'IA" — Centrale WebSocket multi-agents.

Architecture:
  Major (Mic/Text)
      │
      ▼  WebSocket ws://voice-relay:7779
  ┌─────────────────────────────────────────────┐
  │         S25 Voice Relay (CE MODULE)         │
  │  Wake word: "S25" ou "Major"                │
  │  → GPT Realtime API (WebSocket)             │
  │  → Function Calls → Dispatcher              │
  └──────┬──────┬──────┬──────┬─────────────────┘
         │      │      │      │
         ▼      ▼      ▼      ▼
     COCKPIT  COMET  ARKON  TRINITY
     :7777    :7778  :7780  HA TTS

Usage:
  python agents/s25_voice_relay.py            # Server mode
  python agents/s25_voice_relay.py --test     # Test avec mock
  python agents/s25_voice_relay.py --client   # Client test interactif
"""

import os
import json
import time
import asyncio
import logging
import argparse
import requests
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

# WebSocket
try:
    import websockets
    import websockets.server
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

logger = logging.getLogger("s25.voice_relay")

# ─── Config ──────────────────────────────────────────────────────────
PORT             = int(os.getenv("VOICE_RELAY_PORT", "7779"))
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
COCKPIT_URL      = os.getenv("COCKPIT_URL",    "http://localhost:7777")
COMET_URL        = os.getenv("COMET_URL",      "http://localhost:7778")
ARKON_URL        = os.getenv("ARKON_URL",      "http://localhost:7780")
HA_URL           = os.getenv("HA_URL",         "http://homeassistant.local:8123")
HA_TOKEN         = os.getenv("HA_TOKEN",       "")
S25_SECRET       = os.getenv("S25_SHARED_SECRET", "s25-inter-service-key-2026")

# Wake words
WAKE_WORDS       = ["s25", "major", "arkon", "lumiere", "lumière"]
# Commandes directes (sans passer par GPT)
DIRECT_COMMANDS  = {
    "status":     "cockpit_status",
    "statut":     "cockpit_status",
    "threat":     "get_threat",
    "menace":     "get_threat",
    "kill":       "kill_switch",
    "stop":       "kill_switch",
    "comet":      "comet_feed",
    "intel":      "comet_feed",
    "buy":        "trade_signal_buy",
    "achat":      "trade_signal_buy",
    "sell":       "trade_signal_sell",
    "vente":      "trade_signal_sell",
    "hold":       "trade_signal_hold",
    "maintien":   "trade_signal_hold",
}

# ─── État global ─────────────────────────────────────────────────────
_relay_state = {
    "connections":    0,
    "messages_total": 0,
    "last_message":   None,
    "last_intent":    None,
    "started_at":     datetime.utcnow().isoformat(),
    "agents_online":  {},
}
_clients: set = set()
_broadcast_lock = threading.Lock()


# ─── GPT Function Definitions ────────────────────────────────────────
GPT_FUNCTIONS = [
    {
        "name": "get_s25_status",
        "description": "Obtenir le statut complet du système S25 Lumière (threat level, agents, ARKON signal)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "set_threat_level",
        "description": "Changer le niveau de menace S25 (T0=normal, T1=vigilance, T2=alerte, T3=critique)",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "minimum": 0, "maximum": 3,
                          "description": "Niveau de menace: 0=normal, 1=vigilance, 2=alerte, 3=critique"}
            },
            "required": ["level"]
        }
    },
    {
        "name": "send_trade_signal",
        "description": "Envoyer un signal de trading à l'exécuteur MEXC via ARKON-5",
        "parameters": {
            "type": "object",
            "properties": {
                "action":     {"type": "string", "enum": ["BUY", "SELL", "HOLD"],
                               "description": "Action de trading"},
                "symbol":     {"type": "string", "description": "Paire de trading ex: BTC/USDT"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1,
                               "description": "Niveau de confiance du signal (0-1)"},
                "reason":     {"type": "string", "description": "Raison du signal"}
            },
            "required": ["action", "symbol"]
        }
    },
    {
        "name": "get_intel_feed",
        "description": "Récupérer les dernières nouvelles crypto et alertes du COMET Watchman (Perplexity)",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 5, "description": "Nombre d'entrées à retourner"}
            },
            "required": []
        }
    },
    {
        "name": "speak_message",
        "description": "Jouer un message vocal via TRINITY (HA TTS) sur les speakers",
        "parameters": {
            "type": "object",
            "properties": {
                "message":  {"type": "string", "description": "Message à jouer"},
                "urgent":   {"type": "boolean", "default": False, "description": "Message urgent (prioritaire)"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "activate_kill_switch",
        "description": "Activer le kill switch S25 — arrête tous les trades en cours. CONFIRMATION REQUISE.",
        "parameters": {
            "type": "object",
            "properties": {
                "confirm":  {"type": "boolean", "description": "Confirmation explicite requise (true)"},
                "reason":   {"type": "string", "description": "Raison de l'arrêt d'urgence"}
            },
            "required": ["confirm"]
        }
    },
    {
        "name": "query_market",
        "description": "Interroger les marchés crypto via COMET/Perplexity pour analyse en temps réel",
        "parameters": {
            "type": "object",
            "properties": {
                "query":    {"type": "string", "description": "Question sur les marchés"},
                "symbols":  {"type": "array", "items": {"type": "string"},
                             "description": "Symboles concernés ex: [BTC, ETH, AKT]"}
            },
            "required": ["query"]
        }
    },
]


# ─── Function Executors ───────────────────────────────────────────────
async def execute_function(name: str, args: Dict) -> Dict:
    """Dispatcher — route les Function Calls vers les bons agents."""
    logger.info(f"Function call: {name}({json.dumps(args, ensure_ascii=False)[:100]})")

    try:
        if name == "get_s25_status":
            r = requests.get(f"{COCKPIT_URL}/api/status",
                             headers={"X-S25-Key": S25_SECRET}, timeout=5)
            return r.json() if r.status_code == 200 else {"error": "cockpit unavailable"}

        elif name == "set_threat_level":
            level = args.get("level", 0)
            r = requests.post(f"{COCKPIT_URL}/api/threat",
                              json={"level": level, "source": "voice_relay"},
                              headers={"X-S25-Key": S25_SECRET}, timeout=5)
            return {"ok": r.status_code == 200, "threat_level": level}

        elif name == "send_trade_signal":
            payload = {
                "action":     args.get("action", "HOLD"),
                "symbol":     args.get("symbol", "BTC/USDT"),
                "confidence": args.get("confidence", 0.7),
                "reason":     args.get("reason", "voice command"),
                "source":     "voice_relay",
                "ts":         datetime.utcnow().isoformat(),
            }
            r = requests.post(f"{COCKPIT_URL}/api/signal",
                              json=payload,
                              headers={"X-S25-Key": S25_SECRET}, timeout=5)
            return {"ok": r.status_code == 200, "signal": payload}

        elif name == "get_intel_feed":
            limit = args.get("limit", 5)
            r = requests.get(f"{COCKPIT_URL}/api/comet/feed?n={limit}",
                             headers={"X-S25-Key": S25_SECRET}, timeout=5)
            return r.json() if r.status_code == 200 else {"feed": []}

        elif name == "speak_message":
            message = args.get("message", "")
            urgent  = args.get("urgent", False)
            endpoint = "/api/vocal/alert" if urgent else "/api/vocal/say"
            r = requests.post(f"{COCKPIT_URL}{endpoint}",
                              json={"message": message, "urgent": urgent},
                              headers={"X-S25-Key": S25_SECRET}, timeout=5)
            return {"ok": r.status_code == 200, "message": message}

        elif name == "activate_kill_switch":
            if not args.get("confirm", False):
                return {"ok": False, "error": "Confirmation requise — répète la commande avec confirm=true"}
            r = requests.post(f"{COCKPIT_URL}/api/kill-switch",
                              json={"reason": args.get("reason", "voice command"),
                                    "source": "voice_relay"},
                              headers={"X-S25-Key": S25_SECRET}, timeout=5)
            return {"ok": r.status_code == 200, "kill_switch": "ACTIVATED"}

        elif name == "query_market":
            query   = args.get("query", "")
            symbols = args.get("symbols", [])
            r = requests.post(f"{COCKPIT_URL}/api/intel",
                              json={"source": "voice_relay",
                                    "level": "INFO",
                                    "summary": query,
                                    "data": {"symbols": symbols}},
                              headers={"X-S25-Key": S25_SECRET}, timeout=5)
            return {"ok": r.status_code == 200, "query": query, "routed_to": "comet"}

        else:
            return {"error": f"Fonction inconnue: {name}"}

    except requests.RequestException as e:
        logger.error(f"Function {name} network error: {e}")
        return {"error": str(e), "function": name}


# ─── GPT Realtime Intent Parser ──────────────────────────────────────
async def parse_intent_gpt(text: str) -> Dict:
    """
    Envoyer texte à GPT pour parsing d'intention via Function Calls.
    Utilise OpenAI Chat Completions (pas Realtime pour l'instant).
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set — fallback vers règles directes")
        return await parse_intent_rules(text)

    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es le dispatcher vocal de S25 Lumière — système de trading crypto automatisé. "
                        "Le Major (Stef) te parle en voix ou texte (joual québécois possible). "
                        "Interprète son intention et appelle la bonne fonction. "
                        "Sois rapide, précis. Pas de bavardage."
                    )
                },
                {"role": "user", "content": text}
            ],
            "tools": [{"type": "function", "function": fn} for fn in GPT_FUNCTIONS],
            "tool_choice": "auto",
            "max_tokens": 500,
        }

        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(None, lambda: requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers, json=payload, timeout=10
        ))

        if r.status_code == 200:
            data = r.json()
            choice = data["choices"][0]["message"]
            tool_calls = choice.get("tool_calls", [])

            results = []
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])
                result  = await execute_function(fn_name, fn_args)
                results.append({
                    "function": fn_name,
                    "args":     fn_args,
                    "result":   result,
                })

            return {
                "ok":         True,
                "text":       text,
                "intent":     choice.get("content", ""),
                "tool_calls": results,
                "model":      "gpt-4o-mini",
                "ts":         datetime.utcnow().isoformat(),
            }
        else:
            logger.error(f"GPT error: {r.status_code}")
            return await parse_intent_rules(text)

    except Exception as e:
        logger.error(f"GPT intent failed: {e}")
        return await parse_intent_rules(text)


async def parse_intent_rules(text: str) -> Dict:
    """Fallback: règles directes sans GPT."""
    text_lower = text.lower().strip()

    # Check wake word
    has_wake = any(w in text_lower for w in WAKE_WORDS)

    # Check commandes directes
    matched_cmd = None
    for kw, cmd in DIRECT_COMMANDS.items():
        if kw in text_lower:
            matched_cmd = cmd
            break

    if matched_cmd:
        result = await execute_function_from_shortcut(matched_cmd, text)
        return {
            "ok":       True,
            "text":     text,
            "intent":   matched_cmd,
            "wake":     has_wake,
            "result":   result,
            "model":    "rules",
            "ts":       datetime.utcnow().isoformat(),
        }

    return {
        "ok":    False,
        "text":  text,
        "intent": "unknown",
        "wake":  has_wake,
        "hint":  "Commandes: status, threat, kill, comet, buy/sell/hold [symbol]",
        "ts":    datetime.utcnow().isoformat(),
    }


async def execute_function_from_shortcut(cmd: str, raw_text: str) -> Dict:
    """Exécuter un raccourci commande sans GPT."""
    text_lower = raw_text.lower()

    if cmd == "cockpit_status":
        return await execute_function("get_s25_status", {})
    elif cmd == "get_threat":
        return await execute_function("get_s25_status", {})
    elif cmd == "kill_switch":
        return {"ok": False, "error": "Kill switch nécessite confirmation explicite — dis 'confirme kill switch'"}
    elif cmd == "comet_feed":
        return await execute_function("get_intel_feed", {"limit": 5})
    elif cmd == "trade_signal_buy":
        # Extraire symbole si présent
        symbol = "BTC/USDT"
        for sym in ["BTC", "ETH", "AKT", "SOL", "BNB"]:
            if sym.lower() in text_lower:
                symbol = f"{sym}/USDT"
                break
        return await execute_function("send_trade_signal",
                                      {"action": "BUY", "symbol": symbol, "confidence": 0.75})
    elif cmd == "trade_signal_sell":
        symbol = "BTC/USDT"
        for sym in ["BTC", "ETH", "AKT", "SOL", "BNB"]:
            if sym.lower() in text_lower:
                symbol = f"{sym}/USDT"
                break
        return await execute_function("send_trade_signal",
                                      {"action": "SELL", "symbol": symbol, "confidence": 0.75})
    elif cmd == "trade_signal_hold":
        return await execute_function("send_trade_signal",
                                      {"action": "HOLD", "symbol": "BTC/USDT", "confidence": 0.9})
    return {"ok": False, "error": f"Commande inconnue: {cmd}"}


# ─── WebSocket Handler ────────────────────────────────────────────────
async def ws_handler(websocket):
    """Handler pour chaque connexion WebSocket client."""
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    _clients.add(websocket)
    _relay_state["connections"] = len(_clients)
    logger.info(f"🔗 Nouveau client: {client_id} ({len(_clients)} total)")

    # Message de bienvenue
    await websocket.send(json.dumps({
        "type":    "welcome",
        "message": "S25 Voice Relay connecté — TABARNAK, on est live! 🍁",
        "wake_words": WAKE_WORDS,
        "commands":   list(DIRECT_COMMANDS.keys()),
        "ts":      datetime.utcnow().isoformat(),
    }))

    try:
        async for raw_msg in websocket:
            _relay_state["messages_total"] += 1
            _relay_state["last_message"] = datetime.utcnow().isoformat()

            try:
                # Accepter JSON ou texte brut
                try:
                    msg = json.loads(raw_msg)
                    text = msg.get("text", "") or msg.get("message", "")
                    msg_type = msg.get("type", "text")
                except json.JSONDecodeError:
                    text = str(raw_msg)
                    msg_type = "text"

                if not text.strip():
                    continue

                logger.info(f"📨 [{client_id}] {msg_type}: {text[:100]}")

                # Parser l'intention
                result = await parse_intent_gpt(text)
                _relay_state["last_intent"] = result.get("intent", "unknown")

                # Répondre au client
                await websocket.send(json.dumps({
                    "type":   "response",
                    "input":  text,
                    "result": result,
                    "ts":     datetime.utcnow().isoformat(),
                }))

                # Broadcaster à tous les clients (monitoring)
                await broadcast({
                    "type":   "relay_event",
                    "source": client_id,
                    "intent": result.get("intent", "unknown"),
                    "ok":     result.get("ok", False),
                    "ts":     datetime.utcnow().isoformat(),
                }, exclude=websocket)

            except Exception as e:
                logger.error(f"Message error: {e}")
                await websocket.send(json.dumps({
                    "type":  "error",
                    "error": str(e),
                    "ts":    datetime.utcnow().isoformat(),
                }))

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"🔌 Client déconnecté: {client_id}")
    finally:
        _clients.discard(websocket)
        _relay_state["connections"] = len(_clients)


async def broadcast(message: Dict, exclude=None):
    """Broadcaster à tous les clients connectés."""
    if not _clients:
        return
    msg_str = json.dumps(message)
    targets = {ws for ws in _clients if ws != exclude}
    if targets:
        await asyncio.gather(*[ws.send(msg_str) for ws in targets], return_exceptions=True)


# ─── Flask HTTP API (status + inject) ────────────────────────────────
def register_voice_routes(app, state: Dict):
    """Routes Flask pour cockpit — status + inject text."""
    from flask import request, jsonify

    def _check_key():
        return request.headers.get("X-S25-Key", "") == S25_SECRET

    @app.route("/api/voice/status", methods=["GET"])
    def api_voice_status():
        return jsonify({
            "ok":      True,
            "relay":   "ONLINE",
            "ws_port": PORT,
            "state":   _relay_state,
            "ts":      datetime.utcnow().isoformat(),
        })

    @app.route("/api/voice/inject", methods=["POST"])
    def api_voice_inject():
        """Injecter une commande texte comme si c'était vocal."""
        if not _check_key():
            return jsonify({"error": "unauthorized"}), 401
        data = request.json or {}
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "text requis"}), 400

        # Async loop dans thread Flask
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(parse_intent_gpt(text))
        loop.close()

        return jsonify({"ok": True, "result": result})

    logger.info("Voice Relay routes: /api/voice/status|inject")


# ─── Ping agents ─────────────────────────────────────────────────────
def ping_agents():
    """Vérifier quels agents sont en ligne."""
    agents = {
        "cockpit": COCKPIT_URL,
        "comet":   COMET_URL,
        "ha":      HA_URL,
    }
    for name, url in agents.items():
        try:
            r = requests.get(f"{url}/health", timeout=2)
            _relay_state["agents_online"][name] = r.status_code == 200
        except Exception:
            _relay_state["agents_online"][name] = False
    logger.info(f"Agents: {_relay_state['agents_online']}")


# ─── Main WebSocket server ────────────────────────────────────────────
async def run_server():
    """Démarrer le serveur WebSocket."""
    if not WS_AVAILABLE:
        logger.error("websockets non installé: pip install websockets")
        return

    # Ping agents au démarrage
    ping_agents()

    logger.info(f"""
╔══════════════════════════════════════════╗
║   S25 VOICE RELAY — Central Télécom IA  ║
║   WebSocket: ws://0.0.0.0:{PORT:<4}          ║
║   Wake words: {', '.join(WAKE_WORDS):<22}  ║
║   GPT: {'ONLINE' if OPENAI_API_KEY else 'OFFLINE (mode règles)'}                        ║
╚══════════════════════════════════════════╝
""")

    async with websockets.serve(ws_handler, "0.0.0.0", PORT):
        await asyncio.Future()  # Run forever


# ─── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [VOICE] %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="S25 Voice Relay")
    parser.add_argument("--test",   action="store_true", help="Test Function Calls avec mock")
    parser.add_argument("--client", action="store_true", help="Mode client interactif (test WS)")
    args = parser.parse_args()

    if args.test:
        print("🎙️  Test Voice Relay — Function Calls\n")
        test_phrases = [
            "S25 c'est quoi le statut du système?",
            "Major buy BTC",
            "show me the comet intel feed",
            "set threat level to 2",
            "play a message saying system is online",
            "c'est quoi le hashrate de l'Antminer?",
        ]
        loop = asyncio.new_event_loop()
        for phrase in test_phrases:
            print(f"📨 Input: {phrase}")
            result = loop.run_until_complete(parse_intent_rules(phrase))
            print(f"   Intent: {result.get('intent', '?')}")
            print(f"   OK: {result.get('ok', False)}")
            if result.get("result"):
                print(f"   Result: {json.dumps(result['result'], ensure_ascii=False)[:100]}")
            print()
        loop.close()

    elif args.client:
        # Client interactif (pour tester le serveur)
        async def interactive_client():
            uri = f"ws://localhost:{PORT}"
            print(f"🔗 Connexion à {uri}...")
            try:
                async with websockets.connect(uri) as ws:
                    welcome = await ws.recv()
                    print(f"Server: {json.loads(welcome)['message']}")
                    print("Tape ton message (Ctrl+C pour quitter):")
                    while True:
                        try:
                            text = input("> ").strip()
                            if text:
                                await ws.send(json.dumps({"text": text}))
                                resp = await ws.recv()
                                data = json.loads(resp)
                                intent = data.get("result", {}).get("intent", "?")
                                print(f"  → Intent: {intent}")
                        except EOFError:
                            break
            except Exception as e:
                print(f"❌ Connexion failed: {e}\n   Lance le serveur d'abord: python agents/s25_voice_relay.py")
        asyncio.run(interactive_client())

    else:
        # Server mode
        asyncio.run(run_server())
