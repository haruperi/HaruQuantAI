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

SUPPORTED_TIMEFRAME_STEPS: dict[str, timedelta] = {
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
    """Synthetic broker market data implementation.

    Satisfies:
        FR-BROKER-GENERATE_RAW_BARS: Generates deterministic raw OHLCV bars
        within requested time windows.
    """

    def __init__(self, config: MockFeedConfig | None = None) -> None:
        """Initialize feed with configuration.

        Args:
            config: Optional feed parameters.
        """
        self._config = config or MockFeedConfig()

    @override
    async def retrieve_bars(
        self,
        request: BrokerBarsRequest,
    ) -> Sequence[BrokerRawBar]:
        """Fetch synthetic raw historical bars for the requested window.

        Args:
            request: Raw bar query specification.

        Returns:
            Sequence of synthetic raw price bars.
        """
        if request.end <= request.start:
            return ()

        step = self._resolve_timeframe_step(request.timeframe)
        bars: list[BrokerRawBar] = []
        curr = request.start
        idx = 0
        base = self._config.base_price

        while curr < request.end:
            offset = math.sin(idx * 0.1) * 0.0050
            open_p = round(base + offset, 5)
            high_p = round(open_p + 0.0010, 5)
            low_p = round(open_p - 0.0008, 5)
            close_p = round(open_p + 0.0002, 5)
            vol = 100.0 + (idx % 20) * 10.0

            bar = BrokerRawBar(
                timestamp=curr,
                open_price=open_p,
                high_price=high_p,
                low_price=low_p,
                close_price=close_p,
                volume=vol,
            )
            bars.append(bar)
            curr += step
            idx += 1

            if len(bars) >= MAX_SYNTHETIC_BARS:
                break

        return bars

    def _resolve_timeframe_step(self, timeframe: str) -> timedelta:
        """Map timeframe string to timedelta step.

        Args:
            timeframe: Interval string identifier.

        Returns:
            Timedelta step interval.

        Raises:
            ValueError: If timeframe is not supported.
        """
        tf = timeframe.upper()
        if tf in SUPPORTED_TIMEFRAME_STEPS:
            return SUPPORTED_TIMEFRAME_STEPS[tf]

        allowed = sorted(SUPPORTED_TIMEFRAME_STEPS)
        msg = f"Unsupported timeframe: '{timeframe}'. Supported: {allowed}"
        raise ValueError(msg)
