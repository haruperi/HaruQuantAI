"""Canonical cTrader broker adapter."""

# ruff: noqa: A002 - public protocol signatures are normative.

import asyncio
import importlib
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType
from typing import cast, override

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerDeal,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerMarginRequest,
    BrokerOrder,
    BrokerOrderCheck,
    BrokerOrderFilter,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerResult,
    BrokerSubscription,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.ctrader.mapping import (
    _field,
    _map_bar,
    _map_deal,
    _map_error_code,
    _map_order,
    _map_order_result,
    _map_position,
    _map_quote,
    _map_symbol,
    _map_ticks,
    _optional,
)
from app.services.brokers.ctrader.network import _CTraderNetworkClient
from app.services.brokers.ctrader.transport import _CTraderTransport
from app.services.brokers.runtime.subscription import _BrokerSubscription
from app.utils import generate_id, utc_now


class CTraderBrokerAdapter(_UnsupportedAdapterBase):
    """One isolated cTrader application/account session."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _CTraderTransport | None = None,
    ) -> None:
        """Initialize the CTraderBrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            capabilities: Value supplied to the operation.
            transport: Value supplied to the operation.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if config.environment not in {BrokerEnvironment.LIVE, BrokerEnvironment.DEMO}:
            raise ValueError("cTrader requires LIVE or DEMO")
        if config.endpoint is not None:
            raise ValueError("cTrader custom endpoints are unavailable")
        required = {"client_id", "client_secret", "access_token", "account_id"}
        if config.credentials is None or not required <= set(config.credentials):
            raise ValueError("resolved cTrader credentials are incomplete")
        if (
            config.account_reference
            != config.credentials["account_id"].get_secret_value()
        ):
            raise ValueError("cTrader account_reference must match account_id")
        super().__init__(config, capabilities)
        if transport is not None:
            self._transport = transport
            self._network: _CTraderNetworkClient | None = None
        else:
            network = _CTraderNetworkClient(config)
            self._network = network
            self._transport = _CTraderTransport(
                config,
                sender=network.send,
                register_event_handler=network.add_event_handler,
                unregister_event_handler=network.remove_event_handler,
            )
        self._messages: ModuleType | None = None
        self._light_symbols: dict[str, object] = {}
        self._symbol_names: dict[int, str] = {}
        self._symbol_specs: dict[str, object] = {}
        self._symbol_lot_sizes: dict[int, Decimal] = {}
        self._subscriptions: dict[str, _BrokerSubscription[BrokerQuote]] = {}
        self._event_handler_registered = False
        self._publish_tasks: set[asyncio.Task[bool]] = set()

    @override
    async def connect(self) -> BrokerResult[None]:
        """Require application/account authentication transport evidence.

        Returns:
            Canonical verified connection result.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            if self._network is not None:
                await self._network.connect()
            verified = await self._transport.connect()
        except (
            ConnectionError,
            TimeoutError,
            OSError,
            ImportError,
            ValueError,
        ) as error:
            verified = False
            self._last_error = BrokerError(
                code=BrokerErrorCode.BROKER_CONNECTION_FAILED,
                message="cTrader connection verification failed",
                provider_message=type(error).__name__,
            )
        if not verified:
            await self._transition(
                BrokerConnectionState.FAILED, reason="auth_unverified"
            )
            if self._last_error is not None:
                return self._result(BrokerCapabilityId.CONNECT, error=self._last_error)
            return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    @override
    async def disconnect(self) -> BrokerResult[None]:
        """Release the exact owned cTrader session.

        Returns:
            Canonical idempotent disconnection result.
        """
        for subscription in tuple(self._subscriptions.values()):
            await subscription.unsubscribe()
        if self._event_handler_registered:
            self._transport.unregister_event_handler(self._on_provider_event)
            self._event_handler_registered = False
        await self._transport.close()
        if self._network is not None:
            await self._network.close()
        return await super().disconnect()

    @override
    async def is_connected(self) -> BrokerResult[bool]:
        """Verify current account reachability with one reconcile request.

        Returns:
            Canonical current connectivity evidence.
        """
        await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        return self._result(BrokerCapabilityId.IS_CONNECTED, data=True)

    async def ping(self) -> BrokerResult[None]:
        """Verify current account reachability without mutation.

        Returns:
            Canonical provider-health result.
        """
        await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        return self._result(BrokerCapabilityId.PING)

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]:
        """Return redacted endpoint/environment metadata."""
        endpoint = (
            "live.ctraderapi.com:5035"
            if self._config.environment == BrokerEnvironment.LIVE
            else "demo.ctraderapi.com:5035"
        )
        return self._result(
            BrokerCapabilityId.GET_PLATFORM_INFO,
            data=BrokerPlatformInfo(
                broker_id=self._config.broker_id,
                provider_name="cTrader Open API",
                product_profile="ctrader",
                environment=self._config.environment,
                observed_at=datetime.now(UTC),
                endpoint_metadata={"endpoint": endpoint},
            ),
        )

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

    async def get_positions(
        self,
        filter: BrokerPositionFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerPosition]]:
        """Return bounded reconciled cTrader positions.

        Returns:
            Canonical position page.

        Raises:
            ValueError: If cursor or limit is invalid.
        """
        self._validate_page(cursor, limit)
        await self._ensure_lot_sizes()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        mapped = tuple(
            _map_position(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "position")
        )
        if filter and filter.symbol:
            mapped = tuple(item for item in mapped if item.symbol == filter.symbol)
        if filter and filter.side:
            mapped = tuple(item for item in mapped if item.side == filter.side)
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.GET_POSITIONS,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=len(mapped) > bounded_limit,
            ),
        )

    async def get_orders(
        self,
        filter: BrokerOrderFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return bounded reconciled cTrader orders.

        Returns:
            Canonical order page.

        Raises:
            ValueError: If cursor or limit is invalid.
        """
        self._validate_page(cursor, limit)
        await self._ensure_lot_sizes()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        mapped = tuple(
            _map_order(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "order")
        )
        if filter and filter.symbol:
            mapped = tuple(item for item in mapped if item.symbol == filter.symbol)
        if filter and filter.side:
            mapped = tuple(item for item in mapped if item.side == filter.side)
        if filter and filter.status:
            mapped = tuple(item for item in mapped if item.state == filter.status)
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.GET_ORDERS,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=len(mapped) > bounded_limit,
            ),
        )

    async def list_order_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return bounded cTrader historical orders.

        Returns:
            Canonical historical-order page.

        Raises:
            ValueError: If range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        await self._ensure_lot_sizes()
        response = await self._request(
            "ProtoOAOrderListReq",
            "ProtoOAOrderListRes",
            fromTimestamp=int(cast("datetime", start).timestamp() * 1000),
            toTimestamp=int(cast("datetime", end).timestamp() * 1000),
        )
        mapped = tuple(
            _map_order(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "order")
        )
        if symbol is not None:
            mapped = tuple(item for item in mapped if item.symbol == symbol)
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.LIST_ORDER_HISTORY,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=bool(_optional(response, "hasMore"))
                or len(mapped) > bounded_limit,
            ),
        )

    async def list_deal_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerDeal]]:
        """Return bounded cTrader execution deals.

        Returns:
            Canonical deal page.

        Raises:
            ValueError: If range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        await self._ensure_lot_sizes()
        bounded_limit = cast("int", limit)
        response = await self._request(
            "ProtoOADealListReq",
            "ProtoOADealListRes",
            fromTimestamp=int(cast("datetime", start).timestamp() * 1000),
            toTimestamp=int(cast("datetime", end).timestamp() * 1000),
            maxRows=bounded_limit,
        )
        mapped = tuple(
            _map_deal(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "deal")
        )
        if symbol is not None:
            mapped = tuple(item for item in mapped if item.symbol == symbol)
        return self._result(
            BrokerCapabilityId.LIST_DEAL_HISTORY,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=bool(_optional(response, "hasMore"))
                or len(mapped) > bounded_limit,
            ),
        )

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderCheck]:
        """Validate symbol and obtain provider expected-margin evidence.

        Returns:
            Canonical non-final order check.
        """
        margin = await self.calculate_margin(
            BrokerMarginRequest(
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                quantity_unit=request.quantity_unit,
                product_profile="ctrader",
                account_reference=request.account_reference,
            )
        )
        if margin.error is not None:
            return self._result(BrokerCapabilityId.CHECK_ORDER, error=margin.error)
        return self._result(
            BrokerCapabilityId.CHECK_ORDER,
            data=BrokerOrderCheck(
                accepted_for_submission=True,
                estimated_margin=margin.data,
            ),
        )

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Submit exactly one cTrader order without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        symbol_id, _digits = await self._symbol_identity(request.symbol)
        order_types = {"MARKET": 1, "LIMIT": 2, "STOP": 3, "STOP_LIMIT": 6}
        fields: dict[str, object] = {
            "symbolId": symbol_id,
            "orderType": order_types[request.order_type],
            "tradeSide": 1 if request.side == "BUY" else 2,
            "volume": await self._provider_volume(request.symbol, request.quantity),
        }
        self._copy_order_fields(fields, request)
        return await self._execution(
            BrokerCapabilityId.PLACE_ORDER,
            "ProtoOANewOrderReq",
            fallback_id=None,
            **fields,
        )

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Modify exactly one cTrader order without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        fields: dict[str, object] = {"orderId": int(request.order_id)}
        if request.quantity is not None:
            symbol = await self._symbol_for_order(request.order_id)
            fields["volume"] = await self._provider_volume(symbol, request.quantity)
        self._copy_order_fields(fields, request)
        return await self._execution(
            BrokerCapabilityId.MODIFY_ORDER,
            "ProtoOAAmendOrderReq",
            fallback_id=request.order_id,
            **fields,
        )

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> BrokerResult[BrokerOrderResult]:
        """Cancel exactly one cTrader order without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        del client_request_id
        return await self._execution(
            BrokerCapabilityId.CANCEL_ORDER,
            "ProtoOACancelOrderReq",
            fallback_id=order_id,
            orderId=int(order_id),
        )

    async def modify_position(
        self, request: BrokerPositionModificationRequest
    ) -> BrokerResult[BrokerPosition]:
        """Modify one cTrader position and return refreshed provider state.

        Returns:
            Canonical refreshed position.
        """
        fields: dict[str, object] = {"positionId": int(request.position_id)}
        self._copy_order_fields(fields, request)
        execution = await self._execution(
            BrokerCapabilityId.MODIFY_POSITION,
            "ProtoOAAmendPositionSLTPReq",
            fallback_id=request.position_id,
            **fields,
        )
        if execution.error is not None:
            return self._result(
                BrokerCapabilityId.MODIFY_POSITION, error=execution.error
            )
        positions = await self.get_positions(limit=100)
        if positions.data is not None:
            for position in positions.data.items:
                if position.position_id == request.position_id:
                    return self._result(
                        BrokerCapabilityId.MODIFY_POSITION, data=position
                    )
        return self._error(
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerErrorCode.BROKER_RESPONSE_INVALID,
        )

    async def close_position(
        self, request: BrokerPositionCloseRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Close or reduce exactly one cTrader position without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        symbol = await self._symbol_for_position(request.position_id)
        return await self._execution(
            BrokerCapabilityId.CLOSE_POSITION,
            "ProtoOAClosePositionReq",
            fallback_id=request.position_id,
            positionId=int(request.position_id),
            volume=await self._provider_volume(symbol, request.quantity),
        )

    async def calculate_margin(
        self, request: BrokerMarginRequest
    ) -> BrokerResult[Decimal]:
        """Return cTrader's expected margin for one candidate volume.

        Returns:
            Canonical account-currency margin.
        """
        symbol_id, _digits = await self._symbol_identity(request.symbol)
        response = await self._request(
            "ProtoOAExpectedMarginReq",
            "ProtoOAExpectedMarginRes",
            symbolId=symbol_id,
            volume=(await self._provider_volume(request.symbol, request.quantity),),
        )
        margins = tuple(_field(response, "margin"))
        if not margins:
            return self._error(
                BrokerCapabilityId.CALCULATE_MARGIN,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        value = _field(
            margins[0], "buyMargin" if request.side == "BUY" else "sellMargin"
        )
        divisor = Decimal(10) ** int(_field(response, "moneyDigits"))
        return self._result(
            BrokerCapabilityId.CALCULATE_MARGIN,
            data=Decimal(str(value)) / divisor,
        )

    async def calculate_profit(
        self, request: BrokerProfitRequest
    ) -> BrokerResult[Decimal]:
        """Calculate profit from provider lot-size and exact request prices.

        Returns:
            Canonical quote-currency profit evidence.
        """
        spec = await self._symbol_spec(request.symbol)
        lot_size = _optional(spec, "lotSize")
        if lot_size is None:
            return self._error(
                BrokerCapabilityId.CALCULATE_PROFIT,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        difference = (
            request.close_price - request.open_price
            if request.side == "BUY"
            else request.open_price - request.close_price
        )
        return self._result(
            BrokerCapabilityId.CALCULATE_PROFIT,
            data=difference * request.quantity * Decimal(str(lot_size)),
        )

    async def subscribe_quotes(
        self, symbols: tuple[str, ...]
    ) -> BrokerResult[BrokerSubscription[BrokerQuote]]:
        """Open one bounded cTrader spot-event subscription.

        Returns:
            Adapter-owned canonical quote subscription.
        """
        subscription = await self._open_quote_subscription(symbols)
        return self._result(BrokerCapabilityId.SUBSCRIBE_QUOTES, data=subscription)

    async def unsubscribe(self, subscription_id: str) -> BrokerResult[None]:
        """Close one exact adapter-owned cTrader subscription.

        Returns:
            Canonical unsubscribe result or not-found error.
        """
        subscription = self._subscriptions.get(subscription_id)
        if subscription is None:
            return self._error(
                BrokerCapabilityId.UNSUBSCRIBE,
                BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND,
            )
        await subscription.unsubscribe()
        return self._result(BrokerCapabilityId.UNSUBSCRIBE)

    async def list_subscriptions(
        self,
    ) -> BrokerResult[tuple[BrokerSubscriptionInfo, ...]]:
        """Return immutable cTrader subscription metadata.

        Returns:
            Current adapter-owned subscriptions.
        """
        return self._result(
            BrokerCapabilityId.LIST_SUBSCRIPTIONS,
            data=tuple(item.info for item in self._subscriptions.values()),
        )

    def _message_module(self) -> ModuleType:
        """Load the pinned cTrader protobuf message module lazily.

        Returns:
            Provider protobuf module.
        """
        if self._messages is None:
            self._messages = importlib.import_module(
                "ctrader_open_api.messages.OpenApiMessages_pb2"
            )
        return self._messages

    async def _request(
        self, request_name: str, response_name: str, **fields: object
    ) -> object:
        """Send one typed cTrader request through the correlated transport.

        Returns:
            Exact typed provider response.
        """
        messages = self._message_module()
        request = getattr(messages, request_name)()
        request.ctidTraderAccountId = int(cast("str", self._config.account_reference))
        for name, value in fields.items():
            target = getattr(request, name)
            if isinstance(value, tuple):
                target.extend(value)
            else:
                setattr(request, name, value)
        return await self._transport.send(request, getattr(messages, response_name))

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
            ValueError: If the requested lots are not exactly representable.
        """
        spec = await self._symbol_spec(symbol)
        lot_size = Decimal(str(_field(spec, "lotSize")))
        volume = quantity * lot_size * Decimal(100)
        integral = volume.to_integral_value()
        if volume != integral:
            raise ValueError("quantity is not representable in cTrader volume cents")
        return int(integral)

    async def _symbol_for_order(self, order_id: str) -> str:
        """Resolve an active order's provider symbol without mutation.

        Returns:
            Exact provider symbol name.

        Raises:
            KeyError: If the active order is absent.
        """
        await self._ensure_symbols()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        for order in _field(response, "order"):
            if str(_field(order, "orderId")) == order_id:
                trade = _field(order, "tradeData")
                return self._symbol_names[int(_field(trade, "symbolId"))]
        raise KeyError(order_id)

    async def _symbol_for_position(self, position_id: str) -> str:
        """Resolve an active position's provider symbol without mutation.

        Returns:
            Exact provider symbol name.

        Raises:
            KeyError: If the active position is absent.
        """
        await self._ensure_symbols()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        for position in _field(response, "position"):
            if str(_field(position, "positionId")) == position_id:
                trade = _field(position, "tradeData")
                return self._symbol_names[int(_field(trade, "symbolId"))]
        raise KeyError(position_id)

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

    async def _open_quote_subscription(
        self, symbols: tuple[str, ...]
    ) -> _BrokerSubscription[BrokerQuote]:
        """Open one provider spot subscription and bind local delivery.

        Returns:
            Adapter-owned bounded quote subscription.

        Raises:
            ValueError: If symbols are empty or duplicated.
        """
        if not symbols or len(set(symbols)) != len(symbols):
            raise ValueError("cTrader subscription symbols must be unique")
        identities = [await self._symbol_identity(symbol) for symbol in symbols]
        symbol_ids = tuple(item[0] for item in identities)
        await self._request(
            "ProtoOASubscribeSpotsReq",
            "ProtoOASubscribeSpotsRes",
            symbolId=symbol_ids,
            subscribeToSpotTimestamp=True,
        )
        if not self._event_handler_registered:
            self._transport.register_event_handler(self._on_provider_event)
            self._event_handler_registered = True
        subscription_id = generate_id("evt")

        async def _close() -> None:
            """Handle close."""
            await self._request(
                "ProtoOAUnsubscribeSpotsReq",
                "ProtoOAUnsubscribeSpotsRes",
                symbolId=symbol_ids,
            )
            self._subscriptions.pop(subscription_id, None)

        subscription = _BrokerSubscription[BrokerQuote](
            broker=self._config.broker_id,
            environment=self._config.environment,
            adapter_version=self.ADAPTER_VERSION,
            info=BrokerSubscriptionInfo(
                subscription_id=subscription_id,
                capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
                symbols=symbols,
                created_at=utc_now(),
                buffer_size=self._config.stream_buffer_size,
            ),
            unsubscribe_callback=_close,
        )
        self._subscriptions[subscription_id] = subscription
        return subscription

    def _on_provider_event(self, event: object) -> None:
        """Map and dispatch one cTrader spot event without blocking callback IO."""
        if type(event).__name__ != "ProtoOASpotEvent":
            return
        symbol_id = int(_field(event, "symbolId"))
        symbol = self._symbol_names.get(symbol_id)
        spec = self._symbol_specs.get(symbol or "")
        if symbol is None or spec is None:
            return
        quote = _map_quote(event, symbol, int(_field(spec, "digits")))
        for subscription in tuple(self._subscriptions.values()):
            if symbol in subscription.info.symbols:
                task = asyncio.create_task(subscription.publish(quote))
                self._publish_tasks.add(task)
                task.add_done_callback(self._publish_tasks.discard)

    async def _execution(
        self,
        operation: BrokerCapabilityId,
        request_name: str,
        *,
        fallback_id: str | None = None,
        **fields: object,
    ) -> BrokerResult[BrokerOrderResult]:
        """Send one cTrader mutation once and classify its execution event.

        Returns:
            Canonical acknowledged mutation result or provider rejection.
        """
        event = await self._request(request_name, "ProtoOAExecutionEvent", **fields)
        result = _map_order_result(event, fallback_id)
        if result.outcome == "REJECTED":
            code = str(result.provider_code or "PROVIDER_ERROR")
            return self._error(operation, _map_error_code(code, operation.value))
        return self._result(operation, data=result)

    @staticmethod
    def _copy_order_fields(fields: dict[str, object], request: object) -> None:
        """Copy only explicitly supplied cTrader order fields."""
        for canonical, provider in (
            ("limit_price", "limitPrice"),
            ("stop_price", "stopPrice"),
            ("stop_loss", "stopLoss"),
            ("take_profit", "takeProfit"),
        ):
            value = getattr(request, canonical, None)
            if value is not None:
                fields[provider] = float(value)
        expiration = getattr(request, "expiration", None)
        if expiration is not None:
            fields["expirationTimestamp"] = int(expiration.timestamp() * 1000)
        for canonical, provider in (
            ("comment", "comment"),
            ("label", "label"),
            ("client_order_id", "clientOrderId"),
        ):
            value = getattr(request, canonical, None)
            if value is not None:
                fields[provider] = value

    @staticmethod
    def _validate_page(cursor: str | None, limit: int | None) -> None:
        """Validate bounded cTrader page arguments before provider access.

        Raises:
            ValueError: If cursor is supplied or limit is not positive.
        """
        if cursor is not None:
            raise ValueError("cTrader cursors are unsupported")
        if limit is None or limit <= 0:
            raise ValueError("positive cTrader page limit is required")

    @classmethod
    def _validate_history(
        cls,
        start: datetime | None,
        end: datetime | None,
        cursor: str | None,
        limit: int | None,
    ) -> None:
        """Validate explicit bounded cTrader history arguments.

        Raises:
            ValueError: If range, cursor, or limit is invalid.
        """
        cls._validate_page(cursor, limit)
        if (
            start is None
            or end is None
            or start.tzinfo is None
            or start.utcoffset() is None
            or end.tzinfo is None
            or end.utcoffset() is None
            or start >= end
        ):
            raise ValueError("explicit ordered UTC-aware history range is required")

    def _error[T](
        self, operation: BrokerCapabilityId, code: BrokerErrorCode
    ) -> BrokerResult[T]:
        """Build one canonical cTrader failure result.

        Returns:
            Canonical error result.
        """
        error = BrokerError(
            code=code,
            message=f"cTrader {operation.value} failed",
            capability=operation,
        )
        self._last_error = error
        return self._result(operation, error=error)
