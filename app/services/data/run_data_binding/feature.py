"""Feature lifecycle mount implementation for Run Data Binding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import BIND_RUN_DATA_CAPABILITY
from app.services.data.run_data_binding.config import RunDataBindingConfig
from app.services.data.run_data_binding.manifest import SPEC
from app.services.data.run_data_binding.run_data_binding import BindRunDataService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class RunDataBindingFeature:
    """Composable feature package providing Run Data Binding."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: BindRunDataService | None = None

    @property
    def service(self) -> BindRunDataService | None:
        """Return the underlying run data binding service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the bind run data capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or RunDataBindingConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = RunDataBindingConfig()
        if isinstance(config, dict):
            strict = config.get("strict_precision_check", cfg.strict_precision_check)
            if not isinstance(strict, bool):
                msg = "strict_precision_check must be a boolean"
                raise TypeError(msg)

            synthetic = config.get(
                "allow_synthetic_sources", cfg.allow_synthetic_sources
            )
            if not isinstance(synthetic, bool):
                msg = "allow_synthetic_sources must be a boolean"
                raise TypeError(msg)

            committed = config.get(
                "require_committed_status", cfg.require_committed_status
            )
            if not isinstance(committed, bool):
                msg = "require_committed_status must be a boolean"
                raise TypeError(msg)

            precisions = config.get("supported_precisions", cfg.supported_precisions)
            if not isinstance(precisions, (tuple, list)):
                msg = "supported_precisions must be a tuple or list of strings"
                raise TypeError(msg)

            cfg = RunDataBindingConfig(
                strict_precision_check=strict,
                allow_synthetic_sources=synthetic,
                require_committed_status=committed,
                supported_precisions=tuple(str(p) for p in precisions),
            )
        elif isinstance(config, RunDataBindingConfig):
            cfg = config

        self._service = BindRunDataService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(BIND_RUN_DATA_CAPABILITY, self._service)


def feature() -> RunDataBindingFeature:
    """Factory function for discovery via entry points.

    Returns:
        New RunDataBindingFeature instance.
    """
    return RunDataBindingFeature()
