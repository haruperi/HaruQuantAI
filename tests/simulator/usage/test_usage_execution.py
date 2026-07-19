"""Runnable usage examples for deterministic Simulation execution."""

import asyncio
from decimal import Decimal
from pathlib import Path

from app.services.simulator.execution import (
    SimTrader,
    evaluate_protective_exit,
    match_order,
    price_order,
)
from tests.simulator.unit.test_engine import _engine, _intent, _tick
from tests.simulator.unit.test_pricing import _profile


def test_usage_price_order() -> None:
    """Price one BUY from the current ask."""
    assert price_order(_intent(), _tick(), _profile()) == Decimal("1.10002")


def test_usage_match_order() -> None:
    """Match one approved market order deterministically."""
    assert match_order(_intent(), _tick(), _profile()).status == "filled"


def test_usage_engine_execute_tick(tmp_path: Path) -> None:
    """Advance one engine through one canonical tick."""
    engine = _engine(tmp_path, "usage-engine")
    engine.submit_order(_intent())
    assert engine.execute_tick(_tick())[0].status == "filled"


def test_usage_sim_trader_submit_order(tmp_path: Path) -> None:
    """Use the bound async Trading sim port."""
    trader = SimTrader(_engine(tmp_path, "usage-submit"))
    assert asyncio.run(trader.submit_order(_intent())).status == "accepted"


def test_usage_dispatch_sim_order(tmp_path: Path) -> None:
    """Assign the bound method directly as the dispatch callable."""
    dispatch = SimTrader(_engine(tmp_path, "usage-dispatch")).submit_order
    assert asyncio.run(dispatch(_intent())).status == "accepted"


def test_usage_sim_trader_close_position(tmp_path: Path) -> None:
    """Open and close one simulated position."""
    engine = _engine(tmp_path, "usage-close")
    trader = SimTrader(engine)
    asyncio.run(trader.submit_order(_intent()))
    engine.execute_tick(_tick())
    close = trader.close_position("sim-position-order-engine", Decimal(1))
    assert close["quantity"] == Decimal(1)


def test_usage_sim_trader_snapshot(tmp_path: Path) -> None:
    """Read immutable simulated state."""
    snapshot = SimTrader(_engine(tmp_path, "usage-snapshot")).snapshot()
    assert snapshot["engine_version"] == "v1"


def test_usage_evaluate_protective_exit() -> None:
    """Resolve one open position's protective exit against the current tick."""
    position = {
        "side": "BUY",
        "stop_loss": Decimal("1.20000"),
        "take_profit": Decimal("1.05000"),
    }
    assert evaluate_protective_exit(position, _tick()) == "STOP_LOSS"
