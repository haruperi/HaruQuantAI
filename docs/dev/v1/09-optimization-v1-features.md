## FEAT-OPT-01: Shared optimization-service helpers (app.services.optimization._common)

| Function | Purpose |
|----------|---------|
| `service_strategy_class(strategy_class: Any) -> Any` | Normalize a strategy class or class factory. |
| `optimization_tool_result(tool_name: str, *, data: dict[str, Any] \| None = None, status: str = 'success', errors: list[str] \| None = None, warnings: list[str] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True, side_effects: list[str] \| None = None) -> dict[str, Any]` | Build the standard HaruQuant result envelope for optimization tools. |
| `optimization_business_payload(kwargs: dict[str, Any]) -> dict[str, Any]` | Strip common context fields from optimization request payloads. |
| `package_optimization_request(tool_name: str, kwargs: dict[str, Any]) -> dict[str, Any]` | Package an optimization request without executing compute-heavy jobs. |


## FEAT-OPT-02: Optimization Bayesian search algorithm (app.services.optimization.algorithms.bayesian)

| Function | Purpose |
|----------|---------|
| `BayesianOptimizationResult` (model) | Result of a Bayesian optimization sweep. |
| `bayesian_optimization(strategy_class: type[BaseStrategy], data, param_space: dict[str, tuple[float, float]], param_types: dict[str, str] \| None = None, n_iterations: int = 50, n_initial_points: int = 10, initial_balance: float = 10000.0, scoring_func: Callable[[BacktestResult], float] = sharpe_score, engine_type: str = 'vectorized', max_workers: int \| None = None, random_state: int \| None = None, verbose: bool = True, progress_callback: Callable \| None = None, symbol: str \| None = None) -> OptimizationSummary` | Bayesian optimization using Gaussian Processes. |
| `optimization_bayesian(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, max_candidates: int = 20, seed: int \| None = None, **kwargs: Any) -> dict[str, Any]` | User-facing wrapper for Bayesian parameter optimization. |


## FEAT-OPT-03: Optimization genetic search algorithm (app.services.optimization.algorithms.genetic)

| Function | Purpose |
|----------|---------|
| `GeneticAlgorithmResult` (model) | Result of a genetic algorithm optimization run. |
| `crossover(parent_a: dict[str, Any], parent_b: dict[str, Any], space: ParameterSpace, rng: random.Random) -> dict[str, Any]` | Combine parameters of two parents to produce an offspring. |
| `mutate(params: dict[str, Any], space: ParameterSpace, mutation_rate: float, rng: random.Random) -> dict[str, Any]` | Randomly mutate parameter values in a candidate dictionary. |
| `genetic_algorithm(strategy_class: type[BaseStrategy], data, param_ranges: dict[str, tuple[float, float]], param_types: dict[str, str] \| None = None, population_size: int = 50, generations: int = 30, mutation_rate: float = 0.1, crossover_rate: float = 0.8, elitism_ratio: float = 0.1, tournament_size: int = 3, initial_balance: float = 10000.0, scoring_func: Callable[[BacktestResult], float] = sharpe_score, engine_type: str = 'vectorized', max_workers: int \| None = None, random_state: int \| None = None, verbose: bool = True, progress_callback: Callable \| None = None, symbol: str \| None = None) -> OptimizationSummary` | Genetic algorithm optimization. |
| `optimization_genetic(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, population_size: int = 20, generations: int = 5, seed: int \| None = None, **kwargs: Any) -> dict[str, Any]` | User-facing wrapper for genetic algorithm parameter optimization. |


## FEAT-OPT-04: Optimization grid search algorithm (app.services.optimization.algorithms.grid)

| Function | Purpose |
|----------|---------|
| `check_constraints(params: dict[str, Any], constraints: list[str]) -> bool` | Evaluate all constraint expressions safely against candidate parameters. |
| `generate_parameter_grid(space: ParameterSpace) -> dict[str, list[Any]]` | Generate candidate value lists from parameter space definitions. |
| `grid_search(strategy_class: type[BaseStrategy], data, param_grid: dict[str, list[Any]], initial_balance: float = 10000.0, scoring_func: Callable[[BacktestResult], float] = sharpe_score, engine_type: str = 'vectorized', max_workers: int \| None = None, verbose: bool = True, progress_callback: Callable \| None = None, strategy_file_path: str \| None = None, symbol: str \| None = None, constraint: Callable[[dict[str, Any]], bool] \| None = None, random_subset: int \| None = None) -> OptimizationSummary` | Grid search over parameter space. |
| `parallel_grid_search(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, max_workers: int = 2, **kwargs: Any) -> OptimizationSummary` | Run parameter-grid candidate evaluations in parallel. |
| `optimization_grid_search(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, max_workers: int = 1, dry_run: bool = True, **kwargs: Any) -> dict[str, Any]` | User-facing wrapper for exhaustive parameter grid search. |


