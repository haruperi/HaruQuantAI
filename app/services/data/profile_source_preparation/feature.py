"""Feature lifecycle mount implementation for Volume Profile Source Preparation."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.contracts.data.capabilities import PREPARE_PROFILES_CAPABILITY
from app.services.data.profile_source_preparation.config import (
    ProfileSourcePreparationConfig,
)
from app.services.data.profile_source_preparation.manifest import SPEC
from app.services.data.profile_source_preparation.profile_source_preparation import (
    PrepareProfilesService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ProfileSourcePreparationFeature:
    """Composable feature package providing Volume Profile Source Preparation."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: PrepareProfilesService | None = None

    @property
    def service(self) -> PrepareProfilesService | None:
        """Return the underlying profile source preparation service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the prepare profiles capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or ProfileSourcePreparationConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = ProfileSourcePreparationConfig()
        if isinstance(config, dict):
            price_step = config.get("default_price_step", cfg.default_price_step)
            if isinstance(price_step, (str, float, int)):
                price_step = Decimal(str(price_step))
            elif not isinstance(price_step, Decimal):
                msg = (
                    "default_price_step must be a Decimal or decimal-compatible string"
                )
                raise TypeError(msg)

            bin_count = config.get("default_bin_count", cfg.default_bin_count)
            if bin_count is not None and not isinstance(bin_count, int):
                msg = "default_bin_count must be an integer or None"
                raise TypeError(msg)

            min_step = config.get("min_price_step", cfg.min_price_step)
            if isinstance(min_step, (str, float, int)):
                min_step = Decimal(str(min_step))
            elif not isinstance(min_step, Decimal):
                msg = "min_price_step must be a Decimal or decimal-compatible string"
                raise TypeError(msg)

            max_bins = config.get("max_bin_count", cfg.max_bin_count)
            if not isinstance(max_bins, int):
                msg = "max_bin_count must be an integer"
                raise TypeError(msg)

            require_align = config.get(
                "require_session_alignment", cfg.require_session_alignment
            )
            if not isinstance(require_align, bool):
                msg = "require_session_alignment must be a boolean"
                raise TypeError(msg)

            cfg = ProfileSourcePreparationConfig(
                default_price_step=price_step,
                default_bin_count=bin_count,
                min_price_step=min_step,
                max_bin_count=max_bins,
                require_session_alignment=require_align,
            )
        elif isinstance(config, ProfileSourcePreparationConfig):
            cfg = config

        self._service = PrepareProfilesService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(PREPARE_PROFILES_CAPABILITY, self._service)


def feature() -> ProfileSourcePreparationFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ProfileSourcePreparationFeature instance.
    """
    return ProfileSourcePreparationFeature()
