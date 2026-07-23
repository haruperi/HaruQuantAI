# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""cTrader market-data operations."""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import cast

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapabilityId,
    BrokerError,
    BrokerErrorCode,
    BrokerPage,
    BrokerQuote,
    BrokerResult,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import (
    _RequestValidationError,
)
from app.services.brokers.ctrader_session.mapping import (
    _field,
    _map_bar,
    _map_symbol,
    _map_ticks,
    _optional,
)


class _CTraderMarketDataMixin:
    """Private provider operations owned by this feature."""

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerSymbolInfo]]:
        """Return bounded exact cTrader symbols and provider specifications.

        Returns:
            Canonical symbol page.

        Raises:
            ValueError: If cursor or limit is invalid.
        """
        if cursor is not None:
            raise ValueError("cTrader symbol cursors are unsupported")
        if limit is None or limit <= 0:
            raise ValueError("positive cTrader symbol limit is required")
        await self._ensure_symbols()
        names = tuple(
            name for name in self._light_symbols if query is None or query in name
        )
        selected = names[:limit]
        mapped: list[BrokerSymbolInfo] = []
        for name in selected:
            mapped.append(await self._get_symbol_value(name))
        items = tuple(mapped)
        return self._result(
            BrokerCapabilityId.GET_SYMBOLS,
            data=BrokerPage(
                items=items,
                limit=limit,
                truncated=len(names) > limit,
            ),
        )

    async def get_symbol_info(self, symbol: str) -> BrokerResult[BrokerSymbolInfo]:
        """Return one exact cTrader symbol specification.

        Returns:
            Canonical symbol information or not-found error.
        """
        try:
            data = await self._get_symbol_value(symbol)
        except KeyError:
            return self._error(
                BrokerCapabilityId.GET_SYMBOL_INFO,
                BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND,
            )
        return self._result(BrokerCapabilityId.GET_SYMBOL_INFO, data=data)

    async def get_quote(self, symbol: str) -> BrokerResult[BrokerQuote]:
        """Return the next genuine cTrader spot event for one symbol.

        Returns:
            Canonical current quote.
        """
        try:
            subscription = await self._open_quote_subscription((symbol,))
        except KeyError:
            return self._error(
                BrokerCapabilityId.GET_QUOTE,
                BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND,
            )
        try:
            event = await asyncio.wait_for(
                anext(subscription.events()),
                timeout=self._config.request_timeout_sec,
            )
        finally:
            await subscription.unsubscribe()
        if isinstance(event, BrokerError):
            return self._result(BrokerCapabilityId.GET_QUOTE, error=event)
        return self._result(BrokerCapabilityId.GET_QUOTE, data=event)

    async def get_spread(self, symbol: str) -> BrokerResult[Decimal]:
        """Return the spread from one genuine cTrader spot event.

        Returns:
            Canonical quote-currency spread.
        """
        quote = await self.get_quote(symbol)
        if quote.error is not None:
            return self._result(BrokerCapabilityId.GET_SPREAD, error=quote.error)
        if quote.data is None or quote.data.bid is None or quote.data.ask is None:
            return self._error(
                BrokerCapabilityId.GET_SPREAD,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        return self._result(
            BrokerCapabilityId.GET_SPREAD, data=quote.data.ask - quote.data.bid
        )

    async def get_ticks(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerTick]]:
        """Return bounded merged cTrader BID and ASK tick history.

        Returns:
            Canonical tick page.

        Raises:
            ValueError: If range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        symbol_id, digits = await self._symbol_identity(symbol)
        base_fields = {
            "symbolId": symbol_id,
            "fromTimestamp": int(cast("datetime", start).timestamp() * 1000),
            "toTimestamp": int(cast("datetime", end).timestamp() * 1000),
        }
        bid = await self._request(
            "ProtoOAGetTickDataReq",
            "ProtoOAGetTickDataRes",
            **base_fields,
            type=1,
        )
        ask = await self._request(
            "ProtoOAGetTickDataReq",
            "ProtoOAGetTickDataRes",
            **base_fields,
            type=2,
        )
        bounded_limit = cast("int", limit)
        ticks = _map_ticks(
            _field(bid, "tickData"),
            _field(ask, "tickData"),
            symbol=symbol,
            digits=digits,
            limit=bounded_limit,
        )
        return self._result(
            BrokerCapabilityId.GET_TICKS,
            data=BrokerPage(
                items=ticks,
                limit=bounded_limit,
                truncated=bool(_optional(bid, "hasMore") or _optional(ask, "hasMore")),
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
        """Return bounded cTrader provider trendbars without resampling.

        Returns:
            Canonical provider bar page.

        Raises:
            ValueError: If range, cursor, limit, or timeframe is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        periods = {
            "M1": (1, 60),
            "M2": (2, 120),
            "M3": (3, 180),
            "M4": (4, 240),
            "M5": (5, 300),
            "M10": (6, 600),
            "M15": (7, 900),
            "M30": (8, 1800),
            "H1": (9, 3600),
            "H4": (10, 14400),
            "H12": (11, 43200),
            "D1": (12, 86400),
            "W1": (13, 604800),
        }
        normalized = timeframe.upper()
        try:
            period, duration = periods[normalized]
        except KeyError as error:
            raise ValueError("unsupported cTrader timeframe") from error
        symbol_id, digits = await self._symbol_identity(symbol)
        bounded_limit = cast("int", limit)
        response = await self._request(
            "ProtoOAGetTrendbarsReq",
            "ProtoOAGetTrendbarsRes",
            symbolId=symbol_id,
            fromTimestamp=int(cast("datetime", start).timestamp() * 1000),
            toTimestamp=int(cast("datetime", end).timestamp() * 1000),
            period=period,
            count=bounded_limit,
        )
        available = tuple(_field(response, "trendbar"))
        bars = tuple(
            _map_bar(
                value,
                symbol=symbol,
                digits=digits,
                timeframe=normalized,
                duration_seconds=duration,
            )
            for value in available[:bounded_limit]
        )
        return self._result(
            BrokerCapabilityId.GET_HISTORICAL_BARS,
            data=BrokerPage(
                items=bars,
                limit=bounded_limit,
                truncated=len(available) > bounded_limit,
            ),
        )

    async def _ensure_symbols(self) -> None:
        """Populate exact provider symbol identity caches once."""
        if self._light_symbols:
            return
        response = await self._request(
            "ProtoOASymbolsListReq",
            "ProtoOASymbolsListRes",
            includeArchivedSymbols=False,
        )
        for value in _field(response, "symbol"):
            name = str(_field(value, "symbolName"))
            symbol_id = int(_field(value, "symbolId"))
            self._light_symbols[name] = value
            self._symbol_names[symbol_id] = name

    async def _symbol_spec(self, symbol: str) -> object:
        """Return cached full provider specification for one exact symbol.

        Returns:
            Exact provider symbol payload.

        Raises:
            KeyError: If the provider does not report the exact symbol.
            ValueError: If the provider lot size is absent or invalid.
        """
        await self._ensure_symbols()
        if symbol not in self._light_symbols:
            raise KeyError(symbol)
        if symbol not in self._symbol_specs:
            symbol_id = int(_field(self._light_symbols[symbol], "symbolId"))
            response = await self._request(
                "ProtoOASymbolByIdReq",
                "ProtoOASymbolByIdRes",
                symbolId=(symbol_id,),
            )
            values = tuple(_field(response, "symbol"))
            if not values:
                raise KeyError(symbol)
            spec = values[0]
            lot_size = Decimal(str(_optional(spec, "lotSize") or 0))
            if lot_size <= 0:
                raise ValueError("cTrader symbol lotSize must be positive")
            self._symbol_specs[symbol] = spec
            self._symbol_lot_sizes[symbol_id] = lot_size
        return self._symbol_specs[symbol]

    async def _ensure_lot_sizes(self) -> None:
        """Load positive lot sizes for every cached provider symbol."""
        await self._ensure_symbols()
        for symbol in self._light_symbols:
            await self._symbol_spec(symbol)

    async def _provider_volume(self, symbol: str, quantity: Decimal) -> int:
        """Convert canonical lots to cTrader's native hundredths of a unit.

        Returns:
            Exact integral provider volume.

        Raises:
            _RequestValidationError: If the requested lots are not exactly
                representable before any provider transmission.
        """
        spec = await self._symbol_spec(symbol)
        lot_size = Decimal(str(_field(spec, "lotSize")))
        volume = quantity * lot_size * Decimal(100)
        integral = volume.to_integral_value()
        if volume != integral:
            raise _RequestValidationError(
                "quantity is not representable in cTrader volume cents"
            )
        return int(integral)

    async def _get_symbol_value(self, symbol: str) -> BrokerSymbolInfo:
        """Return one mapped exact provider symbol."""
        spec = await self._symbol_spec(symbol)
        return _map_symbol(
            spec,
            symbol_name=symbol,
            light=self._light_symbols[symbol],
        )

    async def _symbol_identity(self, symbol: str) -> tuple[int, int]:
        """Return provider symbol ID and verified price digits."""
        spec = await self._symbol_spec(symbol)
        return int(_field(spec, "symbolId")), int(_field(spec, "digits"))
