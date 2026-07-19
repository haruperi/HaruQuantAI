"""Unit tests for the async Simulation Trading port."""
# ruff: noqa: INP001

import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.execution import SimTrader
from app.services.trading import ExecutionReceipt, OrderIntent, TradingRoute
from tests.simulator.unit.test_engine import _engine, _intent, _tick


def test_submit_order_never_calls_live_adapter(tmp_path: Path) -> None:
    """Submit directly to the isolated simulation engine."""
    trader = SimTrader(_engine(tmp_path, "submit"))
    receipt = asyncio.run(trader.submit_order(_intent()))
    assert receipt.status == "accepted"
    assert str(receipt.route) == "sim"


def test_dispatch_signature_matches_trading_port(tmp_path: Path) -> None:
    """Prove the bound async method is assignable to Trading's sim port."""
    trader = SimTrader(_engine(tmp_path, "port"))
    dispatch: Callable[[OrderIntent], Awaitable[ExecutionReceipt]] = trader.submit_order
    assert asyncio.run(dispatch(_intent())).status == "accepted"


class _SpyEngine:
    """Engine spy proving the facade rejects before any state mutation."""

    def __init__(self) -> None:
        """Record whether the engine was ever reached."""
        self.called = False

    def submit_order(self, intent: OrderIntent) -> ExecutionReceipt:
        """Record the call and fail if it ever happens.

        Args:
            intent: Order intent that should never arrive.

        Raises:
            AssertionError: Always, because the facade must reject first.
        """
        del intent
        self.called = True
        raise AssertionError("SimTrader forwarded a rejected intent")


def test_submit_order_rejects_non_sim_route_before_engine() -> None:
    """Reject a non-`sim` route at the facade, before the engine is reached."""
    spy = _SpyEngine()
    trader = SimTrader(spy)  # type: ignore[arg-type]
    intent = _intent().model_copy(update={"route": TradingRoute.PAPER})
    with pytest.raises(SimulationError) as captured:
        asyncio.run(trader.submit_order(intent))
    assert captured.value.code == "SIM_INVALID_CONFIG"
    assert not spy.called


def test_submit_order_rejects_altered_volume_before_engine() -> None:
    """Reject an intent whose approved volume no longer matches Risk."""
    spy = _SpyEngine()
    trader = SimTrader(spy)  # type: ignore[arg-type]
    intent = _intent().model_copy(update={"approved_volume": Decimal(2)})
    with pytest.raises(SimulationError) as captured:
        asyncio.run(trader.submit_order(intent))
    assert captured.value.code == "SIM_INVALID_VOLUME"
    assert not spy.called


def test_close_position_rejects_unknown_position(tmp_path: Path) -> None:
    """Fail closed when a position identity is absent."""
    engine = _engine(tmp_path, "close")
    engine.execute_tick(_tick())
    trader = SimTrader(engine)
    with pytest.raises(SimulationError) as captured:
        trader.close_position("missing", Decimal(1))
    assert captured.value.code == "SIM_POSITION_NOT_FOUND"


def test_snapshot_cannot_mutate_engine_state(tmp_path: Path) -> None:
    """Reject mutation through the public state projection."""
    snapshot = SimTrader(_engine(tmp_path, "snapshot")).snapshot()
    with pytest.raises(TypeError, match="does not support item assignment"):
        snapshot["orders"] = ()  # type: ignore[index]
