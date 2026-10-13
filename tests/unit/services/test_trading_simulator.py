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
    PropertyValue,
    ReceiptStatus,
    SymbolSpec,
)
from app.services.brokers.simulator import SimulationBackend
from app.services.trading import SymbolInfo, Trading


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
            assert await trading.symbol.Bid() == 1.1
            assert await trading.symbol.Time() == int(now.timestamp())
            separate = SymbolInfo(backend)
            assert await separate.Name() == ""
            assert await trading.symbol.InfoDouble("point") == PropertyValue(
                ok=True, value=0.00001
            )
            with pytest.raises(BridgeError, match="disarmed"):
                await trading.trade.Buy(0.1, "EURUSD")
            trading.arm()
            assert await trading.trade.Buy(0.1, "EURUSD")
            command = trading.trade.last_command_id
            assert command is not None
            receipt = backend.receipt(command)
            assert receipt is not None
            assert receipt.status == ReceiptStatus.RESOLVED
            assert await trading.trade.ResultRetcode() == 10009
            assert isinstance(await trading.trade.Request(), dict)
            assert isinstance(await trading.trade.Result(), dict)
            assert isinstance(await trading.trade.CheckResult(), dict)
            assert await trading.position.Select("EURUSD")
            assert await trading.position.Volume() == 0.1
            ticket = await trading.position.SelectByIndex(0)
            assert ticket
            assert await trading.position.StoreState() is True
            assert await trading.position.CheckState()
            if mode == MarginMode.RETAIL_HEDGING:
                assert await trading.trade.PositionClosePartial("EURUSD", 0.04)
                assert await trading.position.Select("EURUSD")
                assert await trading.position.Volume() == pytest.approx(0.06)
            assert await trading.trade.PositionClose("EURUSD")
            assert backend.positions() == []
            assert await trading.history_order.SelectByIndex(0)
            assert await trading.history_order.Ticket() > 0
            assert await trading.deal.SelectByIndex(0)
            assert await trading.deal.Commission() == await trading.deal.Commision()
            assert await trading.symbol.Time() == int(now.timestamp())

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
        assert await trading.trade("buy_limit", "EURUSD", 0.1, price=1.09)
        assert await trading.order.SelectByIndex(0)
        ticket = await trading.order.Ticket()
        assert await trading.trade.OrderModify(ticket, 1.08, 0.0, 0.0)
        assert await trading.trade.OrderDelete(ticket)
        assert backend.orders() == []
        assert await trading.trade.BuyStop(0.1, 1.11, "EURUSD")
        backend.feed_tick(
            "EURUSD", bid=1.111, ask=1.1112, time=now + timedelta(seconds=1)
        )
        assert backend.orders() == []
        assert len(backend.positions()) == 1
        assert await trading.trade.PositionClose("EURUSD")
        assert await trading.trade.BuyLimit(
            0.1,
            1.09,
            "EURUSD",
            0.0,
            0.0,
            OrderTime.SPECIFIED,
            now + timedelta(minutes=1),
        )
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
        assert not await trading.trade.Buy(1.0, "EURUSD")
        assert await trading.trade.ResultRetcode() == 10019
        assert backend.positions() == []
        with pytest.raises(BridgeError, match="unsupported"):
            await backend.call(
                object_id="test", class_name="Trade", method_name="Unknown", args=[]
            )
        with pytest.raises(BridgeError, match="numeric property"):
            await trading.symbol.InfoInteger(999)
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
        assert await trading.trade.Buy(0.1, "EURUSD", 0.0, 1.09, 1.12)
        event = await backend.next_event(timeout=0.1)
        assert event.event_type == "simulation_transaction"
        backend.feed_tick("EURUSD", bid=1.121, ask=1.1212)
        assert backend.positions() == []
        assert await trading.trade.Buy(0.1, "EURUSD")
        assert await trading.trade.Sell(0.1, "EURUSD")
        positions = backend.positions()
        assert len(positions) == 2
        assert await trading.trade.PositionCloseBy(
            positions[0].ticket, positions[1].ticket
        )
        assert backend.positions() == []
        with pytest.raises(BridgeError, match="unsupported"):
            await trading.symbol.InfoDouble("does_not_exist")
        await trading.close()

    asyncio.run(scenario())
