"""Workflow integration for Simulation authority dispatch."""

# ruff: noqa: INP001
import pytest
from app.services.trading import submit_order
from tests.trading.conftest import trading_dependencies, trading_request


@pytest.mark.anyio
async def test_sim_dispatch_uses_simulation_authority() -> None:
    """A sim request reaches Simulation and returns its canonical receipt."""
    outcome = await submit_order(trading_request(), trading_dependencies())
    assert outcome.status == "success"
    assert outcome.data is not None
    assert outcome.data.authority == "simulation"
    assert outcome.data.route.value == "sim"
