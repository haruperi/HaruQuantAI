"""Historical bars use case retrieving and coordinating bar data."""

from collections.abc import Sequence
from typing import override

from app.contracts.broker.market_data import BrokerBarsRequest, BrokerMarketData
from app.contracts.data.bar_cache import BarCache
from app.contracts.data.historical_bars import (
    Bar,
    HistoricalBars,
    HistoricalBarsRequest,
)
from app.services.data.historical_bars.normalize import normalize_bars
from app.services.data.historical_bars.validate_request import validate_historical_request


class HistoricalBarsService(HistoricalBars):
    """Normalized historical bar retrieval service with optional cache."""

    def __init__(
        self,
        market_data: BrokerMarketData,
        cache: BarCache | None = None,
    ) -> None:
        self._market_data = market_data
        self._cache = cache

    @override
    async def retrieve(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        """Validate, optionally load from cache, retrieve, normalize, and cache bars."""
        validate_historical_request(request)
        if self._cache is not None:
            cached = await self._cache.get_bars(request)
            if cached is not None:
                return cached

        broker_request = BrokerBarsRequest(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
        )
        raw_bars = await self._market_data.retrieve_bars(broker_request)
        bars = normalize_bars(raw_bars)
        if self._cache is not None:
            await self._cache.put_bars(request, bars)
        return bars
