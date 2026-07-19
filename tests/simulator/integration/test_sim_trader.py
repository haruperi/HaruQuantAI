"""Workflow integration test for Trading's injected Simulation port."""
# ruff: noqa: INP001

import asyncio
from pathlib import Path

from app.services.simulator import SimTrader
from app.utils import logger
from tests.simulator.unit.test_engine import _engine, _intent, _tick


def test_sim_trader_executes_without_a_broker(tmp_path: Path) -> None:
    """Accept through the async port and fill on the canonical next tick."""
    logger.info("Testing WF-SIM-002 simulated Trader execution")
    engine = _engine(tmp_path, "workflow-trader")
    trader = SimTrader(engine)
    accepted = asyncio.run(trader.submit_order(_intent()))
    fills = engine.execute_tick(_tick())
    snapshot = trader.snapshot()
    assert accepted.status == "accepted"
    assert fills[0].status == "filled"
    assert fills[0].authority == "simulation"
    assert len(snapshot["deals"]) == 1  # type: ignore[arg-type]
