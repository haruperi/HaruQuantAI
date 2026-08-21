"""Historical bars use case retrieving and normalizing broker data."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import override

from app.contracts.broker.market_data import BrokerBarsRequest, BrokerMarketData
from app.contracts.data.historical_bars import (
    Bar,
    HistoricalBars,
    HistoricalBarsRequest,
)
from app.services.data.historical_bars.normalize import normalize_bars
from app.services.data.historical_bars.validate_request import (
    validate_historical_request,
)


class HistoricalBarsService(HistoricalBars):
    """Validate, retrieve, and normalize historical OHLCV bars."""

    def __init__(
        self,
        market_data: BrokerMarketData,
        default_timeframe: str = "M1",
    ) -> None:
        """Initialize the use case with its provider and fallback timeframe."""
        self._market_data = market_data
        self._default_timeframe = default_timeframe

    @override
    async def retrieve(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        """Retrieve normalized bars, applying the configured blank-timeframe fallback."""
        effective_request = (
            request
            if request.timeframe.strip()
            else replace(request, timeframe=self._default_timeframe)
        )
        validate_historical_request(effective_request)
        raw_bars = await self._market_data.retrieve_bars(
            BrokerBarsRequest(
                symbol=effective_request.symbol,
                timeframe=effective_request.timeframe,
                start=effective_request.start,
                end=effective_request.end,
            )
        )
        return normalize_bars(raw_bars)
