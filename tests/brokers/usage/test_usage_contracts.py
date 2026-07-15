"""Runnable public usage examples for the canonical broker boundary."""

import asyncio
import importlib
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import TracebackType
from typing import Self, cast

from app.services.brokers import (
    AccountProvider,
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAdapter,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionState,
    BrokerConnectionStatus,
    BrokerDeal,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerFeatureFlags,
    BrokerFeeEstimate,
    BrokerId,
    BrokerMarginRequest,
    BrokerMarketStatus,
    BrokerOrder,
    BrokerOrderBook,
    BrokerOrderCheck,
    BrokerOrderFilter,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerResult,
    BrokerServerTime,
    BrokerSubscription,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
    CalculationProvider,
    MarketDataProvider,
    TradeExecutionProvider,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
LATER = NOW + timedelta(seconds=1)
D = Decimal


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        capability: BrokerCapability(
            capability=capability,
            implementation_status="NOT_IMPLEMENTED",
            availability="UNAVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="NO_PROVIDER_CALL",
            reason="usage example",
        )
        for capability in BrokerCapabilityId
    }


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


class _ExampleAdapter:
    """Self-contained public-contract example with no provider dependency."""

    contract_version = "v1"
    schema_id = "brokers.adapter.v1"

    def _success[T](
        self, operation: BrokerCapabilityId, data: T | None = None
    ) -> BrokerResult[T]:
        return BrokerResult(
            status="success",
            broker=BrokerId.YAHOO,
            operation=operation,
            request_id="usage",
            timestamp=NOW,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="usage",
            data=data,
        )

    def _unsupported(self, operation: BrokerCapabilityId) -> BrokerResult[object]:
        return BrokerResult(
            status="error",
            broker=BrokerId.YAHOO,
            operation=operation,
            request_id="usage",
            timestamp=NOW,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="usage",
            error=BrokerError(
                code=BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
                message="Capability is unavailable in this provider-free example",
                capability=operation,
            ),
        )

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc, traceback
        await self.disconnect()

    async def connect(self) -> BrokerResult[None]:
        return self._success(BrokerCapabilityId.CONNECT)

    async def disconnect(self) -> BrokerResult[None]:
        return self._success(BrokerCapabilityId.DISCONNECT)

    async def reconnect(self) -> BrokerResult[None]:
        await self.disconnect()
        return await self.connect()

    async def is_connected(self) -> BrokerResult[bool]:
        return self._success(BrokerCapabilityId.IS_CONNECTED, False)

    async def get_connection_status(self) -> BrokerResult[BrokerConnectionStatus]:
        return self._success(
            BrokerCapabilityId.GET_CONNECTION_STATUS,
            BrokerConnectionStatus(
                state=BrokerConnectionState.DISCONNECTED,
                transport_connected=False,
                environment=BrokerEnvironment.SANDBOX,
                session_generation=0,
                observed_at=NOW,
            ),
        )

    async def get_last_error(self) -> BrokerResult[BrokerError | None]:
        return self._success(BrokerCapabilityId.GET_LAST_ERROR)

    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]:
        async def _events() -> AsyncIterator[BrokerConnectionEvent]:
            yield BrokerConnectionEvent(
                previous_state=BrokerConnectionState.DISCONNECTED,
                new_state=BrokerConnectionState.CONNECTING,
                timestamp=NOW,
                session_generation=0,
            )

        return _events()

    async def get_feature_flags(self) -> BrokerResult[BrokerFeatureFlags]:
        return self._success(
            BrokerCapabilityId.GET_FEATURE_FLAGS,
            BrokerFeatureFlags(
                broker_id=BrokerId.YAHOO,
                environment=BrokerEnvironment.SANDBOX,
                generated_at=NOW,
                capabilities=_capabilities(),
                adapter_version="usage",
            ),
        )

    async def supports(self, capability: BrokerCapabilityId) -> BrokerResult[bool]:
        del capability
        return self._success(BrokerCapabilityId.SUPPORTS, False)

    def __getattr__(self, name: str) -> Callable[..., Awaitable[BrokerResult[object]]]:
        try:
            operation = BrokerCapabilityId(name)
        except ValueError as error:
            raise AttributeError(name) from error

        async def _call(*args: object, **kwargs: object) -> BrokerResult[object]:
            del args, kwargs
            return self._unsupported(operation)

        return _call


