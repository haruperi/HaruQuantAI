# Optimization — Version 1 Code Audit

> **Audit snapshot:** `haruperi/HaruQuantAI`, branch `main`, commit `68851eb6898b229f49f1295c37748c63eefed3d3`.

## 1. Audit Scope

* **Domain:** Optimization
* **Package path:** `app/services/optimization`
* **Tests path supplied:** `tests/optimization/unit/`
* **Actual unit-test file inspected:** `tests/optimization/unit/test_optimization.py`
* **Related usage package supplied:** `tests/optimization/usage/`
* **Actual usage file inspected:** `tests/optimization/usage/09_optimization.py`
* **Source files inspected:** all 16 Python files under `app/services/optimization`, plus `app/services/optimization/README.md`.
* **Boundary files inspected:** `app/__init__.py`, `app/services/__init__.py`, and `app/services/strategy/base.py`.
* **Missing dependency paths explicitly checked:** `app/services/simulator/orchestrator.py`, `app/services/strategies/registry.py`, and `app/services/strategy/registry.py`; all three are absent on the audited revision.
* **History evidence inspected:** the package-introduction commit `5f385298f54dd01b46b5a0f2e728aa488f4e7e22`, which added only the optimization package, its unit tests, its usage example, README, and changelog entry—no production caller.
* **Excluded:** generated files, caches, virtual environments, unrelated domains, and Version 2 requirements.
* **Audit limitations:**
  * GitHub repository code search returned no indexed results, so a complete repository-wide symbol search could not be executed through code search.
  * The repository could not be cloned into the execution container, so tests were not run.
  * Caller conclusions therefore combine current source inspection, package/test/example imports, package-introduction history, service/root initializers, and explicit checks of known dynamic import paths.
  * Absence-of-caller findings are **Medium confidence** unless stronger evidence is stated.

## 2. Executive Summary

The Version 1 optimization domain is a broad research utility library. It provides parameter-space schemas, exhaustive grid search, pseudo-random search, a genetic search loop, a nominal Bayesian wrapper, scoring and anti-overfitting statistics, chronological and walk-forward splits, trade-sequence Monte Carlo simulations, robustness stress tests, checkpoint files, and an in-memory run repository.

The strongest working behaviour is **self-contained computation on supplied data**: parameter validation, deterministic hashing, constraint evaluation, score calculation, split generation, Monte Carlo analysis, stress transformations, atomic checkpoint writes, and in-memory persistence. The dry-run search workflows also execute mechanically, but they score every candidate from an empty trade list; consequently they validate orchestration rather than optimize parameters meaningfully.

The simulator-backed workflows are not operational on a clean checkout. `helpers.run_strategy_backtest()` imports missing `app.services.simulator.orchestrator.BacktestOrchestrator`, and `helpers.run_strategy_backtest_from_path()` imports missing `app.services.strategies.registry.register_strategy`. The unit test suite hides both gaps by inserting mock modules into `sys.modules` and explicitly comments that they do not exist on disk.

The most important structural problems are: a 151-name root facade; many unused public models and wrappers; duplicated walk-forward, Monte Carlo, ranking, and reporting surfaces; a Bayesian implementation that still delegates to random search even when a backend is installed; Sobol/LHS labels without corresponding sampling; disconnected persistence; background-task functions that only generate IDs and log; inconsistent error contracts; and tests that prove mocked or dry-run behaviour rather than real cross-domain execution.

Evidence quality is **high** for package internals, tests, examples, and the two broken imports; **medium** for repository-wide non-usage because the repository was not code-search indexed.

**Audit metrics:** Module folders: 2 | Python files: 16 | Root exports: 151 | Public-looking top-level symbols: 177 | Symbols with confirmed static callers: 107 (60.5%; 0 confirmed external production callers) | Workflows found: 9

## 3. Actual Package Structure

```text
app/services/optimization

├── __init__.py

│   └── 151 re-exported public names; no runtime entry-point registration

├── errors.py

│   ├── ErrorPayload
│   ├── OptimizationError
│   ├── OptimizationValidationError

│   ├── OPTIMIZATION_ERROR_CODES
│   ├── ERROR_MESSAGES
│   └── to_optimization_error_payload()

├── helpers.py

│   ├── Infinity; OPT_JSON_SERIALIZATION_FAILED

│   ├── OptimizationExecutionError; EngineOptimizationResult

│   └── strategy_id(); normalize_engine_type(); load_strategy_from_path(); run_strategy_backtest();

│       run_strategy_backtest_from_path(); parameter_space_hash(); get_active_parameters();

│       build_candidate_hash(); select_best_candidate(); json_safe_serialize(); parametric_simulation();

│       optimization_tool_context(); optimization_business_payload(); package_optimization_request();

│       optimization_tool_result()

├── models.py

│   ├── OptimizationStatus; Contract

│   ├── ParameterRange; ParameterSpace; ParameterCandidate; OptimizationResult; OptimizationSummary

│   ├── OptimizationRequest; OptimizationResultItem; OptimizationResponse; OptimizationRunDetails; SweepResult

│   ├── UnsupervisedConfigRequest; UnsupervisedRunSummary; UnsupervisedAnalysisRequest

│   ├── PositionSizingRequest; PositionSizingResult

│   ├── WalkForwardWindow; WalkForwardRequest; WalkForwardResponse; SplitterResult

│   ├── MonteCarloResult; MonteCarloRequest; ParametricMonteCarloRequest; MonteCarloResponse

│   ├── ConsecutiveLosingRequest; ConsecutiveLosingScenario; ConsecutiveLosingResponse;

│   │   ConsecutiveLosingScenarioResult

│   ├── ProfitTargetRequest; ProfitTargetResult; ProfitTargetResponse; ProfitTargetScenarioResult

│   ├── MultiEntryRequest; MultiEntryScenarioResult; MultiEntryResponse

│   ├── RobustnessRequest; RobustnessStats; RobustnessResponse

│   └── ParametricSimulationResult; PortfolioOptimizerResult

├── scoring.py

│   └── ScoringFunction; get_daily_returns(); calculate_max_drawdown(); total_return_score();

│       profit_factor_score(); sharpe_score(); sortino_score(); calmar_score(); custom_score();

│       optimization_get_scoring_func(); calculate_dsr(); evaluate_candidate_score(); rank_candidates();

│       nominal_trial_count(); trial_count_independence_warning(); pareto_select()

├── splitting.py

│   └── WalkForwardSplit; chronological_split(); rolling_window_split(); expanding_window_split();

│       splitter_from_rolling(); splitter_from_expanding(); splitter_rolling_split();

│       run_walk_forward_optimization(); run_walk_forward_matrix()

├── robustness.py

│   └── calculate_robustness_score(); bootstrap_simulation(); run_spread_stress_test();

│       run_slippage_stress_test(); run_commission_stress_test(); run_randomize_trade_order_mc();

│       run_resample_trades_mc(); run_skip_trades_mc(); run_randomize_parameters_mc();

│       run_randomize_history_mc(); run_combined_monte_carlo(); run_cross_market_test();

│       run_cross_timeframe_test(); run_second_oos_test(); run_third_oos_test();

│       assess_strategy_robustness(); build_monte_carlo_result(); optimization_monte_carlo();

│       robustness_simulation(); compare_simulation_methods(); run_monte_carlo_task();

│       build_robustness_report()

├── sweeps.py

│   └── calculate_parameter_stability(); detect_overfit_parameters(); rank_parameter_sets();

│       compare_optimization_runs(); walk_forward(); parallel_walk_forward(); print_optimization_report();

│       run_parameter_sweep(); optimization_walk_forward(); run_optimization_task();

│       run_walk_forward_task(); analyze_walk_forward_results(); analyze_parallel_results();

│       save_optimization_result(); build_optimization_report()

├── algorithms

│   ├── __init__.py — 15 algorithm re-exports

│   ├── grid.py — check_constraints(); generate_parameter_grid(); grid_search(); parallel_grid_search(); optimization_grid_search()

│   ├── random.py — six request/result models; sample_parameter(); random_search(); parallel_random_search();

│   │   optimization_random_search(); shuffle_trades_simulation(); random_win_rate_simulation(); monte_carlo_analysis()

│   ├── bayesian.py — BayesianOptimizationResult; bayesian_optimization(); optimization_bayesian()

│   └── genetic.py — GeneticAlgorithmResult; crossover(); mutate(); genetic_algorithm(); optimization_genetic()

└── persistence

    ├── __init__.py — 20 persistence re-exports

    ├── checkpoint.py — nine error constants; validate_safe_path(); save_checkpoint();

    │   validate_checkpoint_schema(); load_checkpoint(); load_checkpoint_with_fallback()

    └── repository.py — R; OptimizationRunRecord; OptimizationRepository; InMemoryOptimizationRepository;

        ProgressTracker; retry_with_backoff(); save_optimization_run(); load_optimization_run();

        update_optimization_progress()
```

