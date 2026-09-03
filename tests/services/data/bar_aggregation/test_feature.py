"""Feature mount and lifecycle tests for Bar Aggregation."""

from typing import Any

import pytest
from app.contracts.data.capabilities import AGGREGATE_BARS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.bar_aggregation.config import BarAggregationConfig
from app.services.data.bar_aggregation.feature import (
    BarAggregationFeature,
    feature,
)
from app.services.data.bar_aggregation.manifest import SPEC


def _context(
    feature_instance: BarAggregationFeature,
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
    assert feat.service is None


@pytest.mark.asyncio
async def test_feature_mount_with_dict_config() -> None:
    """Verify feature mounting with dictionary configuration."""
    feat = feature()
    ctx, registry, _ = _context(feat)
    config_dict = {
        "max_bars_per_request": 50_000,
        "default_timezone": "UTC",
        "allow_custom_timeframes": True,
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    assert feat.service.config.max_bars_per_request == 50_000
    provided = registry.resolve(AGGREGATE_BARS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_object_config() -> None:
    """Verify feature mounting with BarAggregationConfig object."""
    feat = BarAggregationFeature()
    ctx, registry, _ = _context(feat)
    cfg = BarAggregationConfig(max_bars_per_request=25_000)
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service.config.max_bars_per_request == 25_000
    provided = registry.resolve(AGGREGATE_BARS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid configuration value types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="max_bars_per_request must be an integer"):
        await feat.mount(ctx, {"max_bars_per_request": "not_an_int"})

    with pytest.raises(TypeError, match="default_timezone must be a string"):
        await feat.mount(ctx, {"default_timezone": 123})

    with pytest.raises(TypeError, match="allow_custom_timeframes must be a boolean"):
        await feat.mount(ctx, {"allow_custom_timeframes": "yes"})
