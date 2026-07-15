"""Research-only Dukascopy canonical broker adapter."""

from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.brokers.contracts import (
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
from app.services.brokers.dukascopy.instruments import (
    _INSTRUMENT_PRICE_DIVISORS,
    _price_divisor,
)
from app.services.brokers.dukascopy.mapping import _map_ticks
from app.services.brokers.dukascopy.transport import _DukascopyTransport


class DukascopyBrokerAdapter(_UnsupportedAdapterBase):
    """Bounded genuine Dukascopy tick adapter for sandbox research."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _DukascopyTransport | None = None,
    ) -> None:
        if config.environment != BrokerEnvironment.SANDBOX:
            raise ValueError("Dukascopy is sandbox-only")
        if config.credentials or config.account_reference or config.endpoint:
            raise ValueError("Dukascopy accepts no credentials, account, or endpoint")
        super().__init__(config, capabilities)
        self._transport = transport or _DukascopyTransport(config)

    async def connect(self) -> BrokerResult[None]:
        """Verify the provider by retrieving a bounded EURUSD hour file."""
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            await self._transport.get_hour("EURUSD", datetime.now(UTC))
        except (OSError, TimeoutError, ValueError, ConnectionError) as error:
            await self._transition(
                BrokerConnectionState.FAILED, reason=type(error).__name__
            )
            return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    async def ping(self) -> BrokerResult[None]:
        """Run the same genuine bounded provider probe."""
        try:
            await self._transport.get_hour("EURUSD", datetime.now(UTC))
        except (OSError, TimeoutError, ValueError, ConnectionError):
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
        """Return genuine ticks from one caller-bounded provider hour file."""
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
