"""Unit tests for Real-Time Market Events feature manifest."""

from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.services.data.realtime_market_events.manifest import SPEC


def test_manifest_spec() -> None:
    """Test SPEC identity, domain, and provided capabilities."""
    assert SPEC.feature_id == "FEAT-DATA-STREAM_MARKET_EVENTS"
    assert SPEC.domain == "data"
    assert STREAM_MARKET_EVENTS_CAPABILITY in SPEC.provides
    assert SPEC.state is not None
    assert SPEC.state.namespace == "data.realtime_market_events"
    assert "buffer_capacity" in SPEC.config_keys
    assert "max_subscriptions" in SPEC.config_keys
    assert "stale_timeout_seconds" in SPEC.config_keys
