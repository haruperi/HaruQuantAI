"""Phase 5 backend removal matrix for the Market Ticks vertical slice.

Proves the end-to-end removal expectation: removing the observation
D-IFACE feature makes the market tick boundary unavailable while the
transport foundation and the underlying Data provider stay unaffected.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_DATA_CAPABILITY,
    SERVE_API_EVENTS_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.observe_market_data.feature import feature
from app.services.interfaces.serve_api_events.asgi import create_api_asgi_app
from app.services.interfaces.serve_api_events.feature import ServeApiEventsFeature

from tests.services.interfaces.observe_market_data.fakes import (
    QueuedStreamProvider,
    make_event,
)

_EVENT_TIME = datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)


class _FixedClock:
    """Deterministic UTC clock."""

    def __init__(self) -> None:
        """Initialize the controlled instant."""
        self.now = _EVENT_TIME

    def __call__(self) -> datetime:
        """Return the controlled instant."""
        return self.now


async def _settle() -> None:
    """Yield control for background task scheduling."""
    for _ in range(20):
        await asyncio.sleep(0)


def _context_for(
    spec: Any,
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
            owner_id=spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_market_ticks_removal_matrix() -> None:
    """Removing the gateway feature fails only its own surface closed."""
    provider = QueuedStreamProvider()
    registry = ServiceRegistry()
    registry.register(
        STREAM_MARKET_EVENTS_CAPABILITY,
        provider,
        owner_id="FEAT-DATA-STREAM_MARKET_EVENTS",
        scope=FeatureScope(owner_id="FEAT-DATA-STREAM_MARKET_EVENTS"),
    )

    serve_feature = ServeApiEventsFeature()
    serve_scope = FeatureScope(owner_id=serve_feature.spec.feature_id)
    await serve_feature.mount(
        _context_for(serve_feature.spec, registry, serve_scope), None
    )

    observe = feature()
    observe_scope = FeatureScope(owner_id=observe.spec.feature_id)
    await observe.mount(_context_for(observe.spec, registry, observe_scope), None)
    await _settle()
    provider.publish(make_event(1, "EURUSD", occurred_at=_EVENT_TIME))
    await _settle()

    app = create_api_asgi_app(registry)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://boundary"
    ) as client:
        active = await client.get("/api/v1/market/ticks")
        assert active.status_code == 200
        assert active.json()["data"]["quotes"][0]["symbol"] == "EURUSD"

    # Remove the observation feature: its surface becomes explicitly
    # unavailable while everything else keeps running.
    await observe_scope.close()
    await _settle()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_api_asgi_app(registry)),
        base_url="http://boundary",
    ) as client:
        removed = await client.get("/api/v1/market/ticks")
        assert removed.status_code == 503
        assert removed.json()["error"]["code"] == "CAPABILITY_UNAVAILABLE"

    # Other Interfaces features remain active.
    transport_provider = registry.resolve(SERVE_API_EVENTS_CAPABILITY)
    assert transport_provider is not None
    assert transport_provider is serve_feature.transport
    assert registry.resolve(OBSERVE_MARKET_DATA_CAPABILITY) is None

    # The underlying Data provider is unaffected and fully released.
    assert provider.subscriber_count == 0
    provider.publish(make_event(2, "EURUSD", occurred_at=_EVENT_TIME))
    await _settle()
    assert provider.subscriber_count == 0

    await serve_scope.close()
