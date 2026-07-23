"""Research-only Dukascopy canonical broker adapter."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Protocol, override

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerResult,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.dukascopy.candle_mapping import _map_candles
from app.services.brokers.dukascopy.candle_transport import (
    _CandleBatch,
    _DukascopyCandleTransport,
)
from app.services.brokers.dukascopy.instruments import (
    _INSTRUMENT_PRICE_DIVISORS,
    _price_divisor,
)
from app.services.brokers.dukascopy.mapping import _map_ticks
from app.services.brokers.dukascopy.transport import _DukascopyTransport


class _TickTransport(Protocol):
    """Structural transport required for Dukascopy tick reads."""

    async def get_hour(self, symbol: str, hour: datetime) -> bytes:
        """Return one decompressed BI5 hour payload."""
        ...


class _CandleTransport(Protocol):
    """Structural transport required for Dukascopy candle reads."""

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> _CandleBatch:
        """Return one bounded raw candle batch."""
        ...


class DukascopyBrokerAdapter(_UnsupportedAdapterBase):
    """Bounded genuine Dukascopy market-data adapter for sandbox research."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _TickTransport | None = None,
        candle_transport: _CandleTransport | None = None,
    ) -> None:
        """Initialize the DukascopyBrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            capabilities: Value supplied to the operation.
            transport: Value supplied to the operation.
            candle_transport: Optional web-chart candle transport.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if config.environment != BrokerEnvironment.SANDBOX:
            raise ValueError("Dukascopy is sandbox-only")
        if config.credentials or config.account_reference or config.endpoint:
            raise ValueError("Dukascopy accepts no credentials, account, or endpoint")
        super().__init__(config, capabilities)
        self._transport = transport or _DukascopyTransport(
            config, self._record_provider_latency
        )
        self._candle_transport = candle_transport or _DukascopyCandleTransport(
            config, self._record_provider_latency
        )

    @override
    async def connect(self) -> BrokerResult[None]:
        """Verify the provider by retrieving a bounded EURUSD hour file.

        Returns:
            Canonical verified connection result.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            probe_hour = datetime.now(UTC) - timedelta(hours=4)
            await self._transport.get_hour("EURUSD", probe_hour)
        except (OSError, TimeoutError, ValueError, ConnectionError) as error:
            await self._transition(
                BrokerConnectionState.FAILED, reason=type(error).__name__
            )
            return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    @override
    async def is_connected(self) -> BrokerResult[bool]:
        """Verify current reachability with one bounded provider hour probe.

        Returns:
            Canonical current connectivity evidence.
        """
        probe_hour = datetime.now(UTC) - timedelta(hours=4)
        await self._transport.get_hour("EURUSD", probe_hour)
        return self._result(BrokerCapabilityId.IS_CONNECTED, data=True)

    async def ping(self) -> BrokerResult[None]:
        """Run the same genuine bounded provider probe.

        Returns:
            Canonical provider-health result.
        """
        try:
            probe_hour = datetime.now(UTC) - timedelta(hours=4)
            await self._transport.get_hour("EURUSD", probe_hour)
        except OSError, TimeoutError, ValueError, ConnectionError:
            return self._unsupported(BrokerCapabilityId.PING)
        return self._result(BrokerCapabilityId.PING)

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerSymbolInfo]]:
        """Return only fixture-verified exact provider symbols."""
        del cursor
        symbols = tuple(
            symbol
            for symbol in _INSTRUMENT_PRICE_DIVISORS
            if query is None or query in symbol
        )
        bound = limit or len(symbols)
        items = tuple(self._symbol_info(symbol) for symbol in symbols[:bound])
        return self._result(
            BrokerCapabilityId.GET_SYMBOLS,
            data=BrokerPage(items=items, limit=max(1, bound)),
        )

    async def get_symbol_info(self, symbol: str) -> BrokerResult[BrokerSymbolInfo]:
        """Return structural metadata for one exact provider symbol."""
        _price_divisor(symbol)
        return self._result(
            BrokerCapabilityId.GET_SYMBOL_INFO, data=self._symbol_info(symbol)
        )

    def _symbol_info(self, symbol: str) -> BrokerSymbolInfo:
        """Handle symbol info.

        Args:
            symbol: Value supplied to the operation.

        Returns:
            The operation result.
        """
        return BrokerSymbolInfo(
            provider_symbol=symbol,
            product_profile="dukascopy_ticks",
            price_unit="quote_currency",
            quantity_unit="provider_volume",
        )

    async def get_ticks(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerTick]]:
        """Return genuine ticks from one caller-bounded provider hour file.

        Returns:
            Canonical bounded tick page.

        Raises:
            ValueError: If start or limit is invalid.
        """
        del end, cursor
        if start is None or limit is None or limit <= 0:
            raise ValueError("Dukascopy tick start and positive limit are required")
        payload = await self._transport.get_hour(symbol, start)
        ticks = _map_ticks(
            payload,
            symbol=symbol,
            hour=start,
            price_divisor=_price_divisor(symbol),
            limit=limit,
        )
        return self._result(
            BrokerCapabilityId.GET_TICKS,
            data=BrokerPage(
                items=ticks,
                limit=limit,
                truncated=len(payload) // 20 > len(ticks),
                provider_metadata={"provider": "dukascopy", "research_only": True},
            ),
        )

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

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]:
        """Return fixed redacted research-only provider metadata."""
        return self._result(
            BrokerCapabilityId.GET_PLATFORM_INFO,
            data=BrokerPlatformInfo(
                broker_id=self._config.broker_id,
                provider_name="Dukascopy",
                product_profile="tick_datafeed",
                environment=self._config.environment,
                observed_at=datetime.now(UTC),
                endpoint_metadata={"research_only": True},
            ),
        )
