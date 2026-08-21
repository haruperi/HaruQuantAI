"""Normalized historical bars capability contract."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


@dataclass(frozen=True, slots=True)
class HistoricalBarsRequest:
    """Request specification for normalized historical bars.

    Attributes:
        symbol: Financial instrument symbol.
        timeframe: Bar timeframe interval (e.g., 'M1', 'H1', 'D1').
        start: Start datetime in UTC.
        end: End datetime in UTC.
    """

    symbol: str
    timeframe: str
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class Bar:
    """Normalized OHLCV bar representation.

    Attributes:
        datetime: Bar timestamp in UTC.
        open: Opening price.
        high: Highest price during period.
        low: Lowest price during period.
        close: Closing price.
        volume: Volume traded.
    """

    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@runtime_checkable
class HistoricalBars(Protocol):
    """Protocol for normalized historical bar retrieval."""

    async def retrieve(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        """Fetch and return normalized historical price bars.

        Args:
            request: Historical bar query specifications.

        Returns:
            Sequence of normalized price bars.
        """
        ...


HISTORICAL_BARS = CapabilityKey[HistoricalBars](
    name="data.historical-bars",
    major=1,
)


class HistoricalBarsUnavailableError(RuntimeError):
    """Raised when no active historical bars provider is available."""
