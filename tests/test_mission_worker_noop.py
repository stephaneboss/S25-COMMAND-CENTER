"""An unhandled mission must not get a false completion receipt."""
import pytest

from agents import mission_worker as worker


@pytest.mark.parametrize("task_type", ["fallback", "unknown_task_type"])
def test_unhandled_mission_fails_instead_of_completing(monkeypatch, task_type):
    updates = []
    monkeypatch.setattr(worker, "should_skip_non_critical", lambda mission: False)
    monkeypatch.setattr(worker, "_load", lambda *args, **kwargs: {"items": {}})
    monkeypatch.setattr(worker, "choose_target", lambda mission, agents: "LOCAL_CRON")
    monkeypatch.setattr(worker, "_update_mission", lambda mid, data: updates.append(data))
    monkeypatch.setattr(worker, "_journal", lambda *args, **kwargs: None)
    import agents.stability_layer as stability
    monkeypatch.setattr(stability, "breaker_record", lambda *args, **kwargs: None)

    result = worker.execute_mission({"mission_id": "mis_test", "task_type": task_type})

    assert result["status"] == "failed"
    assert result["error"] == f"no_dispatcher_for_task_type:{task_type}"
    assert updates[-1]["status"] == "failed"
    assert all(update.get("status") != "completed" for update in updates)
