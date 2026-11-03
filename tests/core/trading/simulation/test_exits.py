"""Shared exit-policy behavior over typed and dictionary broker responses."""

import asyncio
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import app.workspace.trading.exits as exit_runtime
import pytest
from app.core.data.contracts import SymbolInfo
from app.core.enums import TradeRetcode
from app.core.trading.connection.contracts import TradeResult
from app.core.trading.simulation.client import SimulatorClient
from app.extend.blocks.order.close.close_all_positions import close_all_positions
from app.extend.blocks.order.open.enter_at_limit import enter_at_limit
from app.extend.blocks.order.open.enter_at_market import enter_at_market
from app.extend.functions.order_functions import TradeFilter
from app.workspace.trading import (
    ExitAfterBars,
    ExitPlan,
    MoveSL2BE,
    ProfitTarget,
    StopLoss,
    Trading,
    TrailingStop,
)

START = datetime(2026, 10, 27, 10, tzinfo=UTC)


class WireBackend:
    """Exercise dictionary decoding without connecting to a live broker."""

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
    client = SimulatorClient()
    client.set_clock(START)
    client.add_symbol(SymbolInfo(name="EURUSD"))
    client.feed_tick("EURUSD", bid=1.1, ask=1.1002)
    trading = Trading(WireBackend(client) if request.param else client)
    trading.arm()
    return trading, client


def test_initial_protection_idempotence_and_no_stop_loosening(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=43)
        attached = await trading.exits.attach(
            scope, ExitPlan(stop_loss=StopLoss(1.09), profit_target=ProfitTarget(1.12))
        )
        assert len(attached) == 1
        outcomes = await trading.exits.evaluate(as_of=START)
        assert [o.action for o in outcomes] == ["stop_loss", "profit_target"]
        assert all(o.result.retcode == TradeRetcode.DONE for o in outcomes)
        mine = next(p for p in client.positions() if p.magic == 42)
        other = next(p for p in client.positions() if p.magic == 43)
        assert mine.sl == 1.09 and mine.tp == 1.12
        assert other.sl == 0 and other.tp == 0
        assert await trading.exits.evaluate(as_of=START) == []
        await trading.exits.attach(scope, ExitPlan(stop_loss=StopLoss(1.08)))
        assert await trading.exits.evaluate(as_of=START + timedelta(seconds=1)) == []
        assert next(p for p in client.positions() if p.magic == 42).sl == 1.09
        assert trading.exits.blocked_tickets == ()
        with pytest.raises(ValueError, match="backward"):
            await trading.exits.evaluate(as_of=START)

    asyncio.run(scenario())


@pytest.mark.parametrize("direction", [1, -1], ids=["long", "short"])
def test_break_even_and_trailing_coalesce_tighten_and_keep_state(setup, direction):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_market(trading, "EURUSD", direction, 0.01, magic=42)
        plan = ExitPlan(
            move_sl_to_be=MoveSL2BE(0.001, offset=0.0001),
            trailing_stop=TrailingStop(0.0005, activation=0.001),
        )
        await trading.exits.attach(scope, plan)
        assert await trading.exits.evaluate(as_of=START) == []
        if direction == 1:
            client.feed_tick("EURUSD", bid=1.1022, ask=1.1024)
            expected = 1.1017
        else:
            client.feed_tick("EURUSD", bid=1.0978, ask=1.0980)
            expected = 1.0985
        stamp = START + timedelta(seconds=1)
        outcomes = await trading.exits.evaluate(as_of=stamp)
        assert len(outcomes) == 1 and outcomes[0].action == "stop_loss"
        assert client.positions()[0].sl == pytest.approx(expected)
        # Reattach the same lifecycle, then retrace without crossing its stop.
        await trading.exits.attach(scope, plan)
        if direction == 1:
            client.feed_tick("EURUSD", bid=1.1020, ask=1.1022)
        else:
            client.feed_tick("EURUSD", bid=1.0980, ask=1.0982)
        assert await trading.exits.evaluate(as_of=stamp + timedelta(seconds=1)) == []
        assert client.positions()[0].sl == pytest.approx(expected)

    asyncio.run(scenario())


def test_bar_exit_has_priority_and_counts_chart_starts(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)
    second = START + timedelta(minutes=5)
    third = START + timedelta(days=3)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        await trading.exits.attach(
            scope, ExitPlan(exit_after_bars=ExitAfterBars(2), stop_loss=StopLoss(1.09))
        )
        with pytest.raises(ValueError, match="bar times"):
            await trading.exits.evaluate(as_of=second)
        outcomes = await trading.exits.evaluate(
            as_of=second, bar_times={"EURUSD": [START, second]}
        )
        assert [o.action for o in outcomes] == ["stop_loss"]
        client.set_clock(third)
        outcomes = await trading.exits.evaluate(
            as_of=third, bar_times={"EURUSD": [START, second, third]}
        )
        assert [o.action for o in outcomes] == ["close"]
        assert client.positions() == []
        assert trading.exits.blocked_tickets == ()
        assert await trading.exits.evaluate(as_of=third) == []

    asyncio.run(scenario())


