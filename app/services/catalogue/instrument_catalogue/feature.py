"""Feature lifecycle mount implementation for Instrument Catalogue."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.services.catalogue.instrument_catalogue.config import (
    InstrumentCatalogueConfig,
)
from app.services.catalogue.instrument_catalogue.instrument_catalogue import (
    InstrumentCatalogueService,
)
from app.services.catalogue.instrument_catalogue.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class InstrumentCatalogueFeature:
    """Composable feature package providing Instrument Catalogue capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: InstrumentCatalogueService | None = None

    @property
    def service(self) -> InstrumentCatalogueService | None:
        """Return the underlying instrument catalogue service instance.

        Returns:
            The instrument catalogue service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the instrument catalogue capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If config database_path is not a valid string or path.
        """
        cfg = InstrumentCatalogueConfig()
        if isinstance(config, dict):
            db_path = config.get("database_path")
            if db_path is not None and not isinstance(db_path, str):
                msg = "database_path must be a string if provided"
                raise TypeError(msg)
            cfg = InstrumentCatalogueConfig(
                database_path=db_path,
                auto_migrate=config.get("auto_migrate", True),
            )
        elif isinstance(config, InstrumentCatalogueConfig):
            cfg = config

        self._service = InstrumentCatalogueService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(CATALOG_INSTRUMENTS_CAPABILITY, self._service)


def feature() -> InstrumentCatalogueFeature:
    """Factory function for discovery via entry points.

    Returns:
        New InstrumentCatalogueFeature instance.
    """
    return InstrumentCatalogueFeature()
