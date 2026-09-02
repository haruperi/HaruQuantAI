"""Feature lifecycle mount implementation for Dukascopy Connection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
)
from app.services.brokers.dukascopy.client import DukascopyService
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class DukascopyFeature:
    """Composable feature package providing Dukascopy capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        self.spec = spec
        self._service: DukascopyService | None = None

    @property
    def service(self) -> DukascopyService | None:
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        raw_config = config if isinstance(config, dict) else {}
        parsed_config = (
            config
            if isinstance(config, DukascopyConfig)
            else DukascopyConfig(**raw_config)
        )

        self._service = DukascopyService(config=parsed_config)
        context.provide(BROKER_OPERATIONS_CAPABILITY, self._service)
        context.provide(PROVIDER_DUKASCOPY_CAPABILITY, self._service)


def feature() -> DukascopyFeature:
    """Factory function for discovery via entry points."""
    return DukascopyFeature()
