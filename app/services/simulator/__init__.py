"""Public Simulation domain port."""

from app.services.simulator.errors import (
    SIM_ERROR_CATALOG,
    SimulationError,
    to_simulation_error_payload,
)
from app.services.simulator.execution import SimTrader
from app.services.simulator.reporting import (
    ArtifactManifest,
    ClosedTradeRecord,
    FastResearchResult,
    PortfolioSimulationResult,
    SimulationResult,
)
from app.services.simulator.run import (
    PortfolioBacktestRequestV1,
    PortfolioComponentRequest,
    SimulationBacktestRequestV1,
    SimulationRunDependencies,
    run_backtest,
    run_fast_research,
    run_portfolio_backtest,
)

__all__ = (
    "SIM_ERROR_CATALOG",
    "ArtifactManifest",
    "ClosedTradeRecord",
    "FastResearchResult",
    "PortfolioBacktestRequestV1",
    "PortfolioComponentRequest",
    "PortfolioSimulationResult",
    "SimTrader",
    "SimulationBacktestRequestV1",
    "SimulationError",
    "SimulationResult",
    "SimulationRunDependencies",
    "run_backtest",
    "run_fast_research",
    "run_portfolio_backtest",
    "to_simulation_error_payload",
)
