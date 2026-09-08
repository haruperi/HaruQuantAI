"""Feature lifecycle mount for Plugin Contributions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.plugins.capabilities import (
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.services.plugins.register_contributions.config import (
    PluginContributionsConfig,
)
from app.services.plugins.register_contributions.manifest import SPEC
from app.services.plugins.register_contributions.register_contributions import (
    RegisterContributionsService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec

logger = get_logger(__name__)


class RegisterContributionsFeature:
    """Composable feature package providing plugin contribution registration."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring served capability.
        """
        self.spec = spec
        self._service: RegisterContributionsService | None = None

    @property
    def service(self) -> RegisterContributionsService | None:
        """Return the running RegisterContributionsService instance.

        Returns:
            The service instance if mounted, else None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature into the given feature context.

        Args:
            context: FeatureContext providing service resolution and registration.
            config: Optional configuration dictionary or object.
        """
        logger.info(
            "Mounting RegisterContributionsFeature",
            capability=REGISTER_CONTRIBUTIONS_CAPABILITY.identifier,
            event="feature.register_contributions.mounting",
        )
        raw_config = config if isinstance(config, dict) else {}
        cfg = PluginContributionsConfig.from_dict(raw_config)
        service = RegisterContributionsService(config=cfg)

        def _unmount_callback() -> None:
            logger.info(
                "Unmounting RegisterContributionsFeature callback invoked",
                capability=REGISTER_CONTRIBUTIONS_CAPABILITY.identifier,
                event="feature.register_contributions.unmounted",
            )
            self._service = None

        context.register_callback(_unmount_callback)
        context.provide(REGISTER_CONTRIBUTIONS_CAPABILITY, service)
        self._service = service

    async def unmount(self, _context: FeatureContext) -> None:
        """Unmount the feature and clear active service instance.

        Args:
            _context: FeatureContext being unmounted.
        """
        logger.info(
            "Unmounting RegisterContributionsFeature explicitly",
            capability=REGISTER_CONTRIBUTIONS_CAPABILITY.identifier,
            event="feature.register_contributions.unmounting",
        )
        self._service = None


def feature() -> RegisterContributionsFeature:
    """Entry point factory for the Plugin Contributions feature.

    Returns:
        New RegisterContributionsFeature instance.
    """
    return RegisterContributionsFeature()
