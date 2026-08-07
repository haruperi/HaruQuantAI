"""Workflow integration test for the Optimization adapter boundary."""

from pathlib import Path

from app.services.simulator import run_backtest, unwrap_simulation_response
from app.utils import get_logger

from tests.simulator.component.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)

logger = get_logger(__name__)


def test_external_adapter_can_call_stable_simulation_port(tmp_path: Path) -> None:
    """Return an idempotent immutable result without importing Optimization."""
    logger.info("Testing WF-SIM-003 external Optimization adapter boundary")
    dataset = _dataset("req-dddddddd-dddd-4ddd-8ddd-dddddddddddd")
    request = _request(dataset, suffix="d")
    dependencies = FakeDependencies(tmp_path, dataset)
    first = unwrap_simulation_response(
        run_backtest(request, _auth(request), dependencies),
        operation="test.optimization.run_backtest",
    )
    second = unwrap_simulation_response(
        run_backtest(request, _auth(request), dependencies),
        operation="test.optimization.run_backtest",
    )
    assert first == second
    assert first.status == "completed"
    assert first.model_config["frozen"] is True
