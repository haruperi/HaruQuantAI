"""Lifecycle adapter for profile source preparation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import PREPARE_PROFILES_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.prepare_profiles.config import PrepareProfilesConfig
from app.services.data.prepare_profiles.manifest import SPEC
from app.services.data.prepare_profiles.prepare_profiles import PrepareProfilesService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class PrepareProfilesFeature:
    """Composable profile-source preparation feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve dependencies and publish profile-source validation.

        Args:
            context: Scoped feature runtime context.
            config: Raw mapping or trusted config instance.

        Raises:
            TypeError: If config has an unsupported type.
        """
        if isinstance(config, PrepareProfilesConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = PrepareProfilesConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or PrepareProfilesConfig")
        del parsed
        store = context.require(DATA_SERIES_STORE_CAPABILITY)
        context.provide(PREPARE_PROFILES_CAPABILITY, PrepareProfilesService(store))


def create_feature() -> PrepareProfilesFeature:
    """Create a fresh profile-preparation feature instance.

    Returns:
        Unmounted feature instance.
    """
    return PrepareProfilesFeature()
