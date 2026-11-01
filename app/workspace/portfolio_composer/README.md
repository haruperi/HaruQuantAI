# Portfolio Composer contracts and ownership

Feature: `FEAT-PORTFOLIO-COMPOSER`. Owner: `app/workspace/portfolio_composer`.

The Portfolio Composer workspace provides multi-strategy shared-capital composition, chronological order merging, margin and leverage enforcement, Buy-and-Hold strategy synthesis, automatic allocation weight search (Markowitz and CVaR / Expected Shortfall models), efficient frontier scatter and multi-equity chart projections, execution and margin rejection logging, and databank persistence.

## 1. Architecture and Domain Contracts

`AppPortfolioComposerService` coordinates top-level workspace state, candidate strategy member collections, execution dispatch, and projection services:

- **Root Coordinator & Lifecycle (`app_portfolio_composer.py`, `FR-composer-workspace-state`):**
  - Manages `ComposerWorkspaceState` (project ID, defaults, members, latest receipt, computing flag).
  - Supplies initialized default settings via `ComposerDefaults.create(today_label=...)`.
- **Composition Defaults (`defaults.py`, `PC-001`, `FR-composer-defaults`):**
  - `ComposerDefaults.create(*, today_label: str) -> ComposerViewDefaults`: Constructs fresh initial configuration dictionaries with preformatted date labels and observed default parameters (`SharpRatio`, risk-free rate 0.7, 100k capital, 1x leverage).
- **Selection Identifiers & Precision (`selection.py`, `PC-002`, `FR-composer-selection`):**
  - `ComposerSelection`: Strict StrEnum parsing exact selection type strings (`SharpRatio`, `ReturnDrawdownRatio`, `CAGRMaxDrawdownRatio`, `CAGRMeanDrawdownRatio`, `NetProfit`).
  - `decimals()`: Returns metric decimal precision (3 for Sharpe, 2 for CAGR drawdown metrics, 0 for net profit and return drawdown).
- **Expected Shortfall Calculation (`risk.py`, `PC-003`, `FR-composer-risk`):**
  - `ComposerRisk.expected_shortfall(*, mean: float, standard_deviation: float, confidence: float) -> float`: Parametric Gaussian Conditional Value at Risk ($\mu - \sigma \frac{\phi(z)}{1 - \alpha}$).
- **Automatic Allocation Candidate Generator (`allocations.py`, `PC-004`, `FR-composer-allocations`):**
  - `BoundedRandom`: Protocol for bounded random integer draws.
  - `ComposerAllocations.generate`: Generates integer allocation vectors summing to 100 with bounded step draws and large-cohort base thresholds.
- **Core Composition Engine (`portfolio_composer.py`, `FR-composer-engine-*`):**
  - `add_buy_hold_strategy`: Synthesizes single long trades across specified date bounds.
  - `recompute`: Chronological multi-strategy order merge by `(open_time_ms, close_time_ms, strategy_index, ticket)`, shared-capital margin checking against available free equity, rejection logging, fitness metric calculation, and winning candidate selection.
  - `save_portfolio`: Persists composed portfolio run receipts to a project databank.
- **Frontier & Equity Chart Projections (`results_portfolio_composer_chart.py`, `FR-composer-chart`):**
  - `ResultsPortfolioComposerChartService.get_chart`: Projects simulation scatter points (risk vs return) and multi-strategy equity curves.
- **Execution & Margin Reject Logs (`results_portfolio_composer_log.py`, `FR-composer-log`):**
  - `ResultsPortfolioComposerLogService.get_log`: Projects chronological diagnostic and margin rejection entries.

## 2. Host Capability Ownership

| Capability | Authority | Portfolio Composer Usage |
|---|---|---|
| Composition Engine | `app/workspace/portfolio_composer/portfolio_composer.py::PortfolioComposerService` | Chronological multi-strategy order merging, margin calculation, and optimization |
| Result Store | `app/core/trading/results/store.py::ResultStore` | Preserving composition runs and sub-result keys |
| Statistics Service | `app/core/trading/statistics/service.py::StatisticsService` | Selection criteria calculations (Sharpe, Drawdown ratios, Net Profit) |
| Random Generator | `app/workspace/portfolio_composer/allocations.py::BoundedRandom` | Dependency-injected bounded integer draws for deterministic testing |
| Logging & Errors | `app/core/host/logging.py`, `app/core/lib/responses.py` | Non-silent audit logging and typed `StandardResponse[T]` envelopes |

## 3. Verification and Qualification Evidence

- **Pytest (Backend Services):** Clean execution across 70 tests in `tests/workspace/portfolio_composer/`.
- **Branch-Aware Coverage:** 92.55% branch coverage across retained Python application source (minimum 80% required).
- **Vitest (Frontend UI):** 7 test files, 18 tests passing in `app/web/tests/workspace/portfolio_composer/`.
- **Static Analysis & Linting:**
  - `uv run ruff check app/workspace/portfolio_composer tests/workspace/portfolio_composer`: Clean linting (`All checks passed!`).
  - `uv run ruff format --check app/workspace/portfolio_composer tests/workspace/portfolio_composer`: 100% formatted.
- **Frontend Production Build & Typecheck:**
  - `npm --prefix app/web run typecheck`: Exited 0.
  - `npm --prefix app/web run build`: Exited 0 (built in 10.03s).
