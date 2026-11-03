"""Trading operations run against typed and dictionary-returning execution adapters."""

import asyncio
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.core.data.contracts import (
    SymbolInfo,
)
from app.core.enums import OrderTime, TradeAction, TradeRetcode
from app.core.trading.connection.contracts import (
    BridgeError,
    TradeCheckResult,
    TradeResult,
)
from app.extend.blocks.order.close.close_all_pending_orders import (
    close_all_pending_orders,
)
from app.extend.blocks.order.close.close_all_positions import close_all_positions
from app.extend.blocks.order.close.close_best_position import close_best_position
from app.extend.blocks.order.close.close_pending_order import close_pending_order
from app.extend.blocks.order.close.close_position import close_position
from app.extend.blocks.order.close.close_worst_position import close_worst_position
from app.extend.blocks.order.modify.set_profit_target import set_profit_target
from app.extend.blocks.order.modify.set_stop_loss import set_stop_loss
from app.extend.blocks.order.open.enter_at_limit import enter_at_limit
from app.extend.blocks.order.open.enter_at_market import enter_at_market
from app.extend.blocks.order.open.enter_at_stop import enter_at_stop
from app.extend.blocks.order.open.enter_reverse_at_market import (
    enter_reverse_at_market,
)
from app.extend.functions.order_functions import TradeFilter
from app.workspace.brokers.simulator import SimulatorClient
from app.workspace.trading import Trading


class DictionaryBackend:
    """Exercise the wire response conversion boundary without a live broker."""

    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):
        return getattr(self.client, name)

    async def call(self, **kwargs):
        value = await self.client.call(**kwargs)
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, list):
            return [asdict(item) if is_dataclass(item) else item for item in value]
        return value


@pytest.fixture(params=[False, True], ids=["typed", "wire"])
def setup(request):
    client = SimulatorClient()
    client.set_clock(datetime(2026, 10, 27, tzinfo=UTC))
    for name in ("EURUSD", "GBPUSD"):
        client.add_symbol(SymbolInfo(name=name))
        client.feed_tick(name, bid=1.1000, ask=1.1002)
    backend = DictionaryBackend(client) if request.param else client
    trading = Trading(backend)
    trading.arm()
    return trading, client


def test_market_entry_defaults_duplicate_scope_and_partial_close(setup):
    trading, client = setup

    async def scenario():
        trade = trading.trade
        await trade.SetExpertMagicNumber(42)
        await trade.SetDeviationInPoints(12)
        opened = await enter_at_market(trading, "EURUSD", 1, 0.04, comment="entry")
        assert opened.retcode == TradeRetcode.DONE
        request = await trade.Request()
        assert request.magic == 42 and request.deviation == 12
        assert (
            await enter_at_market(trading, "EURUSD", -1, 0.01, comment="entry") is None
        )
        assert len(client.positions()) == 1
        position = client.positions()[0]
        scope = TradeFilter("EURUSD", magic=42, ticket=position.ticket)
        assert (
            await close_position(trading, scope, volume=0.01)
        ).retcode == TradeRetcode.DONE
        assert client.positions()[0].volume == pytest.approx(0.03)
        assert (await close_position(trading, scope)).retcode == TradeRetcode.DONE
        assert client.positions() == []
        assert await close_position(trading, scope) is None

    asyncio.run(scenario())


def test_limit_stop_replacement_and_cancellation(setup):
    trading, client = setup

    async def scenario():
        expiry = datetime(2026, 10, 28, tzinfo=UTC)
        first = await enter_at_limit(
            trading, "EURUSD", 1, 0.01, 1.09, magic=7, expiration=expiry
        )
        assert first.retcode == TradeRetcode.PLACED
        assert (
            await enter_at_limit(
                trading, "EURUSD", 1, 0.01, 1.08, magic=7, replace_existing=False
            )
            is None
        )
        assert client.orders()[0].ticket == first.order
        invalid = await enter_at_stop(trading, "EURUSD", 1, 0.01, 1.09, magic=7)
        assert invalid.retcode == TradeRetcode.INVALID_PRICE
        assert client.orders()[0].ticket == first.order
        second = await enter_at_stop(
            trading, "EURUSD", 1, 0.01, 1.12, magic=7, expiration=expiry
        )
        assert second.retcode == TradeRetcode.PLACED
        assert len(client.orders()) == 1
        assert client.orders()[0].ticket != first.order
        assert (
            await close_pending_order(trading, TradeFilter("EURUSD", magic=8))
        ) is None
        assert (
            await close_pending_order(trading, TradeFilter("EURUSD", magic=7))
        ).retcode == TradeRetcode.DONE
        await enter_at_limit(trading, "EURUSD", -1, 0.01, 1.12, magic=7)
        await enter_at_stop(trading, "EURUSD", -1, 0.01, 1.08, magic=8)
        results = await close_all_pending_orders(
            trading, TradeFilter("EURUSD", direction=-1)
        )
        assert len(results) == 2
        assert client.orders() == []

    asyncio.run(scenario())


