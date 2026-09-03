"""Feature mount and context lifecycle tests for Tick Normalization."""

from typing import Any

import pytest
from app.contracts.data.capabilities import NORMALIZE_TICKS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.tick_normalization.config import TickNormalizationConfig
from app.services.data.tick_normalization.feature import (
    TickNormalizationFeature,
    feature,
)
from app.services.data.tick_normalization.manifest import SPEC


def _context(
    feature_instance: TickNormalizationFeature,
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
        "max_batch_size": 100_000,
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    assert feat.service.config.max_batch_size == 100_000
    provided = registry.resolve(NORMALIZE_TICKS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_object_config() -> None:
    """Verify feature mounting with TickNormalizationConfig object."""
    feat = TickNormalizationFeature()
    ctx, registry, _ = _context(feat)
    cfg = TickNormalizationConfig(max_batch_size=50_000)
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service.config.max_batch_size == 50_000
    provided = registry.resolve(NORMALIZE_TICKS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid configuration value types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="max_batch_size must be an integer"):
        await feat.mount(ctx, {"max_batch_size": "not_an_int"})
