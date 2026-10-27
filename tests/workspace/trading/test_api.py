"""Contract coverage for the shared trading API and generic broker adapter."""

import asyncio
from datetime import UTC, datetime

import pytest
from app.include.contracts import (
    BridgeError,
    PositionInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.include.enums import OrderType, ReceiptStatus
from app.workspace.brokers.base import TradingClient
from app.workspace.trading import PositionProxy, Trade, Trading
from app.workspace.trading.base import normalize_request, serialize_request


class RecordingClient(TradingClient):
    """Typed broker fixture that records requests without external execution."""

    def __init__(self):
        super().__init__("recording")
        self.requests = []

    def order_send(self, request):
        self.requests.append(request)
        return TradeResult(
            retcode=10009, order=len(self.requests), comment=request.symbol
        )

    def order_check(self, request):
        self.requests.append(request)
        return TradeCheckResult(retcode=10009, comment=request.symbol)

    async def get_positions(self):
        return [
            PositionInfo(ticket=1, symbol="EURUSD"),
            PositionInfo(ticket=2, symbol="GBPUSD"),
        ]


def test_request_roundtrip_preserves_alias_and_aware_expiration():
    wire = serialize_request(
        {"type": OrderType.SELL, "expiration": datetime(2026, 10, 27, tzinfo=UTC)}
    )
    request = normalize_request(wire)
    assert request.order_type == OrderType.SELL
    assert request.expiration == datetime(2026, 10, 27, tzinfo=UTC)
    assert "type" not in wire


def test_naive_expiration_is_rejected():
    with pytest.raises(ValueError, match="timezone"):
        serialize_request({"expiration": datetime(2026, 10, 27)})  # noqa: DTZ001


def test_disarmed_execution_records_rejection():
    async def scenario():
        client = RecordingClient()
        with pytest.raises(BridgeError) as error:
            await Trading(client).trade.OrderSend(TradeRequest())
        assert error.value.code == "NOT_ARMED"
        assert client.requests == []
        assert client.receipt(client.last_command_id()).status == ReceiptStatus.REJECTED

    asyncio.run(scenario())


def test_request_check_does_not_require_arming():
    async def scenario():
        client = RecordingClient()
        trade = Trade(client)
        checked = await trade.OrderCheck({"symbol": "EURUSD"})
        assert checked == await trade.CheckResult()
        assert (await trade.Request()).symbol == "EURUSD"

    asyncio.run(scenario())


def test_trade_snapshots_are_isolated_between_objects_and_from_callers():
    async def scenario():
        client = RecordingClient()
        client.arm()
        first, second = Trade(client), Trade(client)
        await first.OrderSend({"symbol": "EURUSD"})
        await second.OrderSend({"symbol": "GBPUSD"})
        snapshot = await first.Result()
        snapshot.comment = "changed"
        assert (await first.Result()).comment == "EURUSD"
        assert (await second.Result()).comment == "GBPUSD"
        assert (await first.Request()).symbol == "EURUSD"

    asyncio.run(scenario())


def test_async_collection_selection_and_filters():
    async def scenario():
        client = RecordingClient()
        first, second = PositionProxy(client), PositionProxy(client)
        assert await first.SelectByTicket(1)
        assert await second.SelectByTicket(2)
        assert (await first.PositionInfo()).ticket == 1
        assert (await second.PositionInfo()).ticket == 2
        assert [p.ticket for p in await first.PositionsGet(symbol="GBPUSD")] == [2]
        assert [p.ticket for p in await first.PositionsGet(group="*USD,!GBP*")] == [1]
        with pytest.raises(BridgeError, match="filter"):
            await first.PositionsGet(unknown=True)
        with pytest.raises(TypeError, match="positional"):
            await first.PositionsGet("EURUSD", ticket=1)

    asyncio.run(scenario())


def test_queued_execution_is_explicitly_unsupported():
    async def scenario():
        with pytest.raises(BridgeError) as error:
            await Trade(RecordingClient()).SetAsyncMode(True)
        assert error.value.code == "UNSUPPORTED_OPERATION"

    asyncio.run(scenario())
