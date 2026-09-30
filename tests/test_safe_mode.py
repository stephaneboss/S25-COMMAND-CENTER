import json
from agents import safe_mode as sm


def test_stale_april_flag_is_inactive(tmp_path):
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"active": True, "activated_at": 1776823292.1,
                             "reason": "global_status=critical"}))
    assert sm.is_active(p, now=1776823292.1 + 7 * 3600) is False


def test_active_false_file_is_inactive(tmp_path):
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"active": False}))
    assert sm.is_active(p) is False


def test_missing_or_corrupt_file(tmp_path):
    p = tmp_path / "d.json"
    assert sm.is_active(p) is False
    p.write_text("{not json")
    assert sm.is_active(p) is False


def test_reconcile_lifecycle_never_unlinks(tmp_path):
    p = tmp_path / "d.json"
    assert sm.reconcile("critical", p, now=1000) is True
    assert sm.reconcile("unknown", p, now=1001) is True
    assert sm.reconcile("healthy", p, now=1002) is False
    assert p.exists() and json.loads(p.read_text())["active"] is False


def test_critical_refreshes_ttl(tmp_path):
    p = tmp_path / "d.json"
    sm.activate("x", p, ttl_s=100, now=0)
    sm.activate("x", p, ttl_s=100, now=90)
    d = json.loads(p.read_text())
    assert d["activated_at"] == 0 and d["confirmed_at"] == 90
    assert sm.is_active(p, now=150) is True
    assert sm.is_active(p, now=191) is False
