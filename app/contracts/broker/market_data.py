"""Broker raw market data capability contract."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


@dataclass(frozen=True, slots=True)
class BrokerBarsRequest:
    """Request payload for raw broker historical bars.

    Attributes:
        symbol: Financial instrument symbol (e.g., 'EURUSD').
        timeframe: Bar timeframe interval (e.g., 'M1', 'H1', 'D1').
        start: Start datetime in UTC.
        end: End datetime in UTC.
    """

    symbol: str
    timeframe: str
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class BrokerRawBar:
    """Raw OHLCV bar representation from a broker adapter.

    Attributes:
        timestamp: Bar open timestamp in UTC.
        open_price: Opening price.
        high_price: Highest price.
        low_price: Lowest price.
        close_price: Closing price.
        volume: Volume transacted.
    """

    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float


@runtime_checkable
class BrokerMarketData(Protocol):
    """Protocol for broker-level raw market data feed."""

    async def retrieve_bars(
        self,
        request: BrokerBarsRequest,
    ) -> Sequence[BrokerRawBar]:
        """Fetch raw historical price bars from the broker.

        Args:
            request: Bar retrieval specifications.

        Returns:
            Sequence of raw price bars.
        """
        ...


BROKER_MARKET_DATA = CapabilityKey[BrokerMarketData](
    name="broker.market-data",
    major=1,
)
