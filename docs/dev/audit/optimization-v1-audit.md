# Optimization — Version 1 Code Audit

> Source snapshot: `haruperi/HaruQuant` at commit `a39d26498e14772c571d75fa9a5f0e477a1dd912` on the `main` branch.

## 1. Audit Scope

* **Domain:** optimization
* **Package path:** `app/services/optimization`
* **Tests path supplied:** `ttests/unit/app/services/optimization`
* **Tests path actually present:** `tests/unit/app/services/optimization`
* **Known usage file:** `tests/usage/app/services/09_optimization.py`
* **Files inspected:** all 19 Python files in the package; four unit-test files; the usage script; `app/api/routes/optimization.py`; `app/api/main.py`; `app/api/router.py`; `app/services/__init__.py`; and `app/services/utils/standard.py`.
* **Related packages searched:** API routes/application registration, backtest/simulation, analytics, strategy storage/base strategy, data/brokers, research, security permissions, database repositories/manager, utility tool-standardization, scripts/examples and project documentation.
* **Exclusions:** generated files, caches, virtual environments, web build output and Version 2 requirement comparison.
* **Audit limitations:** static read-only inspection only; no broker credentials, live database, deployed configuration, background worker, or full test execution was available. Runtime statuses therefore distinguish confirmed wiring from executed success.

## 2. Executive Summary

The domain currently contains two materially different systems:

1. A **runtime optimization/API implementation**: parameter optimization (grid, random, Bayesian and genetic), simulation-backed candidate execution, walk-forward evaluation, historical and parametric Monte Carlo, and several risk-scenario calculators.
2. A **root agent-tool surface** of 24 exported functions. Most of these functions only package requests into standard envelopes and are not connected to the concrete optimization engines, persistence, or reporting.

The FastAPI application does register the optimization router, so the API route → background task/direct simulation call paths are real runtime entry points. The parameter-optimization path is substantial but only **partially trustworthy**: the default MT5 branch references `pd.DataFrame` without importing pandas, backtest-result persistence is a no-op, and no compatible current tests validate the path. The walk-forward task computes a result and deliberately discards it before marking the run completed. The asynchronous historical Monte Carlo path is **broken** because `BacktestDatabase.load_result()` always returns `None`. Direct statistical endpoints—parametric Monte Carlo, position sizing, losing streak, profit target, random win-rate and multi-entry—are statically complete and router-connected, but were not executed during this audit.

The strongest structural problems are: duplicate/disconnected public surfaces, misleading `run_*`/`save_*`/`build_*` names that perform packaging only, stale tests and examples targeting nonexistent modules and incompatible signatures, a 1,809-line Monte Carlo file with several unrelated scenario families, a broken lazy walk-forward export, ignored parallelism settings, and incompatible historical-Monte-Carlo/backtest result contracts.

**Evidence trust:** high for package structure, exports, static call paths and explicit no-op/discarded behavior; medium for end-to-end operational success because services were not executed against a real database, broker or simulation environment.

```text
Module folders (package root + `methods`): 2 | Files: 19 | Public symbol definitions: 140 (169 qualified surfaces including 29 re-exports) | Symbols with confirmed runtime callers: 74 (52.9%) | Workflows found: 7
```

## 3. Actual Package Structure

```text
app/services/optimization/
├── __init__.py
│   ├── __version__
│   ├── build_optimization_report()  [re-export]
│   ├── calculate_parameter_stability()  [re-export]
│   ├── compare_optimization_runs()  [re-export]
│   ├── detect_overfit_parameters()  [re-export]
│   ├── rank_parameter_sets()  [re-export]
│   ├── run_parameter_sweep()  [re-export]
│   ├── run_walk_forward_matrix()  [re-export]
│   ├── run_walk_forward_optimization()  [re-export]
│   ├── save_optimization_result()  [re-export]
│   ├── build_robustness_report()  [re-export]
│   ├── calculate_robustness_score()  [re-export]
│   ├── run_combined_monte_carlo()  [re-export]
│   ├── run_commission_stress_test()  [re-export]
│   ├── run_cross_market_test()  [re-export]
│   ├── run_cross_timeframe_test()  [re-export]
│   ├── run_randomize_history_mc()  [re-export]
│   ├── run_randomize_parameters_mc()  [re-export]
│   ├── run_randomize_trade_order_mc()  [re-export]
│   ├── run_resample_trades_mc()  [re-export]
│   ├── run_second_oos_test()  [re-export]
│   ├── run_skip_trades_mc()  [re-export]
│   ├── run_slippage_stress_test()  [re-export]
│   ├── run_spread_stress_test()  [re-export]
│   └── run_third_oos_test()  [re-export]
├── _common.py
│   ├── service_strategy_class()
│   ├── optimization_tool_result()
│   ├── optimization_tool_context()
│   ├── optimization_business_payload()
│   └── package_optimization_request()
├── models.py
│   ├── class UnsupervisedConfigRequest
│   ├── class UnsupervisedRunSummary
│   ├── class UnsupervisedAnalysisRequest
│   ├── class ParameterRange
│   ├── class OptimizationRequest
│   ├── class PositionSizingRequest
│   ├── class OptimizationResponse
│   ├── class OptimizationRunDetails
│   ├── class OptimizationResultItem
│   ├── class WalkForwardRequest
│   ├── class WalkForwardWindow
│   ├── class WalkForwardResponse
│   ├── class MonteCarloRequest
│   ├── class ParametricMonteCarloRequest
│   ├── class MonteCarloResponse
│   ├── class ConsecutiveLosingRequest
│   ├── class ConsecutiveLosingScenario
│   ├── class ConsecutiveLosingResponse
│   ├── class ProfitTargetRequest
│   ├── class ProfitTargetResult
│   ├── class ProfitTargetResponse
│   ├── class ManualPairInput
│   ├── class RandomWinRateRequest
│   ├── class RandomWinRatePair
│   ├── class DistributionStats
│   ├── class RandomWinRateResult
│   ├── class RandomWinRateResponse
│   ├── class RobustnessRequest
│   ├── class RobustnessStats
│   ├── class RobustnessResponse
│   ├── class MultiEntryRequest
│   ├── class MultiEntryScenarioResult
│   └── class MultiEntryResponse
├── result.py
│   ├── OptimizationResult
│   ├── OptimizationSummary
│   ├── OptimizationSummary.get_top_n
│   └── OptimizationSummary.to_dataframe
├── scoring.py
│   ├── sharpe_score()
│   ├── sortino_score()
│   ├── calmar_score()
│   ├── profit_factor_score()
│   ├── total_return_score()
│   ├── custom_score()
│   └── optimization_get_scoring_func()
├── splitters.py
│   ├── SplitterResult
│   ├── SplitterResult.plots
│   ├── splitter_from_rolling
│   ├── splitter_from_expanding
│   └── splitter_rolling_split
├── portfolio_optimizer.py
│   ├── PortfolioOptimizerResult
│   ├── PortfolioOptimizerResult.plot
│   ├── pfo_from_optimize_func
│   └── pfo_plot
├── execution.py
│   ├── load_strategy_from_path
│   ├── normalize_engine_type
│   ├── EngineOptimizationResult
│   ├── EngineOptimizationResult.summary
│   ├── run_strategy_backtest
│   └── run_strategy_backtest_from_path
├── methods/
│   ├── __init__.py
│   │   ├── bayesian_optimization  [lazy re-export]
│   │   ├── genetic_algorithm  [lazy re-export]
│   │   ├── grid_search  [lazy re-export]
│   │   ├── random_search  [lazy re-export]
│   │   └── walk_forward_optimization  [broken lazy target]
│   ├── grid_search.py
│   │   ├── grid_search()
│   │   └── optimization_grid_search()
│   ├── random_search.py
│   │   ├── random_search()
│   │   └── optimization_random_search()
│   ├── bayesian.py
│   │   ├── bayesian_optimization()
│   │   └── optimization_bayesian()
│   ├── genetic.py
│   │   ├── genetic_algorithm()
│   │   └── optimization_genetic()
├── walk_forward.py
│   ├── walk_forward
│   ├── print_optimization_report
│   ├── walk_forward_optimization
│   └── optimization_walk_forward
├── parallel.py
│   ├── ProgressTracker
│   ├── ProgressTracker.update
│   ├── parallel_grid_search
│   ├── parallel_random_search
│   ├── parallel_walk_forward
│   ├── compare_parallel_speedup
│   ├── get_optimal_n_jobs
│   ├── estimate_completion_time
│   ├── analyze_parallel_results
│   └── analyze_walk_forward_results
├── monte_carlo.py
│   ├── MonteCarloResult
│   ├── MonteCarloResult.calculate_statistics
│   ├── MonteCarloResult.get_summary
│   ├── ParametricSimulationResult
│   ├── PositionSizingResult
│   ├── ConsecutiveLosingScenarioResult
│   ├── ProfitTargetScenarioResult
│   ├── monte_carlo_analysis
│   ├── shuffle_trades_simulation
│   ├── resample_returns_simulation
│   ├── bootstrap_simulation
│   ├── calculate_probability_of_ruin
│   ├── calculate_confidence_intervals
│   ├── compare_simulation_methods
│   ├── assess_strategy_robustness
│   ├── parametric_simulation
│   ├── position_sizing_simulation
│   ├── consecutive_losing_simulation
│   ├── profit_target_simulation
│   ├── random_win_rate_simulation
│   ├── robustness_simulation
│   └── multi_entry_simulation
├── optimization_tools.py
│   ├── build_optimization_report()
│   ├── calculate_parameter_stability()
│   ├── compare_optimization_runs()
│   ├── detect_overfit_parameters()
│   ├── rank_parameter_sets()
│   ├── run_parameter_sweep()
│   ├── run_walk_forward_matrix()
│   ├── run_walk_forward_optimization()
│   └── save_optimization_result()
├── robustness_tools.py
│   ├── build_robustness_report()
│   ├── calculate_robustness_score()
│   ├── run_combined_monte_carlo()
│   ├── run_commission_stress_test()
│   ├── run_cross_market_test()
│   ├── run_cross_timeframe_test()
│   ├── run_randomize_history_mc()
│   ├── run_randomize_parameters_mc()
│   ├── run_randomize_trade_order_mc()
│   ├── run_resample_trades_mc()
│   ├── run_second_oos_test()
│   ├── run_skip_trades_mc()
│   ├── run_slippage_stress_test()
│   ├── run_spread_stress_test()
│   └── run_third_oos_test()
└── core.py
    ├── BacktestDatabase
    ├── BacktestDatabase.save_result
    ├── BacktestDatabase.load_result
    ├── OBJECTIVE_FUNCTIONS
    ├── run_optimization_task
    ├── run_walk_forward_task
    └── run_monte_carlo_task
```

Notes:

* `__init__.py` exports only the 24 agent-facing functions. It does **not** export the concrete optimizer classes/functions used by the API.
* `standardize_domain_exports(...)` is a logging-only placeholder and adds no dynamic registration.
* `_common.py` has module-level dynamic lookup, but that does not make missing names importable from `app.services.optimization`.