## 4. Module and File Inventory

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- |
| root | `__init__.py` | Package facade; eagerly imports and re-exports nearly the whole domain. | 151 names in `__all__` | Stdlib future; local optimization modules | Possibly used | Questionable |
| root | `errors.py` | Optimization-specific exceptions and redacted error mapping. | 6 symbols | Typing; `app.utils.logger`, `app.utils.security` | Partly used | Supporting |
| root | `models.py` | Pydantic request/result/data contracts for implemented and unimplemented capabilities. | 41 symbols | Stdlib; Pydantic; `optimization.errors`; `app.utils.standard` | Mixed: Used/Test-only/Unused | Supporting |
| root | `helpers.py` | Backtest adapter, dynamic strategy loading, hashing, serialization, simulation, envelope helpers. | 19 symbols | Stdlib; `optimization.errors`; `app.utils.standard`; dynamic simulator/strategy imports | Mixed; real backtest broken | Essential |
| root | `scoring.py` | Trading metrics, candidate scoring, DSR/MTB diagnostics, ranking, Pareto selection. | 16 symbols | Stdlib; NumPy; optional SciPy | Test-only/internal | Essential |
| root | `splitting.py` | Chronological, rolling, expanding, and walk-forward orchestration. | 10 symbols | Stdlib; optimization models; lazy algorithms/helpers/scoring | Test-only/internal | Useful |
| root | `robustness.py` | Trade stress transforms, Monte Carlo wrappers, robustness assessment/reporting. | 22 symbols | Stdlib; NumPy; models; logger; lazy optimization imports | Test-only/internal | Useful |
| root | `sweeps.py` | Main sweep facade, second walk-forward implementation, report/task convenience functions. | 15 symbols | Stdlib; NumPy; algorithms/helpers/models/scoring/splitting; logger | Test-only/internal | Essential |
| algorithms | `__init__.py` | Algorithm subpackage facade. | 15 re-exports | Local algorithm files | Possibly used | Supporting |
| algorithms | `grid.py` | Safe constraint evaluation and sequential/parallel exhaustive search. | 5 symbols | Stdlib; local errors/helpers/models/scoring; logger | Test-only/internal | Essential |
| algorithms | `random.py` | Pseudo-random search plus trade-order and win-rate simulations. | 13 symbols | Stdlib; Pydantic; local grid/errors/helpers/models/scoring; logger; optional SciPy check | Mixed | Useful |
| algorithms | `bayesian.py` | Dependency probe and random-search delegation labelled Bayesian. | 3 symbols | Stdlib; Pydantic; random search; helpers; logger; optional Optuna/skopt probe | Test-only | Questionable |
| algorithms | `genetic.py` | Population initialization, crossover, mutation, selection, evaluation, wrapper. | 5 symbols | Stdlib; Pydantic; grid/random/helpers/models/scoring; logger | Test-only/internal | Useful |
| persistence | `__init__.py` | Persistence subpackage facade. | 20 re-exports | Checkpoint and repository modules | Possibly used | Supporting |
| persistence | `checkpoint.py` | Path-guarded atomic JSON checkpoint persistence and fallback loading. | 14 symbols | Stdlib; `OptimizationExecutionError` | Test-only/example | Useful |
| persistence | `repository.py` | Repository port, thread-safe memory adapter, progress tracker, retry wrappers. | 9 symbols | Stdlib; Pydantic; `OptimizationExecutionError` | Test-only/example | Useful |

### Dependency order observed

`errors.py` / `models.py` → `helpers.py` / `scoring.py` → `algorithms/*` → `splitting.py` / `robustness.py` → `sweeps.py` → optional `persistence/*`.

The source does not actually wire persistence into `sweeps.py`; the ordering above reflects import and conceptual dependency, not an operational save/resume pipeline.

## 5. Public Behaviour Inventory

Usage statuses in this section describe the strongest evidence found. **Test-only/internal** means the symbol has static callers, but every confirmed external trigger is a unit test or usage example.

### `__init__.py`

**File responsibility:** eager public facade.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 151 names in `__all__` | Re-export set | Makes algorithms, models, robustness, splitting, persistence, and helpers importable from `app.services.optimization`. | Import → module namespace | Local state mutation (module import) | Any eager-import failure | Unit test and usage script import the facade. | Broad import coverage | Possibly used | Questionable |

### `errors.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ErrorPayload` | TypedDict | Shape `{code, details}` for error envelopes. | mapping type | None | None | `to_optimization_error_payload` annotation | None direct | Unused | Supporting |
| `OptimizationError(message, *, code=None)` | Exception class | Base optimization exception with mutable `code`. | message → exception | Local state mutation | None | Subclassed by `OptimizationValidationError`; aliased by helpers. | Indirect | Used internally | Supporting |
| `OptimizationValidationError` | Exception class | Validation-specialized optimization error. | message/code → exception | None | None | Imported by grid/random/genetic/models. | Constraint/model tests | Used internally | Supporting |
| `OPTIMIZATION_ERROR_CODES` | Constant | Documents eight approved boundary codes. | frozenset[str] | None | None | No enforcement caller found. | None | Unused | Questionable |
| `ERROR_MESSAGES` | Constant | Maps approved codes to generic messages. | dict[str,str] | None | None | No caller found. | None | Unused | No demonstrated value |
| `to_optimization_error_payload(exception, request_id=None)` | Function | Redacts exception details and returns code/details. | exception → `ErrorPayload` | Read-only | Redaction/logger failures | No caller found. | None | Unused | Questionable |

### `helpers.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Infinity` | Constant | Positive infinity sentinel. | float | None | None | Unit test serialization case. | `test_json_safe_serialize` | Test-only | Supporting |
| `OPT_JSON_SERIALIZATION_FAILED` | Constant | Serialization failure code. | str | None | None | `json_safe_serialize`. | Indirect | Used internally | Supporting |
| `OptimizationExecutionError` | Exception class | Execution failure with optimization code. | message/code → exception | Local state mutation | None | Most algorithms, persistence, tests. | Extensive | Used internally | Essential |
| `EngineOptimizationResult` | Frozen dataclass | Normalized simulator result contract. | engine data → record | None | None | Constructed by `run_strategy_backtest`. | Mock-backed success test | Used internally | Supporting |
| `strategy_id(strategy)` | Function | Derives class/instance identifier. | object → str | None | None | Unit test only. | `test_strategy_id_helper` | Test-only | Useful |
| `normalize_engine_type(engine_type)` | Function | Maps legacy/event-driven labels. | str → str | None | None | `run_strategy_backtest`; unit test. | `test_normalize_engine_type` | Used internally | Supporting |
| `load_strategy_from_path(file_path, class_name)` | Function | Imports arbitrary Python file and returns named class. | path/name → type | Read-only; Local state mutation (`sys.modules`); executes module | `OptimizationExecutionError` | `run_strategy_backtest_from_path`; unit test. | Missing-file and mocked dynamic test | Used internally | Useful |
| `run_strategy_backtest(...)` | Function | Builds simulator payload, executes orchestrator, pairs deals, returns normalized result. | strategy/data/params → `EngineOptimizationResult` | Local state mutation; cross-domain service call | `OptimizationExecutionError`, currently `ModuleNotFoundError` | All non-dry-run searches, WFA, robustness cross-tests; unit test with mocks. | Success test injects simulator mocks | Possibly used; operationally broken | Essential |
| `run_strategy_backtest_from_path(...)` | Function | Loads/registers strategy class then delegates to backtest. | file/class/data/params → result | Read-only; Local state mutation; cross-domain call | Import/registration/backtest errors | Unit test only. | Test injects missing registry mock | Test-only; broken clean checkout | Questionable |
| `parameter_space_hash(space)` | Function | Canonical order-invariant SHA-256 of parameter space. | `ParameterSpace` → str | None | Serialization errors | Tests/examples. | Hash test | Test-only | Useful |
| `get_active_parameters(parameters, space)` | Function | Removes inactive conditional parameters. | dict/space → dict | None | Recursion errors on malformed cycles | `build_candidate_hash`; tests/examples. | Conditional test | Used internally | Supporting |
| `build_candidate_hash(...)` | Function | Canonical candidate deduplication hash. | identity fields/params/space → str | None | Serialization errors | Grid/random/genetic; unit test. | Hash test | Used internally | Essential |
| `select_best_candidate(results)` | Function | Returns highest-score candidate or empty sentinel. | results → `(ParameterCandidate,float)` | None | None | All search algorithms. | Indirect | Used internally | Essential |
| `json_safe_serialize(obj)` | Function | Converts supported values to deterministic JSON-safe forms. | object → JSON-safe object | None | `OptimizationExecutionError` for unsupported type | Unit test only. | Serialization test | Test-only | Useful |
| `parametric_simulation(...)` | Function | Seeded compounding equity/drawdown simulation. | win/risk/count inputs → dict of paths | Local state mutation (local RNG only) | None | Unit test only. | `test_parametric_simulation` | Test-only | Useful |
| `optimization_tool_context(**kwargs)` | Function | Extracts request/tool context defaults. | kwargs → dict | None | None | No caller found. | None | Unused | Questionable |
| `optimization_business_payload(payload)` | Function | Removes routing/context fields. | dict → dict | None | None | No caller found. | None | Unused | Questionable |
| `package_optimization_request(payload)` | Function | Validates `OptimizationRequest` and returns packaged dry-run envelope. | dict → dict | None | Pydantic validation | No caller found. | None | Unused | Questionable |
| `optimization_tool_result(...)` | Function | Builds standard success/error response envelope. | tool result fields → `StandardResponse` | None | Shared response-builder errors | `run_parameter_sweep`. | Facade test | Used internally | Supporting |

### `models.py`

