"""Lifecycle adapter for explicit Data quality resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import RESOLVE_QUALITY_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.resolve_quality.config import ResolveQualityConfig
from app.services.data.resolve_quality.manifest import SPEC
from app.services.data.resolve_quality.quality_store import QualityStore
from app.services.data.resolve_quality.resolve_quality import ResolveQualityService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ResolveQualityFeature:
    """Composable Data quality feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve dependencies, construct storage, and publish quality capability.

        Args:
            context: Scoped feature runtime context.
            config: Raw mapping or trusted config instance.

        Raises:
            TypeError: If config has an unsupported type.
        """
        if isinstance(config, ResolveQualityConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = ResolveQualityConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or ResolveQualityConfig")
        series_store = context.require(DATA_SERIES_STORE_CAPABILITY)
        service = ResolveQualityService(
            series_store,
            QualityStore(parsed.database_path),
        )
        context.provide(RESOLVE_QUALITY_CAPABILITY, service)


def create_feature() -> ResolveQualityFeature:
    """Create a fresh quality feature instance.

    Returns:
        Unmounted feature instance.
    """
    return ResolveQualityFeature()
