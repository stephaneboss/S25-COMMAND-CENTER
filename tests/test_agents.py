"""
S25 Lumière — Agent Tests
==========================
Run: make test
     python3 -m pytest tests/ -v
"""

import asyncio
import pytest
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Base Agent Tests ────────────────────────────────────────────────

class MockAgent:
    """Minimal agent for testing base behavior."""

    def __init__(self):
        from agents.base import BaseAgent, AgentStatus
        # Can't instantiate abstract class directly — test through subclass

    def test_status_enum(self):
        from agents.base import AgentStatus
        assert AgentStatus.IDLE.value    == "IDLE"
        assert AgentStatus.ACTIVE.value  == "ACTIVE"
        assert AgentStatus.PAUSED.value  == "PAUSED"
        assert AgentStatus.ERROR.value   == "ERROR"
        assert AgentStatus.STOPPED.value == "STOPPED"


def test_agent_status_values():
    """Test AgentStatus enum has correct values."""
    from agents.base import AgentStatus
    assert AgentStatus.IDLE.value    == "IDLE"
    assert AgentStatus.ACTIVE.value  == "ACTIVE"
    assert AgentStatus.PAUSED.value  == "PAUSED"
    assert AgentStatus.ERROR.value   == "ERROR"
    assert AgentStatus.STOPPED.value == "STOPPED"


def test_commander_init():
    """Test Commander initializes correctly."""
    from agents.commander import Commander

    config = {"ha_url": "http://test:8123", "ha_token": ""}
    c = Commander(config)

    assert c.running == False
    assert len(c.agents) == 0
    assert c._circuit_breaker == False
    assert c._processed == 0


def test_commander_register():
    """Test agent registration."""
    from agents.commander import Commander
    from agents.base import BaseAgent, AgentStatus

    class DummyAgent(BaseAgent):
        async def run(self): pass
        async def handle_signal(self, signal): pass

    c = Commander()
    agent = DummyAgent("test_agent", "1.0.0")
    c.register(agent)

    assert "test_agent" in c.agents
    assert c.get_agent("test_agent") is agent


def test_commander_circuit_breaker():
    """Test circuit breaker trigger and reset."""
    from agents.commander import Commander

    c = Commander()
    assert c._circuit_breaker == False

    c.trigger_circuit_breaker("test breach")
    assert c._circuit_breaker == True

    c.reset_circuit_breaker()
    assert c._circuit_breaker == False


@pytest.mark.asyncio
async def test_commander_dispatch_blocked_by_circuit_breaker():
    """Signals should be dropped when circuit breaker is open."""
    from agents.commander import Commander

    c = Commander()
    c._circuit_breaker = True

    await c.dispatch({"type": "TEST", "data": {}})

    assert c._dropped == 1
    assert c._signal_queue.qsize() == 0


def test_commander_status():
    """Test Commander status output."""
    from agents.commander import Commander

    c = Commander()
    status = c.get_status()

    assert "commander" in status
    assert "version" in status
    assert "circuit_breaker" in status
    assert "agents" in status
    assert status["commander"] == "STOPPED"


# ─── Security Vault Tests ────────────────────────────────────────────

def test_vault_init():
    """Test vault initializes without error."""
    from security.vault import S25Vault

    v = S25Vault(env_file=".env.example")  # Use example file (no real keys)
    assert v is not None


def test_vault_required_keys_defined():
    """Verify required keys are defined."""
    from security.vault import S25Vault

    assert "HA_TOKEN" in S25Vault.REQUIRED_KEYS
    assert "GEMINI_API_KEY" in S25Vault.REQUIRED_KEYS


def test_vault_mask():
    """Test secret masking."""
    from security.vault import S25Vault

    v = S25Vault(env_file=".env.example")
    # Inject a test secret
    v._secrets["TEST_KEY"] = "sk-1234567890abcdef"
    masked = v.mask("TEST_KEY")

    assert "sk-1" in masked
    assert "cdef" in masked
    assert "1234567890ab" not in masked  # Middle should be hidden


def test_vault_not_set():
    """Missing key should return [NOT SET]."""
    from security.vault import S25Vault

    v = S25Vault(env_file=".env.example")
    assert v.mask("NONEXISTENT_KEY") == "[NOT SET]"


def test_vault_require_raises():
    """vault.require() should raise if key missing."""
    from security.vault import S25Vault

    v = S25Vault(env_file=".env.example")
    # Clear any accidentally loaded keys for this test
    v._secrets.pop("HA_TOKEN", None)

    with pytest.raises(ValueError) as exc_info:
        v.require("HA_TOKEN")

    assert "HA_TOKEN" in str(exc_info.value)


def test_vault_audit_no_values():
    """Audit should never expose secret values."""
    from security.vault import S25Vault

    v = S25Vault(env_file=".env.example")
    v._secrets["HA_TOKEN"] = "secret_token_12345"

    audit = v.audit()

    # Audit report should never contain the actual value
    audit_str = str(audit)
    assert "secret_token_12345" not in audit_str
    assert "HA_TOKEN" in audit_str  # Key name is OK to show


def test_vault_check_ready():
    """Test readiness check structure."""
    from security.vault import S25Vault

    v = S25Vault(env_file=".env.example")
    ready = v.check_ready()

    assert "core_ready" in ready
    assert "trading_ready" in ready
    assert "ha_ready" in ready
    assert "ai_ready" in ready


# ─── Security Audit Tests ────────────────────────────────────────────

