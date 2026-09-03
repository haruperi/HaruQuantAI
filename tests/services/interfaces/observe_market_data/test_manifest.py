"""Unit tests for the observe-market-data manifest."""

from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.contracts.interfaces.capabilities import OBSERVE_MARKET_DATA_CAPABILITY
from app.services.interfaces.observe_market_data.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-IFACE-OBSERVE_MARKET_DATA"
    assert SPEC.domain == "interfaces"
    assert SPEC.provides == frozenset({OBSERVE_MARKET_DATA_CAPABILITY})
    assert SPEC.requires == frozenset({STREAM_MARKET_EVENTS_CAPABILITY})
    assert SPEC.optional == frozenset()
    assert SPEC.conflicts == frozenset()
    assert SPEC.state is None
    assert SPEC.config_keys == frozenset({"stale_after_seconds", "max_symbols"})
    SPEC.validate()


def test_manifest_capability_identifiers() -> None:
    """Verify the provided and required capability identifiers."""
    (provided,) = SPEC.provides
    (required,) = SPEC.requires
    assert provided.identifier == "interfaces.observe-market-data@1"
    assert required.identifier == "data.stream-market-events@1"