## FEAT-OPT-05: Optimization random search algorithm and Monte Carlo simulators (app.services.optimization.algorithms.random)

| Function | Purpose |
|----------|---------|
| `ManualPairInput` (model) | Manual win rate and reward/risk pair input. |
| `RandomWinRateRequest` (model) | Request for running random win-rate simulation sweeps. |
| `DistributionStats` (model) | Statistical summary of final balance distributions. |
| `RandomWinRateResult` (model) | Individual pair results of a win rate simulation. |
| `sample_parameter(p: Any, rng: random.Random) -> Any` | Sample a single parameter range value using the provided RNG. |
| `random_search(strategy_class: type[BaseStrategy], data, param_distributions: dict[str, tuple[Any, Any]], n_iter: int = 100, initial_balance: float = 10000.0, scoring_func: Callable[[BacktestResult], float] = sharpe_score, engine_type: str = 'vectorized', max_workers: int \| None = None, seed: int \| None = None, verbose: bool = True, progress_callback: Callable \| None = None, strategy_file_path: str \| None = None, symbol: str \| None = None) -> OptimizationSummary` | Random search over parameter space. |
| `parallel_random_search(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, max_candidates: int = 50, max_workers: int = 2, seed: int \| None = None, **kwargs: Any) -> OptimizationSummary` | Sample parameter combinations and run parallel sweeps. |
| `optimization_random_search(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, max_candidates: int = 50, seed: int \| None = None, sampler_method: Literal["pseudo", "sobol", "lhs"] = "pseudo", max_workers: int = 1, dry_run: bool = True, **kwargs: Any) -> dict[str, Any]` | User-facing wrapper for random parameter search. |
| `shuffle_trades_simulation(trades: list[dict[str, Any]], initial_balance: float = 10000.0, seed: int \| None = None) -> list[float]` | Randomize trade order while preserving individual trade outcomes. |
| `random_win_rate_simulation(win_rate: float, reward_risk_ratio: float, initial_balance: float = 10000.0, trade_count: int = 100, simulation_count: int = 1000, seed: int \| None = None) -> list[list[float]]` | Simulate trading outcomes with random win-rate and reward/risk parameters. |
| `monte_carlo_analysis(trades: list[dict[str, Any]], simulation_type: str = "shuffle_trades", simulation_count: int = 1000, initial_balance: float = 10000.0, seed: int \| None = None) -> list[list[float]]` | Run Monte Carlo analysis against a backtest result. |


## FEAT-OPT-06: Optimization Core (app.services.optimization.core)

| Function | Purpose |
|----------|---------|
| `BacktestDatabase.save_result(*args, **kwargs) -> None` | Save result dummy method. |
| `BacktestDatabase.load_result(*args, **kwargs) -> None` | Load result dummy method. |
| `run_optimization_task(optimization_id: int, user_id: int, strategy_id: int, request: OptimizationRequest, progress_manager=None) -> None` | Background task for parameter optimization. |
| `run_walk_forward_task(optimization_id: int, user_id: int, strategy_id: int, request: WalkForwardRequest, progress_manager=None) -> None` | Background task for walk-forward analysis. |


