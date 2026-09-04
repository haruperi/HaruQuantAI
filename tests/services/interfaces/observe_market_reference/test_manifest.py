"""Unit tests for the observe-market-reference manifest."""

from app.contracts.data.capabilities import BROWSE_REFERENCE_CAPABILITY
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_REFERENCE_CAPABILITY,
)
from app.services.interfaces.observe_market_reference.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-IFACE-OBSERVE_MARKET_REFERENCE"
    assert SPEC.domain == "interfaces"
    assert SPEC.provides == frozenset({OBSERVE_MARKET_REFERENCE_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset({BROWSE_REFERENCE_CAPABILITY})
    assert SPEC.conflicts == frozenset()
    assert SPEC.state is None
    assert SPEC.config_keys == frozenset()
    SPEC.validate()


def test_manifest_capability_identifiers() -> None:
    """Verify the provided capability identifier."""
    (provided,) = SPEC.provides
    assert provided.identifier == "interfaces.observe-market-reference@1"
