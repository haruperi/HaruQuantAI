"""Lifecycle adapter for external indicator-series import."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import IMPORT_INDICATORS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.import_indicators.config import ImportIndicatorsConfig
from app.services.data.import_indicators.import_indicators import ImportIndicatorsService
from app.services.data.import_indicators.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ImportIndicatorsFeature:
    """Composable external indicator-series import feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve immutable storage and publish the import capability.

        Args:
            context: Scoped feature lifecycle context.
            config: Raw or pre-parsed feature configuration.

        Raises:
            TypeError: If configuration is not a mapping or parsed config.
        """
        if isinstance(config, ImportIndicatorsConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = ImportIndicatorsConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or ImportIndicatorsConfig")
        del parsed
        store = context.require(DATA_SERIES_STORE_CAPABILITY)
        context.provide(
            IMPORT_INDICATORS_CAPABILITY,
            ImportIndicatorsService(store),
        )


def create_feature() -> ImportIndicatorsFeature:
    """Create a fresh external indicator import feature.

    Returns:
        Unmounted feature instance.
    """
    return ImportIndicatorsFeature()