def _fake() -> _ExampleAdapter:
    return _ExampleAdapter()


def _operation(operation: BrokerCapabilityId) -> BrokerResult[object]:
    adapter = _fake()

    async def _call() -> BrokerResult[object]:
        method = getattr(adapter, operation.value)
        return cast("BrokerResult[object]", await method())

    result = asyncio.run(_call())
    assert result.operation is operation
    return result


def _build_models() -> dict[str, object]:
    capabilities = _capabilities()
    return {
        "connection_config": _config(),
        "error": BrokerError(
            code=BrokerErrorCode.BROKER_TIMEOUT, message="provider timeout"
        ),
        "result": BrokerResult[None](
            status="success",
            broker=BrokerId.YAHOO,
            operation=BrokerCapabilityId.DISCONNECT,
            request_id="usage",
            timestamp=NOW,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1",
        ),
        "page": BrokerPage(items=("EURUSD",), limit=1),
        "capability": capabilities[BrokerCapabilityId.GET_QUOTE],
        "feature_flags": BrokerFeatureFlags(
            broker_id=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            generated_at=NOW,
            capabilities=capabilities,
            adapter_version="1",
        ),
        "connection_status": BrokerConnectionStatus(
            state=BrokerConnectionState.DISCONNECTED,
            transport_connected=False,
            environment=BrokerEnvironment.SANDBOX,
            session_generation=0,
            observed_at=NOW,
        ),
        "connection_event": BrokerConnectionEvent(
            previous_state=BrokerConnectionState.DISCONNECTED,
            new_state=BrokerConnectionState.CONNECTING,
            timestamp=NOW,
            session_generation=0,
        ),
        "platform_info": BrokerPlatformInfo(
            broker_id=BrokerId.YAHOO,
            provider_name="Yahoo",
            product_profile="historical",
            environment=BrokerEnvironment.SANDBOX,
            observed_at=NOW,
        ),
        "permissions": BrokerPermissions(observed_at=NOW),
        "account_info": BrokerAccountInfo(account_id="account", retrieved_at=NOW),
        "balance": BrokerBalance(asset="USD", unit="USD", retrieved_at=NOW),
        "asset_info": BrokerAssetInfo(asset_id="USD"),
        "symbol_info": BrokerSymbolInfo(
            provider_symbol="EURUSD",
            product_profile="spot",
            price_unit="USD",
            quantity_unit="lot",
        ),
        "market_status": BrokerMarketStatus(
            symbol="EURUSD", status="UNKNOWN", retrieved_at=NOW
        ),
        "trading_session": BrokerTradingSession(
            symbol="EURUSD", opens_at=NOW, closes_at=LATER
        ),
        "quote": BrokerQuote(
            symbol="EURUSD",
            price_unit="USD",
            quantity_unit="lot",
            retrieved_at=NOW,
            bid=D("1"),
        ),
        "tick": BrokerTick(
            symbol="EURUSD",
            event_timestamp=NOW,
            provider_receipt_timestamp=LATER,
            price_unit="USD",
            quantity_unit="lot",
            bid=D("1"),
        ),
        "bar": BrokerBar(
            symbol="EURUSD",
            opening_timestamp=NOW,
            closing_timestamp=LATER,
            is_closed=True,
            open=D("1"),
            high=D("2"),
            low=D("0.5"),
            close=D("1.5"),
            provider_timeframe="1m",
            requested_timeframe="1m",
            price_unit="USD",
            quantity_unit="lot",
        ),
        "order_book": BrokerOrderBook(
            symbol="EURUSD",
            bids=((D("1"), D("1")),),
            asks=((D("2"), D("1")),),
            is_snapshot=True,
            resnapshot_required=False,
            event_timestamp=NOW,
            price_unit="USD",
            quantity_unit="lot",
        ),
        "subscription_info": BrokerSubscriptionInfo(
            subscription_id="subscription",
            capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
            symbols=("EURUSD",),
            created_at=NOW,
            buffer_size=2,
        ),
        "position": BrokerPosition(
            position_id="position",
            symbol="EURUSD",
            side="LONG",
            quantity=D("1"),
            quantity_unit="lot",
            retrieved_at=NOW,
        ),
        "order_filter": BrokerOrderFilter(symbol="EURUSD"),
        "position_filter": BrokerPositionFilter(symbol="EURUSD"),
        "order": BrokerOrder(
            order_id="order",
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            state="OPEN",
            quantity=D("1"),
            filled=D("0"),
            remaining=D("1"),
            quantity_unit="lot",
            retrieved_at=NOW,
        ),
        "deal": BrokerDeal(
            deal_id="deal",
            symbol="EURUSD",
            side="BUY",
            quantity=D("1"),
            quantity_unit="lot",
            price=D("1"),
            partial=False,
            retrieved_at=NOW,
        ),
        "account_transaction": BrokerAccountTransaction(
            transaction_id="transaction",
            transaction_type="DEPOSIT",
            asset="USD",
            currency="USD",
            amount=D("1"),
            provider_timestamp=NOW,
            retrieved_at=LATER,
        ),
        "order_request": BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=D("1"),
            quantity_unit="lot",
            environment=BrokerEnvironment.DEMO,
        ),
        "order_modification": BrokerOrderModificationRequest(
            order_id="order", quantity=D("2")
        ),
        "order_check": BrokerOrderCheck(accepted_for_submission=True),
        "order_result": BrokerOrderResult(
            acknowledged=True,
            outcome="ACCEPTED",
            order_id="order",
            retrieved_at=NOW,
        ),
        "position_modification": BrokerPositionModificationRequest(
            position_id="position", stop_loss=D("1")
        ),
        "position_close": BrokerPositionCloseRequest(
            position_id="position", quantity=D("1"), quantity_unit="lot"
        ),
        "margin_request": BrokerMarginRequest(
            symbol="EURUSD",
            side="BUY",
            quantity=D("1"),
            quantity_unit="lot",
            product_profile="spot",
        ),
        "profit_request": BrokerProfitRequest(
            symbol="EURUSD",
            side="BUY",
            quantity=D("1"),
            quantity_unit="lot",
            open_price=D("1"),
            close_price=D("2"),
            product_profile="spot",
        ),
        "fee_estimate": BrokerFeeEstimate(amount=D("1"), currency_or_unit="USD"),
        "server_time": BrokerServerTime(
            provider_time=NOW,
            local_send_time=NOW,
            local_receive_time=LATER,
            estimated_clock_offset_ms=0,
            round_trip_latency_ms=1000,
        ),
    }


