"""Feature mount and lifecycle tests for Data Inspection, Export, and Retention."""

from typing import Any

import pytest
from app.contracts.data.capabilities import MANAGE_RETENTION_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.data_inspection_retention.config import (
    DataInspectionRetentionConfig,
)
from app.services.data.data_inspection_retention.feature import (
    DataInspectionRetentionFeature,
    feature,
)
from app.services.data.data_inspection_retention.manifest import SPEC


def _context(
    feature_instance: DataInspectionRetentionFeature,
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
        "default_preview_limit": 50,
        "max_preview_limit": 5_000,
        "default_quarantine_days": 15,
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    assert feat.service.config.default_preview_limit == 50
    assert feat.service.config.max_preview_limit == 5_000
    assert feat.service.config.default_quarantine_days == 15
    provided = registry.resolve(MANAGE_RETENTION_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_object_config() -> None:
    """Verify feature mounting with DataInspectionRetentionConfig object."""
    feat = DataInspectionRetentionFeature()
    ctx, registry, _ = _context(feat)
    cfg = DataInspectionRetentionConfig(
        default_preview_limit=25, default_quarantine_days=10
    )
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service.config.default_preview_limit == 25
    assert feat.service.config.default_quarantine_days == 10
    provided = registry.resolve(MANAGE_RETENTION_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid configuration value types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="default_preview_limit must be an integer"):
        await feat.mount(ctx, {"default_preview_limit": "not_an_int"})

    with pytest.raises(TypeError, match="max_preview_limit must be an integer"):
        await feat.mount(ctx, {"max_preview_limit": "invalid"})

    with pytest.raises(TypeError, match="default_quarantine_days must be an integer"):
        await feat.mount(ctx, {"default_quarantine_days": 12.5})
