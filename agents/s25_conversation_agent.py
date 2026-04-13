"""
S25 Lumiere - Local Conversation Agent
========================================
OpenAI-compatible /v1/chat/completions endpoint for Home Assistant.

This makes the cockpit act as a local AI provider that HA can use
via the openai_conversation integration with a custom base_url.

The agent has full access to:
- All S25 sensors and pipeline state
- Agent mesh status
- Trading signals and wallet data
- System health metrics
- HA services (shell commands, automations, notifications)

HA config (configuration.yaml):
  openai_conversation:
    - api_key: "s25-local-agent-key"
      base_url: "http://10.0.0.97:7777/v1"
      model: "s25-lumiere"
      name: "S25 Agent Local"

Or via UI: Settings > Integrations > OpenAI Conversation > base_url = http://10.0.0.97:7777/v1
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


def _get_system_context(ha_bridge, load_state_fn) -> str:
    """Build a rich system prompt with live S25 data."""

    # Get live pipeline state
    state = load_state_fn() if load_state_fn else {}
    pipeline = state.get("pipeline", {})
    agents = state.get("agents", {})
    intel = state.get("intel", {})

    online_agents = [k for k, v in agents.items() if v.get("status") == "online"]
    last_signal = pipeline.get("last_signal", {})

    # Get live HA data
    ha_data = {}
    if ha_bridge and ha_bridge.connected:
        for entity in [
            "sensor.s25_arkon5_action",
            "sensor.s25_arkon5_conf",
            "sensor.s25_pipeline_status",
            "input_text.s25_comet_intel",
            "input_select.s25_threat_level",
            "input_boolean.s25_kill_switch",
            "input_text.agent_trading_status",
        ]:
            s = ha_bridge.get_state(entity)
            if s:
                ha_data[entity.split(".")[-1]] = s.get("state", "unknown")

    # Recent intel
    feed = intel.get("comet_feed", [])[:5]
    intel_lines = "\n".join(
        f"  - [{e.get('level','INFO')}] {e.get('summary','')}" for e in feed
    )

    return f"""Tu es l'Agent S25 Lumiere, le cerveau local du systeme de trading et d'infrastructure S25.
Tu tournes sur AlienStef (Dell Alienware Aurora R4, Ubuntu 24.04, RTX 3060 12GB).
Tu es connecte directement a Home Assistant (10.0.0.136:8123) via ha_bridge.

== ETAT DU SYSTEME (LIVE) ==
Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
Pipeline mode: {pipeline.get('mode', 'unknown')}
Threat level: {pipeline.get('threat_level', 'T0')}
Kill switch: {'ON' if pipeline.get('kill_switch') else 'OFF'}
Agents en ligne: {len(online_agents)}/{len(agents)} ({', '.join(online_agents[:8])})

== DERNIER SIGNAL ==
Action: {last_signal.get('action', 'N/A')}
Symbol: {last_signal.get('symbol', 'N/A')}
Confidence: {last_signal.get('effective_confidence', 'N/A')}
Verdict: {last_signal.get('verdict', 'N/A')}
Source: {last_signal.get('source', 'N/A')}

== SENSORS HA ==
{json.dumps(ha_data, indent=2) if ha_data else 'Non disponible'}

== INTEL RECENT ==
{intel_lines if intel_lines.strip() else 'Aucun intel recent'}

== TES CAPACITES ==
- Tu peux lire et analyser tous les sensors HA
- Tu peux declencher des automations via ha_bridge
- Tu peux envoyer des notifications mobiles
- Tu peux proposer des trades (BUY/SELL via le pipeline)
- Tu peux changer le threat level et le kill switch
- Tu connais l'etat de tous les 14 agents du mesh

== REGLES ==
- Reponds en francais, sois concis et direct
- Pour les trades: TOUJOURS verifier le kill_switch et threat_level avant
- Ne jamais inventer des donnees — utilise les sensors live
- Si on te demande d'executer une action, confirme d'abord
- Tu es l'agent principal, pas un chatbot generique
"""


def handle_chat_completion(request_data: Dict, ha_bridge=None, load_state_fn=None) -> Dict:
    """Process an OpenAI-compatible chat completion request."""

    messages = request_data.get("messages", [])
    model = request_data.get("model", OLLAMA_MODEL)
    stream = request_data.get("stream", False)
    max_tokens = request_data.get("max_tokens", 1000)

    # Build system context with live data
    system_prompt = _get_system_context(ha_bridge, load_state_fn)

    # Check if user is asking for an action
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break

    # Prepare messages for Ollama
    ollama_messages = [{"role": "system", "content": system_prompt}]

    # Keep conversation history (last 10 messages)
    for m in messages[-10:]:
        if m.get("role") in ("user", "assistant"):
            ollama_messages.append({
                "role": m["role"],
                "content": m.get("content", ""),
            })

    # Call Ollama
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model if model != "s25-lumiere" else OLLAMA_MODEL,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                },
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

    # Check if reply contains an action request
    reply = _maybe_execute_action(reply, user_msg, ha_bridge)

    # Return OpenAI-compatible response
    return {
        "id": f"chatcmpl-s25-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def _maybe_execute_action(reply: str, user_msg: str, ha_bridge) -> str:
    """Check if the user asked for an action and the model suggested one."""
    if not ha_bridge or not ha_bridge.connected:
        return reply

    user_lower = user_msg.lower()

    # Status check shortcuts
    if any(w in user_lower for w in ("status", "etat", "comment va", "ca roule")):
        ping = ha_bridge.ping()
        if ping.get("ok"):
            reply += "\n\n[HA: connecte et fonctionnel]"
        else:
            reply += "\n\n[HA: DECONNECTE]"

    return reply


def list_models() -> Dict:
    """Return available models in OpenAI format."""
    models = [
        {
            "id": "s25-lumiere",
            "object": "model",
            "created": 1700000000,
            "owned_by": "s25-local",
            "permission": [],
        },
    ]

    # Check Ollama for available models
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        for m in resp.json().get("models", []):
            models.append({
                "id": m["name"],
                "object": "model",
                "created": 1700000000,
                "owned_by": "ollama-local",
                "permission": [],
            })
    except Exception:
        pass

    return {"object": "list", "data": models}
