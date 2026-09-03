"""Feature lifecycle mount implementation for QuantDataManager Source."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.contracts.data.capabilities import IMPORT_QUANTDATA_CAPABILITY
from app.services.data.quantdata_manager_source.config import QuantDataManagerConfig
from app.services.data.quantdata_manager_source.manifest import SPEC
from app.services.data.quantdata_manager_source.quantdata_manager_source import (
    QuantDataManagerSourceService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class QuantDataManagerSourceFeature:
    """Composable feature package providing QuantDataManager source capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: QuantDataManagerSourceService | None = None

    @property
    def service(self) -> QuantDataManagerSourceService | None:
        """Return the underlying QuantDataManager source service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the QuantDataManager import capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If configuration parameters are invalid types.
        """
        cfg = QuantDataManagerConfig()
        if isinstance(config, dict):
            allowed_root = config.get("allowed_root")
            if allowed_root is not None and not isinstance(allowed_root, (str, Path)):
                msg = "allowed_root must be a string or Path if provided"
                raise TypeError(msg)
            db_path = config.get("database_path")
            if db_path is not None and not isinstance(db_path, (str, Path)):
                msg = "database_path must be a string or Path if provided"
                raise TypeError(msg)
            cfg = QuantDataManagerConfig(
                allowed_root=allowed_root,
                database_path=db_path,
                auto_migrate=config.get("auto_migrate", True),
            )
        elif isinstance(config, QuantDataManagerConfig):
            cfg = config

        self._service = QuantDataManagerSourceService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(IMPORT_QUANTDATA_CAPABILITY, self._service)


def feature() -> QuantDataManagerSourceFeature:
    """Factory function for discovery via entry points.

    Returns:
        New QuantDataManagerSourceFeature instance.
    """
    return QuantDataManagerSourceFeature()
