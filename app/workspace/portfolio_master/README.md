# Portfolio Master contracts and ownership

Feature: `FEAT-PORTFOLIO-MASTER`. Owner: `app/workspace/portfolio_master`.

The Portfolio Master workspace coordinates automated combinatorial portfolio search, pairwise correlation filtering, multi-strategy trade merging, acceptance condition evaluation, multi-metric fitness ranking, and databank persistence.

## 1. Architecture and Domain Contracts

`AppPortfolioMasterService` coordinates workspace configuration, combinatorial search dispatch, and evaluation pipelines:

- **Root Coordinator & Lifecycle (`app_portfolio_master.py`, `FR-master-service-lifecycle`):**
  - Manages `PortfolioMasterSearchConfig` and execution runs.
  - Enforces portfolio size boundaries `1 <= min_strategies <= max_strategies <= 50` (`DomainError(code="PORTFOLIO_MASTER_INVALID_SIZE_BOUNDS")`).
  - Implements brute-force and genetic candidate generation.
  - Returns structured `StandardResponse[PortfolioMasterRunSummary]` execution receipts.
- **Fitness Target Field Helper (`fitness_target.py`, `PM-001`, `FR-master-target-state`):**
  - `FitnessTarget.apply(*, value_type: int, approximate_type: int, target: float) -> TargetFieldState`: Controls criterion target input state and resets value to `0.0` when disabled.
- **Fitness Method Service (`fitness_method_existing_portfolio.py`, `FR-master-fitness-*`):**
  - `FitnessMethodExistingPortfolioService.normalize_criterion`: Synchronizes criterion target state with type matching.
  - `FitnessMethodExistingPortfolioService.evaluate`: Calculates weighted composite fitness scores in `[0.0, 1.0]` over normalized ranges or approximate targets.
- **Portfolio Metric Selectors & Catalog (`app/extend/portfolio_master_fitness/`):**
  - `NetProfit.compute`: Extracts `NetProfit` (range `-10000..10000`, maximize).
  - `PctStagnation.compute`: Extracts `StagnationPct` (range `0..100`, minimize).
  - `ReturnDD.compute`: Extracts `ReturnDDRatio` (range `-20..20`, maximize).
  - `PortfolioMasterFitnessCatalog`: Central registry for metric descriptors and execution dispatch.
- **CorrelationOf Period Bucketing & Pearson Correlation (`app/extend/correlation_of/`):**
  - `CorrelationOfCatalog.compute_periods`: Buckets orders into `HOUR`, `DAY`, `WEEK`, `MONTH`, `YEAR` UTC periods across 6 definitions (`ProfitLoss`, `Loss`, `NumberOfClosedTrades`, `NumberOfOpenTrades`, `NumberOfClosedPositions`, `NumberOfOpenPositions`).
  - `CorrelationOfCatalog.pearson`: Computes Pearson correlation with definition-specific skip rules (e.g. `Loss` skips periods where both series have no loss).

## 2. Host Capability Ownership

| Capability | Authority | Portfolio Master Usage |
|---|---|---|
| Search Engine & Lifecycle | `app/workspace/portfolio_master/app_portfolio_master.py::AppPortfolioMasterService` | Combinatorial generation, candidate evaluation, and search execution |
| Fitness Evaluation | `app/workspace/portfolio_master/fitness_method_existing_portfolio.py::FitnessMethodExistingPortfolioService` | Multi-metric weighted portfolio fitness calculation |
| Target State Helper | `app/workspace/portfolio_master/fitness_target.py::FitnessTarget` | Dynamic criterion target field visibility and reset |
| Fitness Catalog | `app/extend/portfolio_master_fitness/catalog.py::PortfolioMasterFitnessCatalog` | Metric descriptors and dispatch |
| Correlation Engine | `app/extend/correlation_of/catalog.py::CorrelationOfCatalog` | Temporal period bucketing and Pearson correlation |
| Logging & Errors | `app/core/host/logging.py`, `app/core/lib/responses.py` | Non-silent audit logging and typed `StandardResponse[T]` envelopes |

## 3. Verification and Qualification Evidence

- **Pytest (Backend Services & Extensions):** Clean execution across 27 tests in `tests/workspace/portfolio_master/` and `tests/extend/`.
- **Branch-Aware Coverage:** 94.17% branch coverage across retained Python source (exceeds 80% minimum requirement).
- **Vitest (Frontend UI):** 3 test files, 5 tests passing in `app/web/tests/workspace/portfolio_master/`.
- **Static Analysis & Linting:**
  - `uv run ruff check`: Clean linting (`All checks passed!`).
  - `uv run ruff format --check`: 100% formatted (21 files checked).
- **Frontend Production Build & Typecheck:**
  - `npm --prefix app/web run typecheck`: Exited 0.
  - `npm --prefix app/web run build`: Exited 0.
