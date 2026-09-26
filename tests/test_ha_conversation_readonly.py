"""The Assist conversation must not execute model-generated actions by default."""

from unittest.mock import patch

from agents import s25_conversation_agent as agent


class _Bridge:
    connected = True

    def __init__(self):
        self.actions = []

    def push_signal(self, *args, **kwargs):
        self.actions.append("signal")
        return {"ok": True}


class _OllamaResponse:
    def json(self):
        return {"message": {"content": '{"action":"signal","type":"BUY","symbol":"BTC/USDT"}'}}


def test_model_action_cannot_emit_ha_signal_by_default(monkeypatch):
    monkeypatch.delenv("S25_HA_CONVERSATION_ACTIONS", raising=False)
    bridge = _Bridge()

    with patch.object(agent, "_get_system_context", return_value="lecture seule"), patch.object(
        agent.requests, "post", return_value=_OllamaResponse()
    ):
        result = agent.handle_chat_completion(
            {"model": "s25-lumiere", "messages": [{"role": "user", "content": "statut"}]},
            ha_bridge=bridge,
            load_state_fn=lambda: {},
        )

    assert bridge.actions == []
    assert "[SIGNAL" not in result["choices"][0]["message"]["content"]
