"""Feature lifecycle mount implementation for External Series Alignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import ALIGN_SERIES_CAPABILITY
from app.services.data.external_series_alignment.config import (
    ExternalSeriesAlignmentConfig,
)
from app.services.data.external_series_alignment.external_series_alignment import (
    AlignSeriesService,
)
from app.services.data.external_series_alignment.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ExternalSeriesAlignmentFeature:
    """Composable feature package providing External Series Alignment capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: AlignSeriesService | None = None

    @property
    def service(self) -> AlignSeriesService | None:
        """Return the underlying align series service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the align series capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or ExternalSeriesAlignmentConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = ExternalSeriesAlignmentConfig()
        if isinstance(config, dict):
            max_points = config.get(
                "max_series_points_per_request", cfg.max_series_points_per_request
            )
            if not isinstance(max_points, int):
                msg = "max_series_points_per_request must be an integer"
                raise TypeError(msg)

            tz = config.get("default_timezone", cfg.default_timezone)
            if not isinstance(tz, str):
                msg = "default_timezone must be a string"
                raise TypeError(msg)

            max_age = config.get("default_max_age_seconds", cfg.default_max_age_seconds)
            if not isinstance(max_age, int):
                msg = "default_max_age_seconds must be an integer"
                raise TypeError(msg)

            missing_policy = config.get(
                "default_missing_policy", cfg.default_missing_policy
            )
            if not isinstance(missing_policy, str):
                msg = "default_missing_policy must be a string"
                raise TypeError(msg)

            cfg = ExternalSeriesAlignmentConfig(
                max_series_points_per_request=max_points,
                default_timezone=tz,
                default_max_age_seconds=max_age,
                default_missing_policy=missing_policy,
            )
        elif isinstance(config, ExternalSeriesAlignmentConfig):
            cfg = config

        self._service = AlignSeriesService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(ALIGN_SERIES_CAPABILITY, self._service)


def feature() -> ExternalSeriesAlignmentFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ExternalSeriesAlignmentFeature instance.
    """
    return ExternalSeriesAlignmentFeature()