**File responsibility:** Pydantic data contracts. Data-only models have side effect `None`; invalid construction raises Pydantic validation errors unless noted.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OptimizationStatus` | Type alias | Allowed workflow status literals. | literal value | None | Type-time only | Responses/status annotations | Indirect | Used internally | Supporting |
| `Contract` | BaseModel | Local traceable contract base with metadata validation and canonical hashes. | common trace fields | None | ValueError/`ValidationError` | Inherited by request/response models. | Indirect | Used internally | Supporting |
| `Contract.validate_metadata_structure()` | Class validator | Requires namespaced, non-sensitive, canonically serializable metadata. | metadata → metadata | None | TypeError/ValueError | Pydantic construction. | Indirect | Used internally | Supporting |
| `Contract.validate_trace_identifiers()` | Model validator | Rejects blank trace IDs. | model → model | None | ValueError | Pydantic construction. | Indirect | Used internally | Supporting |
| `Contract.to_json()` | Method | Canonical JSON serialization. | self → str | None | `ValidationError` | No external caller found. | None | Unused | Useful |
| `Contract.content_hash()` | Method | Hashes business fields excluding trace fields. | self → SHA-256 | None | `ValidationError` | No external caller found. | None | Unused | Useful |
| `Contract.contract_hash()` | Method | Hashes full canonical contract. | self → SHA-256 | None | Serialization errors | No external caller found. | None | Unused | Useful |
| `Contract.check_compatibility(target_version)` | Method | Major-version equality/minor-version compatibility check. | version → bool | None | None; returns false on malformed integers | No caller found. | None | Unused | Questionable |
| `ParameterRange` | Model | One typed search dimension with bounds/options/conditional activation. | fields → model | None | ValueError | All search space construction. | Direct | Test-only/internal | Essential |
| `ParameterSpace` | Model | Collection of ranges plus string constraints. | fields → model | None | Pydantic errors | All algorithms/sweeps. | Direct | Test-only/internal | Essential |
| `ParameterCandidate` | Model | Selected parameter mapping plus hash. | fields → model | None | Pydantic errors | `select_best_candidate`, summaries. | Indirect | Used internally | Supporting |
| `OptimizationResult` | Model | One evaluated candidate, score, metrics, metadata. | fields → model | None | Pydantic errors | Search algorithms. | Indirect | Used internally | Essential |
| `OptimizationSummary` | Model | Complete search result and candidate list. | fields → model | None | Pydantic errors | Search algorithms, sweeps/reporting. | Indirect | Used internally | Essential |
| `OptimizationSummary.top_n(n=10)` | Method | Returns highest-scoring N candidates. | n → list | None | None | Sweep/report builders. | Facade test indirect | Used internally | Supporting |
| `OptimizationSummary.to_dataframe()` | Method | Flattens candidates into pandas DataFrame. | self → DataFrame | None | ImportError/pandas errors | No caller found. | None | Unused | Questionable |
| `UnsupervisedConfigRequest` | Model | Configuration for clustering/PCA-like analysis. | fields → model | None | Pydantic errors | No implementation consumes it. | None | Unused | No demonstrated value |
| `UnsupervisedRunSummary` | Model | Cluster labels and silhouette summary. | fields → model | None | Pydantic errors | No producer/consumer found. | None | Unused | No demonstrated value |
| `UnsupervisedAnalysisRequest` | Model | Run ID plus unsupervised config. | fields → model | None | Pydantic errors | No implementation consumes it. | None | Unused | No demonstrated value |
| `OptimizationRequest` | Model | Validated parameter sweep request. | fields → model | None | Pydantic errors | `run_parameter_sweep`, `package_optimization_request`. | Facade test | Used internally | Essential |
| `OptimizationResultItem` | Model | Public response candidate item. | fields → model | None | Pydantic errors | `run_parameter_sweep`. | Indirect | Used internally | Supporting |
| `OptimizationResponse` | Model | Public sweep response payload. | fields → model | None | Pydantic errors | `run_parameter_sweep`. | Indirect | Used internally | Supporting |
| `OptimizationRunDetails` | Model | Saved-run audit details. | fields → model | None | Pydantic errors | No caller found; repository uses a different record. | None | Unused | Questionable |
| `SweepResult` | Model | Run ID plus `OptimizationSummary`. | fields → model | None | Pydantic errors | No caller found. | None | Unused | No demonstrated value |
| `PositionSizingRequest` | Model | Inputs for position-sizing simulation. | fields → model | None | Pydantic errors | No function accepts this model. | None | Unused | No demonstrated value |
| `PositionSizingResult` | Model | Position-sizing simulation curves/results. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `WalkForwardWindow` | Model | Train/test time boundaries. | fields → model | None | Pydantic errors | All split generators. | Direct/indirect | Used internally | Essential |
| `WalkForwardRequest` | Model | Walk-forward configuration. | fields → model | None | Pydantic errors | `walk_forward`, `optimization_walk_forward`. | Indirect | Used internally | Essential |
| `WalkForwardResponse` | Model | Aggregated WFA metrics/evidence. | fields → model | None | Pydantic errors | `_build_wfa_response`, analysis helper. | Indirect | Used internally | Supporting |
| `MonteCarloResult` | Model | Detailed path, drawdown, ruin, target, and streak statistics. | fields → model | None | Pydantic errors | `build_monte_carlo_result`. | Indirect | Used internally | Supporting |
| `MonteCarloRequest` | Model | Trade-level MC request. | fields → model | None | Pydantic errors | No public function accepts the model directly. | None | Unused | Questionable |
| `ParametricMonteCarloRequest` | Model | Parametric MC request. | fields → model | None | Pydantic errors | No public function accepts the model directly. | None | Unused | Questionable |
| `MonteCarloResponse` | Model | MC summary plus detailed result. | fields → model | None | Pydantic errors | `optimization_monte_carlo`. | Direct/indirect | Used internally | Essential |
| `ConsecutiveLosingRequest` | Model | Losing-streak simulation request. | fields → model | None | Pydantic errors | No implementation found. | None | Unused | No demonstrated value |
| `ConsecutiveLosingScenario` | Model | Streak value and probability. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `ConsecutiveLosingResponse` | Model | Losing-streak response. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `ProfitTargetRequest` | Model | Profit-target simulation request. | fields → model | None | Pydantic errors | No implementation consumes it. | None | Unused | No demonstrated value |
| `ProfitTargetResult` | Model | One target probability result. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `ProfitTargetResponse` | Model | Profit-target aggregate response. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `MultiEntryRequest` | Model | Scale-in simulation request. | fields → model | None | Pydantic errors | No implementation consumes it. | None | Unused | No demonstrated value |
| `MultiEntryScenarioResult` | Model | One multi-entry scenario result. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `MultiEntryResponse` | Model | Multi-entry simulation response. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `RobustnessRequest` | Model | Strategy/data robustness request. | fields → model | None | Pydantic errors | No public robustness function accepts it. | None | Unused | Questionable |
| `RobustnessStats` | Model | Pass rate, score, warnings. | fields → model | None | Pydantic errors | `assess_strategy_robustness`. | Indirect | Used internally | Supporting |
| `RobustnessResponse` | Model | Robustness assessment envelope. | fields → model | None | Pydantic errors | `assess_strategy_robustness`, reports. | Direct/indirect | Used internally | Essential |
| `SplitterResult` | Model | Collection of WFA windows. | fields → model | None | Pydantic errors | Split functions/coordinator. | Indirect | Used internally | Supporting |
| `ParametricSimulationResult` | Model | Parametric paths/drawdowns/final equity. | fields → model | None | Pydantic errors | `parametric_simulation` returns plain dict instead. | None | Unused | Questionable |
| `ConsecutiveLosingScenarioResult` | Model | Single losing-streak result. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `ProfitTargetScenarioResult` | Model | Single target-reach result. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `PortfolioOptimizerResult` | Model | Asset weights plus metadata. | fields → model | None | Pydantic errors | No portfolio optimizer implementation found. | None | Unused | No demonstrated value |

### `algorithms/grid.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `check_constraints(params, constraints)` | Function | AST-validates and evaluates all string constraints. | dict/list[str] → bool | None | `OptimizationValidationError` for unsafe/syntax cases | Grid/random/genetic. | Indirect/direct | Used internally | Essential |
| `generate_parameter_grid(space)` | Function | Materializes candidate values per dimension. | space → dict[list] | None | Conversion errors | Sequential/parallel grid search. | Indirect | Used internally | Essential |
| `grid_search(...)` | Function | Sequential lazy Cartesian search; dry-run or simulator evaluation. | request fields → `OptimizationSummary` | Local state mutation; optional cross-domain call | Validation/execution errors; failed candidates skipped | Sweeps, wrapper, WFA, tests/examples. | Direct | Test-only/internal; real mode broken | Essential |
| `parallel_grid_search(...)` | Function | Threaded candidate evaluation over lazy combinations. | request fields → summary | Local state mutation (threads); optional cross-domain call | Worker exceptions may propagate/are logged | `run_parameter_sweep`, wrapper, tests. | Direct | Test-only/internal; real mode broken | Essential |
| `optimization_grid_search(...)` | Function | Dict-returning wrapper selecting sequential/parallel path. | request fields → dict | None beyond delegated work | Catches all and returns error dict | No caller found. | None | Unused | Questionable |

### `algorithms/random.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ManualPairInput` | Model | Win-rate and reward/risk pair. | fields → model | None | Pydantic errors | Only nested in unused request model. | None | Unused | No demonstrated value |
| `RandomWinRatePair` | Model | Pair plus score. | fields → model | None | Pydantic errors | No producer/consumer found. | None | Unused | No demonstrated value |
| `RandomWinRateRequest` | Model | Batch random-win-rate request. | fields → model | None | Pydantic errors | No function accepts it. | None | Unused | No demonstrated value |
| `DistributionStats` | Model | Distribution summary statistics. | fields → model | None | Pydantic errors | Only nested in unused result model. | None | Unused | No demonstrated value |
| `RandomWinRateResult` | Model | Per-pair simulation result. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `RandomWinRateResponse` | Model | Batch simulation response. | fields → model | None | Pydantic errors | No producer found. | None | Unused | No demonstrated value |
| `sample_parameter(p, rng)` | Function | Samples one typed parameter using `random.Random`. | range/RNG → value | Local state mutation (RNG) | Choice errors for empty options/ranges | Random/genetic algorithms. | Indirect | Used internally | Essential |
| `random_search(...)` | Function | Unique pseudo-random candidate search with constraints and hashing. | request fields → summary | Local state mutation; optional cross-domain call | Sampler/validation/execution errors | Bayesian fallback, sweeps, WFA, tests/examples. | Direct | Test-only/internal; real mode broken | Essential |
| `parallel_random_search(...)` | Function | Pre-generates pseudo-random candidates then evaluates with threads. | request fields → summary | Local state mutation (RNG/threads); optional cross-domain call | Worker/execution errors | Sweep facade/wrapper. | Indirect | Test-only/internal; real mode broken | Useful |
| `optimization_random_search(...)` | Function | Dict wrapper selecting sequential/parallel random search. | request fields → dict | None beyond delegated work | Catches all and returns error dict | No caller found. | None | Unused | Questionable |
| `shuffle_trades_simulation(trades, initial_balance, seed)` | Function | Shuffles trade order and builds one equity path. | trades → list[float] | Local state mutation (RNG) | None | `monte_carlo_analysis`. | Indirect | Used internally | Supporting |
| `random_win_rate_simulation(...)` | Function | Generates fixed-1%-risk binary trade paths. | rates/counts → paths | Local state mutation (RNG) | None | No caller found. | None | Unused | Questionable |
| `monte_carlo_analysis(...)` | Function | Creates shuffled or resampled trade equity paths. | trades/method/count → paths | Local state mutation (RNG) | None; unknown methods silently become resampling | Robustness wrappers. | Indirect | Used internally | Essential |

### `algorithms/bayesian.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BayesianOptimizationResult` | Model | Compact wrapper result. | fields → model | None | Pydantic errors | `optimization_bayesian`. | No direct | Used internally only by unused wrapper | Questionable |
| `bayesian_optimization(...)` | Function | Probes Optuna/skopt then always delegates evaluation to `random_search`. | request fields → summary | Optional import probe; delegated work | `OptimizationExecutionError` in strict mode | Sweep facade, wrapper, tests/examples. | Fallback test | Test-only/internal | Questionable |
| `optimization_bayesian(...)` | Function | Dict-returning typed wrapper. | request fields → dict | None beyond delegated work | Catches all and returns error dict | No caller found. | None | Unused | Questionable |

