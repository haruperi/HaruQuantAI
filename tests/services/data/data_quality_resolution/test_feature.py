"""Feature mount and lifecycle tests for Data Quality and Resolution."""

from pathlib import Path
from typing import Any

import pytest
from app.contracts.data.capabilities import RESOLVE_QUALITY_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.data_quality_resolution.config import (
    DataQualityResolutionConfig,
)
from app.services.data.data_quality_resolution.feature import (
    DataQualityResolutionFeature,
    feature,
)
from app.services.data.data_quality_resolution.manifest import SPEC


def _context(
    feature_instance: DataQualityResolutionFeature,
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
    ctx, registry, _ = _context(feat)
    db_file = str(tmp_path / "test.db")
    config_dict = {
        "database_path": db_file,
        "auto_migrate": True,
        "max_findings": 5000,
    }
    await feat.mount(ctx, config_dict)

    assert feat.service is not None
    assert feat.service._config.database_path == db_file
    assert feat.service._config.auto_migrate is True
    assert feat.service._config.max_findings == 5000
    provided = registry.resolve(RESOLVE_QUALITY_CAPABILITY)
    assert provided is feat.service
    if feat.service._db_conn:
        feat.service._db_conn.close()


@pytest.mark.asyncio
async def test_feature_mount_with_object_config(tmp_path: Path) -> None:
    """Verify feature mounting with DataQualityResolutionConfig object."""
    feat = DataQualityResolutionFeature()
    ctx, registry, _ = _context(feat)
    db_file = str(tmp_path / "test2.db")
    cfg = DataQualityResolutionConfig(
        database_path=db_file,
        auto_migrate=False,
        max_findings=2000,
    )
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service._config.database_path == db_file
    assert feat.service._config.auto_migrate is False
    assert feat.service._config.max_findings == 2000
    provided = registry.resolve(RESOLVE_QUALITY_CAPABILITY)
    assert provided is feat.service
    if feat.service._db_conn:
        feat.service._db_conn.close()


@pytest.mark.asyncio
async def test_feature_mount_with_none_config() -> None:
    """Verify feature mounting with None configuration."""
    feat = feature()
    ctx, _registry, _ = _context(feat)
    await feat.mount(ctx, None)
    assert feat.service is not None
    assert feat.service._config.database_path is None
    if feat.service._db_conn:
        feat.service._db_conn.close()


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid database_path type."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="database_path must be a string if provided"):
        await feat.mount(ctx, {"database_path": 12345})
