"""Historical bars use case retrieving and coordinating bar data."""

from collections.abc import Sequence
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
    """Normalized historical bar retrieval service.

    Satisfies:
        FR-DATA-RETRIEVE_BARS: Validates query, calls broker market data contract,
        and normalizes resulting price bars.
    """

    def __init__(self, market_data: BrokerMarketData) -> None:
        """Initialize use case with broker market data provider.

        Args:
            market_data: Active broker market data provider satisfying BrokerMarketData.
        """
        self._market_data = market_data

    @override
    async def retrieve(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        """Validate request and retrieve normalized historical bars.

        Args:
            request: Historical bar query specifications.

        Returns:
            Sequence of canonical normalized Bar instances.
        """
        validate_historical_request(request)

        broker_req = BrokerBarsRequest(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
        )

        raw_bars = await self._market_data.retrieve_bars(broker_req)
        return normalize_bars(raw_bars)