### `algorithms/genetic.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GeneticAlgorithmResult` | Model | Compact genetic-run result. | fields → model | None | Pydantic errors | `optimization_genetic`. | No direct | Used internally only by unused wrapper | Questionable |
| `crossover(parent_a, parent_b, space, rng)` | Function | Builds offspring by choice or numeric averaging. | parents/space/RNG → dict | Local state mutation (RNG) | Conversion errors | `genetic_algorithm`. | Indirect | Used internally | Supporting |
| `mutate(params, space, mutation_rate, rng)` | Function | Resamples non-fixed fields probabilistically. | params/space/rate/RNG → dict | Local state mutation (RNG) | Sampling errors | `genetic_algorithm`. | Indirect | Used internally | Supporting |
| `genetic_algorithm(...)` | Function | Evolves candidates with caching, constraints, elitism, tournament selection. | request fields → summary | Local state mutation; optional cross-domain call | Validation errors; execution failures logged/skipped | Sweep facade, wrapper, tests/examples. | Direct | Test-only/internal; real mode broken | Useful |
| `optimization_genetic(...)` | Function | Dict-returning typed wrapper. | request fields → dict | None beyond delegated work | Catches all and returns error dict | No caller found. | None | Unused | Questionable |

### `scoring.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ScoringFunction` | Protocol | Callable contract for score functions. | trades/balance → float | None | Implementation-defined | Resolver typing. | Indirect | Used internally | Supporting |
| `get_daily_returns(...)` | Function | Groups profits by close date and divides by initial balance. | trades/balance → list[float] | None | ZeroDivisionError if balance zero with dated trades | Sharpe, Sortino, evaluator. | Indirect | Used internally | Essential |
| `calculate_max_drawdown(...)` | Function | Peak-to-trough drawdown from ordered trades. | trades/balance → float | None | None | Calmar/custom/evaluator/tests. | Direct | Used internally | Essential |
| `total_return_score(...)` | Function | Net profit divided by initial balance. | trades/balance → float | None | None | Resolver, robustness, tests. | Direct | Used internally | Essential |
| `profit_factor_score(...)` | Function | Gross wins divided by gross losses. | trades/balance → float | None | None | Resolver/tests. | Direct | Used internally | Useful |
| `sharpe_score(...)` | Function | Annualized daily-return Sharpe. | trades/balance → float | None | NumPy/type errors | Resolver/evaluator/tests. | Direct | Used internally | Essential |
| `sortino_score(...)` | Function | Annualized downside-risk ratio. | trades/balance → float | None | None | Resolver/tests. | Direct | Used internally | Useful |
| `calmar_score(...)` | Function | Total return divided by max drawdown. | trades/balance → float | None | None | Resolver/tests. | Direct | Used internally | Useful |
| `custom_score(...)` | Function | Weighted return/Sharpe/drawdown score. | trades/balance → float | None | None | Resolver/tests. | Direct | Used internally | Useful |
| `optimization_get_scoring_func(name)` | Function | Maps objective name; unknown falls back to total return. | name → callable | None | None | Candidate evaluator, Pareto, tests. | Direct | Used internally | Essential |
| `calculate_dsr(...)` | Function | Approximate deflated Sharpe probability. | Sharpe/trials/moments/samples → float | None | Math errors on invalid inputs | Candidate evaluator/tests. | Direct | Used internally | Useful |
| `evaluate_candidate_score(...)` | Function | Computes objective, raw/deflated Sharpe, drawdown, MTB metadata. | trades/balance/objective/trials → dict | None | Metric errors | All searches and WFA. | Direct | Used internally | Essential |
| `rank_candidates(candidates)` | Function | Stable deterministic score/trade-count/hash sorting. | list[dict] → list[dict] | None | Conversion/key errors | Unit test; single-objective Pareto. | Direct | Test-only/internal | Useful |
| `nominal_trial_count(candidates)` | Function | Counts unique non-empty candidate hashes. | list[dict] → int | None | None | No caller found. | None | Unused | Questionable |
| `trial_count_independence_warning(...)` | Function | Warns for low counts or correlated Bayesian/genetic searches. | count/method → str\|None | None | None | Candidate evaluator calls without method argument. | Indirect | Used internally but partially disconnected | Questionable |
| `pareto_select(...)` | Function | Returns non-dominated candidates over score functions. | candidates/objectives → list | None | Metric/data errors | Unit test only. | Direct | Test-only | Useful |

### `splitting.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WalkForwardSplit(...)` | Class | Stores split configuration and dispatches rolling vs expanding. | dates/config → object | Local state mutation | Date parsing errors | Sweeps and unit/usage examples. | Direct | Test-only/internal | Essential |
| `WalkForwardSplit.split()` | Method | Builds `SplitterResult`. | self → result | None | Division/date errors | WFA implementations/tests. | Direct | Used internally | Essential |
| `chronological_split(...)` | Function | Creates one train/test window. | dates/fraction → tuple | None | Date errors | No caller found. | None | Unused | Useful |
| `rolling_window_split(...)` | Function | Sliding train/test windows with purge/embargo offsets. | dates/config → windows | None | Division/date errors | Coordinator/helpers/tests/examples. | Direct | Used internally | Essential |
| `expanding_window_split(...)` | Function | Anchored expanding train windows. | dates/config → windows | None | Division/date errors | Coordinator/helpers/tests. | Direct | Used internally | Essential |
| `splitter_from_rolling(...)` | Function | ISO-string convenience wrapper. | strings/config → `SplitterResult` | None | Date errors | Unit test only. | Direct | Test-only | Supporting |
| `splitter_from_expanding(...)` | Function | ISO-string convenience wrapper. | strings/config → result | None | Date errors | Unit test only. | Direct | Test-only | Supporting |
| `splitter_rolling_split(data, train_fraction)` | Function | Simple index split for list/DataFrame. | tabular/fraction → train,test | None | Slicing/type errors | Unit test only. | Direct | Test-only | Questionable |
| `run_walk_forward_optimization(...)` | Function | Per-fold random search and optional OOS backtest; returns dict. | request fields → dict | Optional cross-domain call | Per-fold failures embedded | No caller found. | None | Unused; real mode broken | Questionable |
| `run_walk_forward_matrix(...)` | Function | Runs prior function for strategy/space pairs. | lists/config → dict | Delegated | ValueError on length mismatch | No caller found. | None | Unused | Questionable |

### `robustness.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `calculate_robustness_score(checks)` | Function | Percent of boolean checks passing. | dict → float | None | None | `assess_strategy_robustness`. | Indirect | Used internally | Supporting |
| `bootstrap_simulation(...)` | Function | Block-bootstrap trade outcomes. | trades/config → paths | Local state mutation (RNG) | None | `run_randomize_history_mc`. | No direct | Used internally | Useful |
| `run_spread_stress_test(...)` | Function | Subtracts synthetic spread penalty per trade. | trades/config → copied trades | None | Conversion errors | Reports/tests. | Direct | Test-only/internal | Useful |
| `run_slippage_stress_test(...)` | Function | Subtracts synthetic slippage penalty. | trades/config → copied trades | None | Conversion errors | Assessment/reports/tests/examples. | Direct | Test-only/internal | Useful |
| `run_commission_stress_test(...)` | Function | Subtracts extra commission per lot. | trades/config → copied trades | None | Conversion errors | Assessment/reports/tests. | Direct | Test-only/internal | Useful |
| `run_randomize_trade_order_mc(...)` | Function | Wrapper around shuffled trade MC. | trades/config → paths | Local state mutation (RNG) | None | No caller found outside package exports. | None | Unused | Questionable |
| `run_resample_trades_mc(...)` | Function | Wrapper around resampled trade MC. | trades/config → paths | Local state mutation (RNG) | None | Assessment/combined MC. | Indirect | Used internally | Essential |
| `run_skip_trades_mc(...)` | Function | Randomly removes winning trades before equity accumulation. | trades/config → paths | Local state mutation (RNG) | None | Assessment/MC. | Indirect | Used internally | Useful |
| `run_randomize_parameters_mc(...)` | Function | Perturbs numeric parameters then backtests each variant. | strategy/config → scores | Cross-domain call | Swallows all failures into score 0 | No caller found. | None | Unused; real mode broken | Questionable |
| `run_randomize_history_mc(...)` | Function | Fixed-block bootstrap wrapper. | trades/config → paths | Local state mutation (RNG) | None | No external caller found. | None | Used only as internal utility surface | Useful |
| `run_combined_monte_carlo(...)` | Function | Alias-like wrapper to resampled MC. | trades/config → paths | Local state mutation (RNG) | None | No external caller found. | None | Used only through static call relation | Questionable |
| `run_cross_market_test(...)` | Function | Backtests same parameters symbol by symbol. | strategy/config → scores | Cross-domain call | Swallows failures to 0 | No caller found. | None | Unused; real mode broken | Questionable |
| `run_cross_timeframe_test(...)` | Function | Backtests same parameters across timeframes. | strategy/config → scores | Cross-domain call | Swallows failures to 0 | No caller found. | None | Unused; real mode broken | Questionable |
| `run_second_oos_test(...)` | Function | Backtests secondary OOS slice. | strategy/config → float | Cross-domain call | Swallows failures to 0 | `run_third_oos_test`. | None | Used only by another unused function | Questionable |
| `run_third_oos_test(...)` | Function | Alias-like call to second OOS test. | strategy/config → float | Cross-domain call | Delegated | No caller found. | None | Unused | Questionable |
| `assess_strategy_robustness(...)` | Function | Runs slippage, commission, skip-trade, and ruin checks. | trades/config → `RobustnessResponse` | Local state mutation (RNG) | Metric/data errors | Report/tests. | Direct | Test-only/internal | Essential |
| `build_monte_carlo_result(...)` | Function | Aggregates paths into drawdowns, breach/target probabilities, streaks. | paths/config → `MonteCarloResult` | None | None | `optimization_monte_carlo`. | Indirect | Used internally | Essential |
| `optimization_monte_carlo(...)` | Function | Dispatches MC method and returns response with percentiles. | trades/config → `MonteCarloResponse` | Local state mutation (RNG) | Metric/data errors | Comparison/report/tests/examples. | Direct | Test-only/internal | Essential |
| `robustness_simulation(...)` | Function | Deteriorates profits, drops winners, then resamples. | trades/config → paths | Local state mutation (RNG) | None | No caller found. | None | Unused | Questionable |
| `compare_simulation_methods(...)` | Function | Compares ruin probability for shuffle vs resample. | trades/config → dict | Local state mutation (RNG) | Metric errors | Unit test only. | Direct | Test-only | Useful |
| `run_monte_carlo_task(...)` | Function | Generates task ID and logs; schedules nothing. | inputs → str | None (logging only) | Logger errors | No caller found. | None | Unused | No demonstrated value |
| `build_robustness_report(...)` | Function | Combines assessment, three MC methods, and stress profits. | trades/config → dict | Local state mutation (RNG) | Metric/data errors | No caller found. | None | Unused | Useful |

