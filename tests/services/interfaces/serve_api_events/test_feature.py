"""Feature mount and lifecycle tests for serve-api-events."""

from typing import Any

import pytest
from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.contracts.interfaces.errors import InterfaceError
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.feature import (
    ServeApiEventsFeature,
    feature,
)
from app.services.interfaces.serve_api_events.manifest import SPEC


def _context(
    feature_instance: ServeApiEventsFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    """Build a scoped context for testing feature mounting."""
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feature_instance.spec.feature_id)

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

    return (
        DefaultFeatureContext(
            spec=feature_instance.spec,
            scope=scope,
            resolver=registry.resolve,
            provider_registrar=register,
            event_bus=EventBus(),
        ),
        registry,
        scope,
    )


def test_feature_initial_state() -> None:
    """Verify unmounted feature initial state."""
    feat = feature()
    assert feat.spec == SPEC
    assert feat.transport is None


@pytest.mark.asyncio
async def test_feature_mount_with_dict_config() -> None:
    """Verify mounting with a configuration mapping."""
    feat = feature()
    ctx, registry, _scope = _context(feat)
    await feat.mount(ctx, {"stream_retention_events": 5})

    transport = feat.transport
    assert transport is not None
    assert transport.config.stream_retention_events == 5
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is transport


@pytest.mark.asyncio
async def test_feature_mount_with_none_uses_defaults() -> None:
    """Verify mounting without configuration uses defaults."""
    feat = feature()
    ctx, registry, _scope = _context(feat)
    await feat.mount(ctx, None)

    transport = feat.transport
    assert transport is not None
    assert transport.config == ServeApiEventsConfig()
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is transport


@pytest.mark.asyncio
async def test_feature_mount_with_object_config() -> None:
    """Verify mounting with a prebuilt configuration object."""
    feat = ServeApiEventsFeature()
    ctx, registry, _scope = _context(feat)
    config = ServeApiEventsConfig(stream_replay_batch_limit=10)
    await feat.mount(ctx, config)

    transport = feat.transport
    assert transport is not None
    assert transport.config.stream_replay_batch_limit == 10
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is transport


@pytest.mark.asyncio
async def test_feature_mount_rejects_unsupported_config_type() -> None:
    """Verify unsupported configuration objects fail closed."""
    feat = feature()
    ctx, _registry, _scope = _context(feat)
    with pytest.raises(TypeError, match="mapping"):
        await feat.mount(ctx, "v1")
    assert feat.transport is None


@pytest.mark.asyncio
async def test_failed_mount_leaves_no_provider() -> None:
    """Verify invalid configuration rolls back without publication."""
    feat = feature()
    ctx, registry, _scope = _context(feat)
    with pytest.raises(ValueError, match="Unknown serve-api-events"):
        await feat.mount(ctx, {"unexpected": True})

    assert feat.transport is None
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is None
    with pytest.raises(CapabilityUnavailableError):
        registry.require(SERVE_API_EVENTS_CAPABILITY)


@pytest.mark.asyncio
async def test_scope_close_disposes_transport_and_revokes_provider() -> None:
    """Verify scope disposal closes the transport and withdraws the capability."""
    feat = feature()
    ctx, registry, scope = _context(feat)
    await feat.mount(ctx, None)

    transport = feat.transport
    assert transport is not None
    envelope = transport.publish_interface_event("tick", "market", {"symbol": "EURUSD"})
    assert envelope.sequence_number == 1

    await scope.close()
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is None
    with pytest.raises(CapabilityUnavailableError):
        registry.require(SERVE_API_EVENTS_CAPABILITY)
    with pytest.raises(InterfaceError, match="TRANSPORT_CLOSED"):
        transport.publish_interface_event("tick", "market", {})

    await scope.close()
    transport.close()
