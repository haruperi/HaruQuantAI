"""Verify canonical async trading against real local model scenarios.

Description:
    Exercise isolated simulator account, selection and execution state without
    sockets, live authorization or production databases.

Purpose:
    FEAT-TRADING-SIMULATION: Validate local native-style trading behavior.

Key Capabilities:
    - FR-TRADING-SIMULATION-SCENARIOS: Exercise actual order/position lifecycles.
      Associated: `Trading`, `SimulationBackend`
      Logging: Backend emits dispatch metadata; tests assert visible state/results.

Python API Usage:
    Run through pytest with externally supplied simulation ticks and time.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_simulator.py --no-cov
"""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from app.services.brokers.contracts import (
    BridgeError,
    MarginMode,
    OrderTime,
    OrderType,
    ReceiptStatus,
    SymbolSpec,
    TradeAction,
)
from app.services.brokers.simulator import SimulationBackend
from app.services.libs.trading import (
    SymbolInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    Trading,
)


@pytest.mark.parametrize("mode", [MarginMode.RETAIL_HEDGING, MarginMode.RETAIL_NETTING])
def test_market_positions_history_and_clock(mode: MarginMode) -> None:
    """Real local fills expose the same async classes and isolated state."""

    async def scenario() -> None:
        backend = SimulationBackend(margin_mode=mode)
        backend.add_symbol(SymbolSpec(name="EURUSD"))
        now = datetime(2026, 1, 1, tzinfo=UTC)
        backend.feed_tick("EURUSD", bid=1.1, ask=1.1002, time=now)
        async with Trading(backend) as trading:
            assert (await trading.account.AccountInfo()).balance == 10_000
            assert await trading.symbol.Name("EURUSD") is True
            assert await trading.symbol.Name() == "EURUSD"
            info = await trading.symbol.SymbolInfo()
            assert info.bid == 1.1
            assert info.time == int(now.timestamp())
            separate = SymbolInfo(backend)
            assert await separate.Name() == ""
            assert info.point == 0.00001
            buy_req = TradeRequest(
                action=TradeAction.DEAL,
                symbol="EURUSD",
                volume=0.1,
                order_type=OrderType.BUY,
                price=1.1002,
            )
            with pytest.raises(BridgeError, match="disarmed"):
                await trading.trade.OrderSend(buy_req)
            trading.arm()
            res = await trading.trade.OrderSend(buy_req)
            assert res.retcode == 10009
            command = trading.trade.last_command_id
            assert command is not None
            receipt = backend.receipt(command)
            assert receipt is not None
            assert receipt.status == ReceiptStatus.RESOLVED
            assert (await trading.trade.Result()).retcode == 10009
            assert isinstance(await trading.trade.Request(), TradeRequest)
            assert isinstance(await trading.trade.Result(), TradeResult)
            assert isinstance(await trading.trade.CheckResult(), TradeCheckResult)
            assert await trading.position.Select("EURUSD")
            assert (await trading.position.PositionInfo()).volume == 0.1
            assert await trading.position.SelectByIndex(0)
            ticket = (await trading.position.PositionInfo()).ticket
            assert ticket > 0
            assert await trading.position.StoreState() is True
            assert await trading.position.CheckState()
            if mode == MarginMode.RETAIL_HEDGING:
                res_partial = await trading.trade.OrderSend(
                    TradeRequest(
                        action=TradeAction.DEAL,
                        symbol="EURUSD",
                        volume=0.04,
                        order_type=OrderType.SELL,
                        price=1.1,
                        position=ticket,
                    )
                )
                assert res_partial.retcode == 10009
                assert await trading.position.Select("EURUSD")
                assert (await trading.position.PositionInfo()).volume == pytest.approx(
                    0.06
                )
            res_close = await trading.trade.OrderSend(
                TradeRequest(
                    action=TradeAction.DEAL,
                    symbol="EURUSD",
                    volume=0.06 if mode == MarginMode.RETAIL_HEDGING else 0.1,
                    order_type=OrderType.SELL,
                    price=1.1,
                    position=ticket,
                )
            )
            assert res_close.retcode == 10009
            assert backend.positions() == []
            assert await trading.history_order.SelectByIndex(0)
            assert await trading.history_order.Ticket() > 0
            assert await trading.deal.SelectByIndex(0)
            assert (await trading.deal.DealInfo()).commission == 0.0
            assert (await trading.symbol.SymbolInfo()).time == int(now.timestamp())

    asyncio.run(scenario())


