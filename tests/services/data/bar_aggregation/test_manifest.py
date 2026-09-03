"""Unit tests for Bar Aggregation manifest."""

from app.contracts.data.capabilities import AGGREGATE_BARS_CAPABILITY
from app.services.data.bar_aggregation.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-AGGREGATE_BARS"
    assert SPEC.domain == "data"
    assert AGGREGATE_BARS_CAPABILITY in SPEC.provides
    assert SPEC.state is None
    assert "max_bars_per_request" in SPEC.config_keys
    assert "default_timezone" in SPEC.config_keys
    assert "allow_custom_timeframes" in SPEC.config_keys