## 4. Module and File Inventory

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- |
| contracts | models.py | Pydantic API request/response contracts. | 33 model classes | Standard: typing; Third-party: pydantic; Local: none | Used | Essential |
| results | result.py | Candidate and optimization summary containers. | OptimizationResult; OptimizationSummary | Standard: dataclasses, typing; Third-party: pandas; Local: none | Used | Supporting |
| scoring | scoring.py | Objective functions over backtest-result attributes. | 7 scoring/lookup functions | Standard: typing, math; Third-party: none; Local: none | Used | Supporting |
| splitting | splitters.py | Generic index/DataFrame rolling split utilities and plots. | SplitterResult; 3 split functions | Standard: typing; Third-party: pandas, matplotlib; Local: none | Test-only | Questionable |
| portfolio allocation | portfolio_optimizer.py | Periodic allocation callback and plotting. | PortfolioOptimizerResult; pfo_from_optimize_func; pfo_plot | Standard: collections.abc, typing; Third-party: pandas, matplotlib; Local: app.services.data.frames.Data | Unused | Questionable |
| tool support | _common.py | Standard envelopes, context extraction, request packaging and dynamic lower-level lookup. | 5 public functions | Standard: datetime, typing; Third-party: none; Local: app.services resolver; utils.standard | Possibly used | Supporting |
| execution adapter | execution.py | Dynamic strategy loading and one-candidate simulation through portfolio_run. | EngineOptimizationResult; 4 functions | Standard: importlib, dataclasses, typing; Third-party: pandas; Local: API backtest route, analytics, strategy | Used | Essential |
| method exports | methods/__init__.py | Lazy method entry points. | 5 lazy exports | Standard: importlib; Third-party: none; Local: method modules/walk_forward | Possibly used | Questionable |
| method | methods/grid_search.py | Exhaustive search, optional multiprocessing and wrapper. | grid_search; optimization_grid_search | Standard: inspect, time, futures, itertools; Third-party: none; Local: strategy, logger, execution, result, scoring | Used | Essential |
| method | methods/random_search.py | Random numeric-range search, optional multiprocessing and wrapper. | random_search; optimization_random_search | Standard: inspect, time, futures; Third-party: numpy; Local: strategy, logger, execution, result, scoring | Used | Essential |
| method | methods/bayesian.py | Gaussian-process parameter search and wrapper. | bayesian_optimization; optimization_bayesian | Standard: time, typing; Third-party: scikit-optimize (optional); Local: strategy, logger, execution, result, scoring | Used | Useful |
| method | methods/genetic.py | Population-based parameter search and wrapper. | genetic_algorithm; optimization_genetic | Standard: time, typing; Third-party: numpy; Local: strategy, logger, execution, result, scoring | Used | Useful |
| walk-forward | walk_forward.py | Rolling train optimization and OOS evaluation. | walk_forward; report function; alias; wrapper | Standard: typing; Third-party: numpy; Local: logger, execution, grid search, result, scoring | Used | Essential |
| parallel utilities | parallel.py | Standalone process-pool searches, walk-forward and result analysis. | ProgressTracker; 8 functions | Standard: time, futures, multiprocessing; Third-party: pandas, numpy; Local: logger | Test-only | Questionable |
| statistical robustness | monte_carlo.py | Historical and parametric Monte Carlo, scenario and robustness simulations. | 5 result classes; 15 functions | Standard: dataclasses, typing; Third-party: numpy, pandas (local import); Local: models, logger, optional backtest repository | Used | Essential |
| agent tools | optimization_tools.py | Agent-facing request packaging plus three small calculations. | 9 functions | Standard: typing; Third-party: pandas; Local: _common | Test-only | Questionable |
| agent tools | robustness_tools.py | Agent-facing robustness request packaging plus pass-rate calculation. | 15 functions | Standard: typing; Third-party: none; Local: _common | Test-only | Questionable |
| orchestration | core.py | Background optimization, walk-forward and historical Monte Carlo jobs. | BacktestDatabase; OBJECTIVE_FUNCTIONS; 3 async tasks | Standard: asyncio, datetime, hashlib, typing; Third-party: numpy (local); Local: DB, brokers/data, research, strategy storage, security, methods, MC, logger | Used | Essential |
| package surface | __init__.py | Root export surface for 24 agent-facing tools. | 24 re-exports; __version__ | Standard: none; Third-party: none; Local: utils.standard, optimization_tools, robustness_tools | Test-only | Questionable |

## 5. Public Behaviour Inventory

### `__init__.py`

**File responsibility:** Root package export surface. `standardize_domain_exports` is a no-op placeholder; it creates no registry or extra runtime binding.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| __version__ | Constant | Package version string. | None → '1.0.0' | None | None | No caller found | None | Unused | Supporting |
| build_optimization_report | Re-exported function | Package a reporting request; does not build a report. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| calculate_parameter_stability | Re-exported function | Calculate per-parameter sample standard deviation. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | Stale usage/unit tests only | tests/usage/app/services/09_optimization.py; tests/unit/.../test_optimization.py | Test-only | Questionable |
| compare_optimization_runs | Re-exported function | Package run comparison inputs. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | Stale usage/unit tests only | tests/usage/app/services/09_optimization.py; tests/unit/.../test_optimization.py | Test-only | No demonstrated value |
| detect_overfit_parameters | Re-exported function | Flag an in-sample/out-of-sample score gap. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | Stale usage/unit tests only | tests/usage/app/services/09_optimization.py; tests/unit/.../test_optimization.py | Test-only | Questionable |
| rank_parameter_sets | Re-exported function | Sort candidate dictionaries by score. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | Questionable |
| run_parameter_sweep | Re-exported function | Package parameter-sweep arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | Stale usage/unit tests only | tests/usage/app/services/09_optimization.py; tests/unit/.../test_optimization.py | Test-only | No demonstrated value |
| run_walk_forward_matrix | Re-exported function | Package a walk-forward matrix. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_walk_forward_optimization | Re-exported function | Package walk-forward arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| save_optimization_result | Re-exported function | Package a persistence request; does not save. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| build_robustness_report | Re-exported function | Package robustness report arguments; does not build a report. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| calculate_robustness_score | Re-exported function | Calculate percentage of passed checks. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | Questionable |
| run_combined_monte_carlo | Re-exported function | Package combined Monte Carlo arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_commission_stress_test | Re-exported function | Package commission-stress arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | Stale usage/unit tests only | tests/usage/app/services/09_optimization.py; tests/unit/.../test_optimization.py | Test-only | No demonstrated value |
| run_cross_market_test | Re-exported function | Package cross-market test arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_cross_timeframe_test | Re-exported function | Package cross-timeframe test arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_randomize_history_mc | Re-exported function | Package history-randomization arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_randomize_parameters_mc | Re-exported function | Package parameter-randomization arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_randomize_trade_order_mc | Re-exported function | Package trade-order Monte Carlo arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_resample_trades_mc | Re-exported function | Package resampling Monte Carlo arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_second_oos_test | Re-exported function | Package second OOS test arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_skip_trades_mc | Re-exported function | Package skipped-trade Monte Carlo arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |
| run_slippage_stress_test | Re-exported function | Package slippage-stress arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | Stale usage/unit tests only | tests/usage/app/services/09_optimization.py; tests/unit/.../test_optimization.py | Test-only | No demonstrated value |
| run_spread_stress_test | Re-exported function | Package spread-stress arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | Stale usage/unit tests only | tests/usage/app/services/09_optimization.py; tests/unit/.../test_optimization.py | Test-only | No demonstrated value |
| run_third_oos_test | Re-exported function | Package third OOS test arguments. | **kwargs → standard tool envelope | None | Underlying function-specific conversion errors only | No code caller found | None | Unused | No demonstrated value |

### `_common.py`

**File responsibility:** Support layer for the disconnected agent-tool surface and optional lower-level dynamic lookup.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| service_strategy_class | Function | Normalize a class/factory into a strategy class. | class/factory → strategy class | None | TypeError/constructor exceptions | optimization_* wrappers | Indirect stale tool tests | Possibly used | Supporting |
| optimization_tool_result | Function | Build the standard optimization tool response envelope. | tool metadata/data → dict envelope | None | Envelope builder validation errors | optimization_tools.py; robustness_tools.py | Indirect stale tool tests | Possibly used | Supporting |
| optimization_tool_context | Function | Extract trace/environment/dry-run context from kwargs. | kwargs → context dict | None | None expected | calculation tools | Indirect stale tool tests | Possibly used | Supporting |
| optimization_business_payload | Function | Remove tool-context keys from business arguments. | kwargs → filtered dict | None | None expected | package_optimization_request | Indirect stale tool tests | Possibly used | Supporting |
| package_optimization_request | Function | Return a timestamped, packaged request; it does not execute it. | tool_name, kwargs → standard envelope | None | Envelope builder errors | packaging tools | Indirect stale tool tests | Possibly used | Supporting |

### `models.py`

**File responsibility:** API contracts for optimization, walk-forward, unsupervised analysis and Monte Carlo endpoints.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UnsupervisedConfigRequest | Pydantic class | Validate/serialize enabled; feature, PCA, clustering, horizon, labeling, scaling and adaptation settings. | enabled; feature, PCA, clustering, horizon, labeling, scaling and adaptation settings → validated UnsupervisedConfigRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| UnsupervisedRunSummary | Pydantic class | Validate/serialize status, config, features, metadata, strategy/risk context, guardrails, reason, report. | status, config, features, metadata, strategy/risk context, guardrails, reason, report → validated UnsupervisedRunSummary | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| UnsupervisedAnalysisRequest | Pydantic class | Validate/serialize symbol, timeframe, date range, data_source, unsupervised config. | symbol, timeframe, date range, data_source, unsupervised config → validated UnsupervisedAnalysisRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| ParameterRange | Pydantic class | Validate/serialize name, min, max, optional step, type=int\|float. | name, min, max, optional step, type=int\|float → validated ParameterRange | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| OptimizationRequest | Pydantic class | Validate/serialize strategy_id, method, objective, data range/source, capital, parameter ranges, method/execution settings. | strategy_id, method, objective, data range/source, capital, parameter ranges, method/execution settings → validated OptimizationRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| PositionSizingRequest | Pydantic class | Validate/serialize win_rate, reward_risk_ratio, risk_per_trade, num_trades, initial_balance. | win_rate, reward_risk_ratio, risk_per_trade, num_trades, initial_balance → validated PositionSizingRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| OptimizationResponse | Pydantic class | Validate/serialize optimization_id, status, method, total_combinations, message. | optimization_id, status, method, total_combinations, message → validated OptimizationResponse | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| OptimizationRunDetails | Pydantic class | Validate/serialize persisted optimization run metadata, status, best result and optional unsupervised data. | persisted optimization run metadata, status, best result and optional unsupervised data → validated OptimizationRunDetails | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| OptimizationResultItem | Pydantic class | Validate/serialize parameters, score/rank and performance metrics. | parameters, score/rank and performance metrics → validated OptimizationResultItem | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| WalkForwardRequest | Pydantic class | Validate/serialize strategy/data configuration, train/test periods, parameter ranges, n_jobs and optional unsupervised config. | strategy/data configuration, train/test periods, parameter ranges, n_jobs and optional unsupervised config → validated WalkForwardRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| WalkForwardWindow | Pydantic class | Validate/serialize one train/test window, selected parameters and train/test metrics. | one train/test window, selected parameters and train/test metrics → validated WalkForwardWindow | None | pydantic.ValidationError | Stale optimization tests only | tests/unit/.../test_optimization.py (incompatible field expectations) | Test-only | Questionable |
| WalkForwardResponse | Pydantic class | Validate/serialize task_id, windows, aggregate metrics, stability_score, status. | task_id, windows, aggregate metrics, stability_score, status → validated WalkForwardResponse | None | pydantic.ValidationError | Stale optimization tests only | tests/unit/.../test_optimization.py (incompatible field expectations) | Test-only | Questionable |
| MonteCarloRequest | Pydantic class | Validate/serialize backtest_id, simulation_type, simulation count, block size, seed, initial_balance. | backtest_id, simulation_type, simulation count, block size, seed, initial_balance → validated MonteCarloRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| ParametricMonteCarloRequest | Pydantic class | Validate/serialize win_rate, reward/risk, risk/trade, trade count, simulation count, balance. | win_rate, reward/risk, risk/trade, trade count, simulation count, balance → validated ParametricMonteCarloRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| MonteCarloResponse | Pydantic class | Validate/serialize persisted Monte Carlo status, configuration, distribution and risk statistics. | persisted Monte Carlo status, configuration, distribution and risk statistics → validated MonteCarloResponse | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| ConsecutiveLosingRequest | Pydantic class | Validate/serialize paired win rates/RRRs plus trade and simulation counts. | paired win rates/RRRs plus trade and simulation counts → validated ConsecutiveLosingRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| ConsecutiveLosingScenario | Pydantic class | Validate/serialize label and loss-streak distribution statistics. | label and loss-streak distribution statistics → validated ConsecutiveLosingScenario | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| ConsecutiveLosingResponse | Pydantic class | Validate/serialize list of ConsecutiveLosingScenario. | list of ConsecutiveLosingScenario → validated ConsecutiveLosingResponse | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| ProfitTargetRequest | Pydantic class | Validate/serialize initial/target balance, trade count, win rate, simulations. | initial/target balance, trade count, win rate, simulations → validated ProfitTargetRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| ProfitTargetResult | Pydantic class | Validate/serialize risk level and target-hit distribution statistics. | risk level and target-hit distribution statistics → validated ProfitTargetResult | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| ProfitTargetResponse | Pydantic class | Validate/serialize list of ProfitTargetResult. | list of ProfitTargetResult → validated ProfitTargetResponse | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| ManualPairInput | Pydantic class | Validate/serialize win_rate and rrr pair. | win_rate and rrr pair → validated ManualPairInput | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| RandomWinRateRequest | Pydantic class | Validate/serialize initial equity, risk, trades/run, simulations and optional manual pairs. | initial equity, risk, trades/run, simulations and optional manual pairs → validated RandomWinRateRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| RandomWinRatePair | Pydantic class | Validate/serialize win_rate, rrr, expectancy and usage statistics. | win_rate, rrr, expectancy and usage statistics → validated RandomWinRatePair | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| DistributionStats | Pydantic class | Validate/serialize minimum, quartiles, maximum, mean and standard deviation. | minimum, quartiles, maximum, mean and standard deviation → validated DistributionStats | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| RandomWinRateResult | Pydantic class | Validate/serialize pairs plus drawdown/equity/return distributions. | pairs plus drawdown/equity/return distributions → validated RandomWinRateResult | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| RandomWinRateResponse | Pydantic class | Validate/serialize RandomWinRateResult. | RandomWinRateResult → validated RandomWinRateResponse | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| RobustnessRequest | Pydantic class | Validate/serialize backtest_id, simulations, simulation type, skip probability, deterioration. | backtest_id, simulations, simulation type, skip probability, deterioration → validated RobustnessRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| RobustnessStats | Pydantic class | Validate/serialize profit range/mean, drawdown, ruin, VaR/CVaR and confidence bounds. | profit range/mean, drawdown, ruin, VaR/CVaR and confidence bounds → validated RobustnessStats | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| RobustnessResponse | Pydantic class | Validate/serialize original and simulated equity curves, stats and aggregate probabilities. | original and simulated equity curves, stats and aggregate probabilities → validated RobustnessResponse | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| MultiEntryRequest | Pydantic class | Validate/serialize win rate, initial/step RRR, risk, simulations and initial balance. | win rate, initial/step RRR, risk, simulations and initial balance → validated MultiEntryRequest | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |
| MultiEntryScenarioResult | Pydantic class | Validate/serialize trade-count scenario distributions and mean equity curve. | trade-count scenario distributions and mean equity curve → validated MultiEntryScenarioResult | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Supporting |
| MultiEntryResponse | Pydantic class | Validate/serialize single-, double- and triple-entry scenario results. | single-, double- and triple-entry scenario results → validated MultiEntryResponse | None | pydantic.ValidationError | app/api/routes/optimization.py or nested API model | API-route/static model usage; current executable tests not confirmed | Used | Essential |

