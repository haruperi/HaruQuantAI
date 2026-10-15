"""Unit tests for SimulationBackend and _simulation_api dispatch models.

Description:
    Validates in-memory execution, tick feeding, market order placement,
    pending orders, position management, deals, mark-to-market calculations,
    and unified snapshot data structures in SimulationBackend.

Purpose:
    FEAT-BROKER-SIMULATION-TESTS: Verification suite for simulation backend.

Key Capabilities:
    - FR-SIMULATION-MODELS: Verify snapshot models (OrderSnapshot, PositionSnapshot,
      DealSnapshot, SymbolSnapshot, MarketTick) returned directly by simulator.
    - FR-SIMULATION-EXECUTION: Verify order lifecycle, execution fills, and stops.
    - FR-SIMULATION-DISPATCH: Verify async call dispatch with execution receipts.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/test_broker_simulator.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_broker_simulator.py --no-cov
    ```
"""

from __future__ import annotations

import pytest
from app.services.brokers.simulator import SimulationBackend
from app.services.trading import (
    DealEntry,
    DealSnapshot,
    DealType,
    MarginMode,
    OrderFilling,
    OrderSnapshot,
    OrderState,
    OrderTime,
    OrderType,
    PositionSnapshot,
    PositionType,
    ReceiptStatus,
    SymbolSnapshot,
    TradeAction,
    TradeRequest,
    TradeRetcode,
)
from app.workspace.data_manager.contracts import MarketTick


@pytest.fixture
def sim_backend() -> SimulationBackend:
    """Provide an armed and connected SimulationBackend with EURUSD registered."""
    backend = SimulationBackend(
        initial_balance=10_000.0,
        leverage=100,
        margin_mode=MarginMode.RETAIL_HEDGING,
        currency="USD",
    )
    backend.connect()
    backend.arm()
    backend.add_symbol(
        SymbolSnapshot(
            name="EURUSD",
            point=0.00001,
            digits=5,
            trade_contract_size=100_000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            trade_stops_level=5,
        )
    )
    backend.feed_tick("EURUSD", bid=1.1000, ask=1.1002, volume=1.0)
    return backend