MODELS = _build_models()


def _model(name: str, expected_type: type[object]) -> None:
    assert isinstance(MODELS[name], expected_type)


def test_usage_enums_broker_id() -> None:
    assert BrokerId.MT5.value == "mt5"


def test_usage_enums_environment() -> None:
    assert {BrokerEnvironment.DEMO, BrokerEnvironment.LIVE} <= set(BrokerEnvironment)


def test_usage_enums_connection_state() -> None:
    assert BrokerConnectionState.READY.value == "ready"


def test_usage_enums_error_code() -> None:
    assert BrokerErrorCode.BROKER_TIMEOUT.value == "BROKER_TIMEOUT"


def test_usage_enums_capability_id() -> None:
    assert BrokerCapabilityId.GET_QUOTE.value == "get_quote"


def test_usage_models_connection_config() -> None:
    _model("connection_config", BrokerConnectionConfig)


def test_usage_models_error() -> None:
    _model("error", BrokerError)


def test_usage_models_result() -> None:
    _model("result", BrokerResult)


def test_usage_models_page() -> None:
    _model("page", BrokerPage)


def test_usage_models_capability() -> None:
    _model("capability", BrokerCapability)


def test_usage_models_feature_flags() -> None:
    _model("feature_flags", BrokerFeatureFlags)