def test_pending_modify_cancel_trigger_and_expiration() -> None:
    """Pending orders respond only to caller-supplied ticks and time."""

    async def scenario() -> None:
        backend = SimulationBackend()
        backend.add_symbol(SymbolSpec(name="EURUSD"))
        now = datetime(2026, 1, 1, tzinfo=UTC)
        backend.feed_tick("EURUSD", bid=1.1, ask=1.1002, time=now)
        trading = Trading(backend)
        trading.arm()
        limit_req = TradeRequest(
            action=TradeAction.PENDING,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.BUY_LIMIT,
            price=1.09,
        )
        res = await trading.trade(limit_req)
        assert res.retcode == 10008
        assert await trading.order.SelectByIndex(0)
        ticket = (await trading.order.OrderInfo()).ticket
        mod_req = TradeRequest(
            action=TradeAction.MODIFY,
            order=ticket,
            price=1.08,
            symbol="EURUSD",
        )
        res_mod = await trading.trade.OrderSend(mod_req)
        assert res_mod.retcode == 10009
        del_req = TradeRequest(
            action=TradeAction.REMOVE,
            order=ticket,
            symbol="EURUSD",
        )
        res_del = await trading.trade.OrderSend(del_req)
        assert res_del.retcode == 10009
        assert backend.orders() == []
        stop_req = TradeRequest(
            action=TradeAction.PENDING,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.BUY_STOP,
            price=1.11,
        )
        assert (await trading.trade.OrderSend(stop_req)).retcode == 10008
        backend.feed_tick(
            "EURUSD", bid=1.111, ask=1.1112, time=now + timedelta(seconds=1)
        )
        assert backend.orders() == []
        assert len(backend.positions()) == 1
        pos_ticket = backend.positions()[0].ticket
        close_req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.SELL,
            price=1.111,
            position=pos_ticket,
        )
        assert (await trading.trade.OrderSend(close_req)).retcode == 10009
        limit_exp_req = TradeRequest(
            action=TradeAction.PENDING,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.BUY_LIMIT,
            price=1.09,
            type_time=OrderTime.SPECIFIED,
            expiration=now + timedelta(minutes=1),
        )
        assert (await trading.trade.OrderSend(limit_exp_req)).retcode == 10008
        backend.set_clock(now + timedelta(minutes=2))
        assert backend.orders() == []
        assert backend.positions() == []
        await trading.close()

    asyncio.run(scenario())


def test_rejection_and_unknown_operation() -> None:
    """Fail closed on insufficient funds and unsupported operations."""

    async def scenario() -> None:
        backend = SimulationBackend(initial_balance=1)
        backend.add_symbol(SymbolSpec(name="EURUSD"))
        backend.feed_tick("EURUSD", bid=1.1, ask=1.1002)
        trading = Trading(backend)
        trading.arm()
        bad_req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=1.0,
            order_type=OrderType.BUY,
            price=1.1002,
        )
        bad_res = await trading.trade.OrderSend(bad_req)
        assert bad_res.retcode == 10019
        assert (await trading.trade.Result()).retcode == 10019
        assert backend.positions() == []
        with pytest.raises(BridgeError, match="unsupported"):
            await backend.call(
                object_id="test", class_name="Trade", method_name="Unknown", args=[]
            )
        with pytest.raises(BridgeError, match="unsupported"):
            await backend.call(
                object_id="test",
                class_name="OrderInfo",
                method_name="InfoInteger",
                args=[999],
            )
        assert (await trading.terminal.TerminalInfo()).connected is True
        with pytest.raises(BridgeError, match="queued asynchronous"):
            await trading.trade.SetAsyncMode(True)
        assert backend.positions() == []
        await trading.close()

    asyncio.run(scenario())


def test_stops_close_by_and_local_events() -> None:
    """Stops and close-by alter only the local model and emit local events."""

    async def scenario() -> None:
        backend = SimulationBackend()
        backend.add_symbol(SymbolSpec(name="EURUSD"))
        backend.feed_tick("EURUSD", bid=1.1, ask=1.1002)
        trading = Trading(backend)
        trading.arm()
        buy_req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.BUY,
            price=1.1002,
            sl=1.09,
            tp=1.12,
        )
        assert (await trading.trade.OrderSend(buy_req)).retcode == 10009
        event = await backend.next_event(timeout=0.1)
        assert event.event_type == "simulation_transaction"
        backend.feed_tick("EURUSD", bid=1.121, ask=1.1212)
        assert backend.positions() == []
        assert (
            await trading.trade.OrderSend(
                TradeRequest(
                    action=TradeAction.DEAL,
                    symbol="EURUSD",
                    volume=0.1,
                    order_type=OrderType.BUY,
                    price=1.1212,
                )
            )
        ).retcode == 10009
        assert (
            await trading.trade.OrderSend(
                TradeRequest(
                    action=TradeAction.DEAL,
                    symbol="EURUSD",
                    volume=0.1,
                    order_type=OrderType.SELL,
                    price=1.121,
                )
            )
        ).retcode == 10009
        positions = backend.positions()
        assert len(positions) == 2
        close_by_req = TradeRequest(
            action=TradeAction.CLOSE_BY,
            symbol="EURUSD",
            position=positions[0].ticket,
            position_by=positions[1].ticket,
        )
        assert (await trading.trade.OrderSend(close_by_req)).retcode == 10009
        assert backend.positions() == []
        with pytest.raises(BridgeError, match="unsupported"):
            await backend.call(
                object_id="test",
                class_name="SymbolInfo",
                method_name="InfoDouble",
                args=["does_not_exist"],
            )
        await trading.close()

    asyncio.run(scenario())
