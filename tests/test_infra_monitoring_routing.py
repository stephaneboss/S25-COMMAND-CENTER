"""
Regression tests for infra_monitoring routing to system_health.
"""
import agents.mission_worker as mw
from agents.mesh_heartbeat_cron import LOCAL_AGENTS

def _registry():
    return {aid: {"status": "online", "capabilities": list(meta.get("capabilities") or [])}
            for aid, meta in LOCAL_AGENTS.items()}

def _mission(**over):
    m = {"mission_id": "mis_test_infra", "task_type": "infra_monitoring",
         "target_agent": None, "routing": {"fallback_agents": ["LOCAL_CRON"]}}
    m.update(over)
    return m

def test_system_health_declares_infra_monitoring():
    assert "infra_monitoring" in LOCAL_AGENTS["system_health"]["capabilities"]

def test_infra_monitoring_routes_to_system_health():
    assert mw.choose_target(_mission(), _registry()) == "system_health"

def test_offline_system_health_yields_no_target():
    agents = _registry()
    agents["system_health"]["status"] = "offline"
    assert mw.choose_target(_mission(), agents) is None

def test_other_task_types_unchanged():
    agents = _registry()
    for task_type, expected in (("trading_analysis", "quant_brain"),
                                ("strategy_planning", "quant_brain"),
                                ("market_news", "perplexity_news_scanner")):
        assert mw.choose_target(_mission(task_type=task_type), agents) == expected

def test_no_other_agent_gained_infra_monitoring():
    owners = [aid for aid, meta in LOCAL_AGENTS.items()
              if "infra_monitoring" in (meta.get("capabilities") or [])]
    assert owners == ["system_health"]
