# Builder contracts and ownership

Feature: `FEAT-BUILDER-CONTRACTS`. Owner: `app/workspace/builder`.

The Builder workspace provides strategy candidate generation (Genetic Programming and Random Search), building blocks parameterization and selection, ranking condition filtering, multi-objective fitness evaluation, indicator dynamic range calibration, template mutation via Parts to Improve, opposite-direction AST rule negation, and databank storage coordination.

## 1. Architecture and Domain Contracts

`AppBuilderService` acts as the root workspace controller, coordinating candidate generation settings, execution tasks, and RPC dispatching:

- **Root Coordinator & Lifecycle (`app_builder.py`):**
  - Manages `BuilderWorkspaceState` and transitions across `IDLE`, `RUNNING`, `PAUSED`, `COMPLETED`, `STOPPED`, and `FAILED`.
  - Integrates `TaskBuildRunner` execution and updates strategy generation progress metrics.
- **Genetic Algorithm Defaults (`genetic_defaults.py`):**
  - Enforces `GeneticOptionsDefaults` frozen dataclass with exact 20 observed fields.
  - Validates `in_sample_type` strict integer typing with `TypeError` guard (`BLD-001`).
- **Improvement Condition Labels (`improvement_labels.py`):**
  - Pure mapping function `improvement_label` formatting human-readable labels (`add_or_replace`, `add`, `replace`).
- **Builder Settings Services:**
  - `settings_what_to_build.py`: Manages build modes (`GENETIC`, `RANDOM`, `TEMPLATE`), directions, condition boundaries, and period ranges.
  - `settings_genetic_options.py`: Manages genetic algorithm parameters, crossover/mutation probabilities, island migration, and bounds validation (`BUILDER_INVALID_GENETIC_OPTIONS`).
  - `settings_parts_to_improve.py`: Governs selective component mutation rules and condition bounds (`BUILDER_INVALID_IMPROVEMENT_BOUNDS`).
  - `settings_blocks.py`: Governs enabled signals, indicators, price levels, order types, exit rules, sampling weights, and XML preset round-tripping (`BUILDER_MIN_BLOCKS_REQUIRED`).
  - `settings_rankings.py`: Controls databank capacity limits (`BUILDER_INVALID_MAX_RECORDS`) and multi-criteria candidate evaluation.
- **Multi-Objective Strategy Fitness (`fitness_method_strategy_result.py`):**
  - Evaluates normalized fitness scores in `[0.0, 1.0]` across single or weighted multi-criteria configurations with zero-trade protection.
- **Execution Pipeline Runner (`task_build.py`):**
  - `TaskBuildRunner.calibrate_indicators`: Computes observed `(min, max)` output ranges for oscillator and level blocks.
  - `TaskBuildRunner.execute`: Orchestrates `GenerationEngine`, `BacktestRunner`, `SettingsRankingsService`, and databank candidate storage.
- **HTTP/RPC Controller Dispatcher (`servlet_builder.py`):**
  - `ServletBuilderDispatcher`: Routes `build/start`, `build/pause`, `build/resume`, `build/stop`, `build/status`, and `indyTester/calibrate` requests to typed services.

## 2. Concrete Extension Cohorts (`app/extend/`)

The workspace registers and evaluates concrete extension definitions per `08-AppBuilder.md`:

- **Formulas Catalog (`app/extend/formulas/`):** 19 concrete definitions:
  - `close_size/full_position.py`: `FullPosition.evaluate_formula(...) -> 0.0` sentinel (`WO-BLD-FULL-POSITION`).
  - `catalog.py`: `Price/UseFormula`, 4 `Range/*` evaluators, 5 `RangeLevel/*` trigger evaluators, 6 `SLPT/*` distance evaluators, and 2 `Size/*` position sizing evaluators.
- **AST Negater Catalog (`app/extend/negater/`):** 15 concrete negater implementations:
  - `BlockNegaterRegistry` with all 15 negaters: `ActionsNegater`, `AndOrNegater`, `ComparisonsNegater`, `OscillatorComparisonsNegater`, `CDataIndyNegater`, `ConditionsNegater`, `UpperLowerNegater`, `FiboNegater`, `FractalNegater`, `PivotsNegater`, `UlcerNegater`, `FormulaNegater`, `FunctionsNegater`, `CBlockNegater`, `DefaultNegater`.

## 3. Host Capability Ownership

| Capability | Authority | Builder Workspace Usage |
|---|---|---|
| Generation Engine | `app/core/trading/generation/engine.py::GenerationEngine` | Candidate AST rule creation, tournament selection, crossover, and mutation |
| Backtest Runner | `app/core/trading/backtest/runner.py::BacktestRunner` | Historical bar backtesting and trade metric generation |
| Databank Storage | `app/core/jobs/databank.py::DatabankContainer` | Persisting accepted candidate strategies up to max records |
| Result Store | `app/core/trading/results/store.py::ResultStore` | Storing candidate backtest run results and equity series |
| Block Registry | `app/core/trading/blocks/registry.py::block_registry` | Block definitions and parameter ranges |
| Retester Cross-Checks | `app/workspace/retester/` | Robustness cross-check pipeline execution |
| Logging & Errors | `app/core/host/logging.py`, `app/core/lib/errors.py` | Non-silent audit logging and typed `DomainError` envelopes |

## 4. Verification and Qualification Evidence

- **Pytest (Backend & Extensions):** Clean execution across `tests/workspace/builder` and `tests/extend/formulas/`, `tests/extend/test_negater.py`.
- **Branch-Aware Coverage:** >= 80% coverage across retained application source.
- **Vitest (Frontend UI):** 10 test files, 52 tests passing in `app/web/tests/workspace/builder`.
- **Static Analysis & Typing:**
  - `ruff format --check`: Clean formatting.
  - `ruff check`: Clean linting.
  - `mypy --strict`: Clean typechecking.
- **Frontend Production Build:** `npm --prefix app/web run typecheck` and `npm --prefix app/web run build` exit 0.
