# Optimizer contracts and ownership

Feature: `FEAT-OPTIMIZER-CONTRACTS`. Owner: `app/workspace/optimizer`.

The Optimizer workspace provides strategy parameter search (Simple Grid, Genetic Algorithm, Walk-Forward, Walk-Forward Matrix, System Parameter Permutation, and Sequential Optimization), multi-objective walk-forward fitness evaluation, parameter range validation, sensitivity surface grid projections, stitched out-of-sample equity curves, and databank parameter scheduling.

## 1. Architecture and Domain Contracts

`AppOptimizerService` acts as the root workspace controller, coordinating optimization settings, task execution, and result projections:

- **Root Coordinator & Lifecycle (`app_optimizer.py`):**
  - Manages `OptimizerWorkspaceState` and transitions across `IDLE`, `RUNNING`, `PAUSED`, `COMPLETED`, `STOPPED`, and `FAILED`.
  - Coordinates `TaskOptimizeRunner` sweeps, state queries, and settings persistence.
- **Optimization Labels Helper (`labels.py`, `OPT-001`):**
  - `OptimizationLabels.max_tests`: Maps integer maximum test counts to localized strings or descriptive exhaustive labels with strict integer type guards.
  - `OptimizationLabels.period_parameter`: Formats period parameter indices and period unit types into descriptive labels.
- **Walk-Forward Metric Lookup (`wf_metric.py`, `OPT-WF-METRIC-01`):**
  - `first_wf_metric`: Pure function projecting raw metric values from the head of walk-forward results while preserving IEEE nonfinite numbers and validating non-empty metric keys.
- **Walk-Forward Fitness Evaluator (`fitness_method_w_f_result.py`):**
  - `FitnessMethodWFResultService.evaluate`: Evaluates weighted normalized fitness in `[0.0, 1.0]` across registered `Columns/Databanks` and `Columns/WalkForward` metrics with zero-trade protection and `OPTIMIZER_UNKNOWN_WF_METRIC` validation.
- **Optimization Settings Service (`settings_optimization.py`):**
  - `SettingsOptimizationService.count_parameter_steps`: Computes discrete step counts with `OPTIMIZER_INVALID_PARAM_RANGE` validation.
  - `SettingsOptimizationService.get_number_of_tests`: Computes Cartesian product combinations, Walk-Forward window and matrix multipliers, and bounds caps.
- **Optimization Results Projections:**
  - `results_optimization_profile.py`: Projects 1D/2D/3D parameter sensitivity surfaces, chart grid matrices, run tables, and CSV exports.
  - `results_sequential_optimization.py`: Projects step-by-step sequential optimization curves and applies optimal parameters back to strategy documents (`results_sequential_optimization/applyParams`).
  - `results_sys_param_permutation.py`: Computes statistical summaries (median, mean, std dev, 5th/95th percentiles) and histogram bins across permuted parameter runs.
  - `results_walk_forward.py`: Projects stitched out-of-sample equity curves, walk-forward window results, matrix robustness heatmaps, and applies final-window optimal parameters to strategies.
- **Optimization Execution Engine (`task_optimize.py`):**
  - `TaskOptimizeVerifier.verify`: Preflight checks enforcing strategy existence (`OPTIMIZER_STRATEGY_REQUIRED`), active parameter step bounds (`OPTIMIZER_NO_ENABLED_PARAMETERS`), and Walk-Forward grid bounds (`OPTIMIZER_INVALID_WF_GRID`).
  - `TaskOptimizeRunner.execute`: Orchestrates parameter generation, evaluation sweeps over Core `OptimizationEngine` and `BacktestRunner`, records run profiles, and stores optimal parameter variants.

## 2. Host Capability Ownership

| Capability | Authority | Optimizer Workspace Usage |
|---|---|---|
| Optimization Engine | `app/core/trading/optimization/engine.py::OptimizationEngine` | Multi-parameter index permutation mapping and walk-forward window generation |
| Backtest Runner | `app/core/trading/backtest/runner.py::BacktestRunner` | Historical bar backtesting and trade series execution |
| Databank Storage | `app/core/jobs/databank.py::DatabankContainer` | Persisting accepted candidate parameter variants in databanks |
| Result Store | `app/core/trading/results/store.py::ResultStore` | Storing candidate optimization run results, sub-result keys, and equity series |
| Strategy Document | `app/workspace/algo_wizard/strategy_document.py` | HSL strategy AST models and parameter specifications |
| Logging & Errors | `app/core/host/logging.py`, `app/core/lib/errors.py` | Non-silent audit logging and typed `DomainError` envelopes |

## 3. Verification and Qualification Evidence

- **Pytest (Backend Services):** Clean execution across all tests in `tests/workspace/optimizer/`.
- **Branch-Aware Coverage:** Minimum 80% branch coverage across retained Python application source.
- **Vitest (Frontend UI):** 11 test files, 23 tests passing in `app/web/tests/workspace/optimizer/`.
- **Static Analysis & Typing:**
  - `ruff format --check`: Clean formatting.
  - `ruff check`: Clean linting.
- **Frontend Production Build:** `npm --prefix app/web run typecheck` exits 0.
