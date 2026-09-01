"""Lifecycle adapter for deterministic tick normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import NORMALIZE_TICKS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.normalize_ticks.config import NormalizeTicksConfig
from app.services.data.normalize_ticks.manifest import SPEC
from app.services.data.normalize_ticks.normalize_ticks import NormalizeTicksService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class NormalizeTicksFeature:
    """Composable normalize-ticks feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve the series store and publish the normalize-ticks capability.

        Args:
            context: Scoped feature runtime context.
            config: Raw mapping or trusted config instance.

        Raises:
            TypeError: If config has an unsupported type.
        """
        if isinstance(config, NormalizeTicksConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = NormalizeTicksConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or NormalizeTicksConfig")
        del parsed
        store = context.require(DATA_SERIES_STORE_CAPABILITY)
        context.provide(NORMALIZE_TICKS_CAPABILITY, NormalizeTicksService(store))


def create_feature() -> NormalizeTicksFeature:
    """Create a fresh normalize-ticks feature instance.

    Returns:
        Unmounted feature instance.
    """
    return NormalizeTicksFeature()
