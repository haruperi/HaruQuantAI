"""Feature lifecycle mount implementation for cTrader Connection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
)
from app.services.brokers.ctrader.client import CTraderService
from app.services.brokers.ctrader.config import CTraderConfig
from app.services.brokers.ctrader.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class CTraderFeature:
    """Composable feature package providing cTrader capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        self.spec = spec
        self._service: CTraderService | None = None

    @property
    def service(self) -> CTraderService | None:
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        raw_config = config if isinstance(config, dict) else {}
        parsed_config = (
            config if isinstance(config, CTraderConfig) else CTraderConfig(**raw_config)
        )

        self._service = CTraderService(config=parsed_config)
        context.provide(BROKER_OPERATIONS_CAPABILITY, self._service)
        context.provide(PROVIDER_CTRADER_CAPABILITY, self._service)


def feature() -> CTraderFeature:
    """Factory function for discovery via entry points."""
    return CTraderFeature()