### `result.py`

**File responsibility:** Internal candidate/result contracts used by concrete optimization methods.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OptimizationResult | Dataclass | One parameter candidate, backtest result, metrics, score and rank. | parameters, result, metrics, score, rank → instance | None | pandas conversion errors where applicable | all four method implementations | Stale tests reference a different result schema | Used | Supporting |
| OptimizationSummary | Dataclass | Aggregate best result and all evaluated candidates. | best/all candidate data and counters → instance | None | pandas conversion errors where applicable | all four method implementations; print_optimization_report | Stale tests reference a different result schema | Used | Supporting |
| OptimizationSummary.get_top_n | Method | Return the first N ranked candidate results. | n → list[OptimizationResult] | None | pandas conversion errors where applicable | print_optimization_report | Stale tests reference a different result schema | Used | Supporting |
| OptimizationSummary.to_dataframe | Method | Flatten candidates into a pandas DataFrame. | none → pandas.DataFrame | None | pandas conversion errors where applicable | No production caller found | Stale tests reference a different result schema | Unused | Questionable |

### `scoring.py`

**File responsibility:** Attribute-based objective functions for EngineOptimizationResult-like objects.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sharpe_score | Function | Return result.sharpe_ratio. | Backtest-like result (or objective label) → float/callable | None | AttributeError/TypeError for incompatible result | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Stale scoring tests use trade lists, not result objects | Used | Supporting |
| sortino_score | Function | Return result.sortino_ratio. | Backtest-like result (or objective label) → float/callable | None | AttributeError/TypeError for incompatible result | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Stale scoring tests use trade lists, not result objects | Used | Supporting |
| calmar_score | Function | Return result.calmar_ratio. | Backtest-like result (or objective label) → float/callable | None | AttributeError/TypeError for incompatible result | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Stale scoring tests use trade lists, not result objects | Used | Supporting |
| profit_factor_score | Function | Return finite result.profit_factor; converts infinity to zero. | Backtest-like result (or objective label) → float/callable | None | AttributeError/TypeError for incompatible result | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Stale scoring tests use trade lists, not result objects | Used | Supporting |
| total_return_score | Function | Return result.total_return_pct. | Backtest-like result (or objective label) → float/callable | None | AttributeError/TypeError for incompatible result | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Stale scoring tests use trade lists, not result objects | Used | Supporting |
| custom_score | Function | Weighted return/Sharpe/drawdown score. | Backtest-like result (or objective label) → float/callable | None | AttributeError/TypeError for incompatible result | No runtime caller; stale unit test | test_optimization.py expects a different signature | Test-only | Useful |
| optimization_get_scoring_func | Function | Map user-facing objective labels to scoring functions. | Backtest-like result (or objective label) → float/callable | None | AttributeError/TypeError for incompatible result | optimization_* wrappers only | No compatible current test | Possibly used | Supporting |

### `splitters.py`

**File responsibility:** Standalone generic split helpers; not connected to core.walk_forward.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SplitterResult | Class | Container for index, split sets and labels. | index/DataFrame and window parameters → SplitterResult/list | None | ValueError/IndexError/pandas errors on invalid bounds | Stale unit tests and scripts/examples/tools/README.md | tests/unit/.../test_optimization.py targets a different signature | Test-only | Questionable |
| SplitterResult.plots | Method | Plot each split as horizontal bars. | index/DataFrame and window parameters → SplitterResult/list | Local state mutation (matplotlib figure) | ValueError/IndexError/pandas errors on invalid bounds | No caller found | tests/unit/.../test_optimization.py targets a different signature | Unused | Questionable |
| splitter_from_rolling | Function | Build rolling index windows and train/test sets. | index/DataFrame and window parameters → SplitterResult/list | None | ValueError/IndexError/pandas errors on invalid bounds | Stale unit tests and scripts/examples/tools/README.md | tests/unit/.../test_optimization.py targets a different signature | Test-only | Questionable |
| splitter_from_expanding | Function | Delegate to rolling splitter with a fixed minimum length. | index/DataFrame and window parameters → SplitterResult/list | None | ValueError/IndexError/pandas errors on invalid bounds | Stale unit tests and scripts/examples/tools/README.md | tests/unit/.../test_optimization.py targets a different signature | Test-only | Questionable |
| splitter_rolling_split | Function | Slice a DataFrame into rolling train/test windows. | index/DataFrame and window parameters → SplitterResult/list | None | ValueError/IndexError/pandas errors on invalid bounds | Stale unit tests and scripts/examples/tools/README.md | tests/unit/.../test_optimization.py targets a different signature | Test-only | Questionable |

### `portfolio_optimizer.py`

**File responsibility:** Periodic portfolio allocation helper isolated from optimization API/core.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PortfolioOptimizerResult | Class | Hold periodic portfolio weights. | weights/Data/callback → result or axis | None | Plot errors are printed and converted to None | Documentation only; no code caller found | None | Unused | Questionable |
| PortfolioOptimizerResult.plot | Method | Plot allocation weights as area or line chart. | weights/Data/callback → result or axis | Local state mutation (matplotlib figure) | Plot errors are printed and converted to None | Documentation only; no code caller found | None | Unused | Questionable |
| pfo_from_optimize_func | Function | Group HaruQuant Data by period and call an allocation callback. | weights/Data/callback → result or axis | None | ValueError for non-HaruQuant Data; callback/pandas exceptions | Documentation only; no code caller found | None | Unused | Questionable |
| pfo_plot | Function | Delegate to PortfolioOptimizerResult.plot. | weights/Data/callback → result or axis | Local state mutation (matplotlib figure) | Plot errors are printed and converted to None | Documentation only; no code caller found | None | Unused | Questionable |

### `execution.py`

**File responsibility:** Concrete bridge from optimization methods into the simulation/backtest stack.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| load_strategy_from_path | Function | Import and return a named strategy class from a Python file. | path, class_name → strategy class | Read-only (filesystem/module import) | ImportError, FileNotFoundError, AttributeError, strategy import exceptions | run_strategy_backtest_from_path | Current tests target an incompatible older signature | Used | Supporting |
| normalize_engine_type | Function | Normalize vectorised/vectorized labels and validate engine type. | engine_type → normalized string | None | ValueError | run_strategy_backtest | Current tests target an incompatible older signature | Used | Supporting |
| EngineOptimizationResult | Dataclass | Optimization-facing result assembled from simulation portfolio output. | trades/equity/metrics → instance | None | Constructor/type errors | run_strategy_backtest | Current tests target an incompatible older signature | Used | Supporting |
| EngineOptimizationResult.summary | Method | Return scalar performance metrics as a dictionary. | none → dict[str,float] | None | Numeric conversion errors | all optimization methods | Current tests target an incompatible older signature | Used | Supporting |
| run_strategy_backtest | Function | Run one parameter candidate through API-layer portfolio simulation. | strategy class, DataFrame, symbol, params, balance, engine → EngineOptimizationResult | External API call (local API-layer portfolio_run) / Local state mutation (simulation) | ValueError and downstream simulation/analytics errors | grid, random, Bayesian, genetic and walk_forward | Current tests target an incompatible older signature | Used | Essential |
| run_strategy_backtest_from_path | Function | Load a strategy from disk and run one candidate. | strategy path/class plus candidate inputs → EngineOptimizationResult | Read-only + Local state mutation (simulation) | Import and simulation errors | parallel branches of grid/random | Current tests target an incompatible older signature | Used | Essential |

### `methods/__init__.py`

**File responsibility:** Lazy export module. The walk-forward target is prefixed twice and is statically broken.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bayesian_optimization | Lazy re-export | Resolve method implementation on first attribute access. | attribute access → callable | None | Import-time dependency errors | No production caller found | None | Possibly used | Supporting |
| genetic_algorithm | Lazy re-export | Resolve method implementation on first attribute access. | attribute access → callable | None | Import-time dependency errors | No production caller found | None | Possibly used | Supporting |
| grid_search | Lazy re-export | Resolve method implementation on first attribute access. | attribute access → callable | None | Import-time dependency errors | No production caller found | None | Possibly used | Supporting |
| random_search | Lazy re-export | Resolve method implementation on first attribute access. | attribute access → callable | None | Import-time dependency errors | No production caller found | None | Possibly used | Supporting |
| walk_forward_optimization | Lazy re-export | Resolve method implementation on first attribute access. | attribute access → callable | None | ModuleNotFoundError/AttributeError | No production caller found | None | Possibly used | Questionable |

### `methods/grid_search.py`

**File responsibility:** Concrete optimization method implementation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grid_search | Function | Exhaustive candidate evaluation with optional process parallelism. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | RuntimeError for non-resolvable parallel strategy; candidate errors counted as failures | core.run_optimization_task; walk_forward.walk_forward | No compatible current unit test; stale tests call a different API | Used | Essential |
| optimization_grid_search | Function | User-facing wrapper that normalizes strategy/grid/objective. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | RuntimeError for non-resolvable parallel strategy; candidate errors counted as failures | No production caller; dynamically discoverable only through _common resolver | None compatible | Possibly used | Questionable |

### `methods/random_search.py`

**File responsibility:** Concrete optimization method implementation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_search | Function | Sample numeric ranges and evaluate candidates. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | Setup/process errors; candidate errors counted or converted to low fitness | core.run_optimization_task | No compatible current unit test; stale tests call a different API | Used | Essential |
| optimization_random_search | Function | User-facing wrapper for random search. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | Setup/process errors; candidate errors counted or converted to low fitness | No production caller; dynamically discoverable only through _common resolver | None compatible | Possibly used | Questionable |

### `methods/bayesian.py`

**File responsibility:** Concrete optimization method implementation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bayesian_optimization | Function | Gaussian-process optimization using scikit-optimize. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | ImportError when scikit-optimize unavailable; setup errors; candidate errors become penalty | core.run_optimization_task | No compatible current unit test; stale tests call a different API | Used | Useful |
| optimization_bayesian | Function | User-facing wrapper for Bayesian optimization. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | ImportError when scikit-optimize unavailable; setup errors; candidate errors become penalty | No production caller; dynamically discoverable only through _common resolver | None compatible | Possibly used | Questionable |

### `methods/genetic.py`

**File responsibility:** Concrete optimization method implementation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| genetic_algorithm | Function | Population-based search with selection, crossover, mutation and elitism. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | Setup/process errors; candidate errors counted or converted to low fitness | core.run_optimization_task | No compatible current unit test; stale tests call a different API | Used | Useful |
| optimization_genetic | Function | User-facing wrapper for genetic search. | strategy/data/parameter space/settings → OptimizationSummary | Local state mutation (CPU/processes/logging) | Setup/process errors; candidate errors counted or converted to low fitness | No production caller; dynamically discoverable only through _common resolver | None compatible | Possibly used | Questionable |

### `walk_forward.py`

