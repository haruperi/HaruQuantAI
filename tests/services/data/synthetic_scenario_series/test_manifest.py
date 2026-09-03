"""Unit tests for Synthetic and Scenario Series feature manifest."""

from app.contracts.data.capabilities import GENERATE_SCENARIOS_CAPABILITY
from app.services.data.synthetic_scenario_series.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify manifest declares expected feature specification attributes."""
    assert SPEC.feature_id == "FEAT-DATA-GENERATE_SCENARIOS"
    assert SPEC.domain == "data"
    assert SPEC.provides == frozenset({GENERATE_SCENARIOS_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset()
    assert SPEC.conflicts == frozenset()
    assert SPEC.state is None
    assert SPEC.config_keys == frozenset(
        {
            "max_records",
            "default_model",
            "default_rounding",
            "supported_transform_types",
        }
    )
