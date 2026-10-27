"""StrategyControl queries share typed, wire, clock, and trade-history semantics."""

import asyncio
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.include.contracts import BridgeError, DealInfo, SymbolInfo, SymbolPrice
from app.include.enums import DealEntry, DealType, MarginMode
from app.workspace.brokers.simulator import SimulatorClient
from app.workspace.trading import TradeFilter, Trading

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
        p, h = trading.position, trading.history_order
        assert await trading.account.account_balance() == 10000
        assert await trading.account.account_equity() == 10000
        assert await p.market_position(scope) == 0
        assert await p.market_position_is_flat(scope)
        assert not await p.market_position_is_long(scope)
        assert not await p.market_position_is_short(scope)
        assert await p.market_position_is_not_long(scope)
        assert await p.market_position_is_not_short(scope)
        assert await p.market_positions_count(scope) == 0
        assert await p.market_position_size(scope) == 0
        assert await p.order_open_price(scope) == -1
        assert await p.order_sl(scope) == -1
        assert await p.order_pt(scope) == -1
        assert await p.open_pl_in_money(scope) == 0
        assert await p.open_pl_in_pips(scope) == 0
        assert await p.bars_since_order_open(scope, [START], as_of=START) == -1
        assert not await trading.order.pending_order_exists(scope)
        assert await trading.order.pending_order_doesnt_exist(scope)
        assert await trading.order.order_open_price(scope) == -1
        assert await trading.order.order_sl(scope) == -1
        assert await trading.order.order_pt(scope) == -1
        assert await h.closed_pl_in_money(scope) == 0
        assert await h.closed_pl_in_pips(scope) == 0
        assert not await h.last_order_was(scope, 1)
        assert not await h.last_order_was_not(scope, 1)
        assert await h.bars_since_order_closed(scope, [START], as_of=START) == -1
        assert not await h.trade_recently_closed(scope, as_of=START, bar_start=START)
        assert await h.no_trade_recently_closed(scope, as_of=START, bar_start=START)

    asyncio.run(scenario())


def test_hedged_direction_count_size_and_pending_separation(setup):
    trading, _client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        t, p, o = trading.trade, trading.position, trading.order
        await t.enter_at_market("EURUSD", 1, 0.02, magic=42, sl=1.08, tp=1.13)
        await t.enter_at_market(
            "EURUSD", -1, 0.03, magic=42, allow_duplicate_trades=True
        )
        await t.enter_at_limit(
            "EURUSD",
            1,
            0.01,
            1.09,
            magic=42,
            sl=1.07,
            tp=1.12,
            allow_duplicate_trades=True,
        )
        await t.enter_at_market("GBPUSD", 1, 0.01, magic=42)
        await t.enter_at_market("EURUSD", 1, 0.01, magic=43)
        assert await p.market_position(scope) == 1
        assert await p.market_position_is_long(scope)
        assert await p.market_position_is_short(scope)
        assert not await p.market_position_is_not_long(scope)
        assert not await p.market_position_is_not_short(scope)
        assert not await p.market_position_is_flat(scope)
        assert await p.market_positions_count(scope) == 2
        assert await p.market_position_size(scope) == pytest.approx(0.05)
        assert await p.order_open_price(scope) == 1.1002
        assert await p.order_sl(scope) == 1.08
        assert await p.order_pt(scope) == 1.13
        assert await o.pending_order_exists(scope)
        assert not await o.pending_order_doesnt_exist(scope)
        assert await o.order_open_price(scope) == 1.09
        assert await o.order_sl(scope) == 1.07
        assert await o.order_pt(scope) == 1.12
        assert (
            await p.market_position(TradeFilter("EURUSD", direction=-1, magic=42)) == -1
        )

    asyncio.run(scenario())


