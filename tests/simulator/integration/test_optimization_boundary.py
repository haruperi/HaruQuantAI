"""Workflow integration test for the Optimization adapter boundary."""
# ruff: noqa: INP001

from pathlib import Path

from app.services.simulator import run_backtest
from app.utils import logger
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)


def test_external_adapter_can_call_stable_simulation_port(tmp_path: Path) -> None:
    """Return an idempotent immutable result without importing Optimization."""
    logger.info("Testing WF-SIM-003 external Optimization adapter boundary")
    dataset = _dataset(f"req-{'d' * 64}")
    request = _request(dataset, suffix="d")
    dependencies = FakeDependencies(tmp_path, dataset)
    first = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    second = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert first == second
    assert first.status == "completed"
    assert first.model_config["frozen"] is True
