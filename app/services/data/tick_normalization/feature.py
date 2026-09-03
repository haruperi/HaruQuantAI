"""Feature lifecycle mount implementation for Tick Normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import NORMALIZE_TICKS_CAPABILITY
from app.services.data.tick_normalization.config import TickNormalizationConfig
from app.services.data.tick_normalization.manifest import SPEC
from app.services.data.tick_normalization.tick_normalization import (
    TickNormalizationService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class TickNormalizationFeature:
    """Composable feature package providing tick normalization capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: TickNormalizationService | None = None

    @property
    def service(self) -> TickNormalizationService | None:
        """Return the underlying tick normalization service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the tick normalization capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If configuration parameters are invalid types.
        """
        cfg = TickNormalizationConfig()
        if isinstance(config, dict):
            max_batch_size = config.get("max_batch_size")
            if max_batch_size is not None and not isinstance(max_batch_size, int):
                msg = "max_batch_size must be an integer if provided"
                raise TypeError(msg)
            if max_batch_size is not None:
                cfg = TickNormalizationConfig(max_batch_size=max_batch_size)
        elif isinstance(config, TickNormalizationConfig):
            cfg = config

        self._service = TickNormalizationService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(NORMALIZE_TICKS_CAPABILITY, self._service)


def feature() -> TickNormalizationFeature:
    """Factory function for discovery via entry points.

    Returns:
        New TickNormalizationFeature instance.
    """
    return TickNormalizationFeature()
