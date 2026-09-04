"""Feature lifecycle mount for the system settings gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.interfaces.capabilities import OPERATE_SETTINGS_CAPABILITY
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY
from app.services.interfaces.operate_settings.config import (
    OperateSettingsConfig,
    from_dict,
)
from app.services.interfaces.operate_settings.gateway import SettingsGateway
from app.services.interfaces.operate_settings.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class OperateSettingsFeature:
    """Composable feature package providing settings operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._gateway: SettingsGateway | None = None

    @property
    def gateway(self) -> SettingsGateway | None:
        """Return the mounted gateway, or None before mount.

        Returns:
            Active gateway instance if mounted, otherwise None.
        """
        return self._gateway

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the gateway against the resolved Workspace provider.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, OperateSettingsConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
            CapabilityUnavailableError: If the required Workspace
                capability has no active provider.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, OperateSettingsConfig):
            parsed = config
        else:
            message = (
                "operate-settings configuration must be a mapping, "
                "OperateSettingsConfig, or None"
            )
            raise TypeError(message)
        provider = context.require(ADMINISTER_SETTINGS_CAPABILITY)
        gateway = SettingsGateway(provider, parsed)
        context.register_callback(gateway.close)
        context.provide(OPERATE_SETTINGS_CAPABILITY, gateway)
        self._gateway = gateway


def feature() -> OperateSettingsFeature:
    """Factory for discovery via entry points.

    Returns:
        New OperateSettingsFeature instance.
    """
    return OperateSettingsFeature()
