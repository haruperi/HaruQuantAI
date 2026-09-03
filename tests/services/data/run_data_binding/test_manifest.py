"""Unit tests for Run Data Binding manifest."""

from app.contracts.data.capabilities import BIND_RUN_DATA_CAPABILITY
from app.services.data.run_data_binding.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-BIND_RUN_DATA"
    assert SPEC.domain == "data"
    assert BIND_RUN_DATA_CAPABILITY in SPEC.provides
    assert SPEC.state is None
    assert "strict_precision_check" in SPEC.config_keys
    assert "allow_synthetic_sources" in SPEC.config_keys
    assert "require_committed_status" in SPEC.config_keys
    assert "supported_precisions" in SPEC.config_keys
