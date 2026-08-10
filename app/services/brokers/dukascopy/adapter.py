"""Read-only Dukascopy direct broker channel adapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, override

from app.services.brokers.canonical_contracts import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerSymbolInfo,
    BrokerTick,
    StandardResponse,
)
from app.services.brokers.canonical_contracts.protocols import _UnsupportedAdapterBase
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

    async def get_ticks(
        self, symbol: str, start: datetime, end: datetime, limit: int
    ) -> tuple[tuple[object, ...], ...]:
        """Return one bounded raw web-chart tick page.

        Args:
            symbol: Value supplied to the operation.
            start: Inclusive requested range boundary.
            end: Exclusive requested range boundary.
            limit: Positive maximum returned rows.

        Returns:
            Raw provider tick rows.
        """
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
        """Return one bounded raw candle batch.

        Args:
            symbol: Value supplied to the operation.
            timeframe: Value supplied to the operation.
            start: Value supplied to the operation.
            end: Value supplied to the operation.
            limit: Value supplied to the operation.
        """
        ...


from app.services.brokers.dukascopy.snapshots import (  # noqa: E402
    _DukascopyBarsMixin,
)


class DukascopyBrokerAdapter(_DukascopyBarsMixin, _UnsupportedAdapterBase):
    """Bounded genuine Dukascopy market-data adapter for sandbox research."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        *,
        transport: _TickTransport | None = None,
        candle_transport: _CandleTransport | None = None,
    ) -> None:
        """Initialize the DukascopyBrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            transport: Value supplied to the operation.
            candle_transport: Optional web-chart candle transport.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if config.environment != BrokerEnvironment.SANDBOX:
            raise ValueError("Dukascopy is sandbox-only")
        if config.credentials or config.account_reference or config.endpoint:
            raise ValueError("Dukascopy accepts no credentials, account, or endpoint")
        super().__init__(config)
        self._transport = transport or _DukascopyTransport(
            config, self._record_provider_latency
        )
        self._candle_transport = candle_transport or _DukascopyCandleTransport(
            config, self._record_provider_latency
        )

    async def _probe_provider(self) -> None:
        """Verify provider reachability with one genuine bounded candle read.

        Raises:
            ValueError: If Dukascopy returns no validated candle evidence.
            OSError: If the provider transport fails.
            TimeoutError: If the bounded provider request times out.
            ConnectionError: If the transport circuit rejects the request.
        """
        end = datetime.now(UTC)
        batch = await self._candle_transport.get_candles(
            "EURUSD",
            "H1",
            end - timedelta(days=7),
            end,
            1,
        )
        if not batch.rows:
            raise ValueError("Dukascopy readiness probe returned no candle evidence")

    @override
    async def connect(self) -> StandardResponse[None]:
        """Verify the provider through a bounded EUR/USD web-chart candle read.

        Returns:
            Canonical verified connection result.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            await self._probe_provider()
        except (OSError, TimeoutError, ValueError, ConnectionError) as error:
            await self._transition(
                BrokerConnectionState.FAILED, reason=type(error).__name__
            )
            return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    @override
    async def is_connected(self) -> StandardResponse[bool]:
        """Verify current reachability with one bounded provider candle probe.

        Returns:
            Canonical current connectivity evidence.
        """
        await self._probe_provider()
        return self._result(BrokerCapabilityId.IS_CONNECTED, data=True)

    async def ping(self) -> StandardResponse[None]:
        """Run the same genuine bounded provider probe.

        Returns:
            Canonical provider-health result.
        """
        try:
            await self._probe_provider()
        except OSError, TimeoutError, ValueError, ConnectionError:
            return self._unsupported(BrokerCapabilityId.PING)
        return self._result(BrokerCapabilityId.PING)

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> StandardResponse[BrokerPage[BrokerSymbolInfo]]:
        """Return only fixture-verified exact provider symbols.

        Args:
            query: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            StandardResponse[BrokerPage[BrokerSymbolInfo]]: The operation result.
        """
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

    async def get_symbol_info(self, symbol: str) -> StandardResponse[BrokerSymbolInfo]:
        """Return structural metadata for one exact provider symbol.

        Args:
            symbol: Value supplied to the operation.

        Returns:
            StandardResponse[BrokerSymbolInfo]: The operation result.
        """
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
    ) -> StandardResponse[BrokerPage[BrokerTick]]:
        """Return genuine ticks from one caller-bounded provider range.

        Args:
            symbol: Value supplied to the operation.
            start: Value supplied to the operation.
            end: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            Canonical bounded tick page.

        Raises:
            ValueError: If range or limit is invalid.
        """
        del cursor
        if start is None or end is None or limit is None or limit <= 0:
            raise ValueError("Dukascopy tick range and positive limit are required")
        rows = await self._transport.get_ticks(symbol, start, end, limit)
        ticks = _map_ticks(
            rows,
            symbol=symbol,
            start=start,
            end=end,
            limit=limit,
        )
        return self._result(
            BrokerCapabilityId.GET_TICKS,
            data=BrokerPage(
                items=ticks,
                limit=limit,
                truncated=len(rows) == limit,
                provider_metadata={
                    "provider": "dukascopy",
                    "endpoint": "web_chart_json3",
                    "provider_symbol": "EUR/USD",
                    "research_only": True,
                },
            ),
        )

    async def get_platform_info(self) -> StandardResponse[BrokerPlatformInfo]:
        """Return fixed redacted research-only provider metadata.

        Returns:
            StandardResponse[BrokerPlatformInfo]: The operation result.
        """
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
