"""Feature lifecycle mount implementation for Historical Data Ingestion."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import INGEST_HISTORY_CAPABILITY
from app.services.data.historical_data_ingestion.config import (
    HistoricalDataIngestionConfig,
)
from app.services.data.historical_data_ingestion.historical_data_ingestion import (
    HistoricalDataIngestionService,
)
from app.services.data.historical_data_ingestion.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class HistoricalDataIngestionFeature:
    """Composable feature package providing Historical Data Ingestion capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: HistoricalDataIngestionService | None = None

    @property
    def service(self) -> HistoricalDataIngestionService | None:
        """Return the underlying historical data ingestion service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the historical data ingestion capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If config database_path is not a valid string or path.
        """
        cfg = HistoricalDataIngestionConfig()
        if isinstance(config, dict):
            db_path = config.get("database_path")
            if db_path is not None and not isinstance(db_path, str):
                msg = "database_path must be a string if provided"
                raise TypeError(msg)
            cfg = HistoricalDataIngestionConfig(
                database_path=db_path,
                auto_migrate=config.get("auto_migrate", True),
            )
        elif isinstance(config, HistoricalDataIngestionConfig):
            cfg = config

        self._service = HistoricalDataIngestionService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(INGEST_HISTORY_CAPABILITY, self._service)


def feature() -> HistoricalDataIngestionFeature:
    """Factory function for discovery via entry points.

    Returns:
        New HistoricalDataIngestionFeature instance.
    """
    return HistoricalDataIngestionFeature()