def test_stop_and_target_preserve_other_fields_and_pending_expiry(setup):
    trading, client = setup

    async def scenario():
        expiry = datetime(2026, 10, 28, tzinfo=UTC)
        await enter_at_market(trading, "EURUSD", 1, 0.01, sl=1.08, tp=1.14, magic=3)
        await enter_at_limit(
            trading,
            "EURUSD",
            1,
            0.01,
            1.09,
            sl=1.07,
            tp=1.14,
            magic=3,
            expiration=expiry,
            allow_duplicate_trades=True,
        )
        scope = TradeFilter("EURUSD", magic=3)
        results = await set_stop_loss(trading, scope, 1.06)
        assert len(results) == 2
        assert all(r.retcode == TradeRetcode.DONE for r in results)
        assert client.positions()[0].tp == 1.14
        order = client.orders()[0]
        assert order.tp == 1.14 and order.price_open == 1.09
        assert order.type_time == OrderTime.SPECIFIED
        assert order.time_expiration == int(expiry.timestamp())
        assert len(await set_profit_target(trading, scope, 1.15)) == 2
        assert client.positions()[0].sl == 1.06
        assert client.orders()[0].sl == 1.06
        await set_stop_loss(trading, scope, 0)
        assert client.positions()[0].sl == 0
        assert client.orders()[0].sl == 0

    asyncio.run(scenario())


def test_best_worst_and_bulk_close_keep_unrelated_positions(setup):
    trading, client = setup

    async def scenario():
        for direction, magic in [(1, 5), (-1, 5), (1, 6)]:
            await enter_at_market(
                trading,
                "EURUSD",
                direction,
                0.01,
                magic=magic,
                allow_duplicate_trades=True,
            )
        await enter_at_market(trading, "GBPUSD", 1, 0.01, magic=5)
        client.feed_tick("EURUSD", bid=1.11, ask=1.1102)
        owned = [p for p in client.positions() if p.symbol == "EURUSD" and p.magic == 5]
        best = max(owned, key=lambda p: p.profit).ticket
        worst = min(owned, key=lambda p: p.profit).ticket
        scope = TradeFilter("EURUSD", magic=5)
        assert (await close_best_position(trading, scope)).retcode == TradeRetcode.DONE
        assert best not in [p.ticket for p in client.positions()]
        assert (await close_worst_position(trading, scope)).retcode == TradeRetcode.DONE
        assert worst not in [p.ticket for p in client.positions()]
        assert await close_best_position(trading, scope) is None
        assert await close_worst_position(trading, scope) is None
        assert len(await close_all_positions(trading, TradeFilter(None, magic=5))) == 1
        assert [p.magic for p in client.positions()] == [6]

    asyncio.run(scenario())


def test_reversal_closes_only_matching_opposite_and_enters_once(setup):
    trading, client = setup

    async def scenario():
        await enter_at_market(trading, "EURUSD", -1, 0.01, magic=9, comment="mine")
        await enter_at_market(
            trading,
            "EURUSD",
            -1,
            0.01,
            magic=9,
            comment="mine",
            allow_duplicate_trades=True,
        )
        await enter_at_market(trading, "EURUSD", -1, 0.01, magic=10)
        result = await enter_reverse_at_market(
            trading, "EURUSD", 1, 0.02, magic=9, comment="mine"
        )
        assert result.retcode == TradeRetcode.DONE
        positions = client.positions()
        assert len(positions) == 2
        mine = [p for p in positions if p.magic == 9]
        assert len(mine) == 1 and mine[0].position_type == 0
        assert mine[0].volume == 0.02
        assert (
            await enter_reverse_at_market(
                trading, "EURUSD", 1, 0.02, magic=9, comment="mine"
            )
            is None
        )

    asyncio.run(scenario())


def test_expiration_uses_simulation_clock_and_pending_fills(setup):
    trading, client = setup

    async def scenario():
        expiry = datetime(2026, 10, 27, tzinfo=UTC) + timedelta(hours=1)
        await enter_at_limit(trading, "EURUSD", 1, 0.01, 1.09, expiration=expiry)
        client.set_clock(expiry)
        assert client.orders() == []
        await enter_at_stop(trading, "EURUSD", 1, 0.01, 1.12)
        client.feed_tick("EURUSD", bid=1.12, ask=1.1202)
        assert client.orders() == []
        assert len(client.positions()) == 1

    asyncio.run(scenario())


def test_invalid_inputs_and_disarmed_operations_do_not_mutate(setup):
    trading, client = setup

    async def scenario():
        for direction, volume in [(0, 0.01), (True, 0.01), (1, float("nan")), (1, -1)]:
            with pytest.raises(ValueError):
                await enter_at_market(trading, "EURUSD", direction, volume)
        with pytest.raises(ValueError, match="timezone"):
            await enter_at_limit(
                trading,
                "EURUSD",
                1,
                0.01,
                1.09,
                expiration=datetime(2026, 10, 28),  # noqa: DTZ001
            )
        assert client.positions() == [] and client.orders() == []
        trading.disarm()
        with pytest.raises(BridgeError) as error:
            await enter_at_market(trading, "EURUSD", 1, 0.01)
        assert error.value.code == "NOT_ARMED"
        assert client.positions() == []

    asyncio.run(scenario())