def test_open_pl_decision_prices_are_pure_and_include_commission(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await trading.trade.enter_at_market("EURUSD", 1, 0.02, magic=42)
        p = trading.position
        before = replace(client.positions()[0])
        assert before.commission == pytest.approx(-0.04)
        assert await p.open_pl_in_money(scope) == pytest.approx(before.profit - 0.04)
        assert await p.open_pl_in_pips(scope) == pytest.approx(-2)
        assert await p.open_pl_in_pips(
            scope, prices={"EURUSD": 1.1012}
        ) == pytest.approx(10)
        assert await p.open_pl_in_money(
            scope, prices={"EURUSD": 1.1012}
        ) == pytest.approx(1.96)
        assert client.positions()[0] == before
        with pytest.raises(KeyError):
            await p.open_pl_in_pips(scope, prices={})
        with pytest.raises(ValueError, match="valuation"):
            await p.open_pl_in_money(scope, prices={"EURUSD": float("nan")})

    asyncio.run(scenario())


def test_bar_counts_use_real_chart_boundaries_and_explicit_time(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)
    bars = [START, START + timedelta(minutes=5), START + timedelta(days=3)]

    async def scenario():
        await trading.trade.enter_at_market("EURUSD", 1, 0.01, magic=42)
        client.set_clock(bars[-1])
        assert (
            await trading.position.bars_since_order_open(scope, bars, as_of=bars[-1])
            == 2
        )
        assert (
            await trading.position.bars_since_order_open(scope, [START], as_of=START)
            == 0
        )
        with pytest.raises(ValueError, match="cover"):
            await trading.position.bars_since_order_open(
                scope, bars[1:], as_of=bars[-1]
            )
        with pytest.raises(ValueError, match="oldest"):
            await trading.position.bars_since_order_open(
                scope, list(reversed(bars)), as_of=bars[-1]
            )
        with pytest.raises(ValueError, match="evaluation"):
            await trading.position.bars_since_order_open(scope, bars, as_of=START)

    asyncio.run(scenario())


def test_partial_close_only_becomes_history_when_flat_and_costs_reconcile(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42, comment="entry")

    async def scenario():
        await trading.trade.enter_at_market(
            "EURUSD", 1, 0.03, magic=42, comment="entry"
        )
        client.feed_tick(
            "EURUSD", bid=1.1012, ask=1.1014, time=START + timedelta(minutes=1)
        )
        await trading.trade.close_position(scope, volume=0.01)
        assert await trading.history_order.closed_trades(scope) == []
        assert client.positions()[0].commission == pytest.approx(-0.04)
        await trading.trade.close_position(scope)
        h = trading.history_order
        trades = await h.closed_trades(scope)
        assert len(trades) == 1
        trade = trades[0]
        assert trade.direction == 1 and trade.magic == 42 and trade.comment == "entry"
        assert trade.volume == pytest.approx(0.03)
        assert trade.commission == pytest.approx(-0.12)
        assert await h.closed_pl_in_money(scope) == pytest.approx(
            client.account().balance - 10000
        )
        assert await h.closed_pl_in_pips(scope) == pytest.approx(10)
        assert await h.last_order_was(scope, 1)
        assert not await h.last_order_was(scope, -1)
        assert await h.last_order_was_not(scope, -1)
        assert not await h.last_order_was_not(scope, 1)
        assert (
            await h.closed_trades(TradeFilter("EURUSD", ticket=trade.position_id))
            == trades
        )
        assert await h.closed_trades(scope, as_of=START) == []

    asyncio.run(scenario())


def test_trades_ago_recent_close_and_no_future_leak(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)
    closed_at = START + timedelta(minutes=1, milliseconds=123)

    async def scenario():
        t, h = trading.trade, trading.history_order
        await t.enter_at_market("EURUSD", 1, 0.01, magic=42)
        client.set_clock(closed_at)
        await t.close_position(scope)
        client.set_clock(START + timedelta(minutes=2))
        await t.enter_at_market("EURUSD", -1, 0.01, magic=42)
        client.set_clock(START + timedelta(minutes=3))
        await t.close_position(scope)
        assert await h.last_order_was(scope, -1)
        assert await h.last_order_was(scope, 1, as_of=closed_at)
        assert await h.closed_pl_in_money(scope, trades_ago=2) == 0
        assert await h.closed_pl_in_money(scope, trades_ago=1) < 0
        before = closed_at - timedelta(milliseconds=1)
        assert not await h.trade_recently_closed(scope, as_of=before, bar_start=START)
        assert await h.trade_recently_closed(scope, as_of=closed_at, bar_start=START)
        assert await h.trade_recently_closed(scope, as_of=closed_at, bar_start=START)
        assert not await h.no_trade_recently_closed(
            scope, as_of=closed_at, bar_start=START
        )
        assert not await h.trade_recently_closed(
            scope, as_of=START + timedelta(minutes=4), check_this_bar=False
        )
        assert not await h.trade_recently_closed(
            scope, as_of=closed_at, check_this_bar=False, check_this_minute=False
        )
        bars = [START, START + timedelta(minutes=1), START + timedelta(minutes=2)]
        assert await h.bars_since_order_closed(scope, bars, as_of=bars[-1]) == 1
        with pytest.raises(ValueError, match="trades_ago"):
            await h.closed_pl_in_money(scope, trades_ago=-1)
        with pytest.raises(ValueError, match="bar_start"):
            await h.trade_recently_closed(scope, as_of=closed_at)
        with pytest.raises(ValueError, match="timezone"):
            await h.closed_pl_in_money(scope, as_of=START.replace(tzinfo=None))

    asyncio.run(scenario())


def test_cancelled_pending_orders_never_count_as_completed_trades(setup):
    trading, _client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await trading.trade.enter_at_limit("EURUSD", 1, 0.01, 1.09, magic=42)
        await trading.trade.cancel_all_pending_orders(scope)
        assert await trading.history_order.closed_trades(scope) == []
        assert not await trading.history_order.last_order_was_not(scope, 1)

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
        t = trading.trade
        await t.enter_at_market("EURUSD", 1, 0.01, magic=2)
        await t.enter_at_market("EURUSD", 1, 0.02, magic=2, allow_duplicate_trades=True)
        await t.enter_at_market(
            "EURUSD", -1, 0.04, magic=2, allow_duplicate_trades=True
        )
        await t.close_all_positions(scope)
        trades = await trading.history_order.closed_trades(scope)
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
        trades = await trading.history_order.closed_trades(
            TradeFilter("EURUSD", magic=42)
        )
        assert [trade.direction for trade in trades] == [1, -1]
        assert trades[0].comment == "owned"
        assert [trade.net_profit for trade in trades] == pytest.approx([994, 497])
        assert sum(t.commission + t.fee for t in trades) == pytest.approx(-9)
        assert (
            len(
                await trading.history_order.closed_trades(
                    TradeFilter("EURUSD", comment="owned")
                )
            )
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
                await trading.history_order.closed_trades(scope)
            assert error.value.code == code

    asyncio.run(scenario())


def test_unavailable_history_and_profit_calculation_are_not_zero_results():
    from app.workspace.brokers.base import TradingClient

    client = TradingClient("unsupported")
    trading = Trading(client)

    async def scenario():
        with pytest.raises(BridgeError) as error:
            await trading.history_order.closed_trades(TradeFilter("EURUSD"))
        assert error.value.code == "UNSUPPORTED_OPERATION"
        with pytest.raises(BridgeError) as error:
            await trading.account.OrderProfitCheck("EURUSD", 0, 1.0, 1.1, 1.2)
        assert error.value.code == "UNSUPPORTED_OPERATION"

    asyncio.run(scenario())
