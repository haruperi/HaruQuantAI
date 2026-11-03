"""Unit tests for RiskGuard pre-trade sanity and circuit breaker enforcement."""

from __future__ import annotations

import asyncio
from typing import override

from app.core.enums import OrderType, TradeAction, TradeRetcode
from app.core.trading.connection.base import TradingClient
from app.core.trading.connection.contracts import (
    OrderInfo,
    PositionInfo,
    TradeRequest,
    TradeResult,
)
from app.core.trading.strategy.contracts import OrderRequest
from app.workspace.trading.risk_guard import RiskGuard, RiskLimits


class MockRiskClient(TradingClient):
    """Mock client for testing emergency flatten and cancel actions."""

    def __init__(self) -> None:
        super().__init__("MockRiskClient")
        self.positions: list[PositionInfo] = [
            PositionInfo(ticket=101, symbol="EURUSD", volume=1.0, position_type=0),
            PositionInfo(ticket=102, symbol="GBPUSD", volume=0.5, position_type=1),
        ]
        self.orders: list[OrderInfo] = [
            OrderInfo(ticket=201, symbol="EURUSD", volume_initial=1.0),
        ]
        self.sent_requests: list[TradeRequest] = []

    @override
    def get_positions(self) -> list[PositionInfo]:
        return list(self.positions)

    @override
    def get_orders(self) -> list[OrderInfo]:
        return list(self.orders)

    @override
    def order_send(self, request: TradeRequest) -> TradeResult:
        self.sent_requests.append(request)
        return TradeResult(retcode=int(TradeRetcode.DONE))


def test_order_sanity_validation() -> None:
    guard = RiskGuard(
        RiskLimits(max_volume_per_order=5.0, max_open_positions_per_symbol=3)
    )

    valid_order = OrderRequest(
        symbol="EURUSD",
        direction=1,
        order_type=OrderType.BUY,
        volume=2.0,
    )
    assert guard.validate_order(valid_order, current_positions_count=1) is True

    # Volume exceeded
    large_order = OrderRequest(
        symbol="EURUSD",
        direction=1,
        order_type=OrderType.BUY,
        volume=6.0,
    )
    assert guard.validate_order(large_order, current_positions_count=1) is False

    # Negative volume
    bad_vol = OrderRequest(
        symbol="EURUSD",
        direction=1,
        order_type=OrderType.BUY,
        volume=-1.0,
    )
    assert guard.validate_order(bad_vol, current_positions_count=1) is False

    # Max positions exceeded
    assert guard.validate_order(valid_order, current_positions_count=3) is False


def _is_tripped(guard: RiskGuard) -> bool:
    return bool(guard.is_tripped)


def test_circuit_breaker_drawdown_trigger() -> None:
    guard = RiskGuard(RiskLimits(max_drawdown_pct=0.10))  # 10% max drawdown

    # Peak equity: 100k
    guard.update_equity(100000.0)
    assert not _is_tripped(guard)

    # Slight drawdown to 95k (5%) -> not tripped
    guard.update_equity(95000.0)
    assert not _is_tripped(guard)

    # New peak: 110k
    guard.update_equity(110000.0)

    # Drawdown to 98k (10.9% from 110k) -> trips circuit breaker
    tripped = guard.update_equity(98000.0)
    assert tripped is True
    assert _is_tripped(guard)

    # Orders must be rejected while tripped
    order = OrderRequest(
        symbol="EURUSD",
        direction=1,
        order_type=OrderType.BUY,
        volume=1.0,
    )
    assert guard.validate_order(order, current_positions_count=0) is False

    # Reset circuit breaker
    guard.reset_circuit_breaker()
    assert not _is_tripped(guard)
    assert guard.validate_order(order, current_positions_count=0) is True


def test_emergency_flatten_and_cancel() -> None:
    async def scenario() -> None:
        guard = RiskGuard()
        client = MockRiskClient()

        # Flatten all
        results = await guard.flatten_all(client)
        assert len(results) == 2
        assert all(r.retcode == int(TradeRetcode.DONE) for r in results)
        assert len(client.sent_requests) == 2
        assert client.sent_requests[0].action == TradeAction.DEAL
        assert client.sent_requests[0].position == 101
        assert client.sent_requests[1].position == 102

        # Cancel all
        cancel_results = await guard.cancel_all(client)
        assert len(cancel_results) == 1
        assert client.sent_requests[-1].action == TradeAction.REMOVE
        assert client.sent_requests[-1].order == 201

    asyncio.run(scenario())
