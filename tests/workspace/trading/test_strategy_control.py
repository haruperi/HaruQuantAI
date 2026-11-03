"""StrategyControl queries share typed, wire, clock, and trade-history semantics."""

import asyncio
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.core.data.contracts import SymbolInfo, SymbolPrice
from app.core.enums import DealEntry, DealType, MarginMode
from app.core.trading.connection.contracts import BridgeError, DealInfo
from app.extend.blocks.order.close.close_all_pending_orders import (
    close_all_pending_orders,
)
from app.extend.blocks.order.close.close_all_positions import close_all_positions
from app.extend.blocks.order.close.close_position import close_position
from app.extend.blocks.order.open.enter_at_limit import enter_at_limit
from app.extend.blocks.order.open.enter_at_market import enter_at_market
from app.extend.blocks.strategy_control.account_balance import account_balance
from app.extend.blocks.strategy_control.account_equity import account_equity
from app.extend.blocks.strategy_control.bars_since_order_closed import (
    bars_since_order_closed,
)
from app.extend.blocks.strategy_control.bars_since_order_open import (
    bars_since_order_open,
)
from app.extend.blocks.strategy_control.closed_pl_in_money import closed_pl_in_money
from app.extend.blocks.strategy_control.closed_pl_in_pips import closed_pl_in_pips
from app.extend.blocks.strategy_control.history import closed_trades
from app.extend.blocks.strategy_control.last_order_was import last_order_was
from app.extend.blocks.strategy_control.last_order_was_not import last_order_was_not
from app.extend.blocks.strategy_control.market_position import market_position
from app.extend.blocks.strategy_control.market_position_is_flat import (
    market_position_is_flat,
)
from app.extend.blocks.strategy_control.market_position_is_long import (
    market_position_is_long,
)
from app.extend.blocks.strategy_control.market_position_is_not_long import (
    market_position_is_not_long,
)
from app.extend.blocks.strategy_control.market_position_is_not_short import (
    market_position_is_not_short,
)
from app.extend.blocks.strategy_control.market_position_is_short import (
    market_position_is_short,
)
from app.extend.blocks.strategy_control.market_position_size import (
    market_position_size,
)
from app.extend.blocks.strategy_control.market_positions_count import (
    market_positions_count,
)
from app.extend.blocks.strategy_control.no_trade_recently_closed import (
    no_trade_recently_closed,
)
from app.extend.blocks.strategy_control.open_pl_in_money import open_pl_in_money
from app.extend.blocks.strategy_control.open_pl_in_pips import open_pl_in_pips
from app.extend.blocks.strategy_control.order_open_price import order_open_price
from app.extend.blocks.strategy_control.order_pt import order_pt
from app.extend.blocks.strategy_control.order_sl import order_sl
from app.extend.blocks.strategy_control.pending_order_doesnt_exist import (
    pending_order_doesnt_exist,
)
from app.extend.blocks.strategy_control.pending_order_exists import (
    pending_order_exists,
)
from app.extend.blocks.strategy_control.trade_recently_closed import (
    trade_recently_closed,
)
from app.extend.functions.order_functions import TradeFilter
from app.workspace.brokers.simulator import SimulatorClient
from app.workspace.trading import Trading

START = datetime(2026, 10, 27, 10, tzinfo=UTC)


class WireBackend:
    """Convert backend snapshots into dictionaries like the live bridge."""

    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):
        return getattr(self.client, name)

    async def call(self, **kwargs):
        result = await self.client.call(**kwargs)
        if isinstance(result, list):
            return [asdict(item) if is_dataclass(item) else item for item in result]
        return asdict(result) if is_dataclass(result) else result


@pytest.fixture(params=[False, True], ids=["typed", "wire"])
def setup(request):
    client = SimulatorClient(commission_per_lot=2)
    client.set_clock(START)
    for name in ("EURUSD", "GBPUSD"):
        client.add_symbol(SymbolInfo(name=name, price=SymbolPrice(pip_size=0.0001)))
        client.feed_tick(name, bid=1.1, ask=1.1002)
    trading = Trading(WireBackend(client) if request.param else client)
    trading.arm()
    return trading, client


