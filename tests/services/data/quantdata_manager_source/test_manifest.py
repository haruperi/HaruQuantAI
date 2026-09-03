"""Unit tests for QuantDataManager Source manifest."""

from app.contracts.data.capabilities import IMPORT_QUANTDATA_CAPABILITY
from app.kernel.state import RetentionPolicy
from app.services.data.quantdata_manager_source.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-IMPORT_QUANTDATA"
    assert SPEC.domain == "data"
    assert IMPORT_QUANTDATA_CAPABILITY in SPEC.provides
    assert SPEC.state is not None
    assert SPEC.state.namespace == "data.quantdata_manager_source"
    assert SPEC.state.schema_version == 1
    assert SPEC.state.retention_policy == RetentionPolicy.RETAIN
    assert "allowed_root" in SPEC.config_keys
    assert "database_path" in SPEC.config_keys
