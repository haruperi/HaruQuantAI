from typing import TYPE_CHECKING

import pytest

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.kernel.feature import Feature, FeatureSpec, FeatureState

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


def test_feature_states_completeness() -> None:
    """Test all expected lifecycle states are defined in FeatureState."""
    expected_states = {
        "DISCOVERED",
        "DISABLED",
        "MISSING",
        "BLOCKED",
        "PREPARING",
        "ACTIVE",
        "QUIESCING",
        "STOPPING",
        "STOPPED",
        "FAILED_IMPORT",
        "FAILED_CONFIG",
        "FAILED_START",
        "FAILED_RUNTIME",
    }
    actual_states = {state.value for state in FeatureState}
    assert actual_states == expected_states


def test_feature_spec_creation_and_immutability() -> None:
    """Test FeatureSpec instantiation, default values, and immutability."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
        description="Historical bars data provider",
    )
    assert spec.feature_id == "FEAT-DATA-RETRIEVE_BARS"
    assert spec.domain == "data"
    assert HISTORICAL_BARS in spec.provides
    assert BROKER_MARKET_DATA in spec.requires
    assert spec.optional == frozenset()
    assert spec.conflicts == frozenset()
    assert spec.description == "Historical bars data provider"

    # Immutability check
    with pytest.raises(AttributeError):
        spec.feature_id = "NEW-ID"  # type: ignore[misc]


def test_feature_spec_validation_success() -> None:
    """Test valid feature spec validation."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )
    spec.validate()  # Should not raise


def test_feature_spec_validation_empty_id() -> None:
    """Test that empty feature ID raises ValueError."""
    spec = FeatureSpec(
        feature_id="   ",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
    )
    with pytest.raises(ValueError, match="Feature ID must not be empty"):
        spec.validate()


def test_feature_spec_validation_empty_domain() -> None:
    """Test that empty domain raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="",
        provides=frozenset({HISTORICAL_BARS}),
    )
    with pytest.raises(ValueError, match="Domain must not be empty"):
        spec.validate()


def test_feature_spec_validation_overlap() -> None:
    """Test that providing and requiring same capability raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({HISTORICAL_BARS}),
    )
    with pytest.raises(ValueError, match="cannot both provide and require capability"):
        spec.validate()


def test_feature_protocol_conformance() -> None:
    """Test structural subtyping for Feature protocol."""

    class DummyFeature:
        spec = FeatureSpec(
            feature_id="FEAT-TEST-RUN_DUMMY",
            domain="test",
            provides=frozenset(),
        )

        async def mount(self, context: FeatureContext, config: object) -> None:
            pass

    feature_instance: Feature = DummyFeature()
    assert feature_instance.spec.feature_id == "FEAT-TEST-RUN_DUMMY"
