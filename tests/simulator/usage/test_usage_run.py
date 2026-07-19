"""Runnable usage examples for governed Simulation run operations."""

from pathlib import Path

from app.services.simulator.run import (
    PortfolioBacktestRequestV1,
    SimulationBacktestRequestV1,
    run_backtest,
    run_fast_research,
    run_portfolio_backtest,
)
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)
from tests.simulator.unit.test_portfolio_run import _portfolio_auth, _portfolio_request


def test_usage_backtest_request() -> None:
    """Construct the exact reference-only request contract."""
    dataset = _dataset(f"req-{'5' * 64}")
    assert isinstance(_request(dataset), SimulationBacktestRequestV1)


def test_usage_portfolio_backtest_request() -> None:
    """Construct a self-contained portfolio candidate projection."""
    assert isinstance(_portfolio_request(), PortfolioBacktestRequestV1)


def test_usage_run_backtest(tmp_path: Path) -> None:
    """Execute one synchronous canonical backtest."""
    dataset = _dataset(f"req-{'5' * 64}")
    request = _request(dataset)
    result = run_backtest(
        request,
        _auth(request),
        FakeDependencies(tmp_path, dataset),  # type: ignore[arg-type]
    )
    assert result.status == "completed"


def test_usage_run_fast_research(tmp_path: Path) -> None:
    """Execute one explicitly non-canonical approximation."""
    dataset = _dataset(f"req-{'8' * 64}")
    request = _request(
        dataset,
        runtime_profile="fast_research",
        canonical=False,
        suffix="8",
    )
    result = run_fast_research(
        request,
        _auth(request),
        FakeDependencies(tmp_path, dataset),  # type: ignore[arg-type]
    )
    assert result.canonical is False


def test_usage_run_portfolio_backtest(tmp_path: Path) -> None:
    """Execute every component and publish one reconciled result."""
    request = _portfolio_request()
    dataset = _dataset(f"req-{'6' * 64}")
    result = run_portfolio_backtest(
        request,
        _portfolio_auth(request),
        FakeDependencies(tmp_path, dataset),  # type: ignore[arg-type]
    )
    assert result.status == "completed"
