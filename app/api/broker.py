"""Broker domain public capability-aware facade."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from app.contracts.broker.execution import BROKER_EXECUTION
from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerRawBar,
)

if TYPE_CHECKING:
    from app.kernel.registry import ServiceRegistry


class BrokerAPI:
    """Stable facade providing broker domain operations backed by capabilities."""

    def __init__(self, registry: ServiceRegistry) -> None:
        """Initialize BrokerAPI with central service registry.

        Args:
            registry: Central ServiceRegistry tracking active capability providers.
        """
        self._registry = registry

    @property
    def is_market_data_available(self) -> bool:
        """Check if broker market data capability provider is currently active.

        Returns:
            True if broker.market-data@1 is active, False otherwise.
        """
        return self._registry.is_available(BROKER_MARKET_DATA)

    @property
    def is_execution_available(self) -> bool:
        """Check if broker order execution capability provider is currently active.

        Returns:
            True if broker.execution@1 is active, False otherwise.
        """
        return self._registry.is_available(BROKER_EXECUTION)

    async def get_raw_bars(
        self,
        request: BrokerBarsRequest,
    ) -> Sequence[BrokerRawBar]:
        """Retrieve raw OHLCV bars directly from active broker feed.

        Args:
            request: Specification of symbol, timeframe, and date range.

        Returns:
            Sequence of BrokerRawBar instances.

        Raises:
            CapabilityUnavailableError: If broker.market-data@1 provider is absent.
        """
        service = self._registry.require(BROKER_MARKET_DATA)
        return await service.retrieve_bars(request)
