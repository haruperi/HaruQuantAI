"""Unit tests for Volume Profile Source Preparation manifest."""

from app.contracts.data.capabilities import PREPARE_PROFILES_CAPABILITY
from app.services.data.profile_source_preparation.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-PREPARE_PROFILES"
    assert SPEC.domain == "data"
    assert PREPARE_PROFILES_CAPABILITY in SPEC.provides
    assert SPEC.state is None
    assert "default_price_step" in SPEC.config_keys
    assert "default_bin_count" in SPEC.config_keys
    assert "min_price_step" in SPEC.config_keys
    assert "max_bin_count" in SPEC.config_keys
    assert "require_session_alignment" in SPEC.config_keys
