"""Feature mount, blocking, and disposal tests for observe-market-data."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid7

import pytest
from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_DATA_CAPABILITY,
    SERVE_API_EVENTS_CAPABILITY,
)
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    ObserveMarketDataRequest,
    ObserveMarketDataSuccess,
)
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.observe_market_data.config import ObserveMarketDataConfig
from app.services.interfaces.observe_market_data.feature import (
    ObserveMarketDataFeature,
    feature,
)
from app.services.interfaces.observe_market_data.manifest import SPEC
from app.services.interfaces.serve_api_events.feature import (
    ServeApiEventsFeature,
)

from tests.services.interfaces.observe_market_data.fakes import (
    FakeStreamProvider,
    make_event,
)


def _register_provider(registry: ServiceRegistry, provider: FakeStreamProvider) -> None:
    """Register the fake Data stream provider in the registry."""
    registry.register(
        STREAM_MARKET_EVENTS_CAPABILITY,
        provider,
        owner_id="FEAT-DATA-STREAM_MARKET_EVENTS",
        scope=FeatureScope(owner_id="FEAT-DATA-STREAM_MARKET_EVENTS"),
    )


def _context(
    feature_instance: ObserveMarketDataFeature,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    """Build a scoped context wired to the shared registry."""

    def register(
        capability: Any,
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature_instance.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=feature_instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


def _snapshot_request() -> ObserveMarketDataRequest:
    """Build a SNAPSHOT request."""
    return ObserveMarketDataRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="SNAPSHOT",
    )


async def _settle() -> None:
    """Yield control so the spawned consumer task drains."""
    for _ in range(20):
        await asyncio.sleep(0)


def test_feature_initial_state() -> None:
    """Verify unmounted feature initial state."""
    feat = feature()
    assert feat.spec == SPEC
    assert feat.gateway is None


@pytest.mark.asyncio
async def test_feature_mount_provides_gateway() -> None:
    """Verify mount resolves the provider and publishes the capability."""
    registry = ServiceRegistry()
    _register_provider(registry, FakeStreamProvider())
    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, scope)

    await feat.mount(ctx, {"stale_after_seconds": 9.0})
    await _settle()

    gateway = feat.gateway
    assert gateway is not None
    assert gateway.config.stale_after_seconds == 9.0
    assert registry.resolve(OBSERVE_MARKET_DATA_CAPABILITY) is gateway


@pytest.mark.asyncio
async def test_feature_mount_missing_provider_fails_closed() -> None:
    """Verify a missing Data provider blocks the mount entirely."""
    registry = ServiceRegistry()
    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, scope)

    with pytest.raises(CapabilityUnavailableError):
        await feat.mount(ctx, None)

    assert feat.gateway is None
    assert registry.resolve(OBSERVE_MARKET_DATA_CAPABILITY) is None


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_rolls_back() -> None:
    """Verify invalid configuration leaves no provider or gateway."""
    registry = ServiceRegistry()
    _register_provider(registry, FakeStreamProvider())
    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, scope)

    with pytest.raises(ValueError, match="Unknown observe-market-data"):
        await feat.mount(ctx, {"symbols": ["EURUSD"]})

    assert feat.gateway is None
    assert registry.resolve(OBSERVE_MARKET_DATA_CAPABILITY) is None


@pytest.mark.asyncio
async def test_feature_mount_rejects_unsupported_config_type() -> None:
    """Verify unsupported configuration objects fail closed."""
    registry = ServiceRegistry()
    _register_provider(registry, FakeStreamProvider())
    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, scope)

    with pytest.raises(TypeError, match="mapping"):
        await feat.mount(ctx, "v1")
    assert feat.gateway is None


@pytest.mark.asyncio
async def test_mounted_gateway_serves_snapshots() -> None:
    """Verify the spawned consumer projects provider events."""
    provider = FakeStreamProvider((make_event(1, "EURUSD"), make_event(2, "GBPUSD")))
    registry = ServiceRegistry()
    _register_provider(registry, provider)
    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, scope)

    await feat.mount(ctx, ObserveMarketDataConfig())
    await _settle()

    gateway = feat.gateway
    assert gateway is not None
    result = await gateway.observe_market_data(_snapshot_request())
    assert isinstance(result, ObserveMarketDataSuccess)
    assert result.snapshot is not None
    assert [quote.symbol for quote in result.snapshot.quotes] == [
        "EURUSD",
        "GBPUSD",
    ]


@pytest.mark.asyncio
async def test_scope_close_disposes_and_unrelated_features_survive() -> None:
    """Verify disposal revokes only this feature's capability."""
    registry = ServiceRegistry()
    _register_provider(registry, FakeStreamProvider())

    serve_feature = ServeApiEventsFeature()
    serve_scope = FeatureScope(owner_id=serve_feature.spec.feature_id)
    await serve_feature.mount(
        DefaultFeatureContext(
            spec=serve_feature.spec,
            scope=serve_scope,
            resolver=registry.resolve,
            provider_registrar=lambda capability, provider, owner_scope: (
                registry.register(
                    capability,
                    provider,
                    owner_id=serve_feature.spec.feature_id,
                    scope=owner_scope,
                )
            ),
            event_bus=EventBus(),
        ),
        None,
    )

    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, scope)
    await feat.mount(ctx, None)
    await _settle()

    gateway = feat.gateway
    assert gateway is not None
    await scope.close()

    assert registry.resolve(OBSERVE_MARKET_DATA_CAPABILITY) is None
    with pytest.raises(CapabilityUnavailableError):
        registry.require(OBSERVE_MARKET_DATA_CAPABILITY)
    disposed = await gateway.observe_market_data(_snapshot_request())
    assert isinstance(disposed, InterfaceFailure)

    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is serve_feature.transport
    await serve_scope.close()
