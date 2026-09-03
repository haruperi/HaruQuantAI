"""Feature mount and lifecycle tests for Run Data Binding."""

from typing import Any

import pytest
from app.contracts.data.capabilities import BIND_RUN_DATA_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.run_data_binding.config import RunDataBindingConfig
from app.services.data.run_data_binding.feature import (
    RunDataBindingFeature,
    feature,
)
from app.services.data.run_data_binding.manifest import SPEC


def _context(
    feature_instance: RunDataBindingFeature,
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
        "strict_precision_check": False,
        "allow_synthetic_sources": True,
        "require_committed_status": True,
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    assert feat.service.config.strict_precision_check is False
    assert feat.service.config.allow_synthetic_sources is True
    provided = registry.resolve(BIND_RUN_DATA_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_object_config() -> None:
    """Verify feature mounting with RunDataBindingConfig object."""
    feat = RunDataBindingFeature()
    ctx, registry, _ = _context(feat)
    cfg = RunDataBindingConfig(strict_precision_check=True)
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service.config.strict_precision_check is True
    provided = registry.resolve(BIND_RUN_DATA_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid configuration value types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(
        TypeError,
        match="strict_precision_check must be a boolean",
    ):
        await feat.mount(ctx, {"strict_precision_check": "invalid"})

    with pytest.raises(
        TypeError,
        match="allow_synthetic_sources must be a boolean",
    ):
        await feat.mount(ctx, {"allow_synthetic_sources": 123})

    with pytest.raises(
        TypeError,
        match="require_committed_status must be a boolean",
    ):
        await feat.mount(ctx, {"require_committed_status": None})
