"""
S25 Lumiere - Local Conversation Agent v2.0
=============================================
OpenAI-compatible /v1/chat/completions endpoint for Home Assistant.

The agent has full access to:
- All S25 sensors and pipeline state via ha_bridge
- Live market data via ninja_routes (CoinGecko, Fear&Greed, Reddit, DeFi)
- Agent mesh status (14 agents)
- Trading signals and wallet data
- HA services (shell commands, automations, notifications)
- ACTION MODE: can execute trades, change config, send alerts

HA config: openai_conversation with base_url = http://10.0.0.97:7777/v1
"""

import json
import logging
import time
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger("s25.conversation_agent")

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:14b"

# Import ninja routes for free market data
try:
    from agents.ninja_routes import (
        get_prices, get_fear_greed, get_trending,
        get_global_market, get_full_intel_snapshot,
    )
    NINJA_AVAILABLE = True
except ImportError:
    NINJA_AVAILABLE = False


def _get_market_snapshot() -> str:
    """Get live market data from ninja_routes (100% free APIs)."""
    if not NINJA_AVAILABLE:
        return "Market data: ninja_routes non disponible"

    lines = []
    try:
        prices = get_prices(["bitcoin", "ethereum", "dogecoin", "solana", "cosmos", "akash-network"])
        if prices:
            lines.append("PRIX LIVE:")
            for coin, data in prices.items():
                p = data.get("usd", 0)
                chg = data.get("usd_24h_change", 0)
                arrow = "+" if chg >= 0 else ""
                lines.append(f"  {coin}: ${p:,.2f} ({arrow}{chg:.1f}%)")
    except Exception:
        pass

    try:
        fg = get_fear_greed(1)
        if fg:
            lines.append(f"FEAR & GREED: {fg[0]['value']} ({fg[0]['label']})")
    except Exception:
        pass

    try:
        trending = get_trending()
        if trending:
            top3 = ", ".join(t["symbol"] for t in trending[:3])
            lines.append(f"TRENDING: {top3}")
    except Exception:
        pass

    try:
        gm = get_global_market()
        if gm:
            mc = gm.get("total_market_cap_usd", 0)
            btc_dom = gm.get("btc_dominance", 0)
            lines.append(f"MARKET CAP: ${mc/1e12:.2f}T | BTC Dom: {btc_dom:.1f}%")
    except Exception:
        pass

    return "\n".join(lines) if lines else "Market data temporairement indisponible"


