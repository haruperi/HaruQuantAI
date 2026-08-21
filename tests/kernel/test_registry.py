"""Tests for ServiceRegistry capability registration, generations, and exact-token revocation."""

import pytest

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.registry import BindingToken, ServiceRegistry
from app.kernel.scope import FeatureScope


def test_registry_register_and_resolve() -> None:
    """Test registering and resolving capability providers."""
    registry = ServiceRegistry()
    dummy_service = object()

    assert not registry.is_available(HISTORICAL_BARS)
    assert not registry.is_available(HISTORICAL_BARS.identifier)
    assert registry.resolve(HISTORICAL_BARS) is None

    token = registry.register(
        capability=HISTORICAL_BARS,
        provider=dummy_service,
        owner_id="FEAT-DATA-RETRIEVE_BARS",
    )

    assert token.capability == "data.historical-bars@1"
    assert token.owner_id == "FEAT-DATA-RETRIEVE_BARS"
    assert token.generation == 1

    assert registry.is_available(HISTORICAL_BARS)
    assert registry.is_available(HISTORICAL_BARS.identifier)
    assert registry.resolve(HISTORICAL_BARS) is dummy_service
    assert registry.require(HISTORICAL_BARS) is dummy_service

    binding = registry.get_binding(HISTORICAL_BARS.identifier)
    assert binding is not None
    assert binding.token == token
    assert binding.provider is dummy_service


def test_registry_require_missing_raises() -> None:
    """Test require raises CapabilityUnavailableError when no provider exists."""
    registry = ServiceRegistry()
    with pytest.raises(
        CapabilityUnavailableError,
        match=r"Capability 'broker\.market-data@1' is unavailable",
    ):
        registry.require(BROKER_MARKET_DATA)


def test_registry_revoke_active_token() -> None:
    """Test revoking an active provider binding."""
    registry = ServiceRegistry()
    token = registry.register(
        capability=HISTORICAL_BARS,
        provider=object(),
        owner_id="FEAT-DATA-RETRIEVE_BARS",
    )
    assert registry.is_available(HISTORICAL_BARS)

    assert registry.revoke(token) is True
    assert not registry.is_available(HISTORICAL_BARS)
    assert registry.resolve(HISTORICAL_BARS) is None

    # Revoking again returns False
    assert registry.revoke(token) is False


def test_registry_generation_stale_token_protection() -> None:
    """Test that a stale disposer token cannot revoke a newer replacement provider."""
    registry = ServiceRegistry()
    service_v1 = object()
    service_v2 = object()

    token_v1 = registry.register(
        capability=HISTORICAL_BARS,
        provider=service_v1,
        owner_id="FEAT-DATA-RETRIEVE_BARS",
    )
    assert token_v1.generation == 1

    token_v2 = registry.register(
        capability=HISTORICAL_BARS,
        provider=service_v2,
        owner_id="FEAT-DATA-MOCK_BARS",
    )
    assert token_v2.generation == 2
    assert registry.resolve(HISTORICAL_BARS) is service_v2

    # Old disposer for token_v1 attempts revocation
    revoked = registry.revoke(token_v1)
    assert revoked is False
    # Newer provider is still active and safe
    assert registry.resolve(HISTORICAL_BARS) is service_v2

    # New disposer revokes successfully
    assert registry.revoke(token_v2) is True
    assert registry.resolve(HISTORICAL_BARS) is None


@pytest.mark.asyncio
async def test_registry_scope_automatic_revocation() -> None:
    """Test passing scope to register automatically revokes binding on scope close."""
    registry = ServiceRegistry()
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    service = object()

    token = registry.register(
        capability=HISTORICAL_BARS,
        provider=service,
        owner_id="FEAT-DATA-RETRIEVE_BARS",
        scope=scope,
    )
    assert isinstance(token, BindingToken)
    assert registry.is_available(HISTORICAL_BARS)

    await scope.close()
    assert not registry.is_available(HISTORICAL_BARS)
    assert registry.resolve(HISTORICAL_BARS) is None


def test_registry_active_capabilities_and_clear() -> None:
    """Test active_capabilities snapshot and registry clear."""
    registry = ServiceRegistry()
    token1 = registry.register(HISTORICAL_BARS, object(), "FEAT-DATA-RETRIEVE_BARS")
    token2 = registry.register(BROKER_MARKET_DATA, object(), "FEAT-BROKER-FEED_MT5")

    active = registry.active_capabilities()
    assert active[HISTORICAL_BARS.identifier] == token1
    assert active[BROKER_MARKET_DATA.identifier] == token2

    registry.clear()
    assert len(registry.active_capabilities()) == 0
    assert not registry.is_available(HISTORICAL_BARS)