def test_empty_state_and_absence_sentinels(setup):
    trading, _client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        _p, _h = trading.position, trading.history_order
        assert await account_balance(trading) == 10000
        assert await account_equity(trading) == 10000
        assert await market_position(trading, scope) == 0
        assert await market_position_is_flat(trading, scope)
        assert not await market_position_is_long(trading, scope)
        assert not await market_position_is_short(trading, scope)
        assert await market_position_is_not_long(trading, scope)
        assert await market_position_is_not_short(trading, scope)
        assert await market_positions_count(trading, scope) == 0
        assert await market_position_size(trading, scope) == 0
        assert await order_open_price(trading, scope, pending=False) == -1
        assert await order_sl(trading, scope, pending=False) == -1
        assert await order_pt(trading, scope, pending=False) == -1
        assert await open_pl_in_money(trading, scope) == 0
        assert await open_pl_in_pips(trading, scope) == 0
        assert await bars_since_order_open(trading, scope, [START], as_of=START) == -1
        assert not await pending_order_exists(trading, scope)
        assert await pending_order_doesnt_exist(trading, scope)
        assert await order_open_price(trading, scope, pending=True) == -1
        assert await order_sl(trading, scope, pending=True) == -1
        assert await order_pt(trading, scope, pending=True) == -1
        assert await closed_pl_in_money(trading, scope) == 0
        assert await closed_pl_in_pips(trading, scope) == 0
        assert not await last_order_was(trading, scope, 1)
        assert not await last_order_was_not(trading, scope, 1)
        assert await bars_since_order_closed(trading, scope, [START], as_of=START) == -1
        assert not await trade_recently_closed(
            trading, scope, as_of=START, bar_start=START
        )
        assert await no_trade_recently_closed(
            trading, scope, as_of=START, bar_start=START
        )

    asyncio.run(scenario())


def test_hedged_direction_count_size_and_pending_separation(setup):
    trading, _client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        _t, _p, _o = trading.trade, trading.position, trading.order
        await enter_at_market(trading, "EURUSD", 1, 0.02, magic=42, sl=1.08, tp=1.13)
        await enter_at_market(
            trading, "EURUSD", -1, 0.03, magic=42, allow_duplicate_trades=True
        )
        await enter_at_limit(
            trading,
            "EURUSD",
            1,
            0.01,
            1.09,
            magic=42,
            sl=1.07,
            tp=1.12,
            allow_duplicate_trades=True,
        )
        await enter_at_market(trading, "GBPUSD", 1, 0.01, magic=42)
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=43)
        assert await market_position(trading, scope) == 1
        assert await market_position_is_long(trading, scope)
        assert await market_position_is_short(trading, scope)
        assert not await market_position_is_not_long(trading, scope)
        assert not await market_position_is_not_short(trading, scope)
        assert not await market_position_is_flat(trading, scope)
        assert await market_positions_count(trading, scope) == 2
        assert await market_position_size(trading, scope) == pytest.approx(0.05)
        assert await order_open_price(trading, scope, pending=False) == 1.1002
        assert await order_sl(trading, scope, pending=False) == 1.08
        assert await order_pt(trading, scope, pending=False) == 1.13
        assert await pending_order_exists(trading, scope)
        assert not await pending_order_doesnt_exist(trading, scope)
        assert await order_open_price(trading, scope, pending=True) == 1.09
        assert await order_sl(trading, scope, pending=True) == 1.07
        assert await order_pt(trading, scope, pending=True) == 1.12
        assert (
            await market_position(
                trading, TradeFilter("EURUSD", direction=-1, magic=42)
            )
            == -1
        )

    asyncio.run(scenario())


def test_open_pl_decision_prices_are_pure_and_include_commission(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.02, magic=42)
        before = replace(client.positions()[0])
        assert before.commission == pytest.approx(-0.04)
        assert await open_pl_in_money(trading, scope) == pytest.approx(
            before.profit - 0.04
        )
        assert await open_pl_in_pips(trading, scope) == pytest.approx(-2)
        assert await open_pl_in_pips(
            trading, scope, prices={"EURUSD": 1.1012}
        ) == pytest.approx(10)
        assert await open_pl_in_money(
            trading, scope, prices={"EURUSD": 1.1012}
        ) == pytest.approx(1.96)
        assert client.positions()[0] == before
        with pytest.raises(KeyError):
            await open_pl_in_pips(trading, scope, prices={})
        with pytest.raises(ValueError, match="valuation"):
            await open_pl_in_money(trading, scope, prices={"EURUSD": float("nan")})

    asyncio.run(scenario())


