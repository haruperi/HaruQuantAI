"""Tests for ServiceRegistry registration, replacement, and revocation."""

import pytest

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.registry import ActiveBindingError, BindingToken, ServiceRegistry
from app.kernel.scope import FeatureScope


def test_registry_register_and_resolve() -> None:
    registry = ServiceRegistry()
    service = object()
    token = registry.register(
        HISTORICAL_BARS,
        service,
        "FEAT-DATA-RETRIEVE_BARS",
    )
    assert token.generation == 1
    assert registry.resolve(HISTORICAL_BARS) is service
    assert registry.require(HISTORICAL_BARS) is service


def test_registry_require_missing_raises() -> None:
    registry = ServiceRegistry()
    with pytest.raises(
        CapabilityUnavailableError,
        match=r"Capability 'broker\.market-data@1' is unavailable",
    ):
        registry.require(BROKER_MARKET_DATA)


def test_normal_registration_cannot_overwrite_active_binding() -> None:
    registry = ServiceRegistry()
    service_v1 = object()
    registry.register(
        HISTORICAL_BARS,
        service_v1,
        "FEAT-DATA-RETRIEVE_BARS",
    )
    with pytest.raises(ActiveBindingError, match="cannot be overwritten"):
        registry.register(
            HISTORICAL_BARS,
            object(),
            "FEAT-DATA-MOCK_BARS",
        )
    assert registry.resolve(HISTORICAL_BARS) is service_v1


def test_explicit_replacement_increments_generation_and_protects_stale_token() -> None:
    registry = ServiceRegistry()
    service_v1 = object()
    service_v2 = object()
    token_v1 = registry.register(
        HISTORICAL_BARS,
        service_v1,
        "FEAT-DATA-RETRIEVE_BARS",
    )
    token_v2 = registry.replace_many(
        ((HISTORICAL_BARS, service_v2),),
        owner_id="FEAT-DATA-MOCK_BARS",
    )[0]
    assert token_v1.generation == 1
    assert token_v2.generation == 2
    assert registry.resolve(HISTORICAL_BARS) is service_v2
    assert not registry.revoke(token_v1)
    assert registry.resolve(HISTORICAL_BARS) is service_v2
    assert registry.revoke(token_v2)


def test_register_many_is_all_or_nothing_on_overlap() -> None:
    registry = ServiceRegistry()
    registry.register(
        HISTORICAL_BARS,
        object(),
        "FEAT-DATA-RETRIEVE_BARS",
    )
    with pytest.raises(ActiveBindingError):
        registry.register_many(
            (
                (BROKER_MARKET_DATA, object()),
                (HISTORICAL_BARS, object()),
            ),
            owner_id="FEAT-TEST-BUNDLE",
        )
    assert not registry.is_available(BROKER_MARKET_DATA)


@pytest.mark.asyncio
async def test_registry_scope_automatic_revocation() -> None:
    registry = ServiceRegistry()
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    token = registry.register(
        HISTORICAL_BARS,
        object(),
        "FEAT-DATA-RETRIEVE_BARS",
        scope=scope,
    )
    assert isinstance(token, BindingToken)
    assert registry.is_available(HISTORICAL_BARS)
    await scope.close()
    assert not registry.is_available(HISTORICAL_BARS)


def test_registry_active_capabilities_and_clear() -> None:
    registry = ServiceRegistry()
    token1 = registry.register(
        HISTORICAL_BARS,
        object(),
        "FEAT-DATA-RETRIEVE_BARS",
    )
    token2 = registry.register(
        BROKER_MARKET_DATA,
        object(),
        "FEAT-BROKER-FEED_MT5",
    )
    active = registry.active_capabilities()
    assert active[HISTORICAL_BARS.identifier] == token1
    assert active[BROKER_MARKET_DATA.identifier] == token2
    registry.clear()
    assert registry.active_capabilities() == {}