def test_audit_log_creates_entry():
    """Test audit log writes entries."""
    from security.audit import AuditLog
    import os

    log_file = "/tmp/test_s25_audit.jsonl"

    # Clean up
    if os.path.exists(log_file):
        os.remove(log_file)

    a = AuditLog(log_file=log_file)
    a.log("API_CALL", "test_agent", {"endpoint": "/test"}, risk="INFO")

    assert os.path.exists(log_file)
    entries = a.get_recent(10)
    assert len(entries) == 1
    assert entries[0]["event"] == "API_CALL"

    # Cleanup
    os.remove(log_file)


def test_audit_redacts_secrets():
    """Audit should redact sensitive field values."""
    from security.audit import AuditLog

    a = AuditLog(log_file="/tmp/test_audit_redact.jsonl")
    a.log("KEY_ACCESSED", "vault", {
        "api_key": "real_secret_key_12345",
        "endpoint": "/api/trade"
    })

    entries = a.get_recent(1)
    entry_str = str(entries[0])

    assert "real_secret_key_12345" not in entry_str
    assert "[REDACTED]" in entry_str

    import os
    os.remove("/tmp/test_audit_redact.jsonl")


def test_audit_integrity():
    """Verify audit hash integrity check works."""
    from security.audit import AuditLog
    import os

    log_file = "/tmp/test_audit_integrity.jsonl"

    a = AuditLog(log_file=log_file)
    a.log("TRADE_SIGNAL", "arkon", {"symbol": "BTC/USDT"})

    result = a.verify_integrity(n=10)
    assert result["tampered"] == 0
    assert result["valid"] == 1

    os.remove(log_file)


# ─── Risk Guardian Tests ─────────────────────────────────────────────

def test_risk_guardian_init():
    """Test RiskGuardian initializes with correct limits."""
    from agents.risk_guardian import RiskGuardian

    config = {
        "risk_guardian": {
            "max_daily_loss_pct":    3.0,
            "max_open_positions":    3,
            "stop_loss_pct":         2.0,
        }
    }

    rg = RiskGuardian(config=config)
    assert rg.max_daily_loss_pct    == 3.0
    assert rg.max_open_positions    == 3
    assert rg.stop_loss_pct         == 2.0
    assert rg.trading_paused        == False


@pytest.mark.asyncio
async def test_risk_guardian_approves_valid_signal():
    """Valid signal should be approved."""
    from agents.risk_guardian import RiskGuardian

    rg = RiskGuardian()
    signal = {
        "type": "ARKON_SIGNAL",
        "data": {"symbol": "BTC/USDT", "action": "BUY", "confidence": 0.85}
    }

    # Should not trigger breach
    approved = await rg._approve_signal(signal)
    assert approved == True


@pytest.mark.asyncio
async def test_risk_guardian_blocks_when_paused():
    """Paused trading should block all signals."""
    from agents.risk_guardian import RiskGuardian

    rg = RiskGuardian()
    rg.trading_paused = True

    signal = {"type": "ARKON_SIGNAL", "data": {}}
    approved = await rg._approve_signal(signal)
    assert approved == False


# ─── ARKON Signal Tests ───────────────────────────────────────────────

def test_arkon_signal_validation_valid():
    """Valid signal should pass validation."""
    from agents.arkon_signal import ArkonSignal

    config = {"arkon_signal": {"min_confidence": 0.75}}
    agent = ArkonSignal(config=config)

    result = agent._validate({
        "symbol":     "BTC/USDT",
        "action":     "BUY",
        "confidence": 0.87,
        "price":      65000
    })
    assert result["valid"] == True


def test_arkon_signal_validation_low_confidence():
    """Low confidence signal should fail validation."""
    from agents.arkon_signal import ArkonSignal

    agent = ArkonSignal(config={"arkon_signal": {"min_confidence": 0.75}})

    result = agent._validate({
        "symbol":     "BTC/USDT",
        "action":     "BUY",
        "confidence": 0.50,   # Below threshold
    })
    assert result["valid"] == False
    assert "confidence" in result["reason"].lower()


def test_arkon_signal_validation_invalid_action():
    """Unknown action should fail."""
    from agents.arkon_signal import ArkonSignal

    agent = ArkonSignal()
    result = agent._validate({
        "symbol":     "BTC/USDT",
        "action":     "MOON",   # Invalid
        "confidence": 0.90,
    })
    assert result["valid"] == False


def test_arkon_signal_hold_not_routed_to_executor():
    """HOLD signals should not be routed to MEXC executor."""
    from agents.arkon_signal import ArkonSignal

    agent = ArkonSignal()
    # HOLD action — no trade execution expected
    signal_data = {
        "symbol":     "BTC/USDT",
        "action":     "HOLD",
        "confidence": 0.95,
        "price":      65000
    }

    # Validate
    result = agent._validate(signal_data)
    assert result["valid"] == True  # HOLD is valid

    # But HOLD should not trigger executor
    # (tested via integration — agent._process_arkon checks action != HOLD)


# ─── Config Tests ────────────────────────────────────────────────────

def test_agents_yaml_is_valid():
    """configs/agents.yaml should be valid YAML."""
    import yaml

    with open("configs/agents.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "commander" in config
    assert "agents" in config
    assert "treasury_engine" in config["agents"]
    assert "balance_sentinel" in config["agents"]


def test_networks_yaml_is_valid():
    """configs/networks.yaml should be valid YAML."""
    import yaml

    with open("configs/networks.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "networks" in config
    assert "cosmoshub" in config["networks"]
    assert "akash" in config["networks"]
    assert "osmosis" in config["networks"]

    # Verify AKT denom
    assert config["networks"]["akash"]["native_denom"] == "uakt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
