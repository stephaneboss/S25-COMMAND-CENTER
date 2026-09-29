from datetime import datetime, timezone

from agents import command_mesh as cm


def test_pipeline_freshness_semantics_are_explicit():
    source = open(cm.__file__, encoding="utf-8").read()
    assert '"NO_SIGNAL"' in source
    assert '"SIGNAL_FRESH"' in source
    assert '"SIGNAL_STALE"' in source
    assert 'MESH_SIGNAL_STALE_SEC' in source
    assert '"signal_age_sec"' in source


def test_historical_signal_age_is_computable():
    age = cm._age_sec("2026-04-22T02:01:01.645750+00:00", datetime(2026, 9, 29, tzinfo=timezone.utc))
    assert age is not None and age > 7200