## FEAT-OPT-07: Deterministic error-code mapping for the optimization service boundary (app.services.optimization.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `OptimizationError` (exception) | Base exception for optimization domain errors. |
| `OptimizationValidationError` (exception) | Validation exception for optimization domain. |
| `to_optimization_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Optimization error payload. |


## FEAT-OPT-08: Optimization Service helpers and backtest adapters (app.services.optimization.helpers)

| Function | Purpose |
|----------|---------|
| `OptimizationExecutionError` (exception) | Execution error within the optimization service. |
| `EngineOptimizationResult` (dataclass) | Optimization-ready result contract built from engine outputs. |
| `strategy_id(strategy: Any) -> str` | Return the deterministic strategy identifier. |
| `normalize_engine_type(engine_type: str) -> str` | Normalize legacy engine labels to supported execution engine names. |
| `load_strategy_from_path(path: str, class_name: str) -> type[BaseStrategy]` | Dynamically load a strategy class from a file path. |
| `run_strategy_backtest(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameters: dict[str, Any], initial_balance: float = 10000.0, engine_type: str = "event_driven", **kwargs: Any) -> EngineOptimizationResult` | Run one optimization candidate through the backtest engine. |
| `run_strategy_backtest_from_path(file_path: str, class_name: str, symbols: list[str], timeframe: str, start: str, end: str, parameters: dict[str, Any], initial_balance: float = 10000.0, engine_type: str = "event_driven", **kwargs: Any) -> EngineOptimizationResult` | Load a strategy class from disk and run one candidate simulation. |
| `parameter_space_hash(parameter_space: ParameterSpace) -> str` | Generate a deterministic order-invariant SHA-256 hash of a space. |
| `get_active_parameters(parameters: dict[str, Any], space: ParameterSpace) -> dict[str, Any]` | Filter out inactive conditional parameters. |
| `build_candidate_hash(strategy_hash: str, data_hash: str, cost_model_hash: str, realism_profile_hash: str, objective_hash: str, engine_type: str, module_version: str, parameters: dict[str, Any], space: ParameterSpace) -> str` | Deterministically generate a candidate deduplication hash. |
| `select_best_candidate(results: list[OptimizationResult]) -> tuple[ParameterCandidate, float]` | Return the best candidate and its score from evaluated results. |
| `json_safe_serialize(obj: Any) -> Any` | Serialize an object into a JSON-safe representation. |
| `optimization_tool_context(**kwargs: Any) -> dict[str, Any]` | Extract standard request parameters from tool keyword arguments. |
| `EngineOptimizationResult.summary() -> dict[str, float]` | Small optimization-facing result contract built from Engine outputs. |


## FEAT-OPT-09: Optimization Service data models and schemas (app.services.optimization.models)

| Function | Purpose |
|----------|---------|
| `Contract.validate_metadata_structure(value: dict[str, Any]) -> dict[str, Any]` | Validate metadata namespacing and secret safety. |
| `Contract.validate_trace_identifiers() -> Contract` | Validate trace identifier fields. |
| `Contract.to_json() -> str` | Serialize this contract to deterministic canonical JSON. |
| `Contract.content_hash() -> str` | Calculate a stable SHA256 hash over business-data fields only. |
| `Contract.contract_hash() -> str` | Calculate SHA256 hash over the full serialized contract. |
| `Contract.check_compatibility(target_version: str) -> bool` | Check whether this contract version is compatible with a target. |
| `ParameterRange.validate_range_boundaries() -> ParameterRange` | Validate numeric boundaries, options, and fixed values. |
| `ParameterSpace` (model) | Defines the complete search space including constraints. |
| `ParameterCandidate` (model) | Represents a single evaluated or proposed parameter set. |
| `OptimizationResult` (model) | Represent one candidate optimization result. |
| `OptimizationSummary.top_n(n: int = 10) -> list[OptimizationResult]` | Return the top N candidates sorted by score descending. |
| `UnsupervisedConfigRequest` (model) | Optional unsupervised-analysis configuration for optimization runs. |
| `UnsupervisedRunSummary` (model) | Summary of unsupervised model runs attached to optimization. |
| `UnsupervisedAnalysisRequest` (model) | Request for running unsupervised clustering on optimization results. |
| `OptimizationRequest` (class) | Request package for running parameter optimization sweeps. |
| `OptimizationResultItem` (model) | Single item returned inside public optimization response payloads. |
| `OptimizationResponse` (class) | Official envelope returned by optimization public sweep methods. |
| `OptimizationRunDetails` (class) | Audit details representing a single saved optimization run record. |
| `SweepResult` (model) | Sweep result mapping data structure. |
| `PositionSizingRequest` (class) | Request for running position sizing simulations. |
| `WalkForwardWindow` (model) | Represents a single train-test split window. |
| `WalkForwardRequest` (class) | Request for executing Walk-Forward Analysis (WFA). |
| `WalkForwardResponse` (model) | Response from Walk-Forward Optimization. |
| `MonteCarloResult` (model) | Result of a Monte Carlo simulation run. |
| `MonteCarloRequest` (class) | Request for running trade-level Monte Carlo simulations. |
| `ParametricMonteCarloRequest` (class) | Request for running parametric Monte Carlo simulations. |
| `MonteCarloResponse` (class) | Monte Carlo analysis envelope response. |
| `ConsecutiveLosingRequest` (class) | Request to simulate consecutive losing streaks. |
| `ConsecutiveLosingScenario` (model) | Result scenario for consecutive losing simulation. |
| `ConsecutiveLosingResponse` (class) | Response containing simulated consecutive losing streak details. |
| `ProfitTargetRequest` (model) | Request to calculate probability of reaching a profit target. |
| `ProfitTargetResult` (model) | Individual scenario results for profit target simulations. |
| `ProfitTargetResponse` (class) | Response containing profit target probability estimates. |
| `MultiEntryRequest` (class) | Request to simulate multi-entry strategy parameters. |
| `MultiEntryScenarioResult` (model) | Results of a multi-entry grid simulation scenario. |
| `MultiEntryResponse` (model) | Response containing results for 1, 2, and 3 trade entry scenarios. |
| `RobustnessRequest` (class) | Request for running robustness checks against evaluated strategies. |
| `RobustnessStats` (model) | Summary statistics from Robustness simulation. |
| `RobustnessResponse` (model) | Response containing Robustness simulation results. |
| `SplitterResult` (model) | Data model holding train/test split index windows. |
| `ConsecutiveLosingScenarioResult` (model) | Model holding details of a consecutive loss simulation run. |
| `ProfitTargetScenarioResult` (model) | Model holding details of a profit target simulation run. |
| `PortfolioOptimizerResult` (model) | Portfolio manager allocation weight outputs. |
| `ParameterRange` (model) | Parameter range for optimization. |
| `RandomWinRatePair` (model) | Statistics for a WinRate/RRR pair used in simulation. |
| `RandomWinRateResponse` (model) | Response containing Random Win Rate simulation results. |


## FEAT-OPT-10: Monte Carlo Simulation Module (app.services.optimization.monte_carlo)

| Function | Purpose |
|----------|---------|
| `MonteCarloResult.calculate_statistics() -> None` | Calculate statistical measures from simulation results. |
| `MonteCarloResult.get_summary() -> dict[str, Any]` | Get summary statistics. |
| `ParametricSimulationResult` (model) | Results from Parametric Monte Carlo simulation. |
| `resample_returns_simulation(result: BacktestResult, num_simulations: int = 1000, num_trades: int \| None = None) -> MonteCarloResult` | Sample from return distribution with replacement. |
| `calculate_probability_of_ruin(result: BacktestResult, ruin_threshold_pct: float = 50.0, num_simulations: int = 10000, simulation_type: str = 'resample_returns') -> float` | Calculate probability of ruin (catastrophic loss). |
| `calculate_confidence_intervals(result: BacktestResult, metric: str = 'total_return_pct', confidence_levels: list[float] \| None = None, num_simulations: int = 1000, simulation_type: str = 'shuffle_trades') -> dict[float, tuple[float, float]]` | Calculate confidence intervals for a specific metric. |
| `parametric_simulation(win_rate: float, reward_risk_ratio: float, risk_per_trade: float, num_trades: int = 1000, num_simulations: int = 1000, initial_balance: float = 10000.0) -> ParametricSimulationResult` | Run Parametric Monte Carlo simulation based on statistical inputs. |
| `PositionSizingResult` (model) | Results from Position Sizing simulation (Linear vs Compounding). |
| `position_sizing_simulation(win_rate: float, reward_risk_ratio: float, risk_per_trade: float, num_trades: int = 1000, initial_balance: float = 10000.0) -> PositionSizingResult` | Run Position Sizing simulation comparing Linear vs Compounding growth. |
| `consecutive_losing_simulation(win_rates: list[float], rrrs: list[float], num_trades: int = 1000, num_simulations: int = 200) -> list[ConsecutiveLosingScenarioResult]` | Simulate max consecutive losses for multiple Win Rate / RRR pairs. |
| `profit_target_simulation(initial_balance: float, target_balance: float, num_trades: int, win_rate: float, num_simulations: int = 500) -> list[ProfitTargetScenarioResult]` | Simulate the probability of reaching a target balance for a grid of RRR and Risk%. |
| `multi_entry_simulation(request: MultiEntryRequest) -> MultiEntryResponse` | Simulate multi-entry strategies with varying RRR as per MQL5 Article 19693. |


## FEAT-OPT-11: Parallel Processing Module (app.services.optimization.parallel)

| Function | Purpose |
|----------|---------|
| `ProgressTracker.__init__(total: int, description: str = 'Processing') -> None` | Initialize progress tracker. |
| `ProgressTracker.update(increment: int = 1) -> None` | Update progress (thread-safe). |
| `compare_parallel_speedup(engine_factory: Callable, param_grid: dict[str, list[Any]], n_jobs_list: list[int] \| None = None) -> dict[int, float]` | Compare speedup with different numbers of parallel workers. |
| `get_optimal_n_jobs() -> int` | Get recommended number of parallel jobs. |
| `estimate_completion_time(single_run_time: float, total_runs: int, n_jobs: int) -> float` | Estimate total completion time for parallel execution. |
| `analyze_walk_forward_results(wf_results: list[dict[str, Any]]) -> dict[str, Any]` | Analyze walk-forward optimization results. |


## FEAT-OPT-12: Optimization checkpointing and atomic persistence (app.services.optimization.persistence.checkpoint)

| Function | Purpose |
|----------|---------|
| `validate_safe_path(target_path: str, base_dir: str \| None = None) -> str` | Resolve and validate target path to prevent directory traversal. |
| `save_checkpoint(file_path: str, data: dict[str, Any], run_id: str, base_dir: str \| None = None) -> None` | Save checkpoint atomically. |
| `validate_checkpoint_schema(data: Any) -> None` | Validate that the loaded checkpoint conforms to the schema. |
| `load_checkpoint(file_path: str, base_dir: str \| None = None) -> dict[str, Any]` | Load and parse checkpoint state, rejecting corrupted or schema-invalid outputs. |
| `load_checkpoint_with_fallback(file_path: str, fallback_paths: list[str], base_dir: str \| None = None) -> dict[str, Any] \| None` | Attempt to load a checkpoint, falling back to alternative paths on failure. |


## FEAT-OPT-13: Optimization run storage repositories and progress trackers (app.services.optimization.persistence.repository)

| Function | Purpose |
|----------|---------|
| `OptimizationRunRecord` (model) | Database record for saving optimization run state. |
| `OptimizationRepository.save_run(run_id: str, record: OptimizationRunRecord) -> None` | Persist optimization run record. |
| `OptimizationRepository.load_run(run_id: str) -> OptimizationRunRecord` | Load optimization run record. |
| `OptimizationRepository.update_progress(run_id: str, progress: float, status: str) -> None` | Update progress status fields. |
| `InMemoryOptimizationRepository.save_run(run_id: str, record: OptimizationRunRecord) -> None` | Save run record under lock. |
| `InMemoryOptimizationRepository.load_run(run_id: str) -> OptimizationRunRecord` | Load run record under lock. |
| `InMemoryOptimizationRepository.update_progress(run_id: str, progress: float, status: str) -> None` | Update progress fields under lock; no-ops when run does not exist. |
| `ProgressTracker.increment() -> None` | Safely record one finished unit under lock. |
| `ProgressTracker.get_progress() -> float` | Return progress fraction (0-100). |
| `retry_with_backoff(action: Callable[..., R], *args: Any, attempts: int = 3, initial_delay: float = 0.1, **kwargs: Any) -> R` | Execute action retrying Safe transient errors with exponential backoff. |
| `save_optimization_run(repo: OptimizationRepository, run_id: str, record: OptimizationRunRecord) -> None` | Save optimization run via repository with retries. |
| `load_optimization_run(repo: OptimizationRepository, run_id: str) -> OptimizationRunRecord` | Load optimization run via repository with retries. |
| `update_optimization_progress(repo: OptimizationRepository, run_id: str, progress: float, status: str) -> None` | Update optimization progress via repository with retries. |


## FEAT-OPT-14: Periodic portfolio optimization tools (app.services.optimization.portfolio_optimizer)

| Function | Purpose |
|----------|---------|
| `PortfolioOptimizerResult.__init__(weights: pd.DataFrame) -> None` | Initialize a portfolio optimizer result. |
| `PortfolioOptimizerResult.plot() -> Any` | Plot portfolio weights over time. |
| `pfo_from_optimize_func(data: Any, optimize_func: Callable[[Any], Any], every: str = 'M') -> PortfolioOptimizerResult` | Periodically optimize portfolio weights from a callback. |
| `pfo_plot(portfolio_optimizer: PortfolioOptimizerResult) -> Any` | Plot a portfolio optimizer result. |


## FEAT-OPT-15: Optimization Result Data Classes (app.services.optimization.result)

| Function | Purpose |
|----------|---------|
| `OptimizationSummary.get_top_n(n: int = 10) -> list[OptimizationResult]` | Get top N results by score. |
| `OptimizationSummary.to_dataframe() -> pd.DataFrame` | Convert results to DataFrame for analysis. |


## FEAT-OPT-16: Strategy robustness scoring, stress testing, and Monte Carlo simulation (app.services.optimization.robustness)

| Function | Purpose |
|----------|---------|
| `calculate_robustness_score(checks: dict[str, bool]) -> float` | Calculate deterministic robustness percentage from pass/fail checks. |
| `bootstrap_simulation(trades: list[dict[str, Any]], block_size: int = 5, simulation_count: int = 1000, initial_balance: float = 10000.0, seed: int \| None = None) -> list[list[float]]` | Sample blocks of contiguous trades to preserve short-term temporal structure. |
| `run_spread_stress_test(trades: list[dict[str, Any]], spread_multiplier: float = _SPREAD_MULTIPLIER_DEFAULT, pip_value: float = _PIP_VALUE_DEFAULT) -> list[dict[str, Any]]` | Simulate spread-widening costs on trades. |
| `run_slippage_stress_test(trades: list[dict[str, Any]], slippage_pips: float = _DEFAULT_SLIPPAGE_PIPS, pip_value: float = _PIP_VALUE_DEFAULT) -> list[dict[str, Any]]` | Simulate execution-slippage costs on trades. |
| `run_commission_stress_test(trades: list[dict[str, Any]], extra_commission_per_lot: float = _DEFAULT_COMMISSION_PER_LOT) -> list[dict[str, Any]]` | Simulate commission-increase costs on trades. |
| `run_randomize_trade_order_mc(trades: list[dict[str, Any]], initial_balance: float = 10000.0, simulation_count: int = 1000, seed: int \| None = None) -> list[list[float]]` | Shuffle trade order in Monte Carlo paths. |
| `run_resample_trades_mc(trades: list[dict[str, Any]], initial_balance: float = 10000.0, simulation_count: int = 1000, seed: int \| None = None) -> list[list[float]]` | Resample trades with replacement in Monte Carlo paths. |
| `run_skip_trades_mc(trades: list[dict[str, Any]], skip_fraction: float = _STRESS_SKIP_FRACTION, simulation_count: int = 100, initial_balance: float = 10000.0, seed: int \| None = None) -> list[list[float]]` | Randomly drop winning trades to stress-test robustness. |
| `run_randomize_parameters_mc(strategy_ref: str, parameters: dict[str, Any], space: ParameterSpace, symbols: list[str], timeframe: str, start: str, end: str, initial_balance: float = 10000.0, simulation_count: int = 10, seed: int \| None = None) -> list[float]` | Perturb strategy parameters randomly and evaluate scores. |
| `run_randomize_history_mc(trades: list[dict[str, Any]], initial_balance: float = 10000.0, simulation_count: int = 100, seed: int \| None = None) -> list[list[float]]` | Simulate history bootstrap paths using block resampling. |
| `run_combined_monte_carlo(trades: list[dict[str, Any]], initial_balance: float = 10000.0, simulation_count: int = 100, seed: int \| None = None) -> list[list[float]]` | Run combined Monte Carlo using trade resampling. |
| `run_cross_market_test(strategy_ref: str, parameters: dict[str, Any], other_symbols: list[str], timeframe: str, start: str, end: str, initial_balance: float = 10000.0) -> dict[str, float]` | Test strategy parameter stability on out-of-universe asset symbols. |
| `run_cross_timeframe_test(strategy_ref: str, parameters: dict[str, Any], symbols: list[str], other_timeframes: list[str], start: str, end: str, initial_balance: float = 10000.0) -> dict[str, float]` | Test strategy parameter stability across bar resolution timeframes. |
| `run_second_oos_test(strategy_ref: str, parameters: dict[str, Any], symbols: list[str], timeframe: str, start: str, end: str, initial_balance: float = 10000.0) -> float` | Evaluate strategy performance on a secondary out-of-sample data slice. |
| `run_third_oos_test(strategy_ref: str, parameters: dict[str, Any], symbols: list[str], timeframe: str, start: str, end: str, initial_balance: float = 10000.0) -> float` | Evaluate strategy performance on a tertiary out-of-sample data slice. |
| `assess_strategy_robustness(trades: list[dict[str, Any]], initial_balance: float = 10000.0, seed: int \| None = None) -> RobustnessResponse` | Assess strategy robustness under commission, slippage, and MC shocks. |
| `build_monte_carlo_result(paths: list[list[float]], initial_balance: float, ruin_threshold: float, target_balance: float) -> MonteCarloResult` | Compute statistics and return a structured ``MonteCarloResult``. |
| `optimization_monte_carlo(trades: list[dict[str, Any]], simulation_method: Literal["shuffle_trades", "resample_trades", "skip_trades"] = "shuffle_trades", simulation_count: int = 1000, initial_balance: float = 10000.0, ruin_threshold: float = _RUIN_FRACTION, target_balance: float = 12000.0, seed: int \| None = None) -> MonteCarloResponse` | Expose Monte Carlo analysis over trade results. |
| `robustness_simulation(trades: list[dict[str, Any]], skip_fraction: float = _STRESS_SKIP_FRACTION, deterioration_pct: float = 0.05, mode: Literal["shuffle_trades", "resample_trades"] = "shuffle_trades", simulation_count: int = 1000, initial_balance: float = 10000.0, seed: int \| None = None) -> list[list[float]]` | Simulate robustness under trade dropping, cost deterioration, and shuffling. |
| `compare_simulation_methods(trades: list[dict[str, Any]], initial_balance: float = 10000.0, simulation_count: int = 1000, seed: int \| None = None) -> dict[str, float]` | Compare ruin probabilities across different Monte Carlo methods. |
| `run_monte_carlo_task(trades: list[dict[str, Any]], simulation_method: str = "shuffle_trades", simulation_count: int = 1000, initial_balance: float = 10000.0, seed: int \| None = None) -> str` | Register a background Monte Carlo simulation run and return a task ID. |
| `build_robustness_report(trades: list[dict[str, Any]], initial_balance: float = 10000.0, simulation_count: int = 1000, ruin_threshold: float = _RUIN_FRACTION, target_balance: float \| None = None, seed: int \| None = None) -> dict[str, Any]` | Produce a comprehensive robustness report combining stress tests and MC. |


## FEAT-OPT-17: Optimization scoring and metrics assessment (app.services.optimization.scoring)

| Function | Purpose |
|----------|---------|
| `ScoringFunction` (protocol) | Protocol that all candidate scoring callables must satisfy. |
| `get_daily_returns(trades: list[dict[str, Any]], initial_balance: float) -> list[float]` | Group trade profits by close day and compute fractional returns. |
| `calculate_max_drawdown(trades: list[dict[str, Any]], initial_balance: float) -> float` | Calculate peak-to-trough maximum drawdown from trade sequence. |
| `total_return_score(trades: list[dict[str, Any]], initial_balance: float) -> float` | Calculate total net return as a fraction of initial balance. |
| `profit_factor_score(trades: list[dict[str, Any]], initial_balance: float) -> float` | Calculate profit factor (gross wins divided by absolute gross loss). |
| `sharpe_score(trades: list[dict[str, Any]], initial_balance: float) -> float` | Calculate annualized Sharpe ratio from daily returns. |
| `sortino_score(trades: list[dict[str, Any]], initial_balance: float) -> float` | Calculate annualized Sortino ratio from daily returns. |
| `calmar_score(trades: list[dict[str, Any]], initial_balance: float) -> float` | Calculate Calmar ratio (total return divided by max drawdown). |
| `custom_score(result: BacktestResult, return_weight: float = 0.3, sharpe_weight: float = 0.4, dd_weight: float = 0.3) -> float` | Compute a custom composite score. |
| `optimization_get_scoring_func(name: str) -> ScoringFunction` | Resolve a supported objective name to its scoring function. |
| `calculate_dsr(sharpe: float, trial_count: int, skew: float = 0.0, kurtosis: float = 3.0, t_samples: int = 100) -> float` | Calculate Deflated Sharpe Ratio (DSR) probability. |
| `evaluate_candidate_score(trades: list[dict[str, Any]], initial_balance: float, objective: str = "sharpe", trial_count: int = 1) -> dict[str, Any]` | Evaluate performance score and anti-overfitting metrics for a candidate. |
| `rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]` | Sort parameter candidates deterministically by score and tie-breakers. |
| `nominal_trial_count(candidates: list[dict[str, Any]]) -> int` | Calculate nominal trial count from unique candidate hashes. |
| `trial_count_independence_warning(trial_count: int, search_method: str = "grid") -> str \| None` | Return a warning string when trial-count independence may be overstated. |
| `pareto_select(candidates: list[dict[str, Any]], objectives: list[str], initial_balance: float = 10000.0) -> list[dict[str, Any]]` | Perform deterministic Pareto front selection over multiple objectives. |


## FEAT-OPT-18: Optimization walk-forward and chronological time-series splitting (app.services.optimization.splitting)

| Function | Purpose |
|----------|---------|
| `WalkForwardSplit.split() -> SplitterResult` | Generate time-series split windows. |
| `chronological_split(start: datetime \| str, end: datetime \| str, train_fraction: float = 0.7) -> tuple[WalkForwardWindow, ...]` | Create a single train-test split window. |
| `rolling_window_split(start: datetime, end: datetime, folds: int = 5, train_fraction: float = 0.7, purging_bars: int = 0, embargo_bars: int = 0, bar_duration: timedelta = _DEFAULT_BAR_DURATION) -> list[WalkForwardWindow]` | Create deterministic rolling time-series train/test windows. |
| `expanding_window_split(start: datetime, end: datetime, folds: int = 5, train_fraction: float = 0.7, purging_bars: int = 0, embargo_bars: int = 0, bar_duration: timedelta = _DEFAULT_BAR_DURATION) -> list[WalkForwardWindow]` | Create deterministic expanding time-series train/test windows. |
| `splitter_from_rolling(start: str, end: str, folds: int = 5, train_fraction: float = 0.7, purging_bars: int = 0, embargo_bars: int = 0, bar_duration: timedelta = _DEFAULT_BAR_DURATION) -> SplitterResult` | Create rolling split windows from ISO date strings. |
| `splitter_from_expanding(start: str, end: str, folds: int = 5, train_fraction: float = 0.7, purging_bars: int = 0, embargo_bars: int = 0, bar_duration: timedelta = _DEFAULT_BAR_DURATION) -> SplitterResult` | Create expanding split windows from ISO date strings. |
| `splitter_rolling_split(data: Any, window_len: int, set_lens: tuple[int, ...] = (1, 1), left_to_right: bool = False, step: int = 1) -> list[dict[str, pd.DataFrame]]` | Split tabular data into rolling train/test or train/valid/test windows. |
| `run_walk_forward_optimization(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, folds: int = 5, train_fraction: float = 0.7, fold_mode: str = "rolling", purging_bars: int = 0, embargo_bars: int = 0, bar_duration: timedelta = _DEFAULT_BAR_DURATION, max_candidates: int = 20, seed: int \| None = None, **kwargs: Any) -> dict[str, Any]` | Run walk-forward optimization: optimize on train folds, evaluate on test folds. |
| `run_walk_forward_matrix(strategy_refs: list[str], symbols: list[str], timeframe: str, start: str, end: str, parameter_spaces: list[ParameterSpace], objective: str = "sharpe", initial_balance: float = 10000.0, folds: int = 5, train_fraction: float = 0.7, fold_mode: str = "rolling", purging_bars: int = 0, embargo_bars: int = 0, bar_duration: timedelta = _DEFAULT_BAR_DURATION, max_candidates: int = 20, seed: int \| None = None, **kwargs: Any) -> dict[str, Any]` | Run walk-forward optimization across multiple strategy configurations. |
| `SplitterResult.__init__(index: pd.Index, splits: list[dict[str, pd.Index]], set_labels: list[str]) -> None` | Initialize a split result container. |
| `SplitterResult.plots() -> Any` | Visualize split windows with matplotlib. |


## FEAT-OPT-19: Optimization sweeps, walk-forward analysis, and public facades (app.services.optimization.sweeps)

| Function | Purpose |
|----------|---------|
| `calculate_parameter_stability(candidates: list[dict[str, Any]]) -> dict[str, float]` | Calculate standard-deviation stability across selected candidates. |
| `detect_overfit_parameters(in_sample_score: float, out_of_sample_score: float) -> dict[str, Any]` | Detect overfit risk from the gap between in-sample and out-of-sample scores. |
| `rank_parameter_sets(candidates: list[dict[str, Any]], objective: str = "score") -> list[dict[str, Any]]` | Rank candidate parameter sets by their objective score descending. |
| `compare_optimization_runs(run_ids: list[str], results_payloads: list[dict[str, Any]]) -> dict[str, Any]` | Package candidate optimization runs or result payloads for comparison. |
| `walk_forward(strategy_class: type[BaseStrategy], data, param_grid: dict[str, list[Any]], train_period: int = 252, test_period: int = 63, initial_balance: float = 10000.0, scoring_func: Callable[[BacktestResult], float] = sharpe_score, verbose: bool = True, progress_callback: Callable \| None = None, strategy_file_path: str \| None = None, symbol: str \| None = None) -> dict[str, Any]` | Walk-forward optimization. |
| `parallel_walk_forward(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, request: WalkForwardRequest, max_workers: int = 2, **kwargs: Any) -> WalkForwardResponse` | Run walk-forward optimization with genuine fold-level parallelism. |
| `print_optimization_report(summary: OptimizationSummary) -> str` | Format a top-candidate optimization report as Markdown. |
| `run_parameter_sweep(payload: dict[str, Any]) -> StandardResponse` | Co-ordinate an optimization sweep request and return a standard envelope. |
| `optimization_walk_forward(strategy_ref: str, symbols: list[str], timeframe: str, start: str, end: str, parameter_space: ParameterSpace, objective: str = "sharpe", initial_balance: float = 10000.0, fold_mode: Literal["rolling", "anchored", "expanding"] = "rolling", folds: int = 5, dry_run: bool = True) -> dict[str, Any]` | User-facing wrapper around walk-forward parameter optimization. |
| `analyze_parallel_results(results: list[dict[str, Any]]) -> dict[str, Any]` | Convert parallel optimization results into tabular analysis output. |
| `save_optimization_result(result: dict[str, Any]) -> dict[str, Any]` | Package optimization result metadata for downstream storage. |
| `build_optimization_report(summary: OptimizationSummary) -> dict[str, Any]` | Package optimization report creation inputs for downstream reporting. |