def _get_system_context(ha_bridge, load_state_fn) -> str:
    """Build a rich system prompt with live S25 + market data."""

    state = load_state_fn() if load_state_fn else {}
    pipeline = state.get("pipeline", {})
    agents = state.get("agents", {})
    intel = state.get("intel", {})

    online_agents = [k for k, v in agents.items() if v.get("status") == "online"]
    last_signal = pipeline.get("last_signal", {})

    # Live HA sensors
    ha_data = {}
    if ha_bridge and ha_bridge.connected:
        for entity in [
            "sensor.s25_arkon5_action",
            "sensor.s25_arkon5_conf",
            "sensor.s25_pipeline_status",
            "input_text.s25_comet_intel",
            "input_select.s25_threat_level",
            "input_boolean.s25_kill_switch",
            "input_boolean.mexc_paper_trading",
            "input_boolean.multi_agent_enabled",
            "input_text.agent_trading_status",
            "sensor.s25_portfolio_total",
            "sensor.s_25_battery_level",
        ]:
            s = ha_bridge.get_state(entity)
            if s:
                ha_data[entity.split(".")[-1]] = s.get("state", "unknown")

    # Recent intel
    feed = intel.get("comet_feed", [])[:5]
    intel_lines = "\n".join(
        f"  - [{e.get('level','INFO')}] {e.get('summary','')}" for e in feed
    )

    # Market snapshot
    market = _get_market_snapshot()

    return f"""Tu es l'Agent S25 Lumiere v2.0, le cerveau local du systeme de trading et d'infrastructure S25.
Tu tournes sur AlienStef (Dell Alienware Aurora R4, Ubuntu 24.04, RTX 3060 12GB, Qwen 14b).
Tu es connecte a Home Assistant via ha_bridge et tu as acces aux donnees marche en temps reel.

IMPORTANT: Tu peux AGIR, pas juste parler. Quand on te demande une action, execute-la.

== ETAT SYSTEME (LIVE) ==
Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
Pipeline: {pipeline.get('mode', 'unknown')} | Threat: {pipeline.get('threat_level', 'T0')} | Kill: {'ON' if pipeline.get('kill_switch') else 'OFF'}
Agents: {len(online_agents)}/{len(agents)} online ({', '.join(online_agents[:8])})
Paper trading: {ha_data.get('mexc_paper_trading', '?')} | Multi-agent: {ha_data.get('multi_agent_enabled', '?')}

== DERNIER SIGNAL ==
{last_signal.get('action', 'N/A')} {last_signal.get('symbol', '')} | Conf: {last_signal.get('effective_confidence', 'N/A')} | Verdict: {last_signal.get('verdict', 'N/A')} | Source: {last_signal.get('source', 'N/A')}

== MARCHE (LIVE) ==
{market}

== SENSORS HA ==
{json.dumps(ha_data, indent=2, ensure_ascii=False) if ha_data else 'Non disponible'}

== INTEL RECENT ==
{intel_lines if intel_lines.strip() else 'Aucun intel recent'}

== TES ACTIONS DISPONIBLES ==
Quand on te demande d'agir, reponds avec un bloc JSON ACTION:
- STATUS: {{"action": "status"}} — rapport complet
- NOTIFY: {{"action": "notify", "message": "...", "title": "..."}} — notification mobile
- SIGNAL: {{"action": "signal", "type": "BUY/SELL/HOLD", "symbol": "BTC/USDT", "confidence": 0.8}} — envoyer signal
- CONFIG: {{"action": "config", "key": "pipeline.mode", "value": "authorized"}} — changer config
- THREAT: {{"action": "threat", "level": 0-3, "reason": "..."}} — changer threat level

== REGLES ==
- Reponds TOUJOURS en francais, sois concis et direct
- Pour les trades: verifier kill_switch et threat_level AVANT
- Utilise les donnees marche live pour tes analyses, jamais inventer
- Si Fear & Greed < 25: mentionne l'opportunite d'achat potentielle
- Si on te demande un rapport: inclus marche + pipeline + agents + recommandation
"""


def _execute_action(action_data: dict, ha_bridge) -> str:
    """Execute an action command from the agent's response."""
    if not ha_bridge or not ha_bridge.connected:
        return "[ACTION FAILED: HA non connecte]"

    action = action_data.get("action", "")

    if action == "notify":
        msg = action_data.get("message", "")
        title = action_data.get("title", "S25 Agent")
        ok = ha_bridge.notify(msg, title=title, importance="high")
        return f"[NOTIF {'SENT' if ok else 'FAILED'}]"

    elif action == "signal":
        sig_type = action_data.get("type", "HOLD")
        symbol = action_data.get("symbol", "BTC/USDT")
        conf = float(action_data.get("confidence", 0.5))
        result = ha_bridge.push_signal(
            sig_type, symbol, conf, conf, 0, "Agent local recommendation", "SIMULATE", "S25_LOCAL"
        )
        return f"[SIGNAL {sig_type} {symbol} pushed: {result.get('ok', False)}]"

    elif action == "threat":
        level = int(action_data.get("level", 0))
        reason = action_data.get("reason", "Agent adjustment")
        ha_bridge.push_sensor("input_select.s25_threat_level", f"T{level}", {
            "friendly_name": "S25 Threat Level",
            "reason": reason,
        })
        return f"[THREAT -> T{level}: {reason}]"

    elif action == "status":
        ping = ha_bridge.ping()
        return f"[HA: {'OK' if ping.get('ok') else 'DOWN'}]"

    return f"[ACTION UNKNOWN: {action}]"


