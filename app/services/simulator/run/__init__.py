"""Supported Simulation run API."""

from app.services.simulator.run.contracts import (
    PortfolioBacktestRequestV1,
    PortfolioComponentRequest,
    SimulationBacktestRequestV1,
    SimulationBacktestRequestV2,
    SimulationRunDependencies,
)
from app.services.simulator.run.dependencies import build_simulation_run_dependencies
from app.services.simulator.run.evaluation import (
    build_evaluation_latency,
    build_point_in_time_dataset,
    run_point_in_time_evaluation,
)
from app.services.simulator.run.orchestrator import run_backtest, run_backtest_async
from app.services.simulator.run.portfolio import run_portfolio_backtest
from app.services.simulator.run.research import run_fast_research

__all__ = [
    "PortfolioBacktestRequestV1",
    "PortfolioComponentRequest",
    "SimulationBacktestRequestV1",
    "SimulationBacktestRequestV2",
    "SimulationRunDependencies",
    "build_evaluation_latency",
    "build_point_in_time_dataset",
    "build_simulation_run_dependencies",
    "run_backtest",
    "run_backtest_async",
    "run_fast_research",
    "run_point_in_time_evaluation",
    "run_portfolio_backtest",
]
