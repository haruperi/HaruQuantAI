"""Feature mount and lifecycle tests for External Indicator Series."""

from typing import Any

import pytest
from app.contracts.data.capabilities import IMPORT_INDICATORS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.external_indicator_series.config import (
    ExternalIndicatorSeriesConfig,
)
from app.services.data.external_indicator_series.feature import (
    ExternalIndicatorSeriesFeature,
    feature,
)
from app.services.data.external_indicator_series.manifest import SPEC


def _context(
    feature_instance: ExternalIndicatorSeriesFeature,
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
        "default_timezone": "UTC",
        "max_points_per_series": 200_000,
        "require_deterministic_reimport": True,
        "allow_future_timestamps": False,
        "default_missing_policy": "ZERO_FILL",
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    assert feat.service.config.default_timezone == "UTC"
    assert feat.service.config.max_points_per_series == 200_000
    assert feat.service.config.require_deterministic_reimport is True
    assert feat.service.config.allow_future_timestamps is False
    assert feat.service.config.default_missing_policy == "ZERO_FILL"
    provided = registry.resolve(IMPORT_INDICATORS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_object_config() -> None:
    """Verify feature mounting with ExternalIndicatorSeriesConfig object."""
    feat = ExternalIndicatorSeriesFeature()
    ctx, registry, _ = _context(feat)
    cfg = ExternalIndicatorSeriesConfig(max_points_per_series=50_000)
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service.config.max_points_per_series == 50_000
    provided = registry.resolve(IMPORT_INDICATORS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid configuration value types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="default_timezone must be a string"):
        await feat.mount(ctx, {"default_timezone": 123})

    with pytest.raises(TypeError, match="max_points_per_series must be an integer"):
        await feat.mount(ctx, {"max_points_per_series": "200000"})

    with pytest.raises(
        TypeError, match="require_deterministic_reimport must be a boolean"
    ):
        await feat.mount(ctx, {"require_deterministic_reimport": "true"})

    with pytest.raises(TypeError, match="allow_future_timestamps must be a boolean"):
        await feat.mount(ctx, {"allow_future_timestamps": 0})

    with pytest.raises(TypeError, match="default_missing_policy must be a string"):
        await feat.mount(ctx, {"default_missing_policy": None})
