"""Feature lifecycle mount implementation for Bar Aggregation and Timeframes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import AGGREGATE_BARS_CAPABILITY
from app.services.data.bar_aggregation.bar_aggregation import BarAggregationService
from app.services.data.bar_aggregation.config import BarAggregationConfig
from app.services.data.bar_aggregation.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class BarAggregationFeature:
    """Composable feature package providing Bar Aggregation capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: BarAggregationService | None = None

    @property
    def service(self) -> BarAggregationService | None:
        """Return the underlying bar aggregation service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the bar aggregation capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or BarAggregationConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = BarAggregationConfig()
        if isinstance(config, dict):
            max_bars = config.get("max_bars_per_request", 100_000)
            if not isinstance(max_bars, int):
                msg = "max_bars_per_request must be an integer"
                raise TypeError(msg)
            tz = config.get("default_timezone", "UTC")
            if not isinstance(tz, str):
                msg = "default_timezone must be a string"
                raise TypeError(msg)
            allow_custom = config.get("allow_custom_timeframes", True)
            if not isinstance(allow_custom, bool):
                msg = "allow_custom_timeframes must be a boolean"
                raise TypeError(msg)
            cfg = BarAggregationConfig(
                max_bars_per_request=max_bars,
                default_timezone=tz,
                allow_custom_timeframes=allow_custom,
            )
        elif isinstance(config, BarAggregationConfig):
            cfg = config

        self._service = BarAggregationService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(AGGREGATE_BARS_CAPABILITY, self._service)


def feature() -> BarAggregationFeature:
    """Factory function for discovery via entry points.

    Returns:
        New BarAggregationFeature instance.
    """
    return BarAggregationFeature()