def test_pending_attachment_and_same_ticket_protection_are_isolated(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_limit(trading, "EURUSD", 1, 0.01, 1.09, magic=42)
        assert (
            await trading.exits.attach(scope, ExitPlan(stop_loss=StopLoss(1.08))) == []
        )
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        position = client.positions()[0]
        # Exercise ticket collision between distinct position and pending-order spaces.
        pending = client.orders()[0]
        client._orders.pop(pending.ticket)
        pending.ticket = position.ticket
        client._orders[pending.ticket] = pending
        await trading.exits.attach(scope, ExitPlan(stop_loss=StopLoss(1.08)))
        await trading.exits.evaluate(as_of=START)
        assert client.positions()[0].sl == 1.08 and pending.sl == 0

    asyncio.run(scenario())


def test_decision_prices_do_not_mutate_quotes_and_respect_execution_distance(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        plan = ExitPlan(
            move_sl_to_be=MoveSL2BE(0.001, 0.0001),
            trailing_stop=TrailingStop(0.0001, activation=0.001),
        )
        await trading.exits.attach(scope, plan)
        client.feed_tick("EURUSD", bid=1.1013, ask=1.1015)
        client._symbols["EURUSD"].trade.stops_level = 50
        outcome = await trading.exits.evaluate(as_of=START, prices={"EURUSD": 1.1013})
        assert len(outcome) == 1
        # The trailing candidate is too close; the valid break-even candidate wins.
        assert client.positions()[0].sl == pytest.approx(1.1003)
        assert client.tick("EURUSD").bid == 1.1013
        with pytest.raises(KeyError):
            await trading.exits.evaluate(as_of=START + timedelta(seconds=1), prices={})
        with pytest.raises(ValueError, match="timezone"):
            await trading.exits.evaluate(as_of=START.replace(tzinfo=None))

    asyncio.run(scenario())


def test_rejected_or_unconfirmed_actions_block_until_explicit_resume(
    setup,
    monkeypatch,
):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        ticket = client.positions()[0].ticket
        await trading.exits.attach(
            scope, ExitPlan(stop_loss=StopLoss(1.09), profit_target=ProfitTarget(1.12))
        )
        monkeypatch.setattr(exit_runtime, "set_stop_loss", exit_runtime.set_stop_loss)
        monkeypatch.setattr(
            exit_runtime, "set_profit_target", exit_runtime.set_profit_target
        )
        original = exit_runtime.set_stop_loss
        exit_runtime.set_stop_loss = AsyncMock(
            return_value=[TradeResult(retcode=TradeRetcode.REJECT)]
        )
        target = exit_runtime.set_profit_target
        exit_runtime.set_profit_target = AsyncMock()
        result = await trading.exits.evaluate(as_of=START)
        assert len(result) == 1
        assert trading.exits.blocked_tickets == (ticket,)
        exit_runtime.set_profit_target.assert_not_awaited()
        assert await trading.exits.evaluate(as_of=START + timedelta(seconds=1)) == []
        assert exit_runtime.set_stop_loss.await_count == 1
        trading.exits.resume(ticket)
        # DONE without applying the stop must also block.
        exit_runtime.set_stop_loss = AsyncMock(
            return_value=[TradeResult(retcode=TradeRetcode.DONE)]
        )
        await trading.exits.evaluate(as_of=START + timedelta(seconds=2))
        assert trading.exits.blocked_tickets == (ticket,)
        exit_runtime.set_stop_loss = original
        exit_runtime.set_profit_target = target
        trading.exits.resume(ticket)
        assert (
            len(await trading.exits.evaluate(as_of=START + timedelta(seconds=3))) == 2
        )
        assert trading.exits.blocked_tickets == ()

    asyncio.run(scenario())


def test_timeout_and_partial_close_do_not_retry(setup, monkeypatch):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)
    later = START + timedelta(minutes=1)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        ticket = client.positions()[0].ticket
        await trading.exits.attach(scope, ExitPlan(stop_loss=StopLoss(1.09)))
        monkeypatch.setattr(
            exit_runtime, "set_stop_loss", AsyncMock(side_effect=TimeoutError)
        )
        with pytest.raises(TimeoutError):
            await trading.exits.evaluate(as_of=START)
        assert trading.exits.blocked_tickets == (ticket,)
        assert await trading.exits.evaluate(as_of=later) == []
        await trading.exits.attach(scope, ExitPlan(exit_after_bars=ExitAfterBars(1)))
        trading.exits.resume(ticket)
        trading.trade.close = AsyncMock(
            return_value=TradeResult(retcode=TradeRetcode.DONE_PARTIAL)
        )
        outcomes = await trading.exits.evaluate(
            as_of=later, bar_times={"EURUSD": [START, later]}
        )
        assert outcomes[0].result.retcode == TradeRetcode.DONE_PARTIAL
        assert await trading.exits.evaluate(as_of=later + timedelta(seconds=1)) == []
        assert trading.trade.close.await_count == 1

    asyncio.run(scenario())


def test_concurrent_events_detach_and_new_lifecycle_reset(setup):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        ticket = client.positions()[0].ticket
        await trading.exits.attach(scope, ExitPlan(stop_loss=StopLoss(1.09)))
        outcomes = await asyncio.gather(
            *[trading.exits.evaluate(as_of=START) for _ in range(2)]
        )
        assert sum(len(result) for result in outcomes) == 1
        trading.exits.detach(ticket)
        assert await trading.exits.evaluate(as_of=START + timedelta(seconds=1)) == []
        await trading.exits.attach(scope, ExitPlan(stop_loss=StopLoss(1.09)))
        await close_all_positions(trading, scope)
        await enter_at_market(trading, "EURUSD", -1, 0.01, magic=42)
        assert await trading.exits.evaluate(as_of=START + timedelta(seconds=2)) == []
        assert client.positions()[0].sl == 0
        assert trading.exits.blocked_tickets == ()

    asyncio.run(scenario())


def test_market_closed_does_not_consume_event(setup):
    trading, client = setup

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        await trading.exits.attach(
            TradeFilter("EURUSD", magic=42), ExitPlan(stop_loss=StopLoss(1.09))
        )
        assert await trading.exits.evaluate(as_of=START, market_open=False) == []
        assert client.positions()[0].sl == 0
        assert len(await trading.exits.evaluate(as_of=START)) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "factory",
    [
        lambda: StopLoss(0),
        lambda: ProfitTarget(float("nan")),
        lambda: MoveSL2BE(-1),
        lambda: TrailingStop(0),
        lambda: ExitAfterBars(True),
        lambda: ExitAfterBars(-1),
    ],
)
def test_invalid_policy_configuration_is_rejected(factory):
    with pytest.raises(ValueError):
        factory()


