"""Paired paper/simulation Trading action-path convergence tests."""

import asyncio
from decimal import Decimal
from pathlib import Path

from app.services.trading import dispatch_order_intent

from tests.trading.unit.routing.test_dispatcher import (
    NOW,
    _Adapter,
    _connection,
    _intent,
    _sim_connection,
)


def _dispatch(route: str) -> object:
    """Dispatch one alpha-equivalent intent through the selected Broker channel."""
    adapter = _Adapter(
        broker="sim" if route == "sim" else "mt5",
        environment="simulation" if route == "sim" else "demo",
    )
    return asyncio.run(
        dispatch_order_intent(
            _intent(route=route),
            _sim_connection() if route == "sim" else _connection(),
            adapter,
            operation_timeout_seconds=Decimal(10),
            clock=lambda: NOW,
        )
    )


def test_two_routes_share_mutation_mapping_and_response_classification() -> None:
    """Route changes authority transport, not action or outcome classification."""
    simulation = _dispatch("sim")
    paper = _dispatch("paper")
    assert simulation.status == paper.status == "success"
    assert simulation.data.status == paper.data.status == "accepted"
    assert simulation.data.response_classification == paper.data.response_classification
    assert simulation.data.requested_quantity == paper.data.requested_quantity


def test_no_private_simulation_import_or_callback_remains() -> None:
    """Trading production source has no Simulation import or divergent callback."""
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/services/trading").rglob("*.py")
    )
    assert "app.services.simulator" not in source
    assert "simulation_dispatch" not in source
