# Retester contracts and ownership

Feature: `FEAT-RETESTER-CONTRACTS`. Owner: `app/workspace/retester`.

The Retester workspace provides strategy retesting, robustness verification, multi-market/higher-precision evaluation, Monte Carlo analysis, Walk-Forward optimization checks, and trade analytics.

## 1. Architecture and Domain Contracts

`AppRetesterService` acts as the root workspace controller, coordinating candidate strategy selection, market data configuration, cross-check evaluation, task execution, and result projection:

- **Root Coordinator & Lifecycle (`app_retester.py`):**
  - Manages `RetesterWorkspaceState` and transitions across `IDLE`, `RUNNING`, `PAUSED`, `COMPLETED`, `STOPPED`, and `FAILED`.
  - Delegates execution to `TaskRetestRunner` and validates project boundaries.
- **Value Source Normalization (`value_source.py`):**
  - Normalizes legacy boolean string flags (`"false"` -> `"custom"`, `"true"` -> `"strategy"`) while preserving explicit `"custom"` and `"strategy"` inputs.
  - Strictly rejects non-string/non-None types with `TypeError`.
- **Preflight & Mode Resolution (`preflight.py`):**
  - Computes strategy selection: empty selection evaluates to empty list (`processed=0`), `None` selects all strategies in databank, and explicit tuple filters by membership.
  - Resolves execution Mode 0 (subjobs created by Monte Carlo Retest, Walk-Forward, etc.) vs Mode 1 (standard backtests).
- **Retest Settings (`settings_what_to_retest.py`, `settings_auto_retest_data.py`, `settings_cross_checks.py`):**
  - Validates source and target databanks, dismissal policy, market overrides, date ranges, and initial capital.
  - Provides master cross-checks snapshot and canonical default acceptance conditions for Walk Forward and SPP.
- **9 Robustness Cross-Checks Services:**
  1. `cross_check_what_if.py`: Sequential What-If trade filtering and acceptance validation.
  2. `cross_check_monte_carlo_manipulation.py`: 5 trade manipulation simulations and empirical confidence band evaluation (50%..99%).
  3. `cross_check_monte_carlo_retest.py`: 9 market/parameter perturbation simulations and confidence band evaluation.
  4. `cross_check_retest_with_higher_precision.py`: Finer time-precision retesting and profit retention threshold validation.
  5. `cross_check_retest_on_additional_markets.py`: Multi-symbol/market retesting and combined portfolio net profit evaluation.
  6. `cross_check_sequential_optimization.py`: Coordinate-wise parameter sweeping locking in optimal parameters in sequence.
  7. `cross_check_walk_forward_optimization.py`: Rolling and anchored Walk-Forward IS/OOS window optimization and efficiency metrics.
  8. `cross_check_walk_forward_matrix.py`: 2D parameter grid Walk-Forward evaluation and 8-connected passing cluster analysis.
  9. `cross_check_opt_profile_sys_param_permutation.py`: System parameter permutation (SPP) neighborhood stability and profitable run ratio.
- **Execution Pipeline Runner (`task_retest.py`):**
  - Enforces `OBS-145-RETEST-PREFLIGHT-002` execution order.
  - Supports same-databank result clearing (clearing sub-results while preserving strategy definitions).
  - Evaluates cross-checks and dismisses failed strategies from target databanks when configured.
- **Results Workspace Projection (`results_robustness_tests.py`):**
  - Provides view management (CRUD) for the Robustness Tests tab.
  - Projects Monte Carlo equity fan curves (25 curves, 20 points), baseline equity, and 11 confidence level bands (50%..99%).

## 2. Concrete Extension Cohorts (`app/extend/`)

The workspace registers and evaluates concrete extension definitions per `07-AppRetester.md`:

- **What-If Scenarios (`app/extend/what_if/`):** 15 relocated scenarios across temporal filters (`by_days.py`, `by_hours.py`, `by_months.py`), trade exclusions (`exclude_short_trades.py`, `exclude_overlapping_trades.py`, `exclude_pct_trades_with_biggest_pl.py`, etc.), transaction management, swap toggling, and fixed lot sizing.
- **Monte Carlo Trade Manipulation (`app/extend/monte_carlo/manipulation/`):** 5 manipulation methods: `RandomlySkipTrades`, `RandomizeTradesOrder`, `RandomlyDegradeExecution`, `MACHRBlockRandomization`, and `SimulateParameterJitter`.
- **Monte Carlo Retest Perturbations (`app/extend/monte_carlo/retest/catalog.py`):** `MCRetestPerturbator` implementing all 9 perturbations on OHLC history data, fixed ranges, minimum distance, spreads, slippage, starting bars, and strategy parameters.
- **Strategy Checkers (`app/extend/checker/checkers.py`):** `ComparisonChecker`, `IndicatorFastSlowChecker`, and `PropertyChecker`.
- **Trade Analysis Catalog (`app/extend/trade_analysis/charts.py`):** 27 concrete trade analysis charts across hour, weekday, month, day, duration, close type, and direction dimensions.

## 3. Host Capability Ownership

| Capability | Authority | Retester Workspace Usage |
|---|---|---|
| Databank Storage | `app/core/jobs/databank.py::DatabankContainer` | Strategy resolution, target databank insertion, and failure dismissal |
| Result Store | `app/core/trading/results/store.py::ResultStore` | Backtest run results, sub-result keys, and same-databank clearing |
| Host State | `app/core/host/persistence.py::HostPersistence` | Retester workspace state, view presets, and configuration snapshots |
| Logging & Errors | `app/core/host/logging.py`, `app/core/lib/errors.py` | Non-silent audit logging and typed `DomainError` failure envelopes |

## 4. Verification and Qualification Evidence

- **Pytest (Backend & Extensions):** `106 passed in 3.92s` across `tests/workspace/retester` and `tests/extend`.
- **Branch-Aware Coverage:** `90.36%` across `app/workspace/retester` and `app/extend/` (exceeding the constitutional 80.0% requirement).
- **Vitest (Frontend UI):** `2 test files, 4 passed` in `app/web/tests/workspace/retester`.
- **Static Analysis & Typing:**
  - `ruff format --check`: Clean (73 source and test files).
  - `ruff check`: Clean with zero lint violations across all 73 files.
  - `mypy --strict`: Clean with zero type diagnostics across all 48 source files.
- **Frontend Production Build:** `npm --prefix app/web run typecheck` and `npm --prefix app/web run build` completed cleanly with exit code 0.