### `sweeps.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `calculate_parameter_stability(candidates)` | Function | Sample standard deviation per numeric parameter. | candidates → dict | None | Conversion errors | Unit test only. | Direct | Test-only | Useful |
| `detect_overfit_parameters(IS, OOS)` | Function | Flags score gap above 0.5. | two floats → dict | None | None | Tests/examples. | Direct | Test-only | Useful |
| `rank_parameter_sets(candidates, objective='score')` | Function | Sorts and mutates candidate dicts by adding rank. | list/objective → list | Local state mutation (input dicts) | Conversion errors | No caller found. | None | Unused | Questionable |
| `compare_optimization_runs(run_ids, payloads)` | Function | Summarizes best score/count/objective by run ID. | parallel lists → dict | None | ValueError via strict zip on mismatch | Usage example only. | Direct | Test-only | Useful |
| `walk_forward(...)` | Function | Sequential fold evaluation using grid or random search. | request/config → `WalkForwardResponse` | Optional cross-domain call | Algorithm/date errors | `optimization_walk_forward`. | Indirect | Used internally; real mode broken | Essential |
| `parallel_walk_forward(...)` | Function | Threaded fold-level walk-forward. | request/config → response | Local state mutation (threads); optional cross-domain call | Worker errors propagate | No caller found. | None | Unused; real mode broken | Questionable |
| `print_optimization_report(summary)` | Function | Formats top five candidates as Markdown. | summary → str | None | Formatting errors | `build_optimization_report`. | No direct | Used internally | Useful |
| `run_parameter_sweep(payload)` | Function | Validates request, dispatches search method, maps result into standard envelope. | dict → `StandardResponse` | Optional cross-domain call | Returns failed envelope on validation/execution errors | Unit test; README example. | Direct dry-run | Test-only | Essential |
| `optimization_walk_forward(...)` | Function | Dict wrapper around `walk_forward`. | fields → dict | Delegated | Catches all and returns error dict | No caller found. | None | Unused | Questionable |
| `run_optimization_task(payload)` | Function | Generates ID and logs; does not enqueue work. | dict → str | None (logging only) | Logger errors | No caller found. | None | Unused | No demonstrated value |
| `run_walk_forward_task(payload)` | Function | Generates ID and logs; does not enqueue work. | dict → str | None (logging only) | Logger errors | No caller found. | None | Unused | No demonstrated value |
| `analyze_walk_forward_results(res)` | Function | Returns WFA evidence unchanged. | response → dict | None | None | No caller found. | None | Unused | Questionable |
| `analyze_parallel_results(results)` | Function | Returns count and current timestamp only. | list → dict | Read-only | None | No caller found. | None | Unused | No demonstrated value |
| `save_optimization_result(result)` | Function | Returns `{saved: true}` envelope without writing. | dict → dict | None | None | No caller found. | None | Unused | No demonstrated value |
| `build_optimization_report(summary)` | Function | Wraps Markdown report in a dict. | summary → dict | None | Formatting errors | No external caller found. | None | Used only through static call relation | Questionable |

### `persistence/checkpoint.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OPT_ATOMIC_WRITE_FAILED` | Constant | Atomic save failure code. | str | None | None | `save_checkpoint`. | Indirect | Used internally | Supporting |
| `OPT_CHECKPOINT_CORRUPTED` | Constant | Load/schema failure code. | str | None | None | `load_checkpoint`. | Indirect | Used internally | Supporting |
| `OPT_INTRADAY_RULE_DATA_UNAVAILABLE` | Constant | Declared rule-data code. | str | None | None | No caller found. | None | Unused | No demonstrated value |
| `OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED` | Constant | Declared prop-firm evaluation code. | str | None | None | No caller found. | None | Unused | No demonstrated value |
| `OPT_TRIAL_COUNT_METHOD_UNSUPPORTED` | Constant | Declared trial-method code. | str | None | None | No caller found. | None | Unused | No demonstrated value |
| `OPT_PRUNED_BY_HARD_GATE` | Constant | Declared pruning code. | str | None | None | No caller found. | None | Unused | No demonstrated value |
| `OPT_PBO_THRESHOLD_FAILED` | Constant | Declared overfitting threshold code. | str | None | None | No caller found. | None | Unused | No demonstrated value |
| `OPT_NOISY_OBJECTIVE_NOT_ALLOWED` | Constant | Declared deterministic-objective code. | str | None | None | Root export; helper uses same literal but not this constant. | None | Unused | Questionable |
| `STOCHASTIC_REALISM_CONFLICT` | Constant | Declared realism conflict code. | str | None | None | No caller found. | None | Unused | No demonstrated value |
| `validate_safe_path(target_path, base_dir=None)` | Function | Resolves path and rejects traversal outside root. | paths → absolute str | Read-only | `OptimizationExecutionError` | Save/load checkpoint. | Traversal test | Used internally | Essential |
| `save_checkpoint(file_path, data, run_id, base_dir=None)` | Function | Atomic temp-file JSON write and replace. | path/data → None | Persistence write | `OptimizationExecutionError` | Tests/examples only. | Direct | Test-only | Useful |
| `validate_checkpoint_schema(data)` | Function | Requires dict with `run_id`. | object → None | None | TypeError/ValueError | `load_checkpoint`. | Indirect | Used internally | Supporting |
| `load_checkpoint(file_path, base_dir=None)` | Function | Reads JSON and validates schema. | path → dict | Read-only | `OptimizationExecutionError` | Fallback/tests/examples. | Direct | Test-only/internal | Useful |
| `load_checkpoint_with_fallback(file_path, fallback_paths, base_dir=None)` | Function | Returns first loadable checkpoint or `None`. | paths → dict\|None | Read-only | Suppresses optimization errors | No caller found. | None | Unused | Useful |

### `persistence/repository.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `R` | TypeVar | Generic return type for retry helper. | type variable | None | None | `retry_with_backoff` annotation. | None | Used internally | Supporting |
| `OptimizationRunRecord` | Model | Stored optimization run state. | fields → model | None | Pydantic errors | Repository/tests/examples. | Direct | Test-only/internal | Essential |
| `OptimizationRepository` | ABC | Persistence port with save/load/progress methods. | interface | None | Implementation-defined | In-memory adapter and wrapper functions. | Indirect | Used internally | Essential |
| `OptimizationRepository.save_run/load_run/update_progress` | Abstract methods | Repository contract. | calls → None/record | Persistence write/read | Implementation-defined | Wrapper functions. | Indirect | Used internally | Supporting |
| `InMemoryOptimizationRepository` | Class | Thread-safe process-local run store. | constructor → repo | Local state mutation | `OptimizationExecutionError` on missing load | Tests/examples. | Direct | Test-only | Useful |
| `InMemoryOptimizationRepository.save_run()` | Method | Deep-copies record into map. | run/record → None | Local state mutation | None | Save wrapper/tests. | Indirect | Used internally | Supporting |
| `InMemoryOptimizationRepository.load_run()` | Method | Returns deep copy. | run → record | Read-only | `OptimizationExecutionError` | Load wrapper/tests. | Indirect | Used internally | Supporting |
| `InMemoryOptimizationRepository.update_progress()` | Method | Mutates existing record; silently no-ops if absent. | run/progress/status → None | Local state mutation | None | Update wrapper/tests. | Indirect | Used internally | Supporting |
| `ProgressTracker(total)` | Class | Thread-safe completed/total counter. | total → tracker | Local state mutation | None | Unit test only. | Direct | Test-only | Useful |
| `ProgressTracker.increment()` | Method | Increments completed. | None → None | Local state mutation | None | Unit test. | Direct | Test-only | Supporting |
| `ProgressTracker.get_progress()` | Method | Returns percentage; 100 for nonpositive total. | None → float | Read-only | None | Unit test. | Direct | Test-only | Supporting |
| `retry_with_backoff(action, ..., attempts=3, initial_delay=.1)` | Function | Retries every exception with exponential sleep. | callable → result | Local state mutation (sleep/time) | Re-raises final exception | Repository wrappers. | Indirect | Used internally | Supporting |
| `save_optimization_run(repo, run_id, record)` | Function | Retrying repository save. | repo/record → None | Persistence write or local mutation | Repository errors | Tests/examples. | Direct | Test-only | Useful |
| `load_optimization_run(repo, run_id)` | Function | Retrying repository load. | repo/run → record | Read-only | Repository errors | Tests/examples. | Direct | Test-only | Useful |
| `update_optimization_progress(repo, run_id, progress, status)` | Function | Retrying progress update. | repo/fields → None | Persistence write or local mutation | Repository errors | Unit test. | Direct | Test-only | Useful |

### `algorithms/__init__.py` and `persistence/__init__.py`

| File | Public surface | Evidence | Usage status | Value status |
| --- | --- | --- | --- | --- |
| `algorithms/__init__.py` | 15 re-exports from four algorithm files. | Imported by root facade. | Possibly used | Supporting |
| `persistence/__init__.py` | 20 re-exports from checkpoint/repository. | Imported by root facade. | Possibly used | Supporting |

## 6. Actual Workflows

### `V1-WF-OPT-001` — Dry-run parameter sweep

