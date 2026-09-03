"""Unit tests for External Series Alignment manifest."""

from app.contracts.data.capabilities import ALIGN_SERIES_CAPABILITY
from app.services.data.external_series_alignment.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-ALIGN_SERIES"
    assert SPEC.domain == "data"
    assert ALIGN_SERIES_CAPABILITY in SPEC.provides
    assert SPEC.state is None
    assert "max_series_points_per_request" in SPEC.config_keys
    assert "default_timezone" in SPEC.config_keys
    assert "default_max_age_seconds" in SPEC.config_keys
    assert "default_missing_policy" in SPEC.config_keys
