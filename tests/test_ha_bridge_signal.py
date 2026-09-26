"""Signal result semantics without contacting Home Assistant or an exchange."""
from unittest.mock import Mock

from agents.ha_bridge import HABridge


def bridge_with_mocks():
    bridge = HABridge()
    bridge.url = "http://localhost:8123"
    bridge.token = "test-only"
    bridge.push_sensor = Mock(return_value=True)
    bridge.call_service = Mock(return_value=True)
    bridge.notify = Mock(return_value=True)
    return bridge


def signal(bridge, verdict="EXECUTE"):
    return bridge.push_signal(
        action="BUY", symbol="BTC/USDT", confidence=0.9,
        effective_confidence=0.9, price=100.0,
        reason="test", verdict=verdict, source="unit-test",
    )


def test_failed_ha_service_is_not_reported_as_executed():
    bridge = bridge_with_mocks()
    bridge.call_service.return_value = False

    result = signal(bridge)

    assert result["mexc_service_requested"] == "spot_buy_btc"
    assert result["mexc_service_accepted"] is False
    assert "mexc_executed" not in result
    assert result["ok"] is False
    assert bridge.call_service.call_count == 1


def test_accepted_service_is_only_reported_as_requested():
    bridge = bridge_with_mocks()

    result = signal(bridge)

    assert result["mexc_service_accepted"] is True
    assert result["trading_status"] == "REQUESTED_BUY_BTC"
    assert "mexc_executed" not in result
    assert result["ok"] is True


def test_failed_sensor_write_makes_pipeline_result_false():
    bridge = bridge_with_mocks()
    bridge.push_sensor.return_value = False

    result = signal(bridge, verdict="HOLD")

    assert result["sensors_ok"] is False
    assert result["ok"] is False
    bridge.call_service.assert_not_called()