def test_usage_models_connection_status() -> None:
    _model("connection_status", BrokerConnectionStatus)


def test_usage_models_connection_event() -> None:
    _model("connection_event", BrokerConnectionEvent)


def test_usage_models_platform_info() -> None:
    _model("platform_info", BrokerPlatformInfo)


def test_usage_models_permissions() -> None:
    _model("permissions", BrokerPermissions)


def test_usage_models_account_info() -> None:
    _model("account_info", BrokerAccountInfo)


def test_usage_models_balance() -> None:
    _model("balance", BrokerBalance)


def test_usage_models_asset_info() -> None:
    _model("asset_info", BrokerAssetInfo)


def test_usage_models_symbol_info() -> None:
    _model("symbol_info", BrokerSymbolInfo)


def test_usage_models_market_status() -> None:
    _model("market_status", BrokerMarketStatus)


def test_usage_models_trading_session() -> None:
    _model("trading_session", BrokerTradingSession)


def test_usage_models_quote() -> None:
    _model("quote", BrokerQuote)


def test_usage_models_tick() -> None:
    _model("tick", BrokerTick)


def test_usage_models_bar() -> None:
    _model("bar", BrokerBar)


def test_usage_models_order_book() -> None:
    _model("order_book", BrokerOrderBook)


def test_usage_models_subscription_info() -> None:
    _model("subscription_info", BrokerSubscriptionInfo)


def test_usage_models_position() -> None:
    _model("position", BrokerPosition)


def test_usage_models_order_filter() -> None:
    _model("order_filter", BrokerOrderFilter)


def test_usage_models_position_filter() -> None:
    _model("position_filter", BrokerPositionFilter)


def test_usage_models_order() -> None:
    _model("order", BrokerOrder)


def test_usage_models_deal() -> None:
    _model("deal", BrokerDeal)


def test_usage_models_account_transaction() -> None:
    _model("account_transaction", BrokerAccountTransaction)


def test_usage_models_order_request() -> None:
    _model("order_request", BrokerOrderRequest)


def test_usage_models_order_modification() -> None:
    _model("order_modification", BrokerOrderModificationRequest)


def test_usage_models_order_check() -> None:
    _model("order_check", BrokerOrderCheck)


def test_usage_models_order_result() -> None:
    _model("order_result", BrokerOrderResult)


def test_usage_models_position_modification() -> None:
    _model("position_modification", BrokerPositionModificationRequest)


def test_usage_models_position_close() -> None:
    _model("position_close", BrokerPositionCloseRequest)


def test_usage_models_margin_request() -> None:
    _model("margin_request", BrokerMarginRequest)


def test_usage_models_profit_request() -> None:
    _model("profit_request", BrokerProfitRequest)


def test_usage_models_fee_estimate() -> None:
    _model("fee_estimate", BrokerFeeEstimate)


def test_usage_models_server_time() -> None:
    _model("server_time", BrokerServerTime)


def test_usage_protocols_market_data_provider() -> None:
    provider = cast("MarketDataProvider", _fake())
    assert callable(provider.get_quote)


def test_usage_protocols_account_provider() -> None:
    provider = cast("AccountProvider", _fake())
    assert callable(provider.get_account_info)


def test_usage_protocols_trade_execution_provider() -> None:
    provider = cast("TradeExecutionProvider", _fake())
    assert callable(provider.place_order)


def test_usage_protocols_calculation_provider() -> None:
    provider = cast("CalculationProvider", _fake())
    assert callable(provider.calculate_margin)