* **Scope:** Internal
* **Trigger:** Call `run_parameter_sweep(payload)` from test/example or another Python caller.
* **Input boundary:** `OptimizationRequest` payload.
* **Functions and methods used:** `run_parameter_sweep` → grid/random/Bayesian/genetic search → constraints → hash → `evaluate_candidate_score([])` → `select_best_candidate` → `OptimizationResponse` → `optimization_tool_result`.
* **Files involved:** `sweeps.py`; `models.py`; selected algorithm; `helpers.py`; `scoring.py`.
* **External dependencies:** NumPy, Pydantic, `app.utils.standard`.
* **Output boundary:** Standard response envelope.
* **Failure behaviour:** Validation becomes failed envelope; algorithm exceptions become failed envelope.
* **Operational status:** **Working mechanically, but not a meaningful optimization because dry-run candidates are scored from empty trades.**
* **Evidence:** `tests/optimization/unit/test_optimization.py::test_run_parameter_sweep_facade`; `tests/optimization/usage/09_optimization.py::example_02_grid_and_random_search`; `sweeps.run_parameter_sweep`.

```text
`run_parameter_sweep`
→ grid/random/Bayesian/genetic search
→ constraints
→ hash
→ `evaluate_candidate_score([])`
→ `select_best_candidate`
→ `OptimizationResponse`
→ `optimization_tool_result`.
```

### `V1-WF-OPT-002` — Simulator-backed candidate search

* **Scope:** Cross-domain
* **Trigger:** Any grid/random/genetic/Bayesian call with `dry_run=False`.
* **Input boundary:** Strategy reference, symbols, dates, parameter space.
* **Functions and methods used:** Search algorithm → `helpers.run_strategy_backtest` → simulator engine/orchestrator → deal pairing → scoring → summary.
* **Files involved:** `algorithms/*.py`; `helpers.py`; `scoring.py`.
* **External dependencies:** `app.services.simulator.engine.EventDrivenExecutionEngine`; missing `app.services.simulator.orchestrator.BacktestOrchestrator`.
* **Output boundary:** `OptimizationSummary` with real candidate metrics.
* **Failure behaviour:** Missing module prevents execution; per-candidate code may log/skip, yielding empty sentinel results.
* **Operational status:** **Broken.**
* **Evidence:** `helpers.run_strategy_backtest` imports missing orchestrator; unit test lines 16–17 and fixture inject mock module.

```text
Search algorithm
→ `helpers.run_strategy_backtest`
→ simulator engine/orchestrator
→ deal pairing
→ scoring
→ summary.
```

### `V1-WF-OPT-003` — Dynamic strategy-file optimization

* **Scope:** Cross-domain
* **Trigger:** Call `run_strategy_backtest_from_path`.
* **Input boundary:** Python file path, class name, market inputs, parameters.
* **Functions and methods used:** `load_strategy_from_path` → set class identity → missing registry `register_strategy` → `run_strategy_backtest`.
* **Files involved:** `helpers.py`.
* **External dependencies:** Filesystem; missing `app.services.strategies.registry`; simulator.
* **Output boundary:** `EngineOptimizationResult`.
* **Failure behaviour:** Missing registry import before simulator execution.
* **Operational status:** **Broken on clean checkout; passes only with unit-test mocks.**
* **Evidence:** `helpers.run_strategy_backtest_from_path`; `test_run_strategy_backtest_from_path` fixture injects plural registry.

```text
`load_strategy_from_path`
→ set class identity
→ missing registry `register_strategy`
→ `run_strategy_backtest`.
```

### `V1-WF-OPT-004` — Walk-forward analysis

* **Scope:** Internal / Cross-domain
* **Trigger:** Call `walk_forward`, `parallel_walk_forward`, `optimization_walk_forward`, or the alternate splitting facade.
* **Input boundary:** Strategy/data range, folds, search space.
* **Functions and methods used:** Split windows → optimize each train window → evaluate selected parameters on test window → aggregate WFE/retention/drift.
* **Files involved:** `sweeps.py` and separately `splitting.py`; algorithms/helpers/scoring/models.
* **External dependencies:** ThreadPoolExecutor in parallel mode; simulator in real mode.
* **Output boundary:** `WalkForwardResponse` or dict response.
* **Failure behaviour:** Dry-run produces zero train/OOS scores; real mode hits missing orchestrator; one implementation embeds fold errors while the other may replace failures with zero.
* **Operational status:** **Partial.**
* **Evidence:** `sweeps.walk_forward`; `splitting.run_walk_forward_optimization`; split tests only, no end-to-end real WFA test.

```text
Split windows
→ optimize each train window
→ evaluate selected parameters on test window
→ aggregate WFE/retention/drift.
```

### `V1-WF-OPT-005` — Trade-sequence Monte Carlo and robustness

* **Scope:** Internal
* **Trigger:** Supply realized trade dictionaries to MC/robustness functions.
* **Input boundary:** Trades, balance, method/count/seed.
* **Functions and methods used:** Shuffle/resample/skip/bootstrap paths → drawdown/streak/ruin/target aggregation → optional stress checks/report.
* **Files involved:** `algorithms/random.py`; `robustness.py`; `models.py`.
* **External dependencies:** NumPy; local RNG.
* **Output boundary:** `MonteCarloResponse`, `RobustnessResponse`, or report dict.
* **Failure behaviour:** Malformed trade values can raise; several wrappers do not validate method/ranges.
* **Operational status:** **Working for supplied in-memory trades.**
* **Evidence:** `test_monte_carlo_simulations`; `test_strategy_robustness_assessment`; usage example 06.

```text
Shuffle/resample/skip/bootstrap paths
→ drawdown/streak/ruin/target aggregation
→ optional stress checks/report.
```

### `V1-WF-OPT-006` — Score, rank, and anti-overfitting analysis

* **Scope:** Internal
* **Trigger:** Supply closed-trade dictionaries or candidate dictionaries.
* **Input boundary:** Trades, balance, objective, trial count.
* **Functions and methods used:** Daily aggregation → score metrics → DSR/MTB → ranking/Pareto selection.
* **Files involved:** `scoring.py`.
* **External dependencies:** NumPy; optional SciPy for inverse normal.
* **Output boundary:** Scalar score or metric/ranking dicts.
* **Failure behaviour:** Invalid balances/timestamps/types can distort or fail; malformed date strings are replaced with current UTC date.
* **Operational status:** **Working with valid supplied data.**
* **Evidence:** `test_scoring_functions`; `test_evaluate_candidate_score`; `test_rank_candidates_tie_breaker`; `test_pareto_select`.

```text
Daily aggregation
→ score metrics
→ DSR/MTB
→ ranking/Pareto selection.
```

### `V1-WF-OPT-007` — Checkpoint save/load

* **Scope:** Internal
* **Trigger:** Explicit calls to checkpoint functions.
* **Input boundary:** Path, run-state dict containing `run_id`.
* **Functions and methods used:** Safe-path validation → temp JSON write/fsync/replace → later JSON read/schema validation → optional fallback.
* **Files involved:** `persistence/checkpoint.py`.
* **External dependencies:** Local filesystem.
* **Output boundary:** Persisted/loaded dict.
* **Failure behaviour:** Traversal, missing file, malformed JSON, or missing `run_id` become `OptimizationExecutionError`.
* **Operational status:** **Working in tests/examples; not connected to sweep orchestration.**
* **Evidence:** `test_checkpoint_atomic_saves_and_loads`; usage example 07.

```text
Safe-path validation
→ temp JSON write/fsync/replace
→ later JSON read/schema validation
→ optional fallback.
```

### `V1-WF-OPT-008` — In-memory run repository and progress

* **Scope:** Internal
* **Trigger:** Explicit repository wrapper calls.
* **Input boundary:** `OptimizationRunRecord`, run ID, progress/status.
* **Functions and methods used:** Retry wrapper → thread-safe save/load/update.
* **Files involved:** `persistence/repository.py`.
* **External dependencies:** Threading/time.
* **Output boundary:** Stored record or updated process-local state.
* **Failure behaviour:** Missing load raises; missing update silently no-ops; retry catches all exceptions.
* **Operational status:** **Working in tests/examples; not connected to sweeps.**
* **Evidence:** `test_optimization_repository`; `test_progress_tracker`; usage example 07.

```text
Retry wrapper
→ thread-safe save/load/update.
```

### `V1-WF-OPT-009` — Background task registration

* **Scope:** Internal
* **Trigger:** Call `run_optimization_task`, `run_walk_forward_task`, or `run_monte_carlo_task`.
* **Input boundary:** Payload or MC inputs.
* **Functions and methods used:** Generate UUID-derived string → log → return ID.
* **Files involved:** `sweeps.py`; `robustness.py`.
* **External dependencies:** Logger only.
* **Output boundary:** Task ID string.
* **Failure behaviour:** No scheduling, storage, worker, status lookup, or execution occurs.
* **Operational status:** **Partial/misnamed.**
* **Evidence:** Direct function bodies; no caller or scheduler registration found.

```text
Generate UUID-derived string
→ log
→ return ID.
```

## 7. Usage and Caller Map

| Public symbol/group | Called from | Call type | Runtime or test | Evidence |
| --- | --- | --- | --- | --- |
| Root facade exports | `tests/optimization/unit/test_optimization.py`; `tests/optimization/usage/09_optimization.py` | Direct import | Test/example | No production initializer imports optimization. |
| `run_parameter_sweep` | README example; unit facade test | Direct call | Test/example | No production route/tool/scheduler caller confirmed. |
| `grid_search`, `parallel_grid_search` | Sweeps/WFA wrappers; tests/examples | Direct/internal | Internal + test | Real-mode branch delegates to broken backtest adapter. |
| `random_search`, `parallel_random_search` | Bayesian wrapper; sweeps; WFA; tests/examples | Direct/internal | Internal + test | No production external trigger confirmed. |
| `bayesian_optimization` | `sweeps.run_parameter_sweep`; tests/examples | Internal/direct | Internal + test | Implementation delegates to random search. |
| `genetic_algorithm` | `sweeps.run_parameter_sweep`; tests/examples | Internal/direct | Internal + test | No production external trigger confirmed. |
| `optimization_grid_search`, `optimization_random_search`, `optimization_bayesian`, `optimization_genetic` | No caller found | None | None | Medium-confidence unused. |
| `run_strategy_backtest` | Search algorithms, WFA, robustness cross-tests, mocked unit test | Internal | Internal + test | Cross-domain target unresolved. |
| `run_strategy_backtest_from_path` | Unit test only | Direct | Test | Registry and orchestrator mocked. |
| Hash/constraint helpers | Search algorithms and tests | Internal | Internal + test | `check_constraints`, `get_active_parameters`, `build_candidate_hash`, `select_best_candidate`. |
| Scoring functions | Candidate evaluator, resolver, robustness, tests | Internal/direct | Internal + test | No caller outside optimization/tests confirmed. |
| Split generators | `WalkForwardSplit`, helper wrappers, tests/examples | Internal/direct | Internal + test | No runtime scheduling/API integration found. |
| Walk-forward facades | Each other only in limited cases; no external caller | Internal/none | Internal | Two overlapping implementations. |
| Monte Carlo primitives | Robustness wrappers, tests/examples | Internal/direct | Internal + test | Working on supplied trades. |
| Robustness cross-market/timeframe/OOS functions | No caller, except third OOS delegates to second | None/internal | None | Real mode also depends on broken adapter. |
| Checkpoint functions | Unit test and usage example | Direct | Test/example | Not called by sweeps. |
| Repository functions/classes | Unit test and usage example | Direct | Test/example | Not called by sweeps. |
| Task functions | No caller or registration found | None | None | Only log and return IDs. |
| Unused scenario models | No constructors/producers/consumers found | None | None | Unsupervised, position sizing, consecutive-loss, profit-target, multi-entry, portfolio models. |
| Dynamic registrations/decorators/config strings | Only explicit dynamic imports in helpers; no decorators/registry configuration in package | Dynamic import | Internal/test | Known dynamic targets checked and absent. |

