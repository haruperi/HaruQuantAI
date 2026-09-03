"""Unit tests for Tick Normalization manifest."""

from app.contracts.data.capabilities import NORMALIZE_TICKS_CAPABILITY
from app.services.data.tick_normalization.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-NORMALIZE_TICKS"
    assert SPEC.domain == "data"
    assert NORMALIZE_TICKS_CAPABILITY in SPEC.provides
    assert SPEC.state is None
    assert "max_batch_size" in SPEC.config_keys
