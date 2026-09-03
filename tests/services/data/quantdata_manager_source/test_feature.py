"""Feature mount and context lifecycle tests for QuantDataManager Source."""

from pathlib import Path
from typing import Any

import pytest
from app.contracts.data.capabilities import IMPORT_QUANTDATA_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.quantdata_manager_source.config import (
    QuantDataManagerConfig,
)
from app.services.data.quantdata_manager_source.feature import (
    QuantDataManagerSourceFeature,
    feature,
)
from app.services.data.quantdata_manager_source.manifest import SPEC


def _context(
    feature_instance: QuantDataManagerSourceFeature,
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
async def test_feature_mount_with_dict_config(tmp_path: Path) -> None:
    """Verify feature mounting with dictionary configuration."""
    feat = feature()
    ctx, registry, _scope = _context(feat)
    config_dict = {
        "allowed_root": str(tmp_path),
        "database_path": str(tmp_path / "metadata.db"),
        "auto_migrate": True,
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    provided = registry.resolve(IMPORT_QUANTDATA_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_with_object_config(tmp_path: Path) -> None:
    """Verify feature mounting with QuantDataManagerConfig object."""
    feat = QuantDataManagerSourceFeature()
    ctx, registry, _scope = _context(feat)
    cfg = QuantDataManagerConfig(allowed_root=tmp_path)
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    provided = registry.resolve(IMPORT_QUANTDATA_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type(tmp_path: Path) -> None:
    """Verify TypeError on invalid configuration value types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="allowed_root must be a string or Path"):
        await feat.mount(ctx, {"allowed_root": 12345})

    with pytest.raises(TypeError, match="database_path must be a string or Path"):
        await feat.mount(ctx, {"database_path": 12345})
