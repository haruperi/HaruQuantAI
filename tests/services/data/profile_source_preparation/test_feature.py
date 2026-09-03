"""Feature mount and lifecycle tests for Volume Profile Source Preparation."""

from decimal import Decimal
from typing import Any

import pytest
from app.contracts.data.capabilities import PREPARE_PROFILES_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.profile_source_preparation.config import (
    ProfileSourcePreparationConfig,
)
from app.services.data.profile_source_preparation.feature import (
    ProfileSourcePreparationFeature,
    feature,
)
from app.services.data.profile_source_preparation.manifest import SPEC


def _context(
    feature_instance: ProfileSourcePreparationFeature,
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
        "default_price_step": "0.05",
        "default_bin_count": 150,
        "min_price_step": "0.0001",
        "max_bin_count": 2000,
        "require_session_alignment": True,
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    assert feat.service.config.default_price_step == Decimal("0.05")
    assert feat.service.config.default_bin_count == 150
    assert feat.service.config.min_price_step == Decimal("0.0001")
    assert feat.service.config.max_bin_count == 2000
    assert feat.service.config.require_session_alignment is True
    provided = registry.resolve(PREPARE_PROFILES_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_object_config() -> None:
    """Verify feature mounting with ProfileSourcePreparationConfig object."""
    feat = ProfileSourcePreparationFeature()
    ctx, registry, _ = _context(feat)
    cfg = ProfileSourcePreparationConfig(default_bin_count=300)
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service.config.default_bin_count == 300
    provided = registry.resolve(PREPARE_PROFILES_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid configuration value types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(
        TypeError,
        match="default_price_step must be a Decimal or decimal-compatible string",
    ):
        await feat.mount(ctx, {"default_price_step": []})

    with pytest.raises(TypeError, match="default_bin_count must be an integer or None"):
        await feat.mount(ctx, {"default_bin_count": "100"})

    with pytest.raises(
        TypeError, match="min_price_step must be a Decimal or decimal-compatible string"
    ):
        await feat.mount(ctx, {"min_price_step": object()})

    with pytest.raises(TypeError, match="max_bin_count must be an integer"):
        await feat.mount(ctx, {"max_bin_count": "2000"})

    with pytest.raises(TypeError, match="require_session_alignment must be a boolean"):
        await feat.mount(ctx, {"require_session_alignment": 1})
