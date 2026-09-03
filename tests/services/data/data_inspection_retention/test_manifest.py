"""Tests for FEAT-DATA-MANAGE_RETENTION manifest specification."""

from app.contracts.data.capabilities import MANAGE_RETENTION_CAPABILITY
from app.services.data.data_inspection_retention.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify manifest properties."""
    assert SPEC.feature_id == "FEAT-DATA-MANAGE_RETENTION"
    assert SPEC.domain == "data"
    assert MANAGE_RETENTION_CAPABILITY in SPEC.provides
    assert SPEC.requires == frozenset()
    assert "default_preview_limit" in SPEC.config_keys
    assert "max_preview_limit" in SPEC.config_keys
    assert "default_quarantine_days" in SPEC.config_keys
