"""Tests for HTTP and Event Contracts feature lifecycle and mount."""

from typing import TYPE_CHECKING, Any

import pytest

from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.contracts.interfaces.ports import ServeApiEventsCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.api_events.feature import (
    ApiEventsFeature,
    feature,
)
from app.services.interfaces.api_events.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.mark.asyncio
async def test_feature_mount_and_provide() -> None:
    """Verify feature mount provides the capability in the context."""
    feat = feature()
    assert isinstance(feat, ApiEventsFeature)
    assert feat.spec == SPEC

    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def registrar(
        cap: CapabilityKey[Any],
        impl: object,
        sc: FeatureScope,
    ) -> None:
        registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=event_bus,
    )

    await feat.mount(context, {"title": "Test Gateway", "event_buffer_size": 200})
    assert feat.service is not None

    resolved = registry.resolve(SERVE_API_EVENTS_CAPABILITY)
    assert resolved is not None
    assert isinstance(resolved, ServeApiEventsCapability)

    await scope.close()
