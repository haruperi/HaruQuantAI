"""Mock broker market data provider generating synthetic raw price bars."""

import math
from collections.abc import Sequence
from datetime import timedelta
from typing import override

from app.contracts.broker.market_data import (
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.services.broker.mock_feed.config import MockFeedConfig

MAX_SYNTHETIC_BARS: int = 10_000
TIMEFRAME_STEPS: dict[str, timedelta] = {
    "M1": timedelta(minutes=1),
    "M5": timedelta(minutes=5),
    "M15": timedelta(minutes=15),
    "M30": timedelta(minutes=30),
    "H1": timedelta(hours=1),
    "H4": timedelta(hours=4),
    "D1": timedelta(days=1),
    "W1": timedelta(weeks=1),
    "MN1": timedelta(days=30),
}


class MockBrokerMarketData(BrokerMarketData):
    """Deterministic synthetic broker market-data implementation."""

    def __init__(self, config: MockFeedConfig | None = None) -> None:
        self._config = config or MockFeedConfig()

    @override
    async def retrieve_bars(
        self,
        request: BrokerBarsRequest,
    ) -> Sequence[BrokerRawBar]:
        """Generate synthetic raw OHLCV bars for the requested interval."""
        if request.end <= request.start:
            return ()
        step = self._resolve_timeframe_step(request.timeframe)
        bars: list[BrokerRawBar] = []
        current = request.start
        index = 0
        base_price = self._config.base_price
        while current < request.end and len(bars) < MAX_SYNTHETIC_BARS:
            offset = math.sin(index * 0.1) * 0.0050
            open_price = round(base_price + offset, 5)
            bars.append(
                BrokerRawBar(
                    timestamp=current,
                    open_price=open_price,
                    high_price=round(open_price + 0.0010, 5),
                    low_price=round(open_price - 0.0008, 5),
                    close_price=round(open_price + 0.0002, 5),
                    volume=100.0 + (index % 20) * 10.0,
                )
            )
            current += step
            index += 1
        return tuple(bars)

    def _resolve_timeframe_step(self, timeframe: str) -> timedelta:
        """Map a supported timeframe identifier to its deterministic interval."""
        normalized = timeframe.upper()
        try:
            return TIMEFRAME_STEPS[normalized]
        except KeyError as error:
            allowed = ", ".join(TIMEFRAME_STEPS)
            msg = f"Unsupported timeframe '{timeframe}'. Allowed: {allowed}"
            raise ValueError(msg) from error
