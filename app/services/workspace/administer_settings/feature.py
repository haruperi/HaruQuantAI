"""Feature lifecycle mount for system settings administration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY
from app.services.workspace.administer_settings.administer_settings import (
    SettingsService,
)
from app.services.workspace.administer_settings.config import (
    AdministerSettingsConfig,
    from_dict,
)
from app.services.workspace.administer_settings.manifest import SPEC

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class AdministerSettingsFeature:
    """Composable feature package providing settings administration."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._service: SettingsService | None = None

    @property
    def service(self) -> SettingsService | None:
        """Return the mounted service, or None before mount.

        Returns:
            Active settings service if mounted, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the settings service and provide its capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, AdministerSettingsConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        logger.info(
            "Mounting AdministerSettingsFeature",
            capability=ADMINISTER_SETTINGS_CAPABILITY.identifier,
            event="feature.administer_settings.mounting",
        )
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, AdministerSettingsConfig):
            parsed = config
        else:
            message = "administer-settings configuration must be a mapping or config"
            raise TypeError(message)
        service = SettingsService(parsed)

        def _unmount_callback() -> None:
            logger.info(
                "Unmounting AdministerSettingsFeature",
                capability=ADMINISTER_SETTINGS_CAPABILITY.identifier,
                event="feature.administer_settings.unmounted",
            )
            self._service = None

        context.register_callback(_unmount_callback)
        context.provide(ADMINISTER_SETTINGS_CAPABILITY, service)
        self._service = service


def feature() -> AdministerSettingsFeature:
    """Factory for discovery via entry points.

    Returns:
        New AdministerSettingsFeature instance.
    """
    return AdministerSettingsFeature()
