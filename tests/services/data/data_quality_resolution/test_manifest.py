"""Unit tests for Data Quality Resolution manifest."""

from app.contracts.data.capabilities import RESOLVE_QUALITY_CAPABILITY
from app.services.data.data_quality_resolution.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-RESOLVE_QUALITY"
    assert SPEC.domain == "data"
    assert RESOLVE_QUALITY_CAPABILITY in SPEC.provides
    assert SPEC.state is None
    assert "database_path" in SPEC.config_keys
    assert "auto_migrate" in SPEC.config_keys
    assert "max_findings" in SPEC.config_keys
