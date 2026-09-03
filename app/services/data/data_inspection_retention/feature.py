"""Feature lifecycle mount implementation for Data Inspection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import MANAGE_RETENTION_CAPABILITY
from app.services.data.data_inspection_retention.config import (
    DataInspectionRetentionConfig,
)
from app.services.data.data_inspection_retention.data_inspection_retention import (
    DataInspectionRetentionService,
)
from app.services.data.data_inspection_retention.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class DataInspectionRetentionFeature:
    """Composable feature package for Data Inspection and Retention."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: DataInspectionRetentionService | None = None

    @property
    def service(self) -> DataInspectionRetentionService | None:
        """Return the underlying data inspection retention service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the manage-retention capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or DataInspectionRetentionConfig.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = DataInspectionRetentionConfig()
        if isinstance(config, dict):
            preview_limit = config.get("default_preview_limit", 100)
            if not isinstance(preview_limit, int):
                msg = "default_preview_limit must be an integer"
                raise TypeError(msg)
            max_preview = config.get("max_preview_limit", 10_000)
            if not isinstance(max_preview, int):
                msg = "max_preview_limit must be an integer"
                raise TypeError(msg)
            quarantine_days = config.get("default_quarantine_days", 30)
            if not isinstance(quarantine_days, int):
                msg = "default_quarantine_days must be an integer"
                raise TypeError(msg)
            cfg = DataInspectionRetentionConfig(
                default_preview_limit=preview_limit,
                max_preview_limit=max_preview,
                default_quarantine_days=quarantine_days,
            )
        elif isinstance(config, DataInspectionRetentionConfig):
            cfg = config

        self._service = DataInspectionRetentionService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(MANAGE_RETENTION_CAPABILITY, self._service)


def feature() -> DataInspectionRetentionFeature:
    """Factory function for discovery via entry points.

    Returns:
        New DataInspectionRetentionFeature instance.
    """
    return DataInspectionRetentionFeature()
