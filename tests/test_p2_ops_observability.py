"""P2 observability: watchdog HA/proxy semantics, opsRun log_tail cockpit + deploy_receipt."""
import importlib
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def watchdog(monkeypatch):
    sys.path.insert(0, str(ROOT))
    sys.modules.pop("watchdog", None)
    mod = importlib.import_module("watchdog")
    mod.DETAILS.clear()
    return mod


def test_ha_without_token_is_explained(watchdog, monkeypatch):
    monkeypatch.setattr(watchdog, "HA_TOKEN", "")
    assert watchdog.check_ha() is False
    assert watchdog.DETAILS["ha"] == "no_token"


def test_ha_http_status_is_recorded(watchdog, monkeypatch):
    monkeypatch.setattr(watchdog, "HA_TOKEN", "t")

    class R:
        status_code = 401
    monkeypatch.setattr(watchdog.requests, "get", lambda *a, **k: R())
    assert watchdog.check_ha() is False
    assert watchdog.DETAILS["ha"] == "http_401"


def test_token_comes_from_vault_like_cockpit(watchdog, monkeypatch):
    import security.vault as vault
    monkeypatch.setattr(vault, "vault_get", lambda k, d=None: "from-vault" if k == "HA_TOKEN" else d)
    assert watchdog._cfg("HA_TOKEN") == "from-vault"


def test_proxy_not_installed_is_na(watchdog, monkeypatch, tmp_path):
    monkeypatch.setattr(watchdog, "PROXY_SCRIPT", str(tmp_path / "absent.py"))
    assert watchdog.proxy_installed() is False


def test_watchdog_source_publishes_details_and_na():
    src = (ROOT / "watchdog.py").read_text(encoding="utf-8")
    assert 'status["details"] = dict(DETAILS)' in src
    assert 'status["checks"]["proxy"] = None' in src


@pytest.fixture
def cockpit(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))
    monkeypatch.setenv("S25_SHARED_SECRET", "test-secret")
    monkeypatch.setenv("HOME", str(tmp_path))
    sys.path.insert(0, str(ROOT))
    sys.modules.pop("cockpit_lumiere", None)
    return importlib.import_module("cockpit_lumiere")


def _ops(client, op, args=None):
    return client.post("/api/ops/run", json={"op": op, "args": args or {}},
                       headers={"X-S25-Secret": "test-secret"})


def test_log_tail_cockpit_uses_journal_not_mission_worker(cockpit, monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.run", lambda cmd, **k: (calls.append(cmd), type(
        "R", (), {"returncode": 0, "stdout": "x", "stderr": ""})())[1])
    r = _ops(cockpit.app.test_client(), "log_tail", {"file": "cockpit", "n": 20})
    assert r.status_code == 200 and r.get_json()["log"] == "cockpit"
    assert calls and calls[-1][:4] == ["journalctl", "--user", "-u", "s25-cockpit"]


def test_log_tail_unknown_lists_cockpit(cockpit):
    r = _ops(cockpit.app.test_client(), "log_tail", {"file": "nope"})
    assert r.status_code == 400 and "cockpit" in r.get_json()["allowed"]


def test_deploy_receipt_reads_state(cockpit, tmp_path):
    d = tmp_path / ".local" / "state" / "s25"
    d.mkdir(parents=True)
    (d / "deploy.json").write_text(json.dumps({"status": "verified", "expected_sha": "abc"}))
    r = _ops(cockpit.app.test_client(), "deploy_receipt")
    body = r.get_json()
    assert r.status_code == 200 and body["receipt"]["status"] == "verified"
    assert "runtime_sha" in body


def test_deploy_receipt_missing_is_none(cockpit):
    body = _ops(cockpit.app.test_client(), "deploy_receipt").get_json()
    assert body["ok"] is True and body["receipt"] is None


def test_ops_run_still_requires_secret(cockpit):
    r = cockpit.app.test_client().post("/api/ops/run", json={"op": "deploy_receipt"})
    assert r.status_code == 401
