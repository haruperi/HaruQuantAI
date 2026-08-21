"""Data domain event contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.data.realtime_ticks import Tick


@dataclass(frozen=True, slots=True)
class TickReceivedEvent:
    """Emitted when a real-time market price tick is received.

    Attributes:
        symbol: Financial instrument symbol.
        tick: Real-time price tick data.
        timestamp: Time tick was received.
    """

    symbol: str
    tick: Tick
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class HistoricalBarsRetrievedEvent:
    """Emitted when historical price bars are successfully retrieved.

    Attributes:
        symbol: Financial instrument symbol.
        timeframe: Bar interval.
        bar_count: Number of bars retrieved.
        timestamp: Time of retrieval in UTC.
    """

    symbol: str
    timeframe: str
    bar_count: int
    timestamp: datetime