**File responsibility:** Serial rolling train/test optimization used by the API background task.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| walk_forward | Function | Optimize or use defaults on rolling training windows, then test out of sample. | strategy/data/grid/window settings → summary dict or None | Local state mutation (repeated simulations/logging) | Data slicing, grid search and simulation errors | core.run_walk_forward_task | No compatible current tests | Used | Essential |
| print_optimization_report | Function | Print an OptimizationSummary and top candidates. | strategy/data/grid/window settings → summary dict or None | Local state mutation (stdout) | KeyError for missing metrics | No caller found | No compatible current tests | Unused | Questionable |
| walk_forward_optimization | Alias | Alias of walk_forward. | strategy/data/grid/window settings → summary dict or None | Local state mutation (simulations) | Same as walk_forward | methods lazy export intends to expose it but target import is broken | No compatible current tests | Possibly used | Questionable |
| optimization_walk_forward | Function | User-facing wrapper for walk-forward optimization. | strategy/data/grid/window settings → summary dict or None | Local state mutation (simulations) | Same as walk_forward | No production caller; dynamically discoverable wrapper | No compatible current tests | Possibly used | Questionable |

### `parallel.py`

**File responsibility:** A second parallel-search implementation not used by core or method modules.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ProgressTracker | Class | Track completed parallel tasks and elapsed time. | factory/results/settings → list/dict/DataFrame/number | Local state mutation (processes/logging/stdout) | Numeric/pandas errors | parallel.py internals and/or stale test_optimization.py | Only stale/incompatible tests | Test-only | Questionable |
| ProgressTracker.update | Method | Increment progress and print a console progress bar. | factory/results/settings → list/dict/DataFrame/number | Local state mutation (processes/logging/stdout) | Numeric/pandas errors | parallel.py internals and/or stale test_optimization.py | Only stale/incompatible tests | Test-only | Questionable |
| parallel_grid_search | Function | Evaluate a Cartesian grid with ProcessPoolExecutor. | factory/results/settings → list/dict/DataFrame/number | Local state mutation (processes/logging/stdout) | Process/pickling/worker exceptions; empty result can raise IndexError | parallel.py internals and/or stale test_optimization.py | Only stale/incompatible tests | Test-only | Questionable |
| parallel_random_search | Function | Sample and evaluate parameter dictionaries in processes. | factory/results/settings → list/dict/DataFrame/number | Local state mutation (processes/logging/stdout) | Process/pickling/worker exceptions; empty result can raise IndexError | No code caller found | Only stale/incompatible tests | Unused | Questionable |
| parallel_walk_forward | Function | Optimize rolling train windows and evaluate test windows. | factory/results/settings → list/dict/DataFrame/number | Local state mutation (processes/logging/stdout) | Process/pickling/worker exceptions; empty result can raise IndexError | No code caller found | Only stale/incompatible tests | Unused | Questionable |
| compare_parallel_speedup | Function | Benchmark grid search at several worker counts. | factory/results/settings → list/dict/DataFrame/number | Local state mutation (processes/logging/stdout) | Process/pickling/worker exceptions; empty result can raise IndexError | No code caller found | Only stale/incompatible tests | Unused | Questionable |
| get_optimal_n_jobs | Function | Return CPU count minus one, bounded to one. | factory/results/settings → list/dict/DataFrame/number | None | Numeric/pandas errors | No code caller found | Only stale/incompatible tests | Unused | Questionable |
| estimate_completion_time | Function | Estimate parallel runtime with a fixed overhead factor. | factory/results/settings → list/dict/DataFrame/number | None | Numeric/pandas errors | No code caller found | Only stale/incompatible tests | Unused | Questionable |
| analyze_parallel_results | Function | Flatten parallel result dictionaries into a DataFrame. | factory/results/settings → list/dict/DataFrame/number | None | Process/pickling/worker exceptions; empty result can raise IndexError | No code caller found | Only stale/incompatible tests | Unused | Questionable |
| analyze_walk_forward_results | Function | Aggregate train/test statistics and an overfitting label. | factory/results/settings → list/dict/DataFrame/number | None | Numeric/pandas errors | No code caller found | Only stale/incompatible tests | Unused | Questionable |

### `monte_carlo.py`

**File responsibility:** Large mixed-responsibility module containing both API-active scenario calculators and disconnected historical helpers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MonteCarloResult | Dataclass | Historical-trade simulation distributions and statistics. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | No caller found | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| MonteCarloResult.calculate_statistics | Method | Populate percentiles, confidence intervals and risk metrics. | simulation-specific inputs → dataclass/dict/list/float | Local state mutation | ValueError for invalid type/input; numpy/data-shape errors | monte_carlo_analysis | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| MonteCarloResult.get_summary | Method | Return selected Monte Carlo statistics. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | No caller found | Current tests mostly target a different Monte Carlo API | Unused | Questionable |
| ParametricSimulationResult | Dataclass | Parametric Monte Carlo configuration and distributions. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | Corresponding simulation function | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| PositionSizingResult | Dataclass | Linear-versus-compounding curves and risk metrics. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | Corresponding simulation function | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| ConsecutiveLosingScenarioResult | Dataclass | Loss-streak distribution for one win-rate/RRR pair. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | Corresponding simulation function | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| ProfitTargetScenarioResult | Dataclass | Target-reaching results for one risk scenario. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | Corresponding simulation function | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| monte_carlo_analysis | Function | Dispatch historical trade shuffle/resample/bootstrap simulation. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | core.run_monte_carlo_task and Monte Carlo helper functions | Current tests mostly target a different Monte Carlo API | Used | Essential |
| shuffle_trades_simulation | Function | Shuffle historical trade order. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | monte_carlo_analysis | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| resample_returns_simulation | Function | Resample trade P&L with replacement. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | monte_carlo_analysis | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| bootstrap_simulation | Function | Block-bootstrap trade P&L. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | monte_carlo_analysis | Current tests mostly target a different Monte Carlo API | Used | Supporting |
| calculate_probability_of_ruin | Function | Estimate threshold-exceeding drawdown probability. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | Stale unit tests / internal helper calls only | Current tests mostly target a different Monte Carlo API | Test-only | Useful |
| calculate_confidence_intervals | Function | Compute simulation percentile intervals for one metric. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | No caller found | Current tests mostly target a different Monte Carlo API | Unused | Questionable |
| compare_simulation_methods | Function | Run all three historical Monte Carlo methods. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | Stale unit tests / internal helper calls only | Current tests mostly target a different Monte Carlo API | Test-only | Useful |
| assess_strategy_robustness | Function | Combine Monte Carlo outcomes into a qualitative assessment. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | Stale unit tests / internal helper calls only | Current tests mostly target a different Monte Carlo API | Test-only | Useful |
| parametric_simulation | Function | Simulate compounded outcomes from win rate, RRR and risk. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | app/api/routes/optimization.py | Current tests mostly target a different Monte Carlo API | Used | Essential |
| position_sizing_simulation | Function | Compare fixed-cash and fixed-percent risk paths. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | app/api/routes/optimization.py | Current tests mostly target a different Monte Carlo API | Used | Essential |
| consecutive_losing_simulation | Function | Simulate maximum losing streaks across paired systems. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | app/api/routes/optimization.py | Current tests mostly target a different Monte Carlo API | Used | Essential |
| profit_target_simulation | Function | Estimate target-reaching outcomes over risk levels. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | app/api/routes/optimization.py | Current tests mostly target a different Monte Carlo API | Used | Essential |
| random_win_rate_simulation | Function | Simulate trades using multiple win-rate/RRR pairs. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | app/api/routes/optimization.py | Current tests mostly target a different Monte Carlo API | Used | Essential |
| robustness_simulation | Function | Bootstrap/shuffle persisted or supplied trades with skips/deterioration. | simulation-specific inputs → dataclass/dict/list/float | Read-only (optional database trade read) | ValueError for missing/invalid trades; repository exceptions are swallowed and returned as None | app/api/routes/optimization.py | Current tests mostly target a different Monte Carlo API | Used | Essential |
| multi_entry_simulation | Function | Compare one-, two- and three-entry execution scenarios. | simulation-specific inputs → dataclass/dict/list/float | None | ValueError for invalid type/input; numpy/data-shape errors | app/api/routes/optimization.py | Current tests mostly target a different Monte Carlo API | Used | Essential |

### `optimization_tools.py`

**File responsibility:** Agent-facing names; six of nine only package requests, and none is connected to an executor.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| build_optimization_report | Function | Package a reporting request; does not build a report. | **kwargs → standard envelope containing unchanged request | None | Envelope construction errors | No code caller found | Stale tests expect non-envelope behavior | Unused | No demonstrated value |
| calculate_parameter_stability | Function | Calculate per-parameter sample standard deviation. | **kwargs → standard envelope containing calculated data | None | Numeric conversion/type errors | Stale tests/examples only | Stale tests expect non-envelope behavior | Test-only | Useful |
| compare_optimization_runs | Function | Package run comparison inputs. | **kwargs → standard envelope containing unchanged request | None | Envelope construction errors | Stale tests/examples only | Stale tests expect non-envelope behavior | Test-only | No demonstrated value |
| detect_overfit_parameters | Function | Flag an in-sample/out-of-sample score gap. | **kwargs → standard envelope containing calculated data | None | Numeric conversion/type errors | Stale tests/examples only | Stale tests expect non-envelope behavior | Test-only | Useful |
| rank_parameter_sets | Function | Sort candidate dictionaries by score. | **kwargs → standard envelope containing calculated data | None | Numeric conversion/type errors | No code caller found | Stale tests expect non-envelope behavior | Unused | Questionable |
| run_parameter_sweep | Function | Package parameter-sweep arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope construction errors | Stale tests/examples only | Stale tests expect non-envelope behavior | Test-only | No demonstrated value |
| run_walk_forward_matrix | Function | Package a walk-forward matrix. | **kwargs → standard envelope containing unchanged request | None | Envelope construction errors | No code caller found | Stale tests expect non-envelope behavior | Unused | No demonstrated value |
| run_walk_forward_optimization | Function | Package walk-forward arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope construction errors | No code caller found | Stale tests expect non-envelope behavior | Unused | No demonstrated value |
| save_optimization_result | Function | Package a persistence request; does not save. | **kwargs → standard envelope containing unchanged request | None | Envelope construction errors | No code caller found | Stale tests expect non-envelope behavior | Unused | No demonstrated value |

### `robustness_tools.py`

**File responsibility:** Agent-facing robustness names; fourteen functions only package requests and execute no robustness logic.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| build_robustness_report | Function | Package robustness report arguments; does not build a report. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| calculate_robustness_score | Function | Calculate percentage of passed checks. | **kwargs(checks) → standard envelope with pass percentage | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | Questionable |
| run_combined_monte_carlo | Function | Package combined Monte Carlo arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_commission_stress_test | Function | Package commission-stress arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | Stale tests/examples only | Stale tests call stress functions positionally and expect transformed trades | Test-only | No demonstrated value |
| run_cross_market_test | Function | Package cross-market test arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_cross_timeframe_test | Function | Package cross-timeframe test arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_randomize_history_mc | Function | Package history-randomization arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_randomize_parameters_mc | Function | Package parameter-randomization arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_randomize_trade_order_mc | Function | Package trade-order Monte Carlo arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_resample_trades_mc | Function | Package resampling Monte Carlo arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_second_oos_test | Function | Package second OOS test arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_skip_trades_mc | Function | Package skipped-trade Monte Carlo arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |
| run_slippage_stress_test | Function | Package slippage-stress arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | Stale tests/examples only | Stale tests call stress functions positionally and expect transformed trades | Test-only | No demonstrated value |
| run_spread_stress_test | Function | Package spread-stress arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | Stale tests/examples only | Stale tests call stress functions positionally and expect transformed trades | Test-only | No demonstrated value |
| run_third_oos_test | Function | Package third OOS test arguments. | **kwargs → standard envelope containing unchanged request | None | Envelope/type errors only | No code caller found | Stale tests call stress functions positionally and expect transformed trades | Unused | No demonstrated value |

### `core.py`

**File responsibility:** Background job orchestration used by the registered FastAPI router.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BacktestDatabase | Class | Placeholder backtest-result persistence adapter. | none → instance | None | None | core tasks | No compatible executable tests; route wiring confirmed | Used | Questionable |
| BacktestDatabase.save_result | Method | No-op placeholder; accepts a result and stores nothing. | result → None | None (despite persistence name) | None | run_optimization_task | No compatible executable tests; route wiring confirmed | Used | No demonstrated value |
| BacktestDatabase.load_result | Method | No-op placeholder; always returns None. | backtest_id → None | None | None | run_monte_carlo_task | No compatible executable tests; route wiring confirmed | Used | No demonstrated value |
| OBJECTIVE_FUNCTIONS | Constant | Maps supported objective names to scoring functions. | objective name → scoring function | None | Key lookup handled by caller default | all core tasks | No compatible executable tests; route wiring confirmed | Used | Supporting |
| run_optimization_task | Async function | Execute an API-created parameter optimization job. | IDs, OptimizationRequest, optional progress manager → None | Read-only + External API call + Persistence write + Event publication | Permission, strategy/data, simulation, DB and missing-name errors; marks run failed | FastAPI POST /api/optimization/runs background task | No compatible executable tests; route wiring confirmed | Used | Essential |
| run_walk_forward_task | Async function | Execute an API-created walk-forward job. | IDs, WalkForwardRequest, optional progress manager → None | Read-only + External API call + Persistence write | Permission, strategy/data, simulation and DB errors; marks run failed | FastAPI POST /api/optimization/walk-forward background task | No compatible executable tests; route wiring confirmed | Used | Essential |
| run_monte_carlo_task | Async function | Load a backtest, run historical Monte Carlo and persist results. | simulation_id, MonteCarloRequest → None | Read-only + Persistence write | Always ValueError with current BacktestDatabase; re-raised | FastAPI POST /api/optimization/monte-carlo background task | No compatible executable tests; route wiring confirmed | Used | Essential |