def handle_chat_completion(request_data: Dict, ha_bridge=None, load_state_fn=None) -> Dict:
    """Process an OpenAI-compatible chat completion request."""

    messages = request_data.get("messages", [])
    model = request_data.get("model", OLLAMA_MODEL)
    stream = request_data.get("stream", False)
    max_tokens = request_data.get("max_tokens", 1000)

    system_prompt = _get_system_context(ha_bridge, load_state_fn)

    # Prepare messages for Ollama
    ollama_messages = [{"role": "system", "content": system_prompt}]
    for m in messages[-10:]:
        if m.get("role") in ("user", "assistant"):
            ollama_messages.append({"role": m["role"], "content": m.get("content", "")})

    # Call Ollama
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model if model != "s25-lumiere" else OLLAMA_MODEL,
                "messages": ollama_messages,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.7},
            },
            timeout=120,
        )
        data = resp.json()
        reply = data.get("message", {}).get("content", "Erreur: pas de reponse")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
    except Exception as e:
        logger.error("Ollama error: %s", e)
        reply = f"Erreur de communication avec le modele local: {e}"
        prompt_tokens = 0
        completion_tokens = 0

    # Check for action blocks in the response
    if '{"action"' in reply and ha_bridge:
        try:
            import re
            action_match = re.search(r'\{[^}]*"action"[^}]*\}', reply)
            if action_match:
                action_data = json.loads(action_match.group())
                action_result = _execute_action(action_data, ha_bridge)
                reply += f"\n\n{action_result}"
        except Exception:
            pass

    return {
        "id": f"chatcmpl-s25-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens},
    }


def push_mesh_to_ha(ha_bridge, load_state_fn) -> dict:
    """Push full mesh status to HA sensors — called by heartbeat cron."""
    if not ha_bridge or not ha_bridge.connected:
        return {"ok": False}

    state = load_state_fn() if load_state_fn else {}
    agents = state.get("agents", {})
    pipeline = state.get("pipeline", {})

    online = sum(1 for a in agents.values() if a.get("status") == "online")
    total = len(agents)

    # Push mesh summary
    ha_bridge.push_sensor("sensor.s25_mesh_online", f"{online}/{total}", {
        "friendly_name": "S25 Mesh Agents",
        "online": online, "total": total,
        "icon": "mdi:lan",
    })

    # Push each agent status
    for name, data in agents.items():
        ha_bridge.push_agent_status(name, data.get("status", "unknown"), {
            "last_seen": data.get("last_seen", ""),
        })

    # Push pipeline summary
    ha_bridge.push_sensor("sensor.s25_pipeline_mode", pipeline.get("mode", "unknown"), {
        "friendly_name": "S25 Pipeline Mode",
        "threat_level": pipeline.get("threat_level", "T0"),
        "kill_switch": pipeline.get("kill_switch", False),
        "icon": "mdi:pipe",
    })

    # Push market data to HA
    if NINJA_AVAILABLE:
        try:
            fg = get_fear_greed(1)
            if fg:
                ha_bridge.push_sensor("sensor.s25_fear_greed", str(fg[0]["value"]), {
                    "friendly_name": "S25 Fear & Greed Index",
                    "label": fg[0]["label"],
                    "icon": "mdi:emoticon-outline",
                })
            prices = get_prices(["bitcoin", "ethereum", "dogecoin"])
            if prices:
                for coin, data in prices.items():
                    p = data.get("usd", 0)
                    chg = data.get("usd_24h_change", 0)
                    symbol = {"bitcoin": "BTC", "ethereum": "ETH", "dogecoin": "DOGE"}.get(coin, coin)
                    ha_bridge.push_sensor(f"sensor.s25_price_{symbol.lower()}", str(round(p, 2)), {
                        "friendly_name": f"S25 {symbol} Price",
                        "unit_of_measurement": "USD",
                        "change_24h": round(chg, 2),
                        "icon": "mdi:currency-usd",
                    })
        except Exception as e:
            logger.warning("Market push error: %s", e)

    return {"ok": True, "online": online, "total": total}


def list_models() -> Dict:
    """Return available models in OpenAI format."""
    models = [{"id": "s25-lumiere", "object": "model", "created": 1700000000, "owned_by": "s25-local", "permission": []}]
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        for m in resp.json().get("models", []):
            models.append({"id": m["name"], "object": "model", "created": 1700000000, "owned_by": "ollama-local", "permission": []})
    except Exception:
        pass
    return {"object": "list", "data": models}
