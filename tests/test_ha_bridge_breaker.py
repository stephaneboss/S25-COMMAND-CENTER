"""HA circuit breaker: an unreachable HA must not make /api/status take 6 x 8 s."""
import requests

from agents.ha_bridge import HABridge


def _bridge(monkeypatch):
    monkeypatch.setenv("HA_URL", "http://192.0.2.1:8123")
    b = HABridge()
    b.token = "t"
    return b


def test_connection_error_opens_breaker(monkeypatch):
    b = _bridge(monkeypatch)
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise requests.ConnectionError("No route to host")
    monkeypatch.setattr(requests, "get", boom)
    assert b.get_state("sensor.a") is None
    assert b.get_state("sensor.b") is None      # fail fast, no second network call
    assert len(calls) == 1
    assert b.reachable is False and "No route" in b.last_error


def test_breaker_closes_after_ttl(monkeypatch):
    b = _bridge(monkeypatch)
    monkeypatch.setattr(requests, "get", lambda *a, **k: (_ for _ in ()).throw(requests.Timeout()))
    b.get_state("sensor.a")
    b._down_until = 0.0                           # ttl elapsed

    class R:
        status_code = 200

        def json(self):
            return {"state": "on"}
    monkeypatch.setattr(requests, "get", lambda *a, **k: R())
    assert b.get_state("sensor.a") == {"state": "on"}
    assert b.reachable is True and b.last_error == ""


def test_http_error_does_not_open_breaker(monkeypatch):
    b = _bridge(monkeypatch)

    class R:
        status_code = 404
    monkeypatch.setattr(requests, "get", lambda *a, **k: R())
    assert b.get_state("sensor.missing") is None
    assert b.reachable is True


def test_push_sensor_skipped_while_down(monkeypatch):
    b = _bridge(monkeypatch)
    b._mark_down(requests.ConnectionError("x"))
    monkeypatch.setattr(requests, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no call")))
    assert b.push_sensor("sensor.x", 1) is False


def test_push_sensor_error_opens_breaker_from_closed(monkeypatch):
    # GPT Work review: two pushes from a closed circuit -> one network call only
    b = _bridge(monkeypatch)
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise requests.ConnectionError("No route to host")
    monkeypatch.setattr(requests, "post", boom)
    assert b.push_sensor("sensor.x", 1) is False
    assert b.push_sensor("sensor.y", 2) is False
    assert len(calls) == 1
    assert b.reachable is False and "No route" in b.last_error


def test_call_service_error_opens_breaker(monkeypatch):
    b = _bridge(monkeypatch)
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise requests.Timeout("slow")
    monkeypatch.setattr(requests, "post", boom)
    assert b.call_service("notify", "x") is False
    assert b.call_service("notify", "x") is False
    assert len(calls) == 1


def test_cockpit_heartbeat_uses_version_probe():
    import agents.mesh_heartbeat_cron as hb
    src = open(hb.__file__, encoding="utf-8").read()
    assert '/api/version", timeout=5' in src
    assert 'f"{COCKPIT}/api/status", timeout=3' not in src
