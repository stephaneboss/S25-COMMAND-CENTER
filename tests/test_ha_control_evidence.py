import ast
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.mesh_status_view import pipeline_control_evidence


@pytest.mark.parametrize("local,ha,effective,consistent", [
    (False, "on", True, False), (True, "off", True, False),
    (False, "off", False, True), (True, "on", True, True),
    (False, "unknown", None, None), (True, "unknown", True, None),
    (False, "unavailable", None, None),
])
def test_control_sources(local, ha, effective, consistent):
    original = {"kill_switch": local, "mode": "authorized"}
    result = pipeline_control_evidence(original, ha)
    assert result["effective_kill_switch"] is effective
    assert result["kill_switch_sources_consistent"] is consistent
    assert result["kill_switch"] is local
    assert result["mode"] == "authorized"
    assert original == {"kill_switch": local, "mode": "authorized"}


def load_readers(get, token="test-token"):
    source = Path("cockpit_lumiere.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {"_ha_kill_switch_state", "_ha_kill_switch_active"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    ns = {"os": os, "requests": SimpleNamespace(get=get),
          "vault_get": lambda key, default: token if key == "HA_TOKEN" else "http://ha"}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<readers>", "exec"), ns)
    return ns


@pytest.mark.parametrize("state,expected", [
    ("on", "on"), ("off", "off"), ("unavailable", "unknown"), (None, "unknown"),
])
def test_ha_reader_states(state, expected):
    calls = []
    def get(url, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(status_code=200, json=lambda: {"state": state})
    ns = load_readers(get)
    assert ns["_ha_kill_switch_state"]() == expected
    assert ns["_ha_kill_switch_active"]() is (expected == "on")
    assert calls[0]["timeout"] == 2.0


@pytest.mark.parametrize("failure", ["missing_token", "http_error", "timeout"])
def test_ha_failure_is_unknown_and_preserves_execution_boolean(failure):
    def get(url, **kwargs):
        if failure == "missing_token":
            pytest.fail("No request should be made without a token")
        if failure == "timeout":
            raise TimeoutError
        return SimpleNamespace(status_code=401)
    ns = load_readers(get, token="" if failure == "missing_token" else "test-token")
    assert ns["_ha_kill_switch_state"]() == "unknown"
    assert ns["_ha_kill_switch_active"]() is False

