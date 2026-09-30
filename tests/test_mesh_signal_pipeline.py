"""P1 Signal -> Mesh: system_state.last_signal_at follows the cockpit pipeline."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from agents import command_mesh as cm

NOW = datetime(2026, 9, 30, 4, 0, tzinfo=timezone.utc)
APRIL = "2026-04-22T02:01:01.645750+00:00"
MESH = {"sig_old": {"ts": APRIL, "source_agent": "DEDUP5X"}}


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))

    def write(ts, source="TRADINGVIEW"):
        (tmp_path / "agents_state.json").write_text(json.dumps(
            {"pipeline": {"last_signal": {"ts": ts, "source": source, "symbol": "BTC/USD"}}}))
    return write


def test_tradingview_signal_wins_over_april_mesh_signal(pipeline):
    ts = (NOW - timedelta(minutes=3)).isoformat()
    pipeline(ts)
    latest = cm._latest_signal(MESH, NOW)
    assert latest == {"ts": ts, "source": "TRADINGVIEW", "origin": "pipeline"}


def test_same_event_as_pipeline_last_signal(pipeline):
    ts = "2026-09-30T01:15:02.733501+00:00"
    pipeline(ts)
    latest = cm._latest_signal(MESH, NOW)
    # identical timestamp and source -> same event, delta 0 (< 5 min criterion)
    assert latest["ts"] == ts and latest["source"] == "TRADINGVIEW"


def test_newer_mesh_commit_still_wins(pipeline):
    pipeline((NOW - timedelta(hours=1)).isoformat())
    mesh = {"s": {"ts": (NOW - timedelta(minutes=1)).isoformat(), "source_agent": "TRINITY"}}
    assert cm._latest_signal(mesh, NOW)["origin"] == "mesh"


def test_no_pipeline_file_falls_back_to_mesh(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))
    assert cm._latest_signal(MESH, NOW) == {"ts": APRIL, "source": "DEDUP5X", "origin": "mesh"}


def test_corrupt_pipeline_file_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))
    (tmp_path / "agents_state.json").write_text("{not json")
    assert cm._latest_signal(MESH, NOW)["origin"] == "mesh"


def test_nothing_anywhere(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))
    assert cm._latest_signal({}, NOW) == {}


def test_relative_memory_dir_resolves_under_repo(monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", "./memory")
    assert cm._pipeline_state_path() == cm.REPO / "memory" / "agents_state.json"


def test_state_exposes_source_and_origin():
    src = open(cm.__file__, encoding="utf-8").read()
    assert '"last_signal_source"' in src and '"last_signal_origin"' in src


@pytest.mark.parametrize("age_min,expected", [(1, "SIGNAL_FRESH"), (180, "SIGNAL_STALE")])
def test_recompute_state_end_to_end(tmp_path, monkeypatch, age_min, expected):
    """Pipeline signal drives the mesh state; freshness follows MESH_SIGNAL_STALE_SEC (2 h)."""
    store = tmp_path / "mesh"
    store.mkdir()
    for name in ("AGENTS_PATH", "INCIDENTS_PATH", "SIGNALS_PATH", "STATE_PATH"):
        monkeypatch.setattr(cm, name, store / (name.lower() + ".json"))
    monkeypatch.setattr(cm, "_journal", lambda *a, **k: None)
    from agents import safe_mode
    monkeypatch.setattr(safe_mode, "DEFAULT_PATH", store / "degraded_mode.json")
    (store / "signals_path.json").write_text(json.dumps({"items": MESH}))
    mem = tmp_path / "mem"
    mem.mkdir()
    monkeypatch.setenv("MEMORY_DIR", str(mem))
    ts = (datetime.now(timezone.utc) - timedelta(minutes=age_min)).isoformat()
    (mem / "agents_state.json").write_text(json.dumps(
        {"pipeline": {"last_signal": {"ts": ts, "source": "TRADINGVIEW"}}}))

    cm._recompute_system_state()
    state = json.loads((store / "state_path.json").read_text())
    assert state["last_signal_at"] == ts
    assert state["last_signal_source"] == "TRADINGVIEW"
    assert state["last_signal_origin"] == "pipeline"
    assert state["pipeline_status"] == expected
    assert abs(state["signal_age_sec"] - age_min * 60) < 60
