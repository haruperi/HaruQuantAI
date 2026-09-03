"""Unit tests for Real-Time Market Events feature lifecycle."""

from typing import Any

import pytest
from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.realtime_market_events.config import (
    RealtimeMarketEventsConfig,
)
from app.services.data.realtime_market_events.feature import (
    RealtimeMarketEventsFeature,
    feature,
)
from app.services.data.realtime_market_events.manifest import SPEC


def _context(
    feature_instance: RealtimeMarketEventsFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
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
    feat = feature()
    assert feat.spec == SPEC
    assert feat.service is None


@pytest.mark.asyncio
async def test_feature_mount_dict_config() -> None:
    feat = feature()
    context, registry, _ = _context(feat)

    config_dict = {
        "buffer_capacity": 500,
        "max_subscriptions": 50,
        "max_instruments_per_subscription": 200,
        "stale_timeout_seconds": 20,
        "heartbeat_timeout_seconds": 10,
        "max_replay_limit": 5000,
        "default_ordering_mode": "PROVIDER_SEQUENCE",
        "backpressure_policy": "DROP_AND_GAP",
    }

    await feat.mount(context, config_dict)
    assert feat.service is not None
    assert feat.service.config.buffer_capacity == 500
    assert feat.service.config.max_subscriptions == 50
    assert feat.service.config.default_ordering_mode == "PROVIDER_SEQUENCE"
    provided = registry.resolve(STREAM_MARKET_EVENTS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_typed_config() -> None:
    feat = RealtimeMarketEventsFeature()
    context, registry, _ = _context(feat)

    cfg = RealtimeMarketEventsConfig(buffer_capacity=300)
    await feat.mount(context, cfg)
    assert feat.service is not None
    assert feat.service.config.buffer_capacity == 300
    provided = registry.resolve(STREAM_MARKET_EVENTS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config() -> None:
    feat = RealtimeMarketEventsFeature()
    context, _, _ = _context(feat)

    with pytest.raises(TypeError, match="buffer_capacity must be an integer"):
        await feat.mount(context, {"buffer_capacity": "not_an_int"})

    with pytest.raises(TypeError, match="max_subscriptions must be an integer"):
        await feat.mount(context, {"max_subscriptions": "not_an_int"})

    with pytest.raises(
        TypeError, match="max_instruments_per_subscription must be an integer"
    ):
        await feat.mount(context, {"max_instruments_per_subscription": "not_an_int"})

    with pytest.raises(TypeError, match="stale_timeout_seconds must be an integer"):
        await feat.mount(context, {"stale_timeout_seconds": "not_an_int"})

    with pytest.raises(TypeError, match="heartbeat_timeout_seconds must be an integer"):
        await feat.mount(context, {"heartbeat_timeout_seconds": "not_an_int"})

    with pytest.raises(TypeError, match="max_replay_limit must be an integer"):
        await feat.mount(context, {"max_replay_limit": "not_an_int"})

    with pytest.raises(TypeError, match="default_ordering_mode must be a string"):
        await feat.mount(context, {"default_ordering_mode": 123})

    with pytest.raises(TypeError, match="backpressure_policy must be a string"):
        await feat.mount(context, {"backpressure_policy": 123})
