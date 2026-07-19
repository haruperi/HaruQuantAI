"""Workflow integration for authorized portfolio rebalance execution."""

# ruff: noqa: INP001

import pytest
from app.services.trading.actions import execute_portfolio_rebalance
from tests.trading.conftest import (
    rebalance_dependencies,
    rebalance_request,
)


@pytest.mark.anyio
async def test_authorized_rebalance_uses_existing_order_path() -> None:
    """Every approved correction returns an ordinary authority receipt outcome."""
    item = rebalance_request()
    outcome = await execute_portfolio_rebalance(item, rebalance_dependencies(item))
    assert outcome.data["outcomes"][0]["status"] == "sent"