def test_bar_counts_use_real_chart_boundaries_and_explicit_time(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)
    bars = [START, START + timedelta(minutes=5), START + timedelta(days=3)]

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        client.set_clock(bars[-1])
        assert await bars_since_order_open(trading, scope, bars, as_of=bars[-1]) == 2
        assert await bars_since_order_open(trading, scope, [START], as_of=START) == 0
        with pytest.raises(ValueError, match="cover"):
            await bars_since_order_open(trading, scope, bars[1:], as_of=bars[-1])
        with pytest.raises(ValueError, match="oldest"):
            await bars_since_order_open(
                trading, scope, list(reversed(bars)), as_of=bars[-1]
            )
        with pytest.raises(ValueError, match="evaluation"):
            await bars_since_order_open(trading, scope, bars, as_of=START)

    asyncio.run(scenario())


def test_partial_close_only_becomes_history_when_flat_and_costs_reconcile(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42, comment="entry")

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.03, magic=42, comment="entry")
        client.feed_tick(
            "EURUSD", bid=1.1012, ask=1.1014, time=START + timedelta(minutes=1)
        )
        await close_position(trading, scope, volume=0.01)
        assert await closed_trades(trading, scope) == []
        assert client.positions()[0].commission == pytest.approx(-0.04)
        await close_position(trading, scope)
        trades = await closed_trades(trading, scope)
        assert len(trades) == 1
        trade = trades[0]
        assert trade.direction == 1 and trade.magic == 42 and trade.comment == "entry"
        assert trade.volume == pytest.approx(0.03)
        assert trade.commission == pytest.approx(-0.12)
        assert await closed_pl_in_money(trading, scope) == pytest.approx(
            client.account().balance - 10000
        )
        assert await closed_pl_in_pips(trading, scope) == pytest.approx(10)
        assert await last_order_was(trading, scope, 1)
        assert not await last_order_was(trading, scope, -1)
        assert await last_order_was_not(trading, scope, -1)
        assert not await last_order_was_not(trading, scope, 1)
        assert (
            await closed_trades(
                trading, TradeFilter("EURUSD", ticket=trade.position_id)
            )
            == trades
        )
        assert await closed_trades(trading, scope, as_of=START) == []

    asyncio.run(scenario())


def test_trades_ago_recent_close_and_no_future_leak(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)
    closed_at = START + timedelta(minutes=1, milliseconds=123)

    async def scenario():
        _t, _h = trading.trade, trading.history_order
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        client.set_clock(closed_at)
        await close_position(trading, scope)
        client.set_clock(START + timedelta(minutes=2))
        await enter_at_market(trading, "EURUSD", -1, 0.01, magic=42)
        client.set_clock(START + timedelta(minutes=3))
        await close_position(trading, scope)
        assert await last_order_was(trading, scope, -1)
        assert await last_order_was(trading, scope, 1, as_of=closed_at)
        assert await closed_pl_in_money(trading, scope, trades_ago=2) == 0
        assert await closed_pl_in_money(trading, scope, trades_ago=1) < 0
        before = closed_at - timedelta(milliseconds=1)
        assert not await trade_recently_closed(
            trading, scope, as_of=before, bar_start=START
        )
        assert await trade_recently_closed(
            trading, scope, as_of=closed_at, bar_start=START
        )
        assert await trade_recently_closed(
            trading, scope, as_of=closed_at, bar_start=START
        )
        assert not await no_trade_recently_closed(
            trading, scope, as_of=closed_at, bar_start=START
        )
        assert not await trade_recently_closed(
            trading, scope, as_of=START + timedelta(minutes=4), check_this_bar=False
        )
        assert not await trade_recently_closed(
            trading,
            scope,
            as_of=closed_at,
            check_this_bar=False,
            check_this_minute=False,
        )
        bars = [START, START + timedelta(minutes=1), START + timedelta(minutes=2)]
        assert await bars_since_order_closed(trading, scope, bars, as_of=bars[-1]) == 1
        with pytest.raises(ValueError, match="trades_ago"):
            await closed_pl_in_money(trading, scope, trades_ago=-1)
        with pytest.raises(ValueError, match="bar_start"):
            await trade_recently_closed(trading, scope, as_of=closed_at)
        with pytest.raises(ValueError, match="timezone"):
            await closed_pl_in_money(trading, scope, as_of=START.replace(tzinfo=None))

    asyncio.run(scenario())


def test_cancelled_pending_orders_never_count_as_completed_trades(setup):
    trading, _client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_limit(trading, "EURUSD", 1, 0.01, 1.09, magic=42)
        await close_all_pending_orders(trading, scope)
        assert await closed_trades(trading, scope) == []
        assert not await last_order_was_not(trading, scope, 1)

    asyncio.run(scenario())


