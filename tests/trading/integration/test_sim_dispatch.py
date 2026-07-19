"""Workflow integration for Simulation authority dispatch."""

# ruff: noqa: INP001

import pytest
from app.services.trading.actions import submit_order
from tests.trading.conftest import trading_dependencies, trading_request


@pytest.mark.anyio
async def test_sim_dispatch_uses_simulation_authority() -> None:
    """A sim request reaches Simulation and returns its canonical receipt."""
    outcome = await submit_order(trading_request(), trading_dependencies())
    assert outcome.data["receipt"]["authority"] == "simulation"
    assert outcome.data["receipt"]["route"] == "sim"