## 6. Actual Workflows

### `V1-WF-OPT-001` — API Parameter Optimization

* **Scope:** `Cross-domain`
* **Trigger:** POST `/api/optimization/runs`.
* **Input boundary:** `OptimizationRequest` plus user/strategy identifiers.
* **Functions and methods used:** `start_optimization` → DB run creation → `run_optimization_task` → permission and strategy loading → MT5/Dukascopy data load → optional unsupervised analysis → selected method (`grid_search`, `random_search`, `bayesian_optimization`, or `genetic_algorithm`) → `run_strategy_backtest`/`portfolio_run` → save ranked optimization results/status → optional WebSocket progress.
* **Files involved:** `app/api/routes/optimization.py`; `core.py`; `models.py`; `methods/*.py`; `execution.py`; `result.py`; `scoring.py`.
* **External dependencies:** DatabaseManager; StrategyStorage; permissions; data/broker services; research; backtest API/simulation; analytics; WebSocket manager.
* **Output boundary:** Persisted optimization run/results and progress/status visible through API.
* **Failure behaviour:** Exceptions are logged, run status is changed to failed, failure progress is broadcast, then the exception is re-raised. The default MT5 branch can fail with `NameError: pd is not defined`.
* **Operational status:** `Partial`
* **Evidence:** `app/api/main.py:_include_optional_router`; `app/api/routes/optimization.py:start_optimization`; `app/services/optimization/core.py:run_optimization_task`; concrete method and execution symbols.

```text
HTTP request → DB run → background task → data/strategy → optimizer → simulation → ranked DB results/status
```

### `V1-WF-OPT-002` — Walk-Forward Optimization

* **Scope:** `Cross-domain`
* **Trigger:** POST `/api/optimization/walk-forward`.
* **Input boundary:** `WalkForwardRequest`, user and strategy identifiers.
* **Functions and methods used:** `start_walk_forward` → DB run creation → `run_walk_forward_task` → strategy/data load → optional unsupervised analysis → parameter grid → `walk_forward` → repeated train grid searches and OOS backtests → returned summary discarded → DB status marked completed.
* **Files involved:** `app/api/routes/optimization.py`; `core.py`; `walk_forward.py`; `methods/grid_search.py`; `execution.py`.
* **External dependencies:** DatabaseManager; strategy/data/broker/research services; simulation/analytics.
* **Output boundary:** Only completion/failure status and optional unsupervised report are persisted; window results are not saved.
* **Failure behaviour:** Errors mark the run failed and are re-raised. A successful calculation can still leave no walk-forward result evidence.
* **Operational status:** `Partial`
* **Evidence:** `core.py:run_walk_forward_task` explicitly assigns `_ = walk_forward(...)` and comments that window persistence still needs implementation.

```text
HTTP request → DB run → walk_forward() → train optimization → OOS test → result discarded → status completed
```

### `V1-WF-OPT-003` — Historical Backtest Monte Carlo Job

* **Scope:** `Cross-domain`
* **Trigger:** POST `/api/optimization/monte-carlo`.
* **Input boundary:** `MonteCarloRequest` containing a persisted backtest ID.
* **Functions and methods used:** `start_monte_carlo` → create simulation DB row → `run_monte_carlo_task` → `BacktestDatabase.load_result` → `monte_carlo_analysis` → save Monte Carlo results.
* **Files involved:** `app/api/routes/optimization.py`; `core.py`; `monte_carlo.py`; `models.py`.
* **External dependencies:** DatabaseManager and intended backtest-result store.
* **Output boundary:** Intended persisted Monte Carlo distribution and risk statistics.
* **Failure behaviour:** `BacktestDatabase.load_result()` always returns `None`; the task always raises `ValueError('Backtest ... not found')` before simulation.
* **Operational status:** `Broken`
* **Evidence:** `core.py:BacktestDatabase.load_result`; `core.py:run_monte_carlo_task`.

```text
HTTP request → simulation DB row → load_result() returns None → ValueError → no Monte Carlo result
```

### `V1-WF-OPT-004` — Direct Statistical Scenario Simulations

* **Scope:** `Cross-domain`
* **Trigger:** POST to parametric, position-sizing, consecutive-losing, profit-target, random-win-rate or multi-entry endpoints.
* **Input boundary:** Validated endpoint-specific Pydantic request.
* **Functions and methods used:** API route → one corresponding `monte_carlo.py` function → dataclass/dict/model conversion → API response.
* **Files involved:** `app/api/routes/optimization.py`; `models.py`; `monte_carlo.py`.
* **External dependencies:** NumPy; no broker or database required for these variants.
* **Output boundary:** Distribution statistics, equity curves, target/streak/risk results or multi-entry comparisons.
* **Failure behaviour:** Input/model errors and numeric exceptions are converted by the route to HTTP 500. No deterministic seed is exposed for several endpoints.
* **Operational status:** `Unverified`
* **Evidence:** Direct route calls to `parametric_simulation`, `position_sizing_simulation`, `consecutive_losing_simulation`, `profit_target_simulation`, `random_win_rate_simulation`, and `multi_entry_simulation`.

```text
HTTP request → validated scenario model → NumPy simulation → response model
```

### `V1-WF-OPT-005` — Trade-History Robustness Simulation

* **Scope:** `Cross-domain`
* **Trigger:** POST `/api/optimization/monte-carlo/robustness`.
* **Input boundary:** `RobustnessRequest` with backtest ID and stress settings.
* **Functions and methods used:** `run_robustness` → `robustness_simulation` → dynamic import of backtest repository → load trades → shuffle/bootstrap → optional skipped trades and deterioration → aggregate profit/drawdown/VaR/CVaR.
* **Files involved:** `app/api/routes/optimization.py`; `models.py`; `monte_carlo.py`.
* **External dependencies:** `data.database.repositories.backtest_repository.get_backtest_trades_df`; pandas; NumPy.
* **Output boundary:** `RobustnessResponse` with curves and statistics.
* **Failure behaviour:** Any repository-import/read exception is swallowed and returned as `None`; the API then fails while constructing `RobustnessResponse`.
* **Operational status:** `Partial`
* **Evidence:** `monte_carlo.py:robustness_simulation`; `app/api/routes/optimization.py:run_robustness`.

```text
HTTP request → backtest trade repository → stressed simulations → robustness response
```

### `V1-WF-OPT-006` — Agent-Facing Optimization/Robustness Tool Packaging

* **Scope:** `Internal`
* **Trigger:** Direct call to a root-exported tool from an agent/test/client.
* **Input boundary:** Arbitrary kwargs plus optional trace/environment/dry-run context.
* **Functions and methods used:** Root export → `optimization_tools.py` or `robustness_tools.py` → `_common.package_optimization_request`/small calculation → standard envelope.
* **Files involved:** `__init__.py`; `_common.py`; `optimization_tools.py`; `robustness_tools.py`.
* **External dependencies:** `app.services.utils.standard`.
* **Output boundary:** A standard response envelope containing a packaged request or one small calculation.
* **Failure behaviour:** There is no downstream dispatcher, queue, optimizer, persistence or report builder in this path. Callers may wrongly interpret a success envelope as completed work.
* **Operational status:** `Partial`
* **Evidence:** All packaging functions return `package_optimization_request(...)`; full-repository searches found no production executor consuming these envelopes.

```text
tool call → package_optimization_request() → success envelope → no executor
```

### `V1-WF-OPT-007` — Standalone Split/Parallel/Periodic Allocation Helpers

* **Scope:** `Internal`
* **Trigger:** Direct library call.
* **Input boundary:** Index/DataFrame, factory/callback and window/worker settings.
* **Functions and methods used:** Caller → splitter, standalone process-pool optimizer, or periodic allocation callback → in-memory result/plot.
* **Files involved:** `splitters.py`; `parallel.py`; `portfolio_optimizer.py`.
* **External dependencies:** pandas, NumPy, multiprocessing and optional matplotlib.
* **Output boundary:** SplitterResult, result lists/DataFrames, allocation weights or plot axis.
* **Failure behaviour:** No runtime caller was found. `parallel_walk_forward` defines a nested factory that is not safely pickleable under spawn, and result logging assumes at least one result.
* **Operational status:** `Unverified`
* **Evidence:** Only stale tests, documentation and scripts/examples/tools/README.md reference these helpers.