def test_reverse_does_not_enter_after_partial_or_unconfirmed_close(setup):
    trading, client = setup

    async def scenario():
        trade = trading.trade
        await enter_at_market(trading, "EURUSD", -1, 0.01, magic=1)
        trade.OrderSend = AsyncMock(
            return_value=TradeResult(retcode=TradeRetcode.DONE_PARTIAL)
        )
        result = await enter_reverse_at_market(trading, "EURUSD", 1, 0.01, magic=1)
        assert result.retcode == TradeRetcode.DONE_PARTIAL
        assert trade.OrderSend.await_count == 1
        assert client.positions()[0].position_type == 1
        trade.OrderSend = AsyncMock(return_value=TradeResult(retcode=TradeRetcode.DONE))
        with pytest.raises(BridgeError) as error:
            await enter_reverse_at_market(trading, "EURUSD", 1, 0.01, magic=1)
        assert error.value.code == "OPERATION_UNCONFIRMED"
        assert trade.OrderSend.await_count == 1

    asyncio.run(scenario())


def test_native_zero_check_code_and_rejected_check(setup):
    trading, _client = setup

    async def scenario():
        trade = trading.trade
        trade.OrderCheck = AsyncMock(return_value=TradeCheckResult(retcode=0))
        assert (
            await enter_at_market(trading, "EURUSD", 1, 0.01)
        ).retcode == TradeRetcode.DONE
        trade.OrderCheck = AsyncMock(
            return_value=TradeCheckResult(retcode=TradeRetcode.NO_MONEY)
        )
        trade.OrderSend = AsyncMock()
        result = await enter_at_market(trading, "GBPUSD", 1, 0.01)
        assert result.retcode == TradeRetcode.NO_MONEY
        trade.OrderSend.assert_not_awaited()

    asyncio.run(scenario())


def test_filter_exact_magic_zero_and_comment_direction():
    from app.core.trading.connection.contracts import PositionInfo

    item = PositionInfo(
        symbol="EURUSD", magic=0, comment="strategy.entry", position_type=1
    )
    assert TradeFilter("EURUSD", direction=-1, magic=0, comment="entry").matches(item)
    assert not TradeFilter("EURUSD", magic=1).matches(item)
    assert not TradeFilter("EURUSD", direction=1).matches(item)
    with pytest.raises(ValueError, match="direction"):
        TradeFilter("EURUSD", direction=2)


def test_replacement_stops_on_failed_or_unconfirmed_cancellation(setup):
    trading, client = setup

    async def scenario():
        trade = trading.trade
        await enter_at_limit(trading, "EURUSD", 1, 0.01, 1.09, magic=12)
        existing = client.orders()[0].ticket
        trade.OrderSend = AsyncMock(
            return_value=TradeResult(retcode=TradeRetcode.REJECT)
        )
        result = await enter_at_stop(trading, "EURUSD", 1, 0.01, 1.12, magic=12)
        assert result.retcode == TradeRetcode.REJECT
        assert trade.OrderSend.await_count == 1
        assert trade.OrderSend.call_args.args[0].action == TradeAction.REMOVE
        assert client.orders()[0].ticket == existing
        trade.OrderSend = AsyncMock(return_value=TradeResult(retcode=TradeRetcode.DONE))
        with pytest.raises(BridgeError) as error:
            await enter_at_stop(trading, "EURUSD", 1, 0.01, 1.12, magic=12)
        assert error.value.code == "OPERATION_UNCONFIRMED"
        assert trade.OrderSend.await_count == 1

    asyncio.run(scenario())


def test_close_lot_grid_and_bulk_failure(setup):
    trading, client = setup

    async def scenario():
        trade = trading.trade
        await enter_at_market(trading, "EURUSD", 1, 0.03)
        scope = TradeFilter("EURUSD", magic=0)
        with pytest.raises(ValueError, match="volume"):
            await close_position(trading, scope, volume=0.005)
        assert client.positions()[0].volume == 0.03
        assert (
            await close_position(trading, scope, volume=0.02)
        ).retcode == TradeRetcode.DONE
        assert client.positions()[0].volume == pytest.approx(0.01)
        await enter_at_market(trading, "EURUSD", 1, 0.01, allow_duplicate_trades=True)
        trade.OrderSend = AsyncMock(
            return_value=TradeResult(retcode=TradeRetcode.REJECT)
        )
        results = await close_all_positions(trading, scope)
        assert len(results) == 1 and results[0].retcode == TradeRetcode.REJECT
        assert trade.OrderSend.await_count == 1
        assert len(client.positions()) == 2

    asyncio.run(scenario())


def test_concurrent_entries_share_workflow_lock(setup):
    trading, client = setup

    async def scenario():
        results = await asyncio.gather(
            *[enter_at_market(trading, "EURUSD", 1, 0.01, magic=123) for _ in range(2)]
        )
        assert sum(result is not None for result in results) == 1
        assert len(client.positions()) == 1

    asyncio.run(scenario())