def test_usage_protocols_async_context() -> None:
    adapter = _fake()

    async def _use() -> None:
        async with adapter as entered:
            broker = cast("BrokerAdapter", entered)
            assert broker.contract_version == "v1"

    asyncio.run(_use())


def test_usage_protocols_connect() -> None:
    assert asyncio.run(_fake().connect()).is_success


def test_usage_protocols_disconnect() -> None:
    assert asyncio.run(_fake().disconnect()).is_success


def test_usage_protocols_reconnect() -> None:
    assert asyncio.run(_fake().reconnect()).is_success


def test_usage_protocols_is_connected() -> None:
    assert asyncio.run(_fake().is_connected()).data is False


def test_usage_protocols_connection_status() -> None:
    assert asyncio.run(_fake().get_connection_status()).data is not None


def test_usage_protocols_ping() -> None:
    _operation(BrokerCapabilityId.PING)


def test_usage_protocols_refresh_session() -> None:
    _operation(BrokerCapabilityId.REFRESH_SESSION)


def test_usage_protocols_server_time() -> None:
    _operation(BrokerCapabilityId.GET_SERVER_TIME)


def test_usage_protocols_last_error() -> None:
    assert asyncio.run(_fake().get_last_error()).is_success


def test_usage_protocols_connection_events() -> None:
    adapter = _fake()

    async def _event() -> BrokerConnectionEvent:
        await adapter.connect()
        return await anext(adapter.connection_events())

    assert asyncio.run(_event()).new_state is BrokerConnectionState.CONNECTING


def test_usage_protocols_feature_flags() -> None:
    assert asyncio.run(_fake().get_feature_flags()).data is not None


def test_usage_protocols_supports() -> None:
    result = asyncio.run(_fake().supports(BrokerCapabilityId.GET_QUOTE))
    assert result.data is False


def test_usage_protocols_get_symbols() -> None:
    _operation(BrokerCapabilityId.GET_SYMBOLS)


def test_usage_protocols_get_symbol_info() -> None:
    _operation(BrokerCapabilityId.GET_SYMBOL_INFO)


def test_usage_protocols_select_symbol() -> None:
    _operation(BrokerCapabilityId.SELECT_SYMBOL)


def test_usage_protocols_market_status() -> None:
    _operation(BrokerCapabilityId.GET_MARKET_STATUS)


def test_usage_protocols_trading_sessions() -> None:
    _operation(BrokerCapabilityId.GET_TRADING_SESSIONS)


def test_usage_protocols_quote() -> None:
    _operation(BrokerCapabilityId.GET_QUOTE)


def test_usage_protocols_ticks() -> None:
    _operation(BrokerCapabilityId.GET_TICKS)


def test_usage_protocols_historical_bars() -> None:
    _operation(BrokerCapabilityId.GET_HISTORICAL_BARS)


def test_usage_protocols_order_book() -> None:
    _operation(BrokerCapabilityId.GET_ORDER_BOOK)


def test_usage_protocols_spread() -> None:
    _operation(BrokerCapabilityId.GET_SPREAD)


def test_usage_protocols_subscribe_quotes() -> None:
    _operation(BrokerCapabilityId.SUBSCRIBE_QUOTES)


def test_usage_protocols_subscribe_bars() -> None:
    _operation(BrokerCapabilityId.SUBSCRIBE_BARS)


def test_usage_protocols_subscribe_order_book() -> None:
    _operation(BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK)


def test_usage_protocols_unsubscribe() -> None:
    _operation(BrokerCapabilityId.UNSUBSCRIBE)


def test_usage_protocols_list_subscriptions() -> None:
    _operation(BrokerCapabilityId.LIST_SUBSCRIPTIONS)


def test_usage_protocols_platform_info() -> None:
    _operation(BrokerCapabilityId.GET_PLATFORM_INFO)


def test_usage_protocols_permissions() -> None:
    _operation(BrokerCapabilityId.GET_PERMISSIONS)


def test_usage_protocols_list_accounts() -> None:
    _operation(BrokerCapabilityId.LIST_ACCOUNTS)


