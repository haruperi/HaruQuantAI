"""Feature lifecycle mount implementation for External Indicator Series."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import IMPORT_INDICATORS_CAPABILITY
from app.services.data.external_indicator_series.config import (
    ExternalIndicatorSeriesConfig,
)
from app.services.data.external_indicator_series.external_indicator_series import (
    ImportIndicatorsService,
)
from app.services.data.external_indicator_series.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ExternalIndicatorSeriesFeature:
    """Composable feature package providing External Indicator Series capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: ImportIndicatorsService | None = None

    @property
    def service(self) -> ImportIndicatorsService | None:
        """Return the underlying indicator import service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the import indicators capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or ExternalIndicatorSeriesConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = ExternalIndicatorSeriesConfig()
        if isinstance(config, dict):
            tz = config.get("default_timezone", cfg.default_timezone)
            if not isinstance(tz, str):
                msg = "default_timezone must be a string"
                raise TypeError(msg)

            max_pts = config.get("max_points_per_series", cfg.max_points_per_series)
            if not isinstance(max_pts, int):
                msg = "max_points_per_series must be an integer"
                raise TypeError(msg)

            reimport = config.get(
                "require_deterministic_reimport", cfg.require_deterministic_reimport
            )
            if not isinstance(reimport, bool):
                msg = "require_deterministic_reimport must be a boolean"
                raise TypeError(msg)

            allow_future = config.get(
                "allow_future_timestamps", cfg.allow_future_timestamps
            )
            if not isinstance(allow_future, bool):
                msg = "allow_future_timestamps must be a boolean"
                raise TypeError(msg)

            missing_policy = config.get(
                "default_missing_policy", cfg.default_missing_policy
            )
            if not isinstance(missing_policy, str):
                msg = "default_missing_policy must be a string"
                raise TypeError(msg)

            cfg = ExternalIndicatorSeriesConfig(
                default_timezone=tz,
                max_points_per_series=max_pts,
                require_deterministic_reimport=reimport,
                allow_future_timestamps=allow_future,
                default_missing_policy=missing_policy,
            )
        elif isinstance(config, ExternalIndicatorSeriesConfig):
            cfg = config

        self._service = ImportIndicatorsService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(IMPORT_INDICATORS_CAPABILITY, self._service)


def feature() -> ExternalIndicatorSeriesFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ExternalIndicatorSeriesFeature instance.
    """
    return ExternalIndicatorSeriesFeature()
