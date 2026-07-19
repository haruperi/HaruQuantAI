"""Runnable usage examples for Optimization execution."""

from app.services.optimization.errors import OptimizationError
from app.services.optimization.execution import (
    BacktestExecutionAdapter,
    EngineOptimizationResult,
    execute_candidate,
)
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_execution_contracts import execution_request


def test_usage_contracts_backtest_execution_request() -> None:
    """Construct a versioned candidate request."""
    assert execution_request().contract_version == "v1"


def test_usage_contracts_optimization_error() -> None:
    """Build a redacted controlled domain failure."""
    assert (
        OptimizationError("OPT_EXECUTION_FAILED")
        .to_payload()["code"]
        .startswith("OPT_")
    )


def test_usage_contracts_backtest_execution_adapter() -> None:
    """Inject an implementation of the receiver-owned execution port."""
    assert callable(BacktestExecutionAdapter.__dict__["execute"])


def test_usage_contracts_engine_optimization_result() -> None:
    """Consume measured Simulation and Analytics evidence."""
    result = FakeAdapter().execute(execution_request())
    assert isinstance(result, EngineOptimizationResult)


def test_usage_adapter_execute_candidate() -> None:
    """Execute through a compatible deterministic adapter."""
    result = execute_candidate(
        execution_request(),
        FakeAdapter(),
        deterministic_only=True,
    )
    assert result.candidate_hash == "9" * 64
