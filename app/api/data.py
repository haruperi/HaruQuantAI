"""Data domain public capability-aware facade."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from app.contracts.data.bar_cache import BAR_CACHE
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    Bar,
    HistoricalBarsRequest,
)
from app.contracts.data.realtime_ticks import REALTIME_TICKS

if TYPE_CHECKING:
    from app.kernel.registry import ServiceRegistry


class DataAPI:
    """Stable facade providing data domain operations backed by dynamic capabilities."""

    def __init__(self, registry: ServiceRegistry) -> None:
        """Initialize DataAPI with central service registry.

        Args:
            registry: Central ServiceRegistry tracking active capability providers.
        """
        self._registry = registry

    @property
    def is_historical_bars_available(self) -> bool:
        """Check if historical bars capability provider is currently active.

        Returns:
            True if data.historical-bars@1 is active, False otherwise.
        """
        return self._registry.is_available(HISTORICAL_BARS)

    @property
    def is_realtime_ticks_available(self) -> bool:
        """Check if real-time ticks capability provider is currently active.

        Returns:
            True if data.realtime-ticks@1 is active, False otherwise.
        """
        return self._registry.is_available(REALTIME_TICKS)

    @property
    def is_bar_cache_available(self) -> bool:
        """Check if bar cache capability provider is currently active.

        Returns:
            True if data.bar-cache@1 is active, False otherwise.
        """
        return self._registry.is_available(BAR_CACHE)

    async def get_historical_bars(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        """Retrieve normalized historical OHLCV bars.

        Args:
            request: Specification of symbol, timeframe, and date range.

        Returns:
            Sequence of normalized Bar instances.

        Raises:
            CapabilityUnavailableError: If data.historical-bars@1 provider is absent.
        """
        service = self._registry.require(HISTORICAL_BARS)
        return await service.retrieve(request)
