"""Feature lifecycle mount implementation for Data Quality and Resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import RESOLVE_QUALITY_CAPABILITY
from app.services.data.data_quality_resolution.config import (
    DataQualityResolutionConfig,
)
from app.services.data.data_quality_resolution.data_quality_resolution import (
    DataQualityResolutionService,
)
from app.services.data.data_quality_resolution.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class DataQualityResolutionFeature:
    """Composable feature package providing Data Quality and Resolution capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: DataQualityResolutionService | None = None

    @property
    def service(self) -> DataQualityResolutionService | None:
        """Return the underlying data quality resolution service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the data quality resolution capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = DataQualityResolutionConfig()
        if isinstance(config, dict):
            db_path = config.get("database_path")
            if db_path is not None and not isinstance(db_path, str):
                msg = "database_path must be a string if provided"
                raise TypeError(msg)
            cfg = DataQualityResolutionConfig(
                database_path=db_path,
                auto_migrate=config.get("auto_migrate", True),
                max_findings=int(config.get("max_findings", 10000)),
            )
        elif isinstance(config, DataQualityResolutionConfig):
            cfg = config

        self._service = DataQualityResolutionService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(RESOLVE_QUALITY_CAPABILITY, self._service)


def feature() -> DataQualityResolutionFeature:
    """Factory function for discovery via entry points.

    Returns:
        New DataQualityResolutionFeature instance.
    """
    return DataQualityResolutionFeature()