### Caller-status conclusion

No symbol has a confirmed caller from a production API route, agent tool, scheduled task, CLI entry point, or another service domain. Static call relations inside the package are real, but the only confirmed external triggers are tests, examples, and the README snippet. Because repository code search was unavailable, production non-usage remains Medium confidence rather than High confidence.

## 8. Cross-Domain Surface

**Outbound (this domain depends on):**

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --- | --- | --- | --- |
| `app.utils.standard` | `StandardResponse`, `canonical_json`, `build_metadata`, `success_response`, `error_response`, sensitive-key pattern | `helpers.py`, `models.py` | Current imports resolve in inspected code. |
| `app.utils.logger` | Shared logger | Algorithms, errors, robustness, sweeps | Logging only. |
| `app.utils.security` | `redact_text` | `errors.to_optimization_error_payload` | Helper has no caller. |
| `app.services.simulator.engine` | `EventDrivenExecutionEngine` | `helpers.run_strategy_backtest` | File exists. |
| `app.services.simulator.orchestrator` | `BacktestOrchestrator` | `helpers.run_strategy_backtest` | Path absent; non-dry-run blocked. |
| `app.services.strategies.registry` | `register_strategy` | `helpers.run_strategy_backtest_from_path` | Plural package path absent. |
| Strategy domain | Registered strategy reference expected by simulator | All search methods conceptually | No working registration boundary found in optimization. |
| Pydantic | Models and validation | Most files | Required third-party. |
| NumPy | Scores, percentiles, stability/drift | `scoring.py`, `robustness.py`, `sweeps.py` | Required third-party. |
| Pandas | Optional DataFrame conversion | `OptimizationSummary.to_dataframe` | Deferred import; no caller. |
| SciPy | QMC availability probe and optional normal inverse CDF | `random.py`, `scoring.py` | QMC sampler is probed but not used. |
| Optuna / scikit-optimize | Availability probe | `bayesian.py` | Backend is probed but not used for Bayesian proposals. |
| Filesystem | Strategy loading and checkpoints | `helpers.py`, `checkpoint.py` | Local read/write. |

**Inbound (others depend on this domain):**

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| --- | --- | --- | --- |
| `tests/optimization/unit` | Broad root facade; checkpoint and repository modules | Unit verification | Confirmed direct imports/calls. |
| `tests/optimization/usage` | Search, splitting, robustness, persistence helpers | Executable examples | Confirmed direct imports/calls; all searches use `dry_run=True`. |
| `app/services/optimization/README.md` | `ParameterRange`, `ParameterSpace`, `run_parameter_sweep` | Documentation example | Dry-run only. |
| Production packages | None confirmed | — | No production caller was added in package-introduction commit; root/service initializers do not register optimization; code search unavailable. |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| --- | --- | --- | --- | --- |
| `splitting.run_walk_forward_optimization` | `sweeps.walk_forward` / `optimization_walk_forward` | Both split, optimize train folds, and evaluate OOS; they use different algorithms, response shapes, and failure handling. | Direct function bodies. | Competing behaviour and inconsistent outputs. |
| `algorithms.random.monte_carlo_analysis` | `robustness.optimization_monte_carlo` and wrappers | Core MC engine plus many thin aliases/wrappers. | Call graph in both files. | Large public surface and method ambiguity. |
| `helpers.parametric_simulation` | `algorithms.random.random_win_rate_simulation` | Both generate binary win/loss compounding paths. | Signatures and loops. | Different fixed/configurable risk and return shapes. |
| `scoring.rank_candidates` | `sweeps.rank_parameter_sets` | Both sort candidate dicts by performance. | Function bodies. | Different tie-breaking and mutation semantics. |
| `print_optimization_report` | `build_optimization_report` | Second only wraps first in a dict. | Direct call. | Wrapper adds little value. |
| `save_optimization_result` | Checkpoint/repository save functions | Name implies persistence but returns metadata only. | Function body. | Misleading save semantics. |
| `OptimizationRunDetails` | `OptimizationRunRecord` | Two run-state models with overlapping fields but different purposes/locations. | `models.py`, `repository.py`. | Contract duplication and conversion burden. |
| Error taxonomy in `errors.py` | Checkpoint/helper literal codes | Approved set does not contain many emitted codes. | Constants and raised codes. | Boundary codes are not deterministic in practice. |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| --- | --- | --- | --- | --- |
| Unsupervised models | Three public models but no clustering/PCA implementation or caller. | Root export review; package/tests/examples search. | Medium | `models.Unsupervised*`. |
| Position-sizing models | Request/result models have no producer/consumer. | Package/test/example imports and call graph. | Medium | `models.PositionSizing*`. |
| Consecutive-loss models | Four models but no corresponding simulation facade. | Package/test/example inspection. | Medium | `models.ConsecutiveLosing*`. |
| Profit-target models | Four models but no producer/consumer. | Package/test/example inspection. | Medium | `models.ProfitTarget*`. |
| Multi-entry models | Three models but no simulation implementation. | Package/test/example inspection. | Medium | `models.MultiEntry*`. |
| Portfolio optimizer model | No portfolio optimizer implementation. | Package/test/example inspection. | Medium | `PortfolioOptimizerResult`. |
| Random win-rate models/functions | Six models plus `random_win_rate_simulation` are not exported or called. | Module/root export and caller inspection. | Medium | `algorithms/random.py`. |
| Dict wrappers for four optimizers | No callers; duplicate underlying algorithms and inconsistent envelopes. | Package/tests/examples inspection. | Medium | `optimization_*` wrappers. |
| Error payload mapper and code/message tables | No caller; approved set is not enforced. | Package/tests/examples inspection. | Medium | `errors.py`. |
| Tool context/business/package helpers | No tool invokes them. | Package/tests/examples inspection. | Medium | `helpers.optimization_tool_context`, `optimization_business_payload`, `package_optimization_request`. |
| Checkpoint fallback | No caller. | Package/tests/examples inspection. | Medium | `load_checkpoint_with_fallback`. |
| Cross-market/timeframe/OOS robustness calls | No caller; adapter is broken. | Package/tests/examples inspection. | Medium | `run_cross_*`, `run_*_oos_test`. |
| Task functions | No scheduler or registry caller; only return generated IDs. | Package-introduction files and current source. | Medium | `run_optimization_task`, `run_walk_forward_task`, `run_monte_carlo_task`. |
| Analysis/save/report convenience wrappers | No external callers and minimal behaviour. | Package/tests/examples inspection. | Medium | `analyze_*`, `save_optimization_result`, `build_optimization_report`. |
| Public `R` TypeVar | Implementation annotation accidentally public by naming. | Repository source/root export check. | High | Not exported; only annotation use. |

