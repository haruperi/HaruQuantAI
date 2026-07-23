"""cTrader adapter tests using an injected fake transport."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerMarginRequest,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
)
from app.services.brokers.ctrader_session.adapter import CTraderBrokerAdapter
from pydantic import SecretStr


def _config(**overrides: object) -> BrokerConnectionConfig:
    values: dict[str, object] = {
        "broker_id": BrokerId.CTRADER,
        "environment": BrokerEnvironment.DEMO,
        "provider_enabled": True,
        "connect_timeout_sec": 1,
        "request_timeout_sec": 1,
        "transport_reconnect_max_attempts": 0,
        "stream_buffer_size": 2,
        "circuit_failure_threshold": 2,
        "circuit_recovery_timeout_sec": 1,
        "circuit_half_open_max_calls": 1,
        "account_reference": "998877",
        "credentials": {
            "client_id": SecretStr("client-id"),
            "client_secret": SecretStr("client-secret"),
            "access_token": SecretStr("access-token"),
            "account_id": SecretStr("998877"),
        },
    }
    values.update(overrides)
    return BrokerConnectionConfig(**values)  # type: ignore[arg-type]


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    mutations = {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
        BrokerCapabilityId.REPLACE_ORDER,
    }
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE" if operation in mutations else "AVAILABLE",
            access_mode="WRITE" if operation in mutations else "READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
            reason="test release gate" if operation in mutations else None,
        )
        for operation in BrokerCapabilityId
    }


class _FakeTransport:
    def __init__(self, *, verified: bool = True) -> None:
        self._verified = verified
        self.closed = False

    async def connect(self) -> bool:
        return self._verified

    async def close(self) -> None:
        self.closed = True


def _implementation_adapter(transport: Any) -> CTraderBrokerAdapter:
    """Build a private provider-mapping harness without changing production policy."""
    adapter = CTraderBrokerAdapter(_config(), transport=transport)
    adapter._capabilities = _capabilities()
    return adapter


class _OperationTransport(_FakeTransport):
    """Return deterministic provider-shaped responses through the real adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.handler: Callable[[object], None] | None = None
        self.requests: list[object] = []

    async def send(  # noqa: PLR0911 - provider message fixture router.
        self, request: object, response_type: type[object]
    ) -> object:
        """Return the response shape associated with one request type."""
        del response_type
        self.requests.append(request)
        name = type(request).__name__
        trade = {
            "symbolId": 1,
            "volume": 10_000_000,
            "tradeSide": 1,
            "openTimestamp": 1_700_000_000_000,
        }
        position = {
            "positionId": 21,
            "tradeData": trade,
            "positionStatus": 1,
            "swap": 0,
            "price": 1.1,
            "moneyDigits": 2,
        }
        order = {
            "orderId": 11,
            "tradeData": trade,
            "orderType": 1,
            "orderStatus": 1,
            "executedVolume": 0,
            "limitPrice": 1.1,
        }
        if name == "ProtoOASymbolsListReq":
            return {
                "symbol": [{"symbolName": "EURUSD", "symbolId": 1, "enabled": True}]
            }
        if name == "ProtoOASymbolByIdReq":
            return {
                "symbol": [
                    {
                        "symbolId": 1,
                        "digits": 5,
                        "pipPosition": 4,
                        "minVolume": 100_000,
                        "maxVolume": 100_000_000,
                        "stepVolume": 100_000,
                        "lotSize": 100_000,
                        "enableShortSelling": True,
                    }
                ]
            }
        if name == "ProtoOAReconcileReq":
            return {"position": [position], "order": [order]}
        if name == "ProtoOAOrderListReq":
            return {"order": [order], "hasMore": False}
        if name == "ProtoOADealListReq":
            return {
                "deal": [
                    {
                        "dealId": 31,
                        "orderId": 11,
                        "positionId": 21,
                        "volume": 10_000_000,
                        "filledVolume": 10_000_000,
                        "symbolId": 1,
                        "createTimestamp": 1_700_000_000_000,
                        "executionTimestamp": 1_700_000_000_100,
                        "executionPrice": 1.1,
                        "tradeSide": 1,
                        "dealStatus": 2,
                        "moneyDigits": 2,
                    }
                ],
                "hasMore": False,
            }
        if name == "ProtoOAExpectedMarginReq":
            return {
                "margin": [
                    {"volume": 10_000_000, "buyMargin": 12345, "sellMargin": 12345}
                ],
                "moneyDigits": 2,
            }
        if name == "ProtoOAGetTickDataReq":
            price = 110_000 if request.type == 1 else 110_020  # type: ignore[attr-defined]
            return {
                "tickData": [
                    {"timestamp": 1_700_000_000_000, "tick": price},
                    {"timestamp": 1_000, "tick": 1},
                ],
                "hasMore": False,
            }
        if name == "ProtoOAGetTrendbarsReq":
            return {
                "trendbar": [
                    {
                        "volume": 5,
                        "low": 109_900,
                        "deltaOpen": 100,
                        "deltaHigh": 300,
                        "deltaClose": 200,
                        "utcTimestampInMinutes": 28_333_333,
                    }
                ]
            }
        if name in {
            "ProtoOANewOrderReq",
            "ProtoOAAmendOrderReq",
            "ProtoOACancelOrderReq",
            "ProtoOAAmendPositionSLTPReq",
            "ProtoOAClosePositionReq",
        }:
            return {"order": {"orderId": 11}}
        return {}

    def register_event_handler(self, handler: Callable[[object], None]) -> None:
        """Capture the adapter-owned event callback."""
        self.handler = handler

    def unregister_event_handler(self, handler: Callable[[object], None]) -> None:
        """Release only the registered adapter callback."""
        if self.handler is handler:
            self.handler = None


