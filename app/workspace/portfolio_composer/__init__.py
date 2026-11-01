"""Portfolio Composer workspace package.

Description:
    Provides defaults, selection parsing, expected shortfall calculation,
    allocation vector generation, and portfolio composition services.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-defaults: Construct initial configuration defaults.
    - FR-composer-selection: Parse selection metrics and decimal precision.
    - FR-composer-risk: Compute parametric expected shortfall (CVaR).
    - FR-composer-allocations: Generate bounded candidate weight vectors.
    - FR-composer-engine: Shared-capital chronological order merging.
    - FR-composer-chart: Efficient frontier and equity curve projections.
    - FR-composer-log: Diagnostics and margin rejection logs.
    - FR-composer-workspace: Workspace state coordinator.
Python API Usage:
    import app.workspace.portfolio_composer
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer --no-cov
"""

from __future__ import annotations

__all__ = [
    "AppPortfolioComposerService",
    "BoundedRandom",
    "ComposerAllocations",
    "ComposerDefaults",
    "ComposerLogEntry",
    "ComposerMemberSpec",
    "ComposerRisk",
    "ComposerRunConfig",
    "ComposerRunReceipt",
    "ComposerSelection",
    "ComposerTrade",
    "ComposerViewDefaults",
    "ComposerWorkspaceState",
    "FrontierSimulationPoint",
    "PortfolioComposerChartPayload",
    "PortfolioComposerLogPayload",
    "PortfolioComposerService",
    "ResultsPortfolioComposerChartService",
    "ResultsPortfolioComposerLogService",
]

from app.workspace.portfolio_composer.allocations import (
    BoundedRandom,
    ComposerAllocations,
)
from app.workspace.portfolio_composer.app_portfolio_composer import (
    AppPortfolioComposerService,
    ComposerWorkspaceState,
)
from app.workspace.portfolio_composer.defaults import (
    ComposerDefaults,
    ComposerViewDefaults,
)
from app.workspace.portfolio_composer.portfolio_composer import (
    ComposerMemberSpec,
    ComposerRunConfig,
    ComposerRunReceipt,
    ComposerTrade,
    PortfolioComposerService,
)
from app.workspace.portfolio_composer.results_portfolio_composer_chart import (
    FrontierSimulationPoint,
    PortfolioComposerChartPayload,
    ResultsPortfolioComposerChartService,
)
from app.workspace.portfolio_composer.results_portfolio_composer_log import (
    ComposerLogEntry,
    PortfolioComposerLogPayload,
    ResultsPortfolioComposerLogService,
)
from app.workspace.portfolio_composer.risk import ComposerRisk
from app.workspace.portfolio_composer.selection import ComposerSelection
