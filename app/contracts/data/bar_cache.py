"""Historical bar cache capability contract."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.contracts.data.historical_bars import Bar, HistoricalBarsRequest


@runtime_checkable
class BarCache(Protocol):
    """Protocol for caching and retrieving historical price bars."""

    async def get_bars(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar] | None:
        """Retrieve cached bars matching the request interval.

        Args:
            request: Target historical bar request.

        Returns:
            Cached bars sequence if available and complete, None otherwise.
        """
        ...

    async def put_bars(
        self,
        request: HistoricalBarsRequest,
        bars: Sequence[Bar],
    ) -> None:
        """Store historical bars in cache.

        Args:
            request: Original query request matching the bars.
            bars: Normalized bars to persist.
        """
        ...


BAR_CACHE = CapabilityKey[BarCache](
    name="data.bar-cache",
    major=1,
)
