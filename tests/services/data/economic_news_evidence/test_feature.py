"""Unit tests for EconomicNewsEvidenceFeature mounting."""

from typing import Any

import pytest
from app.contracts.data.capabilities import TRACK_MARKET_NEWS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.economic_news_evidence.config import (
    EconomicNewsEvidenceConfig,
)
from app.services.data.economic_news_evidence.feature import (
    EconomicNewsEvidenceFeature,
    feature,
)
from app.services.data.economic_news_evidence.manifest import SPEC


def _context(
    feature_instance: EconomicNewsEvidenceFeature,
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
async def test_feature_factory_and_mount_dict_config() -> None:
    """Verify mounting with dictionary configuration."""
    feat = feature()
    ctx, registry, _ = _context(feat)

    await feat.mount(
        ctx,
        {
            "max_query_results": 5_000,
            "default_rate_limit_per_minute": 30,
            "max_payload_size_bytes": 2_000_000,
            "default_freshness_limit_seconds": 3_600,
            "allowed_sources": ["SOURCE_A", "SOURCE_B"],
        },
    )

    assert feat.service is not None
    assert feat.service.config.max_query_results == 5_000
    assert feat.service.config.default_rate_limit_per_minute == 30
    assert "SOURCE_A" in feat.service.config.allowed_sources
    provided = registry.resolve(TRACK_MARKET_NEWS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_dataclass_config() -> None:
    """Verify mounting with EconomicNewsEvidenceConfig instance."""
    feat = feature()
    ctx, registry, _ = _context(feat)

    cfg = EconomicNewsEvidenceConfig(max_query_results=1_000)
    await feat.mount(ctx, cfg)

    assert feat.service is not None
    assert feat.service.config.max_query_results == 1_000
    provided = registry.resolve(TRACK_MARKET_NEWS_CAPABILITY)
    assert provided is feat.service


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_type() -> None:
    """Verify TypeError on invalid config values."""
    feat = feature()
    ctx, _, _ = _context(feat)

    with pytest.raises(TypeError, match="max_query_results must be an integer"):
        await feat.mount(ctx, {"max_query_results": "invalid"})

    with pytest.raises(
        TypeError, match="default_rate_limit_per_minute must be an integer"
    ):
        await feat.mount(ctx, {"default_rate_limit_per_minute": "invalid"})

    with pytest.raises(TypeError, match="max_payload_size_bytes must be an integer"):
        await feat.mount(ctx, {"max_payload_size_bytes": "invalid"})

    with pytest.raises(
        TypeError, match="default_freshness_limit_seconds must be an integer"
    ):
        await feat.mount(ctx, {"default_freshness_limit_seconds": "invalid"})

    with pytest.raises(TypeError, match="allowed_sources must be a set or frozenset"):
        await feat.mount(ctx, {"allowed_sources": 123})
