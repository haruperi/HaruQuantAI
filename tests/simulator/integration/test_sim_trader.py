"""Workflow integration test for Trading's injected Simulation port."""

import asyncio
from pathlib import Path

from app.services.simulator import (
    create_simulation_handle,
    execute_simulation_handle_operation,
    unwrap_simulation_response,
)
from app.utils import get_logger

from tests.simulator.unit.test_engine import _engine, _intent, _tick

logger = get_logger(__name__)


def test_sim_trader_executes_without_a_broker(tmp_path: Path) -> None:
    """Accept through the async port and fill on the canonical next tick."""
    logger.info("Testing WF-SIM-002 simulated Trader execution")
    engine = _engine(tmp_path, "workflow-trader")
    trader = create_simulation_handle("SimTrader", engine)
    accepted = unwrap_simulation_response(
        asyncio.run(
            execute_simulation_handle_operation(  # type: ignore[arg-type]
                trader, "submit_order", _intent()
            )
        ),
        operation="test.sim_trader.submit_order",
    )
    fills = unwrap_simulation_response(
        engine.execute_tick(_tick()), operation="test.sim_trader.execute_tick"
    )
    snapshot = unwrap_simulation_response(
        execute_simulation_handle_operation(trader, "snapshot"),
        operation="test.sim_trader.snapshot",
    )
    assert accepted.status == "accepted"
    assert fills[0].status == "filled"
    assert fills[0].authority == "simulation"
    assert len(snapshot["deals"]) == 1  # type: ignore[arg-type]
