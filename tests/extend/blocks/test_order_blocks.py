"""Unit tests for StrategyQuant-faithful order building blocks and facade.

Description:
    Tests direct invocation of all 12 order blocks, the unified Orders facade,
    protection modifying and tightening, pending order replacement, reverse at
    market, and non-silent requirement logging verification.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-ALL-PENDING
    - FR-ORDER-CLOSE-ALL-POSITIONS
    - FR-ORDER-CLOSE-BEST
    - FR-ORDER-CLOSE-PENDING
    - FR-ORDER-CLOSE-POSITION
    - FR-ORDER-CLOSE-WORST
    - FR-ORDER-SET-PROFIT-TARGET
    - FR-ORDER-SET-STOP-LOSS
    - FR-ORDER-ENTER-AT-LIMIT
    - FR-ORDER-ENTER-AT-MARKET
    - FR-ORDER-ENTER-AT-STOP
    - FR-ORDER-ENTER-REVERSE-AT-MARKET
    - FR-ORDER-FACADE
Python API Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from app.core.data.contracts import (
    SymbolInfo,
    SymbolPrice,
)
from app.core.enums import OrderType, TradeRetcode
from app.core.trading.connection.contracts import (
    OrderInfo,
    PositionInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.extend.blocks.order import (
    Orders,
    close_all_pending_orders,
    close_all_positions,
    close_best_position,
    close_pending_order,
    close_position,
    close_worst_position,
    enter_at_limit,
    enter_at_market,
    enter_at_stop,
    enter_reverse_at_market,
    set_profit_target,
    set_stop_loss,
)
from app.extend.functions.order_functions import TradeFilter


def make_mock_runtime(
    positions: list[PositionInfo] | None = None,
    orders: list[OrderInfo] | None = None,
    bid: float = 1.1000,
    ask: float = 1.1002,
    tick_step: float = 0.00001,
) -> SimpleNamespace:
    """Build a mock TradingRuntime for unit tests."""
    current_positions = list(positions or [])
    current_orders = list(orders or [])

    async def prepare_entry_request(
        symbol: str,
        direction: int,
        volume: float,
        buy_type: OrderType,
        *,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int | None = None,
        comment: str = "",
        expiration: Any = None,
    ) -> TradeRequest:
        ot = buy_type if direction == 1 else OrderType(int(buy_type) + 1)
        return TradeRequest(
            symbol=symbol,
            volume=volume,
            order_type=ot,
            price=price,
            sl=sl,
            tp=tp,
            magic=magic or 0,
            comment=comment,
            expiration=expiration,
        )

    async def send_checked(request: TradeRequest) -> TradeResult:
        return TradeResult(retcode=int(TradeRetcode.DONE), price=request.price)

    async def close(position: PositionInfo, volume: float | None = None) -> TradeResult:
        if position in current_positions:
            current_positions.remove(position)
        return TradeResult(
            retcode=int(TradeRetcode.DONE), volume=volume or position.volume
        )

    async def cancel(order: OrderInfo) -> TradeResult:
        if order in current_orders:
            current_orders.remove(order)
        return TradeResult(retcode=int(TradeRetcode.DONE))

    async def modify_protection(
        item: PositionInfo | OrderInfo,
        *,
        sl: float | None = None,
        tp: float | None = None,
    ) -> TradeResult:
        return TradeResult(retcode=int(TradeRetcode.DONE), price=sl or tp or 0.0)

    async def order_check(request: TradeRequest | dict[str, Any]) -> TradeCheckResult:
        return TradeCheckResult(retcode=0)

    trade = SimpleNamespace(
        operation_lock=asyncio.Lock(),
        prepare_entry_request=prepare_entry_request,
        send_checked=AsyncMock(side_effect=send_checked),
        close=AsyncMock(side_effect=close),
        cancel=AsyncMock(side_effect=cancel),
        modify_protection=AsyncMock(side_effect=modify_protection),
        OrderCheck=AsyncMock(side_effect=order_check),
    )

    position_src = SimpleNamespace(
        PositionsGet=AsyncMock(side_effect=lambda: list(current_positions))
    )
    order_src = SimpleNamespace(
        OrdersGet=AsyncMock(side_effect=lambda: list(current_orders))
    )
    symbol_src = SimpleNamespace(
        SymbolInfo=AsyncMock(
            return_value=SymbolInfo(
                name="EURUSD",
                price=SymbolPrice(bid=bid, ask=ask, tick_step=tick_step),
            )
        )
    )

    return SimpleNamespace(
        trade=trade,
        position=position_src,
        order=order_src,
        symbol=symbol_src,
        account=SimpleNamespace(),
        deal=SimpleNamespace(),
    )


def test_close_all_pending_orders(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario() -> None:
        o1 = OrderInfo(ticket=101, symbol="EURUSD", order_type=2, magic=10)  # BUY_LIMIT
        o2 = OrderInfo(ticket=102, symbol="EURUSD", order_type=4, magic=10)  # BUY_STOP
        runtime = make_mock_runtime(orders=[o1, o2])

        scope = TradeFilter("EURUSD", magic=10)
        results = await close_all_pending_orders(runtime, scope)
        assert len(results) == 2
        assert all(r.retcode == int(TradeRetcode.DONE) for r in results)
        assert runtime.trade.cancel.await_count == 2
        assert "FR-ORDER-CLOSE-ALL-PENDING" in caplog.text

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())


def test_close_all_positions(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario() -> None:
        p1 = PositionInfo(ticket=201, symbol="EURUSD", position_type=0, magic=10)
        p2 = PositionInfo(ticket=202, symbol="EURUSD", position_type=1, magic=10)
        runtime = make_mock_runtime(positions=[p1, p2])

        scope = TradeFilter("EURUSD", magic=10)
        results = await close_all_positions(runtime, scope)
        assert len(results) == 2
        assert all(r.retcode == int(TradeRetcode.DONE) for r in results)
        assert runtime.trade.close.await_count == 2
        assert "FR-ORDER-CLOSE-ALL-POSITIONS" in caplog.text

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())


def test_close_best_and_worst_position(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario() -> None:
        p_bad = PositionInfo(
            ticket=301,
            symbol="EURUSD",
            position_type=0,
            profit=-50.0,
            swap=-2.0,
            commission=-5.0,
        )  # net = -57.0
        p_good = PositionInfo(
            ticket=302,
            symbol="EURUSD",
            position_type=0,
            profit=120.0,
            swap=0.0,
            commission=-5.0,
        )  # net = 115.0
        runtime = make_mock_runtime(positions=[p_bad, p_good])

        scope = TradeFilter("EURUSD")

        # Close best
        res_best = await close_best_position(runtime, scope)
        assert res_best is not None
        assert runtime.trade.close.call_args[0][0].ticket == 302
        assert "FR-ORDER-CLOSE-BEST" in caplog.text

        # Now only p_bad remains
        res_worst = await close_worst_position(runtime, scope)
        assert res_worst is not None
        assert runtime.trade.close.call_args[0][0].ticket == 301
        assert "FR-ORDER-CLOSE-WORST" in caplog.text

        # When empty, return None
        assert await close_best_position(runtime, scope) is None
        assert await close_worst_position(runtime, scope) is None

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())


def test_close_pending_order_and_single_position(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def scenario() -> None:
        o = OrderInfo(ticket=401, symbol="EURUSD", order_type=2)
        p = PositionInfo(ticket=402, symbol="EURUSD", position_type=0, volume=1.0)
        runtime = make_mock_runtime(positions=[p], orders=[o])

        scope = TradeFilter("EURUSD")
        res_ord = await close_pending_order(runtime, scope)
        assert res_ord is not None
        assert runtime.trade.cancel.await_count == 1
        assert "FR-ORDER-CLOSE-PENDING" in caplog.text

        res_pos = await close_position(runtime, scope, volume=0.5)
        assert res_pos is not None
        assert runtime.trade.close.await_count == 1
        assert "FR-ORDER-CLOSE-POSITION" in caplog.text

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())


def test_set_profit_target_and_stop_loss(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def scenario() -> None:
        p = PositionInfo(
            ticket=501, symbol="EURUSD", position_type=0, sl=1.0900, tp=1.1200
        )
        runtime = make_mock_runtime(positions=[p])

        scope = TradeFilter("EURUSD")
        res_pt = await set_profit_target(runtime, scope, 1.1300)
        assert len(res_pt) == 1
        assert "FR-ORDER-SET-PROFIT-TARGET" in caplog.text

        # Normal stop loss adjustment
        res_sl = await set_stop_loss(runtime, scope, 1.0950)
        assert len(res_sl) == 1
        assert "FR-ORDER-SET-STOP-LOSS" in caplog.text

        # Tighten only: setting looser stop (1.0800 vs existing 1.0900 on long) preserves tighter stop
        res_tight = await set_stop_loss(runtime, scope, 1.0800, tighten_only=True)
        assert len(res_tight) == 1
        assert res_tight[0].retcode == int(TradeRetcode.NO_CHANGES)

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())


def test_open_market_limit_stop(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario() -> None:
        runtime = make_mock_runtime()

        # Enter market
        mkt = await enter_at_market(runtime, "EURUSD", 1, 0.1, sl=1.0950, tp=1.1100)
        assert mkt is not None
        assert mkt.retcode == int(TradeRetcode.DONE)
        assert "FR-ORDER-ENTER-AT-MARKET" in caplog.text

        # Enter limit
        lmt = await enter_at_limit(runtime, "EURUSD", 1, 0.1, 1.0980)
        assert lmt is not None
        assert lmt.retcode == int(TradeRetcode.DONE)
        assert "FR-ORDER-ENTER-AT-LIMIT" in caplog.text

        # Enter stop
        stp = await enter_at_stop(runtime, "EURUSD", 1, 0.1, 1.1050)
        assert stp is not None
        assert stp.retcode == int(TradeRetcode.DONE)
        assert "FR-ORDER-ENTER-AT-STOP" in caplog.text

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())


def test_duplicate_trade_prevention() -> None:
    async def scenario() -> None:
        existing = PositionInfo(ticket=601, symbol="EURUSD", position_type=0, magic=77)
        runtime = make_mock_runtime(positions=[existing])

        # Allow duplicate trades is False by default -> should be skipped (return None)
        res = await enter_at_market(
            runtime, "EURUSD", 1, 0.1, magic=77, allow_duplicate_trades=False
        )
        assert res is None

    asyncio.run(scenario())


def test_enter_reverse_at_market(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario() -> None:
        # Existing Short position (direction -1)
        short_pos = PositionInfo(ticket=701, symbol="EURUSD", position_type=1, magic=88)
        runtime = make_mock_runtime(positions=[short_pos], ask=1.1005)

        # Reversing to Long (+1)
        rev = await enter_reverse_at_market(runtime, "EURUSD", 1, 0.2, magic=88)
        assert rev is not None
        assert rev.retcode == int(TradeRetcode.DONE)
        assert runtime.trade.close.await_count == 1
        assert runtime.trade.send_checked.await_count == 1
        assert "FR-ORDER-ENTER-REVERSE-AT-MARKET" in caplog.text

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())


def test_orders_facade(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario() -> None:
        p = PositionInfo(ticket=801, symbol="EURUSD", position_type=0, profit=50.0)
        o = OrderInfo(ticket=802, symbol="EURUSD", order_type=2)
        runtime = make_mock_runtime(positions=[p], orders=[o])

        facade = Orders(runtime)
        scope = TradeFilter("EURUSD")

        # Test open via facade (with allow_duplicate_trades=True since EURUSD position exists)
        res_mkt = await facade.enter_at_market(
            "EURUSD", 1, 0.1, allow_duplicate_trades=True
        )
        assert res_mkt is not None

        res_lmt = await facade.enter_at_limit(
            "EURUSD", 1, 0.1, 1.0950, allow_duplicate_trades=True
        )
        assert res_lmt is not None

        res_stp = await facade.enter_at_stop(
            "EURUSD", 1, 0.1, 1.1050, allow_duplicate_trades=True
        )
        assert res_stp is not None

        # Test modify via facade
        res_pt = await facade.set_profit_target(scope, 1.1200)
        assert len(res_pt) >= 1

        res_sl = await facade.set_stop_loss(scope, 1.0900)
        assert len(res_sl) >= 1

        # Test evaluations via facade
        assert facade.evaluate_sizing("fixed", lots=0.5) == 0.5
        level = facade.evaluate_price_level(
            "pips", 1.1000, 1, pips=10.0, pip_size=0.0001
        )
        assert level == pytest.approx(1.1010)

        # Test close via facade
        res_best = await facade.close_best_position(scope)
        assert res_best is not None
        assert "FR-ORDER-FACADE" in caplog.text

    caplog.set_level(logging.DEBUG)
    asyncio.run(scenario())
