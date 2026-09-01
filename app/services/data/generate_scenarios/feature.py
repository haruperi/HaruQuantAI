"""Lifecycle adapter for synthetic/scenario generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import GENERATE_SCENARIOS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.generate_scenarios.config import GenerateScenariosConfig
from app.services.data.generate_scenarios.generate_scenarios import GenerateScenariosService
from app.services.data.generate_scenarios.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class GenerateScenariosFeature:
    """Composable synthetic/scenario generation feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve immutable storage and publish scenario capability."""
        if isinstance(config, GenerateScenariosConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = GenerateScenariosConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or GenerateScenariosConfig")
        store = context.require(DATA_SERIES_STORE_CAPABILITY)
        context.provide(
            GENERATE_SCENARIOS_CAPABILITY,
            GenerateScenariosService(store, parsed),
        )


def create_feature() -> GenerateScenariosFeature:
    """Create a fresh scenario generation feature."""
    return GenerateScenariosFeature()
