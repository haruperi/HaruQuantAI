"""Lifecycle adapter for immutable run-data binding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import BIND_RUN_DATA_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.bind_run_data.bind_run_data import BindRunDataService
from app.services.data.bind_run_data.binding_store import BindingStore
from app.services.data.bind_run_data.config import BindRunDataConfig
from app.services.data.bind_run_data.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class BindRunDataFeature:
    """Composable immutable run-data binding feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve the series store and publish run-data binding capability.

        Args:
            context: Scoped feature runtime context.
            config: Raw mapping or trusted config instance.

        Raises:
            TypeError: If config has an unsupported type.
        """
        if isinstance(config, BindRunDataConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = BindRunDataConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or BindRunDataConfig")
        store = context.require(DATA_SERIES_STORE_CAPABILITY)
        context.provide(
            BIND_RUN_DATA_CAPABILITY,
            BindRunDataService(store, BindingStore(parsed.database_path)),
        )


def create_feature() -> BindRunDataFeature:
    """Create a fresh run-data binding feature instance.

    Returns:
        Unmounted feature instance.
    """
    return BindRunDataFeature()
