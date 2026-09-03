"""Feature lifecycle mount implementation for Synthetic and Scenario Series."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import GENERATE_SCENARIOS_CAPABILITY
from app.services.data.synthetic_scenario_series.config import (
    SyntheticScenarioSeriesConfig,
)
from app.services.data.synthetic_scenario_series.manifest import SPEC
from app.services.data.synthetic_scenario_series.synthetic_scenario_series import (
    GenerateScenariosService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class SyntheticScenarioSeriesFeature:
    """Composable feature package providing Synthetic and Scenario Series capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: GenerateScenariosService | None = None

    @property
    def service(self) -> GenerateScenariosService | None:
        """Return the underlying scenario generation service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the generate scenarios capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or SyntheticScenarioSeriesConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = SyntheticScenarioSeriesConfig()
        if isinstance(config, dict):
            max_rec = config.get("max_records", cfg.max_records)
            if not isinstance(max_rec, int):
                msg = "max_records must be an integer"
                raise TypeError(msg)

            model = config.get("default_model", cfg.default_model)
            if not isinstance(model, str):
                msg = "default_model must be a string"
                raise TypeError(msg)

            rounding = config.get("default_rounding", cfg.default_rounding)
            if not isinstance(rounding, str):
                msg = "default_rounding must be a string"
                raise TypeError(msg)

            transforms = config.get(
                "supported_transform_types", cfg.supported_transform_types
            )
            if isinstance(transforms, (list, set, tuple)):
                transforms = frozenset(transforms)
            elif not isinstance(transforms, frozenset):
                msg = "supported_transform_types must be a set/frozenset of strings"
                raise TypeError(msg)

            cfg = SyntheticScenarioSeriesConfig(
                max_records=max_rec,
                default_model=model,
                default_rounding=rounding,
                supported_transform_types=transforms,
            )
        elif isinstance(config, SyntheticScenarioSeriesConfig):
            cfg = config

        self._service = GenerateScenariosService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(GENERATE_SCENARIOS_CAPABILITY, self._service)


def feature() -> SyntheticScenarioSeriesFeature:
    """Factory function for discovery via entry points.

    Returns:
        New SyntheticScenarioSeriesFeature instance.
    """
    return SyntheticScenarioSeriesFeature()
