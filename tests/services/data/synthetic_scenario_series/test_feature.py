"""Unit tests for SyntheticScenarioSeriesFeature mounting."""

from typing import Any

import pytest
from app.contracts.data.capabilities import GENERATE_SCENARIOS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.synthetic_scenario_series.config import (
    SyntheticScenarioSeriesConfig,
)
from app.services.data.synthetic_scenario_series.feature import (
    SyntheticScenarioSeriesFeature,
    feature,
)
from app.services.data.synthetic_scenario_series.manifest import SPEC


def _context(
    feature_instance: SyntheticScenarioSeriesFeature,
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
async def test_feature_factory_and_mount() -> None:
    """Verify feature factory and mounting into context with dict config."""
    feat = feature()
    ctx, registry, _ = _context(feat)

    await feat.mount(
        ctx,
        {
            "max_records": 10_000,
            "default_model": "gbm",
            "default_rounding": "ROUND_HALF_EVEN",
            "supported_transform_types": ["SHOCK", "GAP", "VOLATILITY"],
        },
    )

    assert feat.service is not None
    assert feat.service.config.max_records == 10_000
    assert feat.service.config.default_model == "gbm"
    provided = registry.resolve(GENERATE_SCENARIOS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_dataclass_config() -> None:
    """Verify mounting with SyntheticScenarioSeriesConfig instance."""
    feat = feature()
    ctx, registry, _ = _context(feat)

    cfg = SyntheticScenarioSeriesConfig(max_records=5_000)
    await feat.mount(ctx, cfg)
    assert feat.service is not None
    assert feat.service.config.max_records == 5_000
    provided = registry.resolve(GENERATE_SCENARIOS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_types() -> None:
    """Verify type validation during mount."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="max_records must be an integer"):
        await feat.mount(ctx, {"max_records": "invalid"})

    with pytest.raises(TypeError, match="default_model must be a string"):
        await feat.mount(ctx, {"default_model": 123})

    with pytest.raises(TypeError, match="default_rounding must be a string"):
        await feat.mount(ctx, {"default_rounding": 123})

    with pytest.raises(
        TypeError, match="supported_transform_types must be a set/frozenset"
    ):
        await feat.mount(ctx, {"supported_transform_types": 123})