```text
direct library call → in-memory split/parallel/allocation result → no confirmed system consumer
```

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
| --- | --- | --- | --- | --- |
| __init__.py:__version__ | No caller found | Import/call/instantiation | None found | `app/services/optimization/__init__.py` → `__version__` |
| __init__.py:build_optimization_report | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `build_optimization_report` |
| __init__.py:calculate_parameter_stability | Stale usage/unit tests only | Re-export | Test/example | `app/services/optimization/__init__.py` → `calculate_parameter_stability` |
| __init__.py:compare_optimization_runs | Stale usage/unit tests only | Re-export | Test/example | `app/services/optimization/__init__.py` → `compare_optimization_runs` |
| __init__.py:detect_overfit_parameters | Stale usage/unit tests only | Re-export | Test/example | `app/services/optimization/__init__.py` → `detect_overfit_parameters` |
| __init__.py:rank_parameter_sets | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `rank_parameter_sets` |
| __init__.py:run_parameter_sweep | Stale usage/unit tests only | Re-export | Test/example | `app/services/optimization/__init__.py` → `run_parameter_sweep` |
| __init__.py:run_walk_forward_matrix | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_walk_forward_matrix` |
| __init__.py:run_walk_forward_optimization | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_walk_forward_optimization` |
| __init__.py:save_optimization_result | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `save_optimization_result` |
| __init__.py:build_robustness_report | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `build_robustness_report` |
| __init__.py:calculate_robustness_score | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `calculate_robustness_score` |
| __init__.py:run_combined_monte_carlo | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_combined_monte_carlo` |
| __init__.py:run_commission_stress_test | Stale usage/unit tests only | Re-export | Test/example | `app/services/optimization/__init__.py` → `run_commission_stress_test` |
| __init__.py:run_cross_market_test | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_cross_market_test` |
| __init__.py:run_cross_timeframe_test | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_cross_timeframe_test` |
| __init__.py:run_randomize_history_mc | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_randomize_history_mc` |
| __init__.py:run_randomize_parameters_mc | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_randomize_parameters_mc` |
| __init__.py:run_randomize_trade_order_mc | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_randomize_trade_order_mc` |
| __init__.py:run_resample_trades_mc | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_resample_trades_mc` |
| __init__.py:run_second_oos_test | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_second_oos_test` |
| __init__.py:run_skip_trades_mc | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_skip_trades_mc` |
| __init__.py:run_slippage_stress_test | Stale usage/unit tests only | Re-export | Test/example | `app/services/optimization/__init__.py` → `run_slippage_stress_test` |
| __init__.py:run_spread_stress_test | Stale usage/unit tests only | Re-export | Test/example | `app/services/optimization/__init__.py` → `run_spread_stress_test` |
| __init__.py:run_third_oos_test | No code caller found | Re-export | None found | `app/services/optimization/__init__.py` → `run_third_oos_test` |
| _common.py:service_strategy_class | optimization_* wrappers | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/_common.py` → `service_strategy_class` |
| _common.py:optimization_tool_result | optimization_tools.py; robustness_tools.py | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/_common.py` → `optimization_tool_result` |
| _common.py:optimization_tool_context | calculation tools | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/_common.py` → `optimization_tool_context` |
| _common.py:optimization_business_payload | package_optimization_request | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/_common.py` → `optimization_business_payload` |
| _common.py:package_optimization_request | packaging tools | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/_common.py` → `package_optimization_request` |
| models.py:UnsupervisedConfigRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `UnsupervisedConfigRequest` |
| models.py:UnsupervisedRunSummary | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `UnsupervisedRunSummary` |
| models.py:UnsupervisedAnalysisRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `UnsupervisedAnalysisRequest` |
| models.py:ParameterRange | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ParameterRange` |
| models.py:OptimizationRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `OptimizationRequest` |
| models.py:PositionSizingRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `PositionSizingRequest` |
| models.py:OptimizationResponse | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `OptimizationResponse` |
| models.py:OptimizationRunDetails | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `OptimizationRunDetails` |
| models.py:OptimizationResultItem | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `OptimizationResultItem` |
| models.py:WalkForwardRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `WalkForwardRequest` |
| models.py:WalkForwardWindow | Stale optimization tests only | Model/config reference | Test/example | `app/services/optimization/models.py` → `WalkForwardWindow` |
| models.py:WalkForwardResponse | Stale optimization tests only | Model/config reference | Test/example | `app/services/optimization/models.py` → `WalkForwardResponse` |
| models.py:MonteCarloRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `MonteCarloRequest` |
| models.py:ParametricMonteCarloRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ParametricMonteCarloRequest` |
| models.py:MonteCarloResponse | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `MonteCarloResponse` |
| models.py:ConsecutiveLosingRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ConsecutiveLosingRequest` |
| models.py:ConsecutiveLosingScenario | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ConsecutiveLosingScenario` |
| models.py:ConsecutiveLosingResponse | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ConsecutiveLosingResponse` |
| models.py:ProfitTargetRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ProfitTargetRequest` |
| models.py:ProfitTargetResult | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ProfitTargetResult` |
| models.py:ProfitTargetResponse | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ProfitTargetResponse` |
| models.py:ManualPairInput | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `ManualPairInput` |
| models.py:RandomWinRateRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `RandomWinRateRequest` |
| models.py:RandomWinRatePair | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `RandomWinRatePair` |
| models.py:DistributionStats | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `DistributionStats` |
| models.py:RandomWinRateResult | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `RandomWinRateResult` |
| models.py:RandomWinRateResponse | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `RandomWinRateResponse` |
| models.py:RobustnessRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `RobustnessRequest` |
| models.py:RobustnessStats | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `RobustnessStats` |
| models.py:RobustnessResponse | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `RobustnessResponse` |
| models.py:MultiEntryRequest | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `MultiEntryRequest` |
| models.py:MultiEntryScenarioResult | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `MultiEntryScenarioResult` |
| models.py:MultiEntryResponse | app/api/routes/optimization.py or nested API model | Model/config reference | Runtime | `app/services/optimization/models.py` → `MultiEntryResponse` |
| result.py:OptimizationResult | all four method implementations | Import/call/instantiation | Runtime | `app/services/optimization/result.py` → `OptimizationResult` |
| result.py:OptimizationSummary | all four method implementations; print_optimization_report | Import/call/instantiation | Runtime | `app/services/optimization/result.py` → `OptimizationSummary` |
| result.py:OptimizationSummary.get_top_n | print_optimization_report | Import/call/instantiation | Runtime | `app/services/optimization/result.py` → `OptimizationSummary.get_top_n` |
| result.py:OptimizationSummary.to_dataframe | No production caller found | Import/call/instantiation | None found | `app/services/optimization/result.py` → `OptimizationSummary.to_dataframe` |
| scoring.py:sharpe_score | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Import/call/instantiation | Runtime | `app/services/optimization/scoring.py` → `sharpe_score` |
| scoring.py:sortino_score | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Import/call/instantiation | Runtime | `app/services/optimization/scoring.py` → `sortino_score` |
| scoring.py:calmar_score | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Import/call/instantiation | Runtime | `app/services/optimization/scoring.py` → `calmar_score` |
| scoring.py:profit_factor_score | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Import/call/instantiation | Runtime | `app/services/optimization/scoring.py` → `profit_factor_score` |
| scoring.py:total_return_score | core.OBJECTIVE_FUNCTIONS and/or optimization methods | Import/call/instantiation | Runtime | `app/services/optimization/scoring.py` → `total_return_score` |
| scoring.py:custom_score | No runtime caller; stale unit test | Import/call/instantiation | Test/example | `app/services/optimization/scoring.py` → `custom_score` |
| scoring.py:optimization_get_scoring_func | optimization_* wrappers only | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/scoring.py` → `optimization_get_scoring_func` |
| splitters.py:SplitterResult | Stale unit tests and scripts/examples/tools/README.md | Import/call/instantiation | Test/example | `app/services/optimization/splitters.py` → `SplitterResult` |
| splitters.py:SplitterResult.plots | No caller found | Import/call/instantiation | None found | `app/services/optimization/splitters.py` → `SplitterResult.plots` |
| splitters.py:splitter_from_rolling | Stale unit tests and scripts/examples/tools/README.md | Import/call/instantiation | Test/example | `app/services/optimization/splitters.py` → `splitter_from_rolling` |
| splitters.py:splitter_from_expanding | Stale unit tests and scripts/examples/tools/README.md | Import/call/instantiation | Test/example | `app/services/optimization/splitters.py` → `splitter_from_expanding` |
| splitters.py:splitter_rolling_split | Stale unit tests and scripts/examples/tools/README.md | Import/call/instantiation | Test/example | `app/services/optimization/splitters.py` → `splitter_rolling_split` |
| portfolio_optimizer.py:PortfolioOptimizerResult | Documentation only; no code caller found | Import/call/instantiation | None found | `app/services/optimization/portfolio_optimizer.py` → `PortfolioOptimizerResult` |
| portfolio_optimizer.py:PortfolioOptimizerResult.plot | Documentation only; no code caller found | Import/call/instantiation | None found | `app/services/optimization/portfolio_optimizer.py` → `PortfolioOptimizerResult.plot` |
| portfolio_optimizer.py:pfo_from_optimize_func | Documentation only; no code caller found | Import/call/instantiation | None found | `app/services/optimization/portfolio_optimizer.py` → `pfo_from_optimize_func` |
| portfolio_optimizer.py:pfo_plot | Documentation only; no code caller found | Import/call/instantiation | None found | `app/services/optimization/portfolio_optimizer.py` → `pfo_plot` |
| execution.py:load_strategy_from_path | run_strategy_backtest_from_path | Import/call/instantiation | Runtime | `app/services/optimization/execution.py` → `load_strategy_from_path` |
| execution.py:normalize_engine_type | run_strategy_backtest | Import/call/instantiation | Runtime | `app/services/optimization/execution.py` → `normalize_engine_type` |
| execution.py:EngineOptimizationResult | run_strategy_backtest | Import/call/instantiation | Runtime | `app/services/optimization/execution.py` → `EngineOptimizationResult` |
| execution.py:EngineOptimizationResult.summary | all optimization methods | Import/call/instantiation | Runtime | `app/services/optimization/execution.py` → `EngineOptimizationResult.summary` |
| execution.py:run_strategy_backtest | grid, random, Bayesian, genetic and walk_forward | Import/call/instantiation | Runtime | `app/services/optimization/execution.py` → `run_strategy_backtest` |
| execution.py:run_strategy_backtest_from_path | parallel branches of grid/random | Import/call/instantiation | Runtime | `app/services/optimization/execution.py` → `run_strategy_backtest_from_path` |
| methods/__init__.py:bayesian_optimization | No production caller found | Re-export | Indirect/dynamic | `app/services/optimization/methods/__init__.py` → `bayesian_optimization` |
| methods/__init__.py:genetic_algorithm | No production caller found | Re-export | Indirect/dynamic | `app/services/optimization/methods/__init__.py` → `genetic_algorithm` |
| methods/__init__.py:grid_search | No production caller found | Re-export | Indirect/dynamic | `app/services/optimization/methods/__init__.py` → `grid_search` |
| methods/__init__.py:random_search | No production caller found | Re-export | Indirect/dynamic | `app/services/optimization/methods/__init__.py` → `random_search` |
| methods/__init__.py:walk_forward_optimization | No production caller found | Re-export | Indirect/dynamic | `app/services/optimization/methods/__init__.py` → `walk_forward_optimization` |
| methods/grid_search.py:grid_search | core.run_optimization_task; walk_forward.walk_forward | Import/call/instantiation | Runtime | `app/services/optimization/methods/grid_search.py` → `grid_search` |
| methods/grid_search.py:optimization_grid_search | No production caller; dynamically discoverable only through _common resolver | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/methods/grid_search.py` → `optimization_grid_search` |
| methods/random_search.py:random_search | core.run_optimization_task | Import/call/instantiation | Runtime | `app/services/optimization/methods/random_search.py` → `random_search` |
| methods/random_search.py:optimization_random_search | No production caller; dynamically discoverable only through _common resolver | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/methods/random_search.py` → `optimization_random_search` |
| methods/bayesian.py:bayesian_optimization | core.run_optimization_task | Import/call/instantiation | Runtime | `app/services/optimization/methods/bayesian.py` → `bayesian_optimization` |
| methods/bayesian.py:optimization_bayesian | No production caller; dynamically discoverable only through _common resolver | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/methods/bayesian.py` → `optimization_bayesian` |
| methods/genetic.py:genetic_algorithm | core.run_optimization_task | Import/call/instantiation | Runtime | `app/services/optimization/methods/genetic.py` → `genetic_algorithm` |
| methods/genetic.py:optimization_genetic | No production caller; dynamically discoverable only through _common resolver | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/methods/genetic.py` → `optimization_genetic` |
| walk_forward.py:walk_forward | core.run_walk_forward_task | Import/call/instantiation | Runtime | `app/services/optimization/walk_forward.py` → `walk_forward` |
| walk_forward.py:print_optimization_report | No caller found | Import/call/instantiation | None found | `app/services/optimization/walk_forward.py` → `print_optimization_report` |
| walk_forward.py:walk_forward_optimization | methods lazy export intends to expose it but target import is broken | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/walk_forward.py` → `walk_forward_optimization` |
| walk_forward.py:optimization_walk_forward | No production caller; dynamically discoverable wrapper | Import/call/instantiation | Indirect/dynamic | `app/services/optimization/walk_forward.py` → `optimization_walk_forward` |
| parallel.py:ProgressTracker | parallel.py internals and/or stale test_optimization.py | Import/call/instantiation | Test/example | `app/services/optimization/parallel.py` → `ProgressTracker` |
| parallel.py:ProgressTracker.update | parallel.py internals and/or stale test_optimization.py | Import/call/instantiation | Test/example | `app/services/optimization/parallel.py` → `ProgressTracker.update` |
| parallel.py:parallel_grid_search | parallel.py internals and/or stale test_optimization.py | Import/call/instantiation | Test/example | `app/services/optimization/parallel.py` → `parallel_grid_search` |
| parallel.py:parallel_random_search | No code caller found | Import/call/instantiation | None found | `app/services/optimization/parallel.py` → `parallel_random_search` |
| parallel.py:parallel_walk_forward | No code caller found | Import/call/instantiation | None found | `app/services/optimization/parallel.py` → `parallel_walk_forward` |
| parallel.py:compare_parallel_speedup | No code caller found | Import/call/instantiation | None found | `app/services/optimization/parallel.py` → `compare_parallel_speedup` |
| parallel.py:get_optimal_n_jobs | No code caller found | Import/call/instantiation | None found | `app/services/optimization/parallel.py` → `get_optimal_n_jobs` |
| parallel.py:estimate_completion_time | No code caller found | Import/call/instantiation | None found | `app/services/optimization/parallel.py` → `estimate_completion_time` |
| parallel.py:analyze_parallel_results | No code caller found | Import/call/instantiation | None found | `app/services/optimization/parallel.py` → `analyze_parallel_results` |
| parallel.py:analyze_walk_forward_results | No code caller found | Import/call/instantiation | None found | `app/services/optimization/parallel.py` → `analyze_walk_forward_results` |
| monte_carlo.py:MonteCarloResult | No caller found | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `MonteCarloResult` |
| monte_carlo.py:MonteCarloResult.calculate_statistics | monte_carlo_analysis | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `MonteCarloResult.calculate_statistics` |
| monte_carlo.py:MonteCarloResult.get_summary | No caller found | Import/call/instantiation | None found | `app/services/optimization/monte_carlo.py` → `MonteCarloResult.get_summary` |
| monte_carlo.py:ParametricSimulationResult | Corresponding simulation function | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `ParametricSimulationResult` |
| monte_carlo.py:PositionSizingResult | Corresponding simulation function | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `PositionSizingResult` |
| monte_carlo.py:ConsecutiveLosingScenarioResult | Corresponding simulation function | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `ConsecutiveLosingScenarioResult` |
| monte_carlo.py:ProfitTargetScenarioResult | Corresponding simulation function | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `ProfitTargetScenarioResult` |
| monte_carlo.py:monte_carlo_analysis | core.run_monte_carlo_task and Monte Carlo helper functions | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `monte_carlo_analysis` |
| monte_carlo.py:shuffle_trades_simulation | monte_carlo_analysis | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `shuffle_trades_simulation` |
| monte_carlo.py:resample_returns_simulation | monte_carlo_analysis | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `resample_returns_simulation` |
| monte_carlo.py:bootstrap_simulation | monte_carlo_analysis | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `bootstrap_simulation` |
| monte_carlo.py:calculate_probability_of_ruin | Stale unit tests / internal helper calls only | Import/call/instantiation | Test/example | `app/services/optimization/monte_carlo.py` → `calculate_probability_of_ruin` |
| monte_carlo.py:calculate_confidence_intervals | No caller found | Import/call/instantiation | None found | `app/services/optimization/monte_carlo.py` → `calculate_confidence_intervals` |
| monte_carlo.py:compare_simulation_methods | Stale unit tests / internal helper calls only | Import/call/instantiation | Test/example | `app/services/optimization/monte_carlo.py` → `compare_simulation_methods` |
| monte_carlo.py:assess_strategy_robustness | Stale unit tests / internal helper calls only | Import/call/instantiation | Test/example | `app/services/optimization/monte_carlo.py` → `assess_strategy_robustness` |
| monte_carlo.py:parametric_simulation | app/api/routes/optimization.py | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `parametric_simulation` |
| monte_carlo.py:position_sizing_simulation | app/api/routes/optimization.py | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `position_sizing_simulation` |
| monte_carlo.py:consecutive_losing_simulation | app/api/routes/optimization.py | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `consecutive_losing_simulation` |
| monte_carlo.py:profit_target_simulation | app/api/routes/optimization.py | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `profit_target_simulation` |
| monte_carlo.py:random_win_rate_simulation | app/api/routes/optimization.py | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `random_win_rate_simulation` |
| monte_carlo.py:robustness_simulation | app/api/routes/optimization.py | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `robustness_simulation` |
| monte_carlo.py:multi_entry_simulation | app/api/routes/optimization.py | Import/call/instantiation | Runtime | `app/services/optimization/monte_carlo.py` → `multi_entry_simulation` |
| optimization_tools.py:build_optimization_report | No code caller found | Import/call/instantiation | None found | `app/services/optimization/optimization_tools.py` → `build_optimization_report` |
| optimization_tools.py:calculate_parameter_stability | Stale tests/examples only | Import/call/instantiation | Test/example | `app/services/optimization/optimization_tools.py` → `calculate_parameter_stability` |
| optimization_tools.py:compare_optimization_runs | Stale tests/examples only | Import/call/instantiation | Test/example | `app/services/optimization/optimization_tools.py` → `compare_optimization_runs` |
| optimization_tools.py:detect_overfit_parameters | Stale tests/examples only | Import/call/instantiation | Test/example | `app/services/optimization/optimization_tools.py` → `detect_overfit_parameters` |
| optimization_tools.py:rank_parameter_sets | No code caller found | Import/call/instantiation | None found | `app/services/optimization/optimization_tools.py` → `rank_parameter_sets` |
| optimization_tools.py:run_parameter_sweep | Stale tests/examples only | Import/call/instantiation | Test/example | `app/services/optimization/optimization_tools.py` → `run_parameter_sweep` |
| optimization_tools.py:run_walk_forward_matrix | No code caller found | Import/call/instantiation | None found | `app/services/optimization/optimization_tools.py` → `run_walk_forward_matrix` |
| optimization_tools.py:run_walk_forward_optimization | No code caller found | Import/call/instantiation | None found | `app/services/optimization/optimization_tools.py` → `run_walk_forward_optimization` |
| optimization_tools.py:save_optimization_result | No code caller found | Import/call/instantiation | None found | `app/services/optimization/optimization_tools.py` → `save_optimization_result` |
| robustness_tools.py:build_robustness_report | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `build_robustness_report` |
| robustness_tools.py:calculate_robustness_score | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `calculate_robustness_score` |
| robustness_tools.py:run_combined_monte_carlo | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_combined_monte_carlo` |
| robustness_tools.py:run_commission_stress_test | Stale tests/examples only | Import/call/instantiation | Test/example | `app/services/optimization/robustness_tools.py` → `run_commission_stress_test` |
| robustness_tools.py:run_cross_market_test | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_cross_market_test` |
| robustness_tools.py:run_cross_timeframe_test | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_cross_timeframe_test` |
| robustness_tools.py:run_randomize_history_mc | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_randomize_history_mc` |
| robustness_tools.py:run_randomize_parameters_mc | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_randomize_parameters_mc` |
| robustness_tools.py:run_randomize_trade_order_mc | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_randomize_trade_order_mc` |
| robustness_tools.py:run_resample_trades_mc | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_resample_trades_mc` |
| robustness_tools.py:run_second_oos_test | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_second_oos_test` |
| robustness_tools.py:run_skip_trades_mc | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_skip_trades_mc` |
| robustness_tools.py:run_slippage_stress_test | Stale tests/examples only | Import/call/instantiation | Test/example | `app/services/optimization/robustness_tools.py` → `run_slippage_stress_test` |
| robustness_tools.py:run_spread_stress_test | Stale tests/examples only | Import/call/instantiation | Test/example | `app/services/optimization/robustness_tools.py` → `run_spread_stress_test` |
| robustness_tools.py:run_third_oos_test | No code caller found | Import/call/instantiation | None found | `app/services/optimization/robustness_tools.py` → `run_third_oos_test` |
| core.py:BacktestDatabase | core tasks | Import/call/instantiation | Runtime | `app/services/optimization/core.py` → `BacktestDatabase` |
| core.py:BacktestDatabase.save_result | run_optimization_task | Import/call/instantiation | Runtime | `app/services/optimization/core.py` → `BacktestDatabase.save_result` |
| core.py:BacktestDatabase.load_result | run_monte_carlo_task | Import/call/instantiation | Runtime | `app/services/optimization/core.py` → `BacktestDatabase.load_result` |
| core.py:OBJECTIVE_FUNCTIONS | all core tasks | Import/call/instantiation | Runtime | `app/services/optimization/core.py` → `OBJECTIVE_FUNCTIONS` |
| core.py:run_optimization_task | FastAPI POST /api/optimization/runs background task | Import/call/instantiation | Runtime | `app/services/optimization/core.py` → `run_optimization_task` |
| core.py:run_walk_forward_task | FastAPI POST /api/optimization/walk-forward background task | Import/call/instantiation | Runtime | `app/services/optimization/core.py` → `run_walk_forward_task` |
| core.py:run_monte_carlo_task | FastAPI POST /api/optimization/monte-carlo background task | Import/call/instantiation | Runtime | `app/services/optimization/core.py` → `run_monte_carlo_task` |

## 8. Cross-Domain Surface

This domain is not isolated. Its runtime path reaches into API, database, data/broker, strategy, research, simulation and analytics packages.

**Outbound (this domain depends on):**

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --- | --- | --- | --- |
| API/backtest | `portfolio_run` simulation entry point | `execution.py:run_strategy_backtest` | `from app.api.routes.backtest import portfolio_run` |
| Analytics | returns, metrics, ratios and drawdowns | `execution.py` result construction/mapping | `app.services.analytics` imports |
| Strategy | `BaseStrategy`; strategy loading/storage | `execution.py`; `core.py`; method type contracts | `app.services.strategy`; `app.services.strategy.storage` |
| Data/brokers | OHLCV loading, Dukascopy and MT5 bars | `core.py` background tasks | `app.services.data`; `app.services.brokers` |
| Research | unsupervised market-structure analysis | `core.py` optional preprocessing/context | `UnsupervisedResearchService` and config |
| Security | optimization permission checks | `core.py` before strategy execution | `check_permission`; `Resources.OPTIMIZATION` |
| Database | optimization/Monte Carlo status and result persistence | `core.py`; route layer; `monte_carlo.py:robustness_simulation` | `DatabaseManager`; dynamic backtest repository import |
| Utilities | logger and standard response metadata | Most modules; agent tools | `app.services.utils.logger`; `utils.standard` |
| Data frame abstraction | `Data` wrapper | `portfolio_optimizer.py` | `app.services.data.frames.Data` |

**Inbound (others depend on this domain):**

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| --- | --- | --- | --- |
| FastAPI application | optimization router registration | Expose `/api/optimization/*` endpoints | `app/api/main.py` imports and includes `app.api.routes.optimization` |
| Optimization API route | core tasks, models and Monte Carlo functions | Start/retrieve/cancel jobs and run scenario endpoints | `app/api/routes/optimization.py` imports |
| Internal optimization methods | execution, scoring and result contracts | Evaluate and rank candidates | `methods/*.py` imports |
| Walk-forward implementation | grid search, execution, scoring | Train/OOS rolling evaluation | `walk_forward.py` imports |
| Stale unit tests | many root and nonexistent symbols | Intended tests, but collection is incompatible | `tests/unit/app/services/optimization/test_optimization*.py` |
| Stale usage script | root symbols and nonexistent persistence package | Illustrative examples, currently non-executable | `tests/usage/app/services/09_optimization.py` |
| Documentation/example README | splitter/portfolio helper names | Documentation only | `scripts/examples/tools/README.md`; upgrade-plan docs |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| --- | --- | --- | --- | --- |
| `optimization_tools.run_parameter_sweep` | `methods.grid_search/random_search` and `core.run_optimization_task` | Same capability name, but the tool only packages a request while the method/core path executes. | Tool body delegates only to `package_optimization_request`; concrete execution exists elsewhere. | Callers can mistake packaging success for optimization success. |
| `optimization_tools.run_walk_forward_optimization` | `walk_forward.walk_forward` / `core.run_walk_forward_task` | Agent tool packages; runtime path executes. | Separate files and no dispatcher between them. | Disconnected public contract. |
| `robustness_tools.run_*` Monte Carlo/stress names | `monte_carlo.py` concrete simulations | Names overlap, implementations do not connect. | Fourteen robustness tools return packaged requests. | False capability signal and duplicated vocabulary. |
| `parallel.parallel_grid_search` | `methods.grid_search.grid_search(max_workers>1)` | Two separate process-pool grid implementations. | Both create Cartesian products and submit backtests. | Divergent result schemas and failure handling. |
| `parallel.parallel_random_search` | `methods.random_search.random_search(max_workers>1)` | Two separate parallel random-search implementations. | Separate worker/result dictionaries versus OptimizationSummary. | Maintenance and behavior drift. |
| `parallel.parallel_walk_forward` | `walk_forward.walk_forward` | Alternative walk-forward implementation with different callback/result contracts. | No shared coordinator or caller. | Unclear canonical workflow. |
| `PortfolioOptimizerResult.plot` | `pfo_plot` | Thin wrapper adds no behavior. | `pfo_plot` directly calls `.plot()`. | Extra public surface. |
| `walk_forward`, `walk_forward_optimization`, `optimization_walk_forward` | Same core capability via function, alias and wrapper. | Three names with different discovery paths. | `walk_forward.py` definitions plus methods lazy export. | Ambiguous entry point; one lazy path is broken. |
| `EngineOptimizationResult` | `OptimizationResult` | One stores a backtest outcome; the other wraps it with parameters/score. | Nested result layers with similar names. | Contract confusion, especially for Monte Carlo persistence. |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| --- | --- | --- | --- | --- |
| Root package agent tools (24 exports) | No production caller found; most execute no operation beyond packaging. | Full-repository import/call search; root export inspection; standardization helper inspection; docs/tests/examples checked. | High for static callers; Medium for external agents not stored in repo | `__init__.py`; `optimization_tools.py`; `robustness_tools.py` |
| `save_optimization_result`; `build_optimization_report`; `build_robustness_report` | Names imply writes/building, but return packaged requests only. | Function bodies and all repo call sites searched. | High | Direct function bodies |
| `rank_parameter_sets`; `calculate_robustness_score` | Real small calculations but no caller found. | Symbol search across repository, tests, examples and docs. | High | Only definition/export/documentation hits |
| `splitters.py` public surface | Only stale tests and documentation; not used by `walk_forward.py`. | Import/call search plus walk-forward dependency inspection. | High | `splitters.py`; search hits |
| `portfolio_optimizer.py` | Documentation-only periodic allocation helper. | Imports/calls and dynamic registry searched. | High | Only definition/docs hits |
| Most of `parallel.py` | Standalone alternative implementation not called by core/methods. | Imports/calls and test references searched. | High | `parallel_grid_search` has only stale test; other helpers have no callers |
| `optimization_*` method wrappers | No production caller; lower-level dynamic discovery is possible but not observed. | Direct symbol searches and `_common.__getattr__` inspection. | Medium | Wrapper definitions; no call hits |
| `print_optimization_report` | Console-only report with no caller. | Import/call search. | High | `walk_forward.py:print_optimization_report` |
| `MonteCarloResult.get_summary` | No caller found. | Method-call and symbol search. | High | `monte_carlo.py` |
| `calculate_confidence_intervals` | Useful helper but no external caller found. | Symbol/call search. | High | `monte_carlo.py` only |
| `compare_simulation_methods`; `assess_strategy_robustness` | Referenced only by stale tests; not API-exposed. | Full-repository symbol search. | High | Definition and stale test hits |
| `WalkForwardWindow`; `WalkForwardResponse` | Not used by the current walk-forward API, which returns `OptimizationResponse` and persists no windows. | Route/model import search. | High | `models.py`; `app/api/routes/optimization.py` |
| `methods.__init__.py:walk_forward_optimization` | Lazy mapping constructs an invalid doubly-prefixed module path. | Direct code inspection and import-path expansion. | High | `methods/__init__.py:_EXPORT_MODULES` and `__getattr__` |

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --- | --- | --- | --- |
| Historical Monte Carlo background job | `BacktestDatabase` has no real persistence implementation. | Every submitted job fails before simulation. | `core.py:BacktestDatabase.load_result`; `run_monte_carlo_task` |
| Optimization-to-Monte-Carlo handoff | Optimization calls a no-op `save_result`, so historical results are not available to Monte Carlo. | Even successful optimization cannot populate the expected store. | `core.py:run_optimization_task`; `BacktestDatabase.save_result` |
| Walk-forward result lifecycle | Computed summary is assigned to `_` and no windows are persisted. | Run may be marked completed without retrievable results. | `core.py:run_walk_forward_task` |
| Agent tool execution | Packaged requests have no dispatcher/consumer. | Success envelopes represent preparation, not execution. | `optimization_tools.py`; `robustness_tools.py`; no caller/consumer hits |
| Default MT5 optimization/data path | `pd.DataFrame` is referenced without pandas import in both core and optimization API route. | Default `data_source='mt5'` requests can fail at runtime. | `models.py` defaults; `core.py`; `app/api/routes/optimization.py` |
| Historical Monte Carlo result contract | Trade simulations call `result.get_trades_df()`, but `EngineOptimizationResult` exposes `.trades` and no such method. | A future non-None loaded engine result would still be incompatible. | `monte_carlo.py`; `execution.py:EngineOptimizationResult` |
| Walk-forward parallel setting | `WalkForwardRequest.n_jobs` is persisted but not passed to `walk_forward`/`grid_search`. | Requested parallelism has no effect. | `models.py`; route/core/walk_forward call chain |
| Bayesian/genetic parallel setting | `max_workers` is explicitly ignored. | API `n_jobs` does not control these methods. | `methods/bayesian.py`; `methods/genetic.py` |
| Cancellation | API cancellation changes DB status only; core task does not check cancellation. | Background compute may continue after a cancelled status. | `app/api/routes/optimization.py:cancel_optimization`; `core.py` loops/callbacks |
| Tests/examples | Current files target nonexistent packages, symbols, fields and return contracts. | They do not validate the current runtime and several fail at import/collection. | `tests/unit/app/services/optimization/*`; `tests/usage/app/services/09_optimization.py` |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| --- | --- | --- | --- | --- |
| V1-ISSUE-OPT-001 | Historical Monte Carlo storage adapter is a no-op. | `core.py:BacktestDatabase` | Breaks the API Monte Carlo job and optimization-to-MC handoff. | Both methods contain no persistence logic; load always returns None. |
| V1-ISSUE-OPT-002 | Walk-forward results are discarded while status becomes completed. | `core.py:run_walk_forward_task` | No auditable/retrievable window results. | Explicit `_ = walk_forward(...)` and TODO comment. |
| V1-ISSUE-OPT-003 | Default MT5 branch references undefined `pd`. | `core.py`; `app/api/routes/optimization.py` | Default optimization, walk-forward and standalone unsupervised MT5 paths can fail. | Models default `data_source` to mt5; neither file imports pandas at module scope. |
| V1-ISSUE-OPT-004 | Agent-facing run/save/build functions mostly package requests only. | `optimization_tools.py`; `robustness_tools.py` | Public names overstate delivered behavior. | Bodies delegate to `package_optimization_request`. |
| V1-ISSUE-OPT-005 | No consumer exists for packaged optimization requests. | Root tool surface | Agent workflow is disconnected. | Full-repository caller/registry/config search found none. |
| V1-ISSUE-OPT-006 | Historical Monte Carlo expects `get_trades_df`, absent from engine result. | `monte_carlo.py`; `execution.py` | Result contracts are incompatible. | Direct attribute/method comparison. |
| V1-ISSUE-OPT-007 | Lazy walk-forward method export builds invalid module path. | `methods/__init__.py` | Import through `methods.walk_forward_optimization` fails. | Absolute module name is incorrectly prefixed with `app.services.optimization.methods`. |
| V1-ISSUE-OPT-008 | Duplicate grid/random/walk-forward implementations. | `parallel.py`; `methods/*.py`; `walk_forward.py` | Different contracts and failure behavior can drift. | Overlapping parameter generation/process-pool/window logic. |
| V1-ISSUE-OPT-009 | Bayesian/genetic `max_workers` is ignored. | `methods/bayesian.py`; `methods/genetic.py` | Advertised/requested parallelism is ineffective. | Assignment `_ = max_workers`; Bayesian backend forced to one job. |
| V1-ISSUE-OPT-010 | Walk-forward `n_jobs` is not propagated. | Route → core → walk_forward | Execution is serial regardless of request. | Call chain omits the value. |
| V1-ISSUE-OPT-011 | Monte Carlo module contains several unrelated simulation families. | `monte_carlo.py` | High change risk and unclear responsibility. | 1,809 lines mixing historical MC, parametric risk, sizing, streaks, targets, random pairs, robustness and multi-entry. |
| V1-ISSUE-OPT-012 | Optimization execution imports an API route. | `execution.py:run_strategy_backtest` | Service behavior depends on API-layer module import and route-side composition. | `from app.api.routes.backtest import portfolio_run`. |
| V1-ISSUE-OPT-013 | Robustness repository failures are swallowed. | `monte_carlo.py:robustness_simulation` | Root cause is hidden and converted into a later response-construction failure. | Broad `except Exception: return None`. |
| V1-ISSUE-OPT-014 | Parallel helpers assume non-empty results and use nested process factories. | `parallel.py` | Empty/failed searches can index `results[0]`; spawn platforms may fail to pickle closures. | Direct control-flow inspection. |
| V1-ISSUE-OPT-015 | Tests and usage examples describe another API. | `tests/unit/...`; `tests/usage/...` | Coverage and examples are not trustworthy evidence for current production behavior. | Missing imports, different fields, positional calls to kwargs-only tools and incompatible result keys. |
| V1-ISSUE-OPT-016 | `splitter_from_expanding` is not expanding. | `splitters.py` | Name does not match behavior. | It delegates to rolling splitter with a fixed minimum length. |
| V1-ISSUE-OPT-017 | Cancellation does not interrupt computation. | API cancel route and core tasks | Status may say cancelled while work continues and later overwrites status. | No cancellation check inside tasks/method loops. |
| V1-ISSUE-OPT-018 | Tool metadata contradicts actual capability semantics. | `_common.py:optimization_tool_result`; tool docstrings | Consumers cannot rely on risk/read-only/write declarations. | Envelope spec is hard-coded while write-named functions do not write and simulation functions are described as no-side-effect. |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| V1-CAP-OPT-001 | Optimization API contracts | `models.py` request/response classes | V1-WF-OPT-001/002/003/004/005 | Used | Essential | Current route boundary. |
| V1-CAP-OPT-002 | Grid parameter search | `methods/grid_search.py:grid_search` | V1-WF-OPT-001/002 | Used | Essential | Sequential and optional process execution. |
| V1-CAP-OPT-003 | Random parameter search | `methods/random_search.py:random_search` | V1-WF-OPT-001 | Used | Essential | Numeric min/max distributions only. |
| V1-CAP-OPT-004 | Bayesian parameter search | `methods/bayesian.py:bayesian_optimization` | V1-WF-OPT-001 | Used | Useful | Requires scikit-optimize; workers ignored. |
| V1-CAP-OPT-005 | Genetic parameter search | `methods/genetic.py:genetic_algorithm` | V1-WF-OPT-001 | Used | Useful | NumPy implementation; workers ignored. |
| V1-CAP-OPT-006 | Candidate simulation and metric extraction | `execution.py:run_strategy_backtest`; `EngineOptimizationResult` | V1-WF-OPT-001/002 | Used | Essential | Runs through API-layer portfolio_run. |
| V1-CAP-OPT-007 | Objective scoring and candidate ranking | `scoring.py`; `result.py` | V1-WF-OPT-001/002 | Used | Supporting | Attribute-based scores. |
| V1-CAP-OPT-008 | Serial walk-forward optimization | `walk_forward.py:walk_forward` | V1-WF-OPT-002 | Used | Essential | Result persistence missing. |
| V1-CAP-OPT-009 | Historical trade Monte Carlo | `monte_carlo_analysis`; shuffle/resample/bootstrap | V1-WF-OPT-003 | Used | Essential | API workflow broken by persistence and contract gaps. |
| V1-CAP-OPT-010 | Parametric risk Monte Carlo | `parametric_simulation` | V1-WF-OPT-004 | Used | Essential | Direct API endpoint. |
| V1-CAP-OPT-011 | Position-sizing comparison | `position_sizing_simulation` | V1-WF-OPT-004 | Used | Useful | Linear versus compounding. |
| V1-CAP-OPT-012 | Loss-streak and profit-target scenarios | `consecutive_losing_simulation`; `profit_target_simulation` | V1-WF-OPT-004 | Used | Useful | Direct API endpoints. |
| V1-CAP-OPT-013 | Random win-rate/RRR and multi-entry scenarios | `random_win_rate_simulation`; `multi_entry_simulation` | V1-WF-OPT-004 | Used | Useful | Direct API endpoints. |
| V1-CAP-OPT-014 | Trade-history robustness stress | `robustness_simulation` | V1-WF-OPT-005 | Used | Useful | Repository failures are obscured. |
| V1-CAP-OPT-015 | Agent optimization request packaging | `optimization_tools.py` | V1-WF-OPT-006 | Test-only | Questionable | No execution consumer. |
| V1-CAP-OPT-016 | Agent robustness request packaging | `robustness_tools.py` | V1-WF-OPT-006 | Test-only | Questionable | No execution consumer. |
| V1-CAP-OPT-017 | Generic rolling split utilities | `splitters.py` | V1-WF-OPT-007 | Test-only | Questionable | Not used by canonical walk-forward. |
| V1-CAP-OPT-018 | Standalone parallel optimization utilities | `parallel.py` | V1-WF-OPT-007 | Test-only | Questionable | Duplicates method-level parallelism. |
| V1-CAP-OPT-019 | Periodic portfolio allocation callback | `portfolio_optimizer.py` | V1-WF-OPT-007 | Unused | Questionable | No system caller. |
| V1-CAP-OPT-020 | Optional unsupervised context before optimization | `core.py` + research service + model fields | V1-WF-OPT-001/002 | Used | Useful | Persists research report/context with optimization status. |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

* The concrete method implementations for grid, random, Bayesian and genetic parameter search.
* The common simulation-backed candidate execution and scalar result contract.
* The serial walk-forward calculation logic, provided its result lifecycle is considered separately from this audit.
* The direct parametric/scenario calculators and their API request/response contracts.
* The optional unsupervised-analysis integration and optimization status/result persistence calls.

### Behaviour that exists but is disconnected

* The 24 root agent-facing tools are largely request packagers with no execution consumer.
* Generic splitters, standalone parallel searches and periodic portfolio allocation have no confirmed runtime caller.
* Historical Monte Carlo helper logic exists, but its API workflow cannot obtain a backtest result.
* Walk-forward response models exist, but the API does not return or persist them.

### Likely dead weight or no demonstrated value

* No-op `BacktestDatabase.save_result/load_result`.
* Packaging-only `save_*` and `build_*` functions without downstream handling.
* Thin `pfo_plot` wrapper, console-only report function and uncalled summary/CI helpers.
* Test files whose imports are wrapped in broad exception suppression and therefore test nothing when modules are absent.

### Duplicated responsibilities

* Two grid-search and two random-search parallel implementations.
* Two walk-forward implementations plus an alias and wrapper.
* Concrete Monte Carlo/stress functions and similarly named packaging-only robustness tools.
* Multiple result layers and overlapping entry-point names.

### Important uncertainties requiring manual confirmation

* Whether an external agent runtime, not stored in this repository, imports the 24 root tools.
* Whether deployment injects pandas into module globals or patches `BacktestDatabase`—no such mechanism exists in the inspected repository.
* Whether the database manager methods and backtest repository schemas match the result dictionaries built here.
* Whether process-based optimization succeeds on the target operating system with the actual strategy classes and data payloads.
* Whether API consumers rely on the current packaging-only success envelopes.

### Final validation

* Every Python file under `app/services/optimization` is represented.
* Every explicit `__init__.py` export was checked.
* The lazy method export map and placeholder export-standardization function were checked.
* Imports, calls, class instantiation, decorators/routes, dynamic lookups, repository imports, tests, examples and documentation references were searched across the available repository.
* Production/API usage is distinguished from stale test/example usage.
* No Version 2 requirements or redesign were introduced.
* No repository code was modified.
