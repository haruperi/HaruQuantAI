"""Feature lifecycle mount for account watchlist management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import MANAGE_WATCHLISTS_CAPABILITY
from app.services.workspace.manage_watchlists.config import (
    ManageWatchlistsConfig,
    from_dict,
)
from app.services.workspace.manage_watchlists.manage_watchlists import WatchlistService
from app.services.workspace.manage_watchlists.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ManageWatchlistsFeature:
    """Composable feature package providing watchlist management."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._service: WatchlistService | None = None

    @property
    def service(self) -> WatchlistService | None:
        """Return the mounted service, or None before mount.

        Returns:
            Active service instance if mounted, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the watchlist service with its durable store.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, ManageWatchlistsConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ManageWatchlistsConfig):
            parsed = config
        else:
            message = (
                "manage-watchlists configuration must be a mapping, "
                "ManageWatchlistsConfig, or None"
            )
            raise TypeError(message)
        service = WatchlistService(parsed)
        context.register_callback(service.close)
        context.provide(MANAGE_WATCHLISTS_CAPABILITY, service)
        self._service = service


def feature() -> ManageWatchlistsFeature:
    """Factory for discovery via entry points.

    Returns:
        New ManageWatchlistsFeature instance.
    """
    return ManageWatchlistsFeature()
