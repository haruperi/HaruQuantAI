"""Unit tests for External Indicator Series manifest."""

from app.contracts.data.capabilities import IMPORT_INDICATORS_CAPABILITY
from app.services.data.external_indicator_series.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-IMPORT_INDICATORS"
    assert SPEC.domain == "data"
    assert IMPORT_INDICATORS_CAPABILITY in SPEC.provides
    assert SPEC.state is None
    assert "default_timezone" in SPEC.config_keys
    assert "max_points_per_series" in SPEC.config_keys
    assert "require_deterministic_reimport" in SPEC.config_keys
    assert "allow_future_timestamps" in SPEC.config_keys
    assert "default_missing_policy" in SPEC.config_keys
