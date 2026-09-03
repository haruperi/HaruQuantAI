"""Feature lifecycle mount for the account watchlist gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.interfaces.capabilities import OPERATE_WATCHLISTS_CAPABILITY
from app.contracts.workspace.capabilities import MANAGE_WATCHLISTS_CAPABILITY
from app.services.interfaces.operate_watchlists.config import (
    OperateWatchlistsConfig,
    from_dict,
)
from app.services.interfaces.operate_watchlists.gateway import WatchlistGateway
from app.services.interfaces.operate_watchlists.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class OperateWatchlistsFeature:
    """Composable feature package providing watchlist operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._gateway: WatchlistGateway | None = None

    @property
    def gateway(self) -> WatchlistGateway | None:
        """Return the mounted gateway, or None before mount.

        Returns:
            Active gateway instance if mounted, otherwise None.
        """
        return self._gateway

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the gateway against the resolved Workspace provider.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, OperateWatchlistsConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
            CapabilityUnavailableError: If the required Workspace
                capability has no active provider.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, OperateWatchlistsConfig):
            parsed = config
        else:
            message = (
                "operate-watchlists configuration must be a mapping, "
                "OperateWatchlistsConfig, or None"
            )
            raise TypeError(message)
        provider = context.require(MANAGE_WATCHLISTS_CAPABILITY)
        gateway = WatchlistGateway(provider, parsed)
        context.register_callback(gateway.close)
        context.provide(OPERATE_WATCHLISTS_CAPABILITY, gateway)
        self._gateway = gateway


def feature() -> OperateWatchlistsFeature:
    """Factory for discovery via entry points.

    Returns:
        New OperateWatchlistsFeature instance.
    """
    return OperateWatchlistsFeature()
