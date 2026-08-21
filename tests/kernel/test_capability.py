"""Tests for kernel capability models and identifiers."""

from app.kernel.capability import CapabilityKey, CapabilityUnavailableError


def test_capability_key_identifier() -> None:
    """Test that capability key formats identifier string correctly."""
    key: CapabilityKey[object] = CapabilityKey(name="data.historical-bars", major=1)
    assert key.name == "data.historical-bars"
    assert key.major == 1
    assert key.identifier == "data.historical-bars@1"


def test_capability_unavailable_error_message() -> None:
    """Test CapabilityUnavailableError formatted messages."""
    err_without_block = CapabilityUnavailableError(capability="data.historical-bars@1")
    assert "Capability 'data.historical-bars@1' is unavailable" in str(
        err_without_block
    )
    assert err_without_block.blocked_by is None

    err_with_block = CapabilityUnavailableError(
        capability="data.historical-bars@1",
        blocked_by="broker.market-data@1",
    )
    assert (
        "Capability 'data.historical-bars@1' is unavailable (blocked by 'broker.market-data@1')"
        in str(err_with_block)
    )
    assert err_with_block.blocked_by == "broker.market-data@1"
