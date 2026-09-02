"""Feature lifecycle mount implementation for Yahoo Finance Provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_YAHOO_CAPABILITY,
)
from app.services.brokers.yahoo.client import YahooService
from app.services.brokers.yahoo.config import YahooConfig
from app.services.brokers.yahoo.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class YahooFeature:
    """Composable feature package providing Yahoo Finance capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        self.spec = spec
        self._service: YahooService | None = None

    @property
    def service(self) -> YahooService | None:
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        raw_config = config if isinstance(config, dict) else {}
        parsed_config = (
            config if isinstance(config, YahooConfig) else YahooConfig(**raw_config)
        )

        self._service = YahooService(config=parsed_config)
        context.provide(BROKER_OPERATIONS_CAPABILITY, self._service)
        context.provide(PROVIDER_YAHOO_CAPABILITY, self._service)


def feature() -> YahooFeature:
    """Factory function for discovery via entry points."""
    return YahooFeature()