> None of the Medium-confidence rows is labelled dead code because repository-wide indexed code search was unavailable.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --- | --- | --- | --- |
| Real candidate optimization | Missing simulator orchestrator module. | All `dry_run=False` search paths fail or skip candidates. | `helpers.run_strategy_backtest`. |
| Dynamic strategy-file execution | Missing plural strategy registry and simulator orchestrator. | Cannot register or execute loaded class on clean checkout. | `helpers.run_strategy_backtest_from_path`. |
| Bayesian optimization | No Bayesian proposal/update loop; always random search. | Method name and metadata overstate implementation. | `bayesian.bayesian_optimization`. |
| Sobol/LHS search | Only dependency check and label; no QMC sample generation. | Requested sampler is still pseudo-random when SciPy exists. | `random.random_search` uses `sample_parameter` regardless. |
| Dry-run optimization | Empty trade list gives every candidate the same objective score. | Best candidate is effectively first/generated order, not performance-selected. | All algorithm dry-run branches. |
| Walk-forward validation | Dry-run train and test scores are zero; real mode broken. | Cannot provide meaningful WFE evidence in confirmed operating mode. | `sweeps._evaluate_single_fold`; `splitting.run_walk_forward_optimization`. |
| Persistence/resume | Checkpoint and repository are never invoked by sweeps. | No automatic save, resume, progress update, or checkpoint recovery. | No imports from persistence in `sweeps.py`/algorithms. |
| Background execution | Task functions do not enqueue or execute jobs. | Returned task IDs have no lifecycle. | Task function bodies. |
| Saved-result workflow | `save_optimization_result` performs no write. | Downstream caller could believe data was persisted. | Function body. |
| Scenario capability models | Many request/result schemas have no implementation. | Public API advertises absent capabilities. | `models.py` vs all functional files. |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| --- | --- | --- | --- | --- |
| `V1-ISSUE-OPT-001` | Missing simulator orchestrator import | `helpers.run_strategy_backtest` | Breaks every real candidate evaluation. | `app/services/simulator/orchestrator.py` absent; tests inject mock. |
| `V1-ISSUE-OPT-002` | Missing/misnamed strategy registry import | `helpers.run_strategy_backtest_from_path` | Breaks dynamic strategy workflow. | `app.services.strategies.registry` absent; tests inject mock. |
| `V1-ISSUE-OPT-003` | Tests conceal missing runtime dependencies | `tests/optimization/unit/test_optimization.py` | Green mocked tests would overstate clean-checkout operability. | Fixture comments and `sys.modules` injection. |
| `V1-ISSUE-OPT-004` | Bayesian implementation is random search under both fallback and available-backend branches | `algorithms/bayesian.py` | Misleading algorithm capability and evidence. | Both branches call `random_search`. |
| `V1-ISSUE-OPT-005` | Sobol/LHS methods are never used to generate candidates | `algorithms/random.py::random_search` | Sampler label/metadata is inaccurate. | SciPy is only imported; `sample_parameter` remains pseudo-random. |
| `V1-ISSUE-OPT-006` | Dry-run candidates all score empty trades | All four algorithms | Dry-run cannot identify better parameters. | Calls `evaluate_candidate_score([], ...)`. |
| `V1-ISSUE-OPT-007` | Duplicate walk-forward implementations | `splitting.py`, `sweeps.py` | Divergent algorithm selection, response types, and error handling. | Two independent call graphs. |
| `V1-ISSUE-OPT-008` | Persistence is isolated from optimization execution | `persistence/*` vs `sweeps.py`/algorithms | No resume/checkpoint/progress workflow. | No call path between them. |
| `V1-ISSUE-OPT-009` | Background-task functions are stubs | `sweeps.py`, `robustness.py` | IDs imply queued work that does not exist. | Only UUID + logger + return. |
| `V1-ISSUE-OPT-010` | Over-broad eager public facade | `optimization/__init__.py` | 151 exports increase coupling and make accidental helpers/models public. | Root `__all__`. |
| `V1-ISSUE-OPT-011` | Large unused contract surface | `models.py` | Public capabilities appear implemented when only schemas exist. | Unsupervised, sizing, streak, target, multi-entry, portfolio models. |
| `V1-ISSUE-OPT-012` | Inconsistent response/error contracts | Algorithm wrappers, sweeps, native functions | Callers receive models, dicts, or `StandardResponse`; some raise, some swallow. | Return/except bodies. |
| `V1-ISSUE-OPT-013` | Error-code registry does not match emitted codes | `errors.py`, helpers, persistence | Boundary mapping is not deterministic or constrained. | Actual codes include `OPT_*`, `PERMISSION_DENIED`, `DATA_NOT_FOUND` outside approved set. |
| `V1-ISSUE-OPT-014` | Parallel grid pending queue is not strictly bounded | `parallel_grid_search` | If no future is complete at threshold, pending continues growing despite bounded-memory claim. | Only completed futures are drained. |
| `V1-ISSUE-OPT-015` | Trial-count handling is inconsistent | Grid/random/parallel branches | DSR/MTB results are not comparable across algorithms. | Grid dry-run passes 1; sequential random passes running count; parallel random passes total count. |
| `V1-ISSUE-OPT-016` | Correlated-search warning is disconnected | `evaluate_candidate_score`, `trial_count_independence_warning` | Evaluator always uses default `search_method='grid'`, so Bayesian/genetic warnings are never emitted. | No search method forwarded. |
| `V1-ISSUE-OPT-017` | Broad exception swallowing converts integration failures to zero scores | Robustness cross-tests and WFA | Missing dependencies can look like poor strategy performance rather than system failure. | `except Exception: return 0.0` / empty-score fallback. |
| `V1-ISSUE-OPT-018` | Hard-coded adapter/version/default request identity | `helpers.run_strategy_backtest` | Tight coupling and misleading trace IDs. | Requires `adapter_version == '0.8.0'`; defaults to `opt_req_123`. |
| `V1-ISSUE-OPT-019` | Misleading save function | `sweeps.save_optimization_result` | Returns `saved=True` without persistence. | Function body. |
| `V1-ISSUE-OPT-020` | README overstates implementation and contains local absolute link | `README.md` | Documentation suggests high-performance operational engine and nonportable file URL. | README lines 5 and 65. |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `V1-CAP-OPT-001` | Parameter range/space validation | `ParameterRange`, `ParameterSpace`, AST constraints | WF-001 | Test-only/internal | Essential | Working with valid schemas. |
| `V1-CAP-OPT-002` | Canonical parameter/candidate hashing | `parameter_space_hash`, `get_active_parameters`, `build_candidate_hash` | WF-001 | Test-only/internal | Essential | Deterministic and conditional-aware. |
| `V1-CAP-OPT-003` | Exhaustive grid search | `grid_search`, `parallel_grid_search` | WF-001/WF-002 | Test-only; real mode broken | Essential | Dry-run only confirmed. |
| `V1-CAP-OPT-004` | Pseudo-random search | `random_search`, `parallel_random_search` | WF-001/WF-002 | Test-only; real mode broken | Essential | Sobol/LHS not actually implemented. |
| `V1-CAP-OPT-005` | Genetic search | `genetic_algorithm`, `crossover`, `mutate` | WF-001/WF-002 | Test-only; real mode broken | Useful | Evolution loop exists. |
| `V1-CAP-OPT-006` | Bayesian-labelled search | `bayesian_optimization` | WF-001/WF-002 | Test-only | Questionable | Always random search. |
| `V1-CAP-OPT-007` | Simulator candidate adapter | `run_strategy_backtest`, `EngineOptimizationResult` | WF-002 | Broken | Essential | Missing orchestrator. |
| `V1-CAP-OPT-008` | Dynamic strategy loading | `load_strategy_from_path`, `run_strategy_backtest_from_path` | WF-003 | Broken | Questionable | Missing registry and orchestrator. |
| `V1-CAP-OPT-009` | Performance scoring and DSR/MTB | `scoring.py` | WF-006 | Test-only/internal | Essential | Works on supplied trades; trial handling inconsistent. |
| `V1-CAP-OPT-010` | Chronological/rolling/expanding splits | `splitting.py` split functions | WF-004 | Test-only/internal | Essential | Mechanically working. |
| `V1-CAP-OPT-011` | Walk-forward optimization | Two implementations in `splitting.py` and `sweeps.py` | WF-004 | Partial | Questionable | Dry-run noninformative; real mode broken. |
| `V1-CAP-OPT-012` | Trade-sequence Monte Carlo | `monte_carlo_analysis`, `optimization_monte_carlo` | WF-005 | Test-only/internal | Essential | Works from supplied trade lists. |
| `V1-CAP-OPT-013` | Robustness stress assessment | Stress transforms and `assess_strategy_robustness` | WF-005 | Test-only/internal | Useful | No production caller. |
| `V1-CAP-OPT-014` | Atomic JSON checkpoints | `save_checkpoint`, `load_checkpoint`, fallback | WF-007 | Test-only/example | Useful | Disconnected from sweeps. |
| `V1-CAP-OPT-015` | Run repository/progress tracking | Repository classes/wrappers | WF-008 | Test-only/example | Useful | Process-local implementation only. |
| `V1-CAP-OPT-016` | Standard sweep response envelope | `run_parameter_sweep`, `optimization_tool_result` | WF-001 | Test-only | Useful | Other wrappers use different envelopes. |
| `V1-CAP-OPT-017` | Markdown optimization report | `print_optimization_report`, `build_optimization_report` | WF-001 | Internal/unused | Useful | No external caller. |
| `V1-CAP-OPT-018` | Background task IDs | Three `run_*_task` functions | WF-009 | Unused | No demonstrated value | No queue/executor/lifecycle. |
| `V1-CAP-OPT-019` | Parametric equity simulation | `parametric_simulation` | Standalone internal | Test-only | Useful | No request/response model integration. |
| `V1-CAP-OPT-020` | Declared scenario schemas | Unsupervised, sizing, streak, target, multi-entry, portfolio models | None | Unused | No demonstrated value | Schemas without implementations. |

## 14. Audit Conclusions

### Valuable behaviour worth preserving as behaviour evidence

The package contains credible, self-contained implementations for parameter schema validation, conditional-parameter hashing, constrained candidate generation, deterministic score functions, DSR calculations, time-series split construction, trade-order/resampling Monte Carlo, stress transformations, atomic checkpoint writes, and a thread-safe in-memory repository. These behaviours are directly evidenced by source call paths and focused tests.

### Behaviour that exists but is disconnected

Grid, random, genetic, and walk-forward orchestration exist, but real evaluation is disconnected from the current simulator. Checkpoint/repository functions are disconnected from all sweeps. Report, analysis, and task functions are disconnected from any API, agent tool, scheduler, or worker. Several robustness functions can only reach the same broken backtest adapter.

### Likely dead weight

The strongest candidates are the unconsumed scenario models, unused optimizer wrappers, unused tool-envelope helpers, declared-but-unused error constants, task-ID stubs, the non-persisting save wrapper, and public random-win-rate request/result models. These are **not labelled dead code** because repository-wide indexed search was unavailable; they have **no demonstrated value** or **Questionable** value with Medium confidence.

### Duplicated responsibilities

Walk-forward analysis has two independent implementations. Monte Carlo behaviour is split between `algorithms/random.py` and `robustness.py` with many wrappers. Candidate ranking appears in both `scoring.py` and `sweeps.py`. Run-state models overlap. Reporting and saving wrappers add little or misleading behaviour.

### Important uncertainties and manual confirmation required

1. Confirm whether any deployment branch, unindexed generated tool registry, or external application imports `app.services.optimization`.
2. Confirm the intended current simulator orchestration entry point and strategy registration API.
3. Confirm whether Optuna/skopt and SciPy QMC support was intentionally left as a placeholder.
4. Confirm whether the unused request/result models represent abandoned features or external contracts implemented outside this repository.
5. Run the unit suite on a clean checkout **without the injected simulator/registry mocks** to establish actual import and integration failures.

### Final validation

* Every Python file under `app/services/optimization` is represented.
* Root, algorithm, and persistence `__init__.py` exports were checked.
* All 151 root exports resolve to definitions in the inspected source.
* Public-looking direct-module symbols not included in the root facade were also inventoried.
* Callers in the package, unit tests, usage examples, README, package-introduction commit, and root/service initializers were checked.
* Known dynamic import targets were checked and found missing.
* Production usage is distinguished from test/example/internal usage.
* Workflows are based on concrete call paths.
* No Version 2 design or requirements were introduced.
* No source code was changed.