class TestSimulationBackendModels:
    """Verify that backend methods operate on and return unified snapshot models."""

    def test_symbol_and_tick_models(self, sim_backend: SimulationBackend) -> None:
        """Verify symbol lookups and ticks return snapshot models."""
        spec = sim_backend.symbol("EURUSD")
        assert spec is not None
        assert isinstance(spec, SymbolSnapshot)
        assert spec.name == "EURUSD"
        assert spec.digits == 5

        symbols = sim_backend.symbols()
        assert len(symbols) == 1
        assert isinstance(symbols[0], SymbolSnapshot)

        tick = sim_backend.tick("EURUSD")
        assert tick is not None
        assert isinstance(tick, MarketTick)
        assert tick.bid == 1.1000
        assert tick.ask == 1.1002
        assert tick.time_msc > 0

    def test_market_buy_and_position_deal_models(
        self, sim_backend: SimulationBackend
    ) -> None:
        """Verify market execution creates PositionSnapshot and DealSnapshot."""
        req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.BUY,
        )
        res = sim_backend.order_send(req)
        assert res.retcode == int(TradeRetcode.DONE)
        assert res.deal > 0
        assert res.order > 0

        positions = sim_backend.positions()
        assert len(positions) == 1
        pos = positions[0]
        assert isinstance(pos, PositionSnapshot)
        assert pos.symbol == "EURUSD"
        assert pos.position_type == int(PositionType.BUY)
        assert pos.volume == 0.1
        assert pos.price_open == 1.1002
        assert pos.time > 0
        assert pos.time_msc > 0

        deals = sim_backend.deals()
        assert len(deals) == 1
        deal = deals[0]
        assert isinstance(deal, DealSnapshot)
        assert deal.deal_type == int(DealType.BUY)
        assert deal.entry == int(DealEntry.IN)
        assert deal.volume == 0.1
        assert deal.price == 1.1002

    def test_market_close_deal_model(self, sim_backend: SimulationBackend) -> None:
        """Verify closing a position creates an OUT deal and clears the position."""
        open_req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.BUY,
        )
        sim_backend.order_send(open_req)
        pos = sim_backend.positions()[0]

        # Feed new price with profit
        sim_backend.feed_tick("EURUSD", bid=1.1010, ask=1.1012, volume=1.0)

        close_req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=0.1,
            order_type=OrderType.SELL,
            position=pos.ticket,
        )
        close_res = sim_backend.order_send(close_req)
        assert close_res.retcode == int(TradeRetcode.DONE)

        assert len(sim_backend.positions()) == 0
        deals = sim_backend.deals()
        assert len(deals) == 2
        out_deal = deals[1]
        assert isinstance(out_deal, DealSnapshot)
        assert out_deal.entry == int(DealEntry.OUT)
        assert out_deal.profit > 0.0

    def test_pending_order_models_and_expiration(
        self, sim_backend: SimulationBackend
    ) -> None:
        """Verify pending order placement returns OrderSnapshot and tracks history."""
        req = TradeRequest(
            action=TradeAction.PENDING,
            symbol="EURUSD",
            volume=0.05,
            order_type=OrderType.BUY_LIMIT,
            price=1.0950,
            type_filling=OrderFilling.FOK,
            type_time=OrderTime.GTC,
        )
        res = sim_backend.order_send(req)
        assert res.retcode == int(TradeRetcode.PLACED)
        assert res.order > 0

        orders = sim_backend.orders()
        assert len(orders) == 1
        ord_snapshot = orders[0]
        assert isinstance(ord_snapshot, OrderSnapshot)
        assert ord_snapshot.state == int(OrderState.PLACED)
        assert ord_snapshot.price_open == 1.0950

        # Cancel the pending order
        cancel_req = TradeRequest(action=TradeAction.REMOVE, order=ord_snapshot.ticket)
        cancel_res = sim_backend.order_send(cancel_req)
        assert cancel_res.retcode == int(TradeRetcode.DONE)

        assert len(sim_backend.orders()) == 0
        hist_orders = sim_backend.history_orders()
        assert len(hist_orders) == 1
        canceled_ord = hist_orders[0]
        assert isinstance(canceled_ord, OrderSnapshot)
        assert canceled_ord.state == int(OrderState.CANCELED)


class TestSimulationBackendDispatch:
    """Verify asynchronous call dispatch and receipts."""

    @pytest.mark.anyio
    async def test_call_symbol_info(self, sim_backend: SimulationBackend) -> None:
        """Verify SymbolInfo dispatch via call returns structured data."""
        res = await sim_backend.call(
            object_id="sym_1",
            class_name="SymbolInfo",
            method_name="Name",
            args=["EURUSD"],
        )
        assert res is True
        last_cmd = sim_backend.last_command_id()
        assert last_cmd is not None
        receipt = sim_backend.receipt(last_cmd)
        assert receipt is not None
        assert receipt.status == ReceiptStatus.RESOLVED

    @pytest.mark.anyio
    async def test_call_account_info(self, sim_backend: SimulationBackend) -> None:
        """Verify AccountInfo dispatch via call."""
        info = await sim_backend.call(
            object_id="acc_1",
            class_name="AccountInfo",
            method_name="AccountInfo",
            args=[],
        )
        balance = info.balance if hasattr(info, "balance") else info["balance"]
        assert balance == 10_000.0

    @pytest.mark.anyio
    async def test_call_trade_order_send(self, sim_backend: SimulationBackend) -> None:
        """Verify Trade.OrderSend dispatch via call creates event and receipt."""
        res = await sim_backend.call(
            object_id="trade_1",
            class_name="Trade",
            method_name="OrderSend",
            args=[
                {
                    "action": int(TradeAction.DEAL),
                    "symbol": "EURUSD",
                    "volume": 0.1,
                    "order_type": int(OrderType.BUY),
                }
            ],
            requires_arm=True,
        )
        retcode = res.retcode if hasattr(res, "retcode") else res.get("retcode")
        assert retcode == int(TradeRetcode.DONE)