def test_adapter_requires_matching_account_reference() -> None:
    """The declared account reference must match the resolved account_id."""
    with pytest.raises(ValueError, match="account_reference must match account_id"):
        CTraderBrokerAdapter(_config(account_reference="000000"))


def test_adapter_rejects_incomplete_credentials() -> None:
    """Every required cTrader credential must be present."""
    with pytest.raises(ValueError, match="resolved cTrader credentials are incomplete"):
        CTraderBrokerAdapter(
            _config(
                credentials={"client_id": SecretStr("client-id")},
                account_reference=None,
            ),
        )


def test_adapter_connect_succeeds_on_verified_transport() -> None:
    """A verified transport session transitions the adapter to ready."""
    adapter = _implementation_adapter(_FakeTransport(verified=True))

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.is_success

    asyncio.run(exercise())


def test_adapter_connect_fails_closed_without_authentication() -> None:
    """An unauthenticated transport never reports a successful connection."""
    adapter = CTraderBrokerAdapter(_config(), transport=_FakeTransport(verified=False))

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success
        assert result.error is not None

    asyncio.run(exercise())


def test_adapter_disconnect_releases_transport() -> None:
    """Disconnecting releases the owned cTrader session transport."""
    transport = _FakeTransport(verified=True)
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        await adapter.disconnect()

    asyncio.run(exercise())
    assert transport.closed


def test_adapter_platform_info_reports_environment_endpoint() -> None:
    """Platform info reports the exact demo/live endpoint without secrets."""
    adapter = _implementation_adapter(_FakeTransport(verified=True))

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_platform_info()
        assert result.data is not None
        assert result.data.endpoint_metadata["endpoint"] == "demo.ctraderapi.com:5035"

    asyncio.run(exercise())


def test_adapter_read_mutation_calculation_and_stream_operations() -> None:  # noqa: PLR0915
    """cTrader operation groups map native units through the public adapter."""
    transport = _OperationTransport()
    adapter = _implementation_adapter(transport)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)

    async def exercise() -> None:
        await adapter.connect()
        symbols = await adapter.get_symbols(limit=10)
        assert symbols.data is not None
        assert symbols.data.items[0].min_quantity == Decimal("0.01")
        ticks = await adapter.get_ticks("EURUSD", start, end, limit=10)
        assert ticks.data is not None
        assert len(ticks.data.items) == 2
        bars = await adapter.get_historical_bars("EURUSD", "M1", start, end, limit=10)
        assert bars.data is not None
        assert len(bars.data.items) == 1
        positions = await adapter.get_positions(limit=10)
        assert positions.data is not None
        assert positions.data.items[0].quantity == Decimal(1)
        orders = await adapter.get_orders(limit=10)
        assert orders.data is not None
        assert orders.data.items[0].quantity == Decimal(1)
        assert (await adapter.list_order_history(start, end, limit=10)).data is not None
        deals = await adapter.list_deal_history(start, end, limit=10)
        assert deals.data is not None
        assert deals.data.items[0].quantity == Decimal(1)

        order = BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal(1),
            quantity_unit="lots",
            environment=BrokerEnvironment.DEMO,
        )
        assert (
            await adapter.check_order(order)
        ).error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert (
            await adapter.place_order(order)
        ).error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert (
            await adapter.modify_order(
                BrokerOrderModificationRequest(order_id="11", quantity=Decimal(1))
            )
        ).error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert (
            await adapter.cancel_order("11")
        ).error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert (
            await adapter.modify_position(
                BrokerPositionModificationRequest(
                    position_id="21", stop_loss=Decimal("1.09")
                )
            )
        ).error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        assert (
            await adapter.close_position(
                BrokerPositionCloseRequest(
                    position_id="21",
                    quantity=Decimal(1),
                    quantity_unit="lots",
                )
            )
        ).error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        margin = await adapter.calculate_margin(
            BrokerMarginRequest(
                symbol="EURUSD",
                side="BUY",
                quantity=Decimal(1),
                quantity_unit="lots",
                product_profile="ctrader",
            )
        )
        assert margin.data == Decimal("123.45")
        profit = await adapter.calculate_profit(
            BrokerProfitRequest(
                symbol="EURUSD",
                side="BUY",
                quantity=Decimal(1),
                quantity_unit="lots",
                open_price=Decimal("1.1"),
                close_price=Decimal("1.2"),
                product_profile="ctrader",
            )
        )
        assert profit.data == Decimal("10000.0")

        stream = await adapter.subscribe_quotes(("EURUSD",))
        assert stream.data is not None
        assert transport.handler is not None
        event_type = type("ProtoOASpotEvent", (), {})
        event = event_type()
        event.symbolId = 1
        event.bid = 110_000
        event.ask = 110_020
        event.timestamp = 1_700_000_000_000
        transport.handler(event)
        quote = await anext(stream.data.events())
        assert not hasattr(quote, "error")
        assert quote.bid == Decimal("1.1")
        assert (await adapter.list_subscriptions()).data
        await adapter.unsubscribe(stream.data.info.subscription_id)

        native_volumes = [
            request.volume  # type: ignore[attr-defined]
            for request in transport.requests
            if type(request).__name__
            in {"ProtoOANewOrderReq", "ProtoOAClosePositionReq"}
        ]
        assert native_volumes == []

    asyncio.run(exercise())
