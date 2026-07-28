"""Workflow integration test for Trading's injected Simulation port."""
# ruff: noqa: INP001

import asyncio
from pathlib import Path

from app.services.simulator import SimTrader, unwrap_simulation_response
from app.utils import logger
from tests.simulator.unit.test_engine import _engine, _intent, _tick


def test_sim_trader_executes_without_a_broker(tmp_path: Path) -> None:
    """Accept through the async port and fill on the canonical next tick."""
    logger.info("Testing WF-SIM-002 simulated Trader execution")
    engine = _engine(tmp_path, "workflow-trader")
    trader = SimTrader(engine)
    accepted = unwrap_simulation_response(
        asyncio.run(trader.submit_order(_intent())),
        operation="test.sim_trader.submit_order",
    )
    fills = unwrap_simulation_response(
        engine.execute_tick(_tick()), operation="test.sim_trader.execute_tick"
    )
    snapshot = unwrap_simulation_response(
        trader.snapshot(), operation="test.sim_trader.snapshot"
    )
    assert accepted.status == "accepted"
    assert fills[0].status == "filled"
    assert fills[0].authority == "simulation"
    assert len(snapshot["deals"]) == 1  # type: ignore[arg-type]