def test_netting_scale_in_and_reversal_keep_separate_lifecycles():
    client = SimulatorClient(margin_mode=MarginMode.RETAIL_NETTING)
    client.set_clock(START)
    client.add_symbol(SymbolInfo(name="EURUSD"))
    client.feed_tick("EURUSD", bid=1.1, ask=1.1002)
    trading = Trading(client)
    trading.arm()
    scope = TradeFilter("EURUSD", magic=2)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=2)
        await enter_at_market(
            trading, "EURUSD", 1, 0.02, magic=2, allow_duplicate_trades=True
        )
        await enter_at_market(
            trading, "EURUSD", -1, 0.04, magic=2, allow_duplicate_trades=True
        )
        await close_all_positions(trading, scope)
        trades = await closed_trades(trading, scope)
        assert [trade.direction for trade in trades] == [1, -1]
        assert [trade.volume for trade in trades] == pytest.approx([0.03, 0.01])

    asyncio.run(scenario())


def test_native_inout_fee_allocation_sorting_and_opening_identity(setup):
    trading, _client = setup
    stamp = int(START.timestamp() * 1000)
    entry = DealInfo(
        ticket=1,
        position_id=100,
        symbol="EURUSD",
        volume=1,
        price=1.1,
        magic=42,
        comment="owned",
        commission=-2,
        fee=-1,
        time_msc=stamp,
    )
    reversal = DealInfo(
        ticket=2,
        position_id=100,
        symbol="EURUSD",
        deal_type=int(DealType.SELL),
        entry=int(DealEntry.INOUT),
        volume=1.5,
        price=1.11,
        magic=42,
        comment="manual close",
        commission=-3,
        fee=-1.5,
        profit=1000,
        time_msc=stamp + 1000,
    )
    close = DealInfo(
        ticket=3,
        position_id=100,
        symbol="EURUSD",
        deal_type=int(DealType.BUY),
        entry=int(DealEntry.OUT),
        volume=0.5,
        price=1.1,
        magic=0,
        comment="manual",
        commission=-1,
        fee=-0.5,
        profit=500,
        time_msc=stamp + 2000,
    )

    async def scenario():
        trading.deal.HistoryDealsGet = AsyncMock(return_value=[close, reversal, entry])
        trades = await closed_trades(trading, TradeFilter("EURUSD", magic=42))
        assert [trade.direction for trade in trades] == [1, -1]
        assert trades[0].comment == "owned"
        assert [trade.net_profit for trade in trades] == pytest.approx([994, 497])
        assert sum(t.commission + t.fee for t in trades) == pytest.approx(-9)
        assert (
            len(await closed_trades(trading, TradeFilter("EURUSD", comment="owned")))
            == 1
        )

    asyncio.run(scenario())


def test_incomplete_duplicate_and_mixed_ownership_history_fails_explicitly(setup):
    trading, _client = setup
    scope = TradeFilter("EURUSD")
    entry = DealInfo(
        ticket=1, position_id=100, symbol="EURUSD", volume=1, price=1.1, magic=42
    )
    close = replace(
        entry, ticket=2, deal_type=int(DealType.SELL), entry=int(DealEntry.OUT)
    )

    async def scenario():
        for deals, code in [
            ([close], "INCOMPLETE_HISTORY"),
            ([entry, entry], "INCOMPLETE_HISTORY"),
            ([entry, replace(entry, ticket=3, magic=43)], "AMBIGUOUS_HISTORY"),
        ]:
            trading.deal.HistoryDealsGet = AsyncMock(return_value=deals)
            with pytest.raises(BridgeError) as error:
                await closed_trades(trading, scope)
            assert error.value.code == code

    asyncio.run(scenario())


def test_unavailable_history_and_profit_calculation_are_not_zero_results():
    from app.workspace.brokers.base import TradingClient

    client = TradingClient("unsupported")
    trading = Trading(client)

    async def scenario():
        with pytest.raises(BridgeError) as error:
            await closed_trades(trading, TradeFilter("EURUSD"))
        assert error.value.code == "UNSUPPORTED_OPERATION"
        with pytest.raises(BridgeError) as error:
            await trading.account.OrderProfitCheck("EURUSD", 0, 1.0, 1.1, 1.2)
        assert error.value.code == "UNSUPPORTED_OPERATION"

    asyncio.run(scenario())
