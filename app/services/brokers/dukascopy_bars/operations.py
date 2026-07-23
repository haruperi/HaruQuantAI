# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""Dukascopy direct BID candle operations."""

from datetime import UTC, datetime

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapabilityId,
    BrokerPage,
    BrokerResult,
)
from app.services.brokers.dukascopy_ticks.candle_mapping import _map_candles


class _DukascopyBarsMixin:
    """Private provider operations owned by this feature."""

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerBar]]:
        """Return bounded provider BID candles from Dukascopy's web chart.

        Returns:
            Canonical BID candle page with explicit provider provenance.

        Raises:
            ValueError: If range, cursor, timeframe, or limit is invalid.
        """
        if (
            start is None
            or end is None
            or start.tzinfo is None
            or start.utcoffset() is None
            or end.tzinfo is None
            or end.utcoffset() is None
            or start >= end
        ):
            raise ValueError("explicit ordered Dukascopy bar range is required")
        if cursor is not None:
            raise ValueError("Dukascopy bar cursors are unsupported")
        if limit is None or limit <= 0:
            raise ValueError("positive Dukascopy bar limit is required")
        normalized_start = start.astimezone(UTC)
        normalized_end = end.astimezone(UTC)
        batch = await self._candle_transport.get_candles(
            symbol,
            timeframe,
            normalized_start,
            normalized_end,
            limit,
        )
        bars = _map_candles(
            batch.rows,
            symbol=symbol,
            timeframe=timeframe,
            start=normalized_start,
            end=normalized_end,
        )
        return self._result(
            BrokerCapabilityId.GET_HISTORICAL_BARS,
            data=BrokerPage(
                items=bars,
                limit=limit,
                truncated=batch.truncated,
                provider_metadata={
                    "provider": "dukascopy",
                    "endpoint": "web_chart_json3",
                    "provider_symbol": batch.provider_symbol,
                    "provider_interval": batch.provider_interval,
                    "offer_side": "BID",
                    "page_count": batch.page_count,
                    "research_only": True,
                },
            ),
        )
