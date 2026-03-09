import importlib
import os
import sys
from pathlib import Path


def _load_cockpit_module(tmp_path):
    os.environ["MEMORY_DIR"] = str(tmp_path)
    module_name = "agents.cockpit_lumiere"
    if module_name in sys.modules:
        del sys.modules[module_name]
    return importlib.import_module(module_name)


def test_mesh_status_and_router_report(tmp_path):
    cockpit = _load_cockpit_module(tmp_path)
    client = cockpit.app.test_client()

    mesh = client.get("/api/mesh/status")
    assert mesh.status_code == 200
    payload = mesh.get_json()
    assert payload["ok"] is True
    assert "TRINITY" in payload["mesh"]["agents"]
    assert "gpt" in payload["gouv4"]

    router = client.post("/api/router/route", json={"task_type": "infra_monitoring"})
    assert router.status_code == 200
    router_payload = router.get_json()
    assert router_payload["recommended_agent"] == "perplexity"


def test_mission_create_update_and_archive(tmp_path):
    cockpit = _load_cockpit_module(tmp_path)
    client = cockpit.app.test_client()

    created = client.post(
        "/api/missions",
        json={
            "created_by": "TRINITY",
            "target": "COMET",
            "task_type": "infra_monitoring",
            "intent": "Verifier le tunnel KIMI",
            "priority": "high",
        },
    )
    assert created.status_code == 200
    mission = created.get_json()["mission"]
    assert mission["target"] == "COMET"
    assert mission["recommended_agent"] == "perplexity"

    active = client.get("/api/missions").get_json()["active"]
    assert any(item["mission_id"] == mission["mission_id"] for item in active)

    updated = client.post(
        "/api/missions/update",
        json={
            "mission_id": mission["mission_id"],
            "status": "completed",
            "actor": "COMET",
            "result": {"summary": "Tunnel confirme offline"},
        },
    )
    assert updated.status_code == 200
    updated_mission = updated.get_json()["mission"]
    assert updated_mission["status"] == "completed"

    missions_payload = client.get("/api/missions").get_json()
    assert not any(item["mission_id"] == mission["mission_id"] for item in missions_payload["active"])
    assert any(item["mission_id"] == mission["mission_id"] for item in missions_payload["history"])


def test_trinity_dispatch_mission_and_comet_feed(tmp_path):
    cockpit = _load_cockpit_module(tmp_path)
    client = cockpit.app.test_client()

    response = client.post(
        "/api/trinity",
        json={
            "intent": "Mission COMET: scan news Akash",
            "action": "mission",
            "data": {
                "target": "COMET",
                "task_type": "market_news",
                "priority": "normal",
            },
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["action"] == "mission"
    assert payload["mission"]["recommended_agent"] == "perplexity"

    feed = client.get("/api/comet/feed").get_json()
    assert feed["count"] >= 1
    assert "Mission queued for COMET" in feed["feed"][0]["summary"]