def test_usage_protocols_select_account_unsupported() -> None:
    _operation(BrokerCapabilityId.SELECT_ACCOUNT)


def test_usage_protocols_account_info() -> None:
    _operation(BrokerCapabilityId.GET_ACCOUNT_INFO)


def test_usage_protocols_balances() -> None:
    _operation(BrokerCapabilityId.GET_BALANCES)


def test_usage_protocols_list_assets() -> None:
    _operation(BrokerCapabilityId.LIST_ASSETS)


def test_usage_protocols_asset_info() -> None:
    _operation(BrokerCapabilityId.GET_ASSET_INFO)


def test_usage_protocols_positions() -> None:
    _operation(BrokerCapabilityId.GET_POSITIONS)


def test_usage_protocols_position() -> None:
    _operation(BrokerCapabilityId.GET_POSITION)


def test_usage_protocols_orders() -> None:
    _operation(BrokerCapabilityId.GET_ORDERS)


def test_usage_protocols_order() -> None:
    _operation(BrokerCapabilityId.GET_ORDER)


def test_usage_protocols_order_history() -> None:
    _operation(BrokerCapabilityId.LIST_ORDER_HISTORY)


def test_usage_protocols_deal_history() -> None:
    _operation(BrokerCapabilityId.LIST_DEAL_HISTORY)


def test_usage_protocols_deal() -> None:
    _operation(BrokerCapabilityId.GET_DEAL)


def test_usage_protocols_account_transactions() -> None:
    _operation(BrokerCapabilityId.LIST_ACCOUNT_TRANSACTIONS)


def test_usage_protocols_check_order() -> None:
    _operation(BrokerCapabilityId.CHECK_ORDER)


def test_usage_protocols_place_order() -> None:
    _operation(BrokerCapabilityId.PLACE_ORDER)


def test_usage_protocols_modify_order() -> None:
    _operation(BrokerCapabilityId.MODIFY_ORDER)


def test_usage_protocols_cancel_order() -> None:
    _operation(BrokerCapabilityId.CANCEL_ORDER)


def test_usage_protocols_modify_position() -> None:
    _operation(BrokerCapabilityId.MODIFY_POSITION)


def test_usage_protocols_close_position() -> None:
    _operation(BrokerCapabilityId.CLOSE_POSITION)


def test_usage_protocols_replace_order() -> None:
    _operation(BrokerCapabilityId.REPLACE_ORDER)


def test_usage_protocols_calculate_margin() -> None:
    _operation(BrokerCapabilityId.CALCULATE_MARGIN)


def test_usage_protocols_calculate_profit() -> None:
    _operation(BrokerCapabilityId.CALCULATE_PROFIT)


def test_usage_protocols_commission_estimate() -> None:
    _operation(BrokerCapabilityId.GET_COMMISSION_ESTIMATE)


class _ExampleSubscription:
    def __init__(self) -> None:
        self.info = cast("BrokerSubscriptionInfo", MODELS["subscription_info"])

    async def events(self) -> AsyncIterator[BrokerQuote | BrokerError]:
        yield cast("BrokerQuote", MODELS["quote"])

    async def unsubscribe(self) -> BrokerResult[None]:
        return cast("BrokerResult[None]", MODELS["result"])


def test_usage_subscription_events() -> None:
    subscription = _ExampleSubscription()
    assert isinstance(subscription, BrokerSubscription)

    async def _first() -> BrokerQuote | BrokerError:
        return await anext(subscription.events())

    assert isinstance(asyncio.run(_first()), BrokerQuote)


def test_usage_unsupported_result() -> None:
    result = _operation(BrokerCapabilityId.GET_QUOTE)
    assert result.error is not None
    assert result.error.code is BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED


def test_usage_contract_exports() -> None:
    contracts = importlib.import_module("app.services.brokers.contracts")
    assert contracts.BrokerAdapter is BrokerAdapter
    assert "_unsupported_result" not in contracts.__all__