def test_existing_tighter_stop_is_rechecked_before_dispatch(setup, monkeypatch):
    trading, client = setup
    scope = TradeFilter("EURUSD", magic=42)

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=42)
        await trading.exits.attach(scope, ExitPlan(stop_loss=StopLoss(1.09)))
        monkeypatch.setattr(exit_runtime, "set_stop_loss", exit_runtime.set_stop_loss)
        monkeypatch.setattr(
            exit_runtime, "set_profit_target", exit_runtime.set_profit_target
        )
        original = exit_runtime.set_stop_loss

        async def changed_between_decision_and_send(context, selected, price, **kwargs):
            await original(context, selected, 1.095, include_pending=False)
            return await original(context, selected, price, **kwargs)

        exit_runtime.set_stop_loss = changed_between_decision_and_send
        outcomes = await trading.exits.evaluate(as_of=START)
        assert outcomes[0].result.retcode == TradeRetcode.NO_CHANGES
        assert client.positions()[0].sl == 1.095
        assert trading.exits.blocked_tickets == ()
        exit_runtime.set_stop_loss = original
        assert (await original(trading, scope, 0, tighten_only=True))[
            0
        ].retcode == TradeRetcode.NO_CHANGES
        assert client.positions()[0].sl == 1.095

    asyncio.run(scenario())


def test_same_plan_has_independent_activation_per_position(setup):
    trading, client = setup

    async def scenario():
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=1)
        client.feed_tick("EURUSD", bid=1.1010, ask=1.1012)
        await enter_at_market(trading, "EURUSD", 1, 0.01, magic=2)
        await trading.exits.attach(
            TradeFilter("EURUSD"), ExitPlan(move_sl_to_be=MoveSL2BE(0.0005))
        )
        outcomes = await trading.exits.evaluate(as_of=START)
        assert len(outcomes) == 1
        first = next(p for p in client.positions() if p.magic == 1)
        second = next(p for p in client.positions() if p.magic == 2)
        assert first.sl == first.price_open
        assert second.sl == 0

    asyncio.run(scenario())
