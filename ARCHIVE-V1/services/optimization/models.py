"""Pydantic models for optimization and unsupervised-analysis APIs.

Classes and functions:
    UnsupervisedConfigRequest: Class. Provides UnsupervisedConfigRequest behavior for optimization workflows.
    UnsupervisedRunSummary: Class. Provides UnsupervisedRunSummary behavior for optimization workflows.
    UnsupervisedAnalysisRequest: Class. Provides UnsupervisedAnalysisRequest behavior for optimization workflows.
    ParameterRange: Class. Provides ParameterRange behavior for optimization workflows.
    OptimizationRequest: Class. Provides OptimizationRequest behavior for optimization workflows.
    PositionSizingRequest: Class. Provides PositionSizingRequest behavior for optimization workflows.
    OptimizationResponse: Class. Provides OptimizationResponse behavior for optimization workflows.
    OptimizationRunDetails: Class. Provides OptimizationRunDetails behavior for optimization workflows.
    OptimizationResultItem: Class. Provides OptimizationResultItem behavior for optimization workflows.
    WalkForwardRequest: Class. Provides WalkForwardRequest behavior for optimization workflows.
    WalkForwardWindow: Class. Provides WalkForwardWindow behavior for optimization workflows.
    WalkForwardResponse: Class. Provides WalkForwardResponse behavior for optimization workflows.
    MonteCarloRequest: Class. Provides MonteCarloRequest behavior for optimization workflows.
    ParametricMonteCarloRequest: Class. Provides ParametricMonteCarloRequest behavior for optimization workflows.
    MonteCarloResponse: Class. Provides MonteCarloResponse behavior for optimization workflows.
    ConsecutiveLosingRequest: Class. Provides ConsecutiveLosingRequest behavior for optimization workflows.
    ConsecutiveLosingScenario: Class. Provides ConsecutiveLosingScenario behavior for optimization workflows.
    ConsecutiveLosingResponse: Class. Provides ConsecutiveLosingResponse behavior for optimization workflows.
    ProfitTargetRequest: Class. Provides ProfitTargetRequest behavior for optimization workflows.
    ProfitTargetResult: Class. Provides ProfitTargetResult behavior for optimization workflows.
    ProfitTargetResponse: Class. Provides ProfitTargetResponse behavior for optimization workflows.
    ManualPairInput: Class. Provides ManualPairInput behavior for optimization workflows.
    RandomWinRateRequest: Class. Provides RandomWinRateRequest behavior for optimization workflows.
    RandomWinRatePair: Class. Provides RandomWinRatePair behavior for optimization workflows.
    DistributionStats: Class. Provides DistributionStats behavior for optimization workflows.
    RandomWinRateResult: Class. Provides RandomWinRateResult behavior for optimization workflows.
    RandomWinRateResponse: Class. Provides RandomWinRateResponse behavior for optimization workflows.
    RobustnessRequest: Class. Provides RobustnessRequest behavior for optimization workflows.
    RobustnessStats: Class. Provides RobustnessStats behavior for optimization workflows.
    RobustnessResponse: Class. Provides RobustnessResponse behavior for optimization workflows.
    MultiEntryRequest: Class. Provides MultiEntryRequest behavior for optimization workflows.
    MultiEntryScenarioResult: Class. Provides MultiEntryScenarioResult behavior for optimization workflows.
    MultiEntryResponse: Class. Provides MultiEntryResponse behavior for optimization workflows.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class UnsupervisedConfigRequest(BaseModel):
    """Optional unsupervised-analysis configuration for optimization runs."""

    enabled: bool = Field(
        False, description="Enable unsupervised market-structure analysis"
    )
    fast_period: int = Field(20, ge=2)
    slow_period: int = Field(50, ge=3)
    volatility_window: int = Field(20, ge=2)
    momentum_window: int = Field(5, ge=1)
    min_feature_periods: int = Field(3, ge=1)
    include_ema_spread: bool = Field(True)
    n_components: int = Field(2, ge=1)
    n_clusters: int = Field(3, ge=2)
    random_state: int = Field(42, ge=0)
    forward_return_horizon: int = Field(1, ge=1)
    label_column: str = Field("cluster_label")
    price_column: str = Field("close")
    min_rows: int = Field(25, ge=3)
    min_cluster_observations: int = Field(3, ge=1)
    scale_features: bool = Field(True)
    enable_signal_adaptation: bool = Field(False)


class UnsupervisedRunSummary(BaseModel):
    """Serialized unsupervised-analysis payload exposed via API."""

    status: str
    config: dict[str, Any]
    feature_columns: list[str] = Field(default_factory=list)
    feature_metadata: dict[str, Any] = Field(default_factory=dict)
    strategy_context: dict[str, Any] = Field(default_factory=dict)
    risk_context: dict[str, Any] = Field(default_factory=dict)
    guardrails: list[str] = Field(default_factory=list)
    reason: str | None = None
    report: dict[str, Any] | None = None


class UnsupervisedAnalysisRequest(BaseModel):
    """Run a standalone unsupervised analysis on market data."""

    symbol: str = Field(..., description="Trading symbol (e.g., EURUSD)")
    timeframe: str = Field(..., description="Timeframe (e.g., H1, D1)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    data_source: str = Field("mt5", description="Data source (mt5 or dukascopy)")
    unsupervised: UnsupervisedConfigRequest = Field(
        default_factory=lambda: UnsupervisedConfigRequest(enabled=True),
        description="Unsupervised-analysis configuration",
    )


class ParameterRange(BaseModel):
    """Parameter range for optimization."""

    name: str = Field(..., description="Parameter name")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    step: float | None = Field(None, description="Step size for grid search (optional)")
    type: Literal["int", "float"] = Field("float", description="Parameter type")


class OptimizationRequest(BaseModel):
    """Request to start an optimization run."""

    strategy_id: int = Field(..., description="Strategy ID to optimize")
    method: Literal["grid", "random", "bayesian", "genetic"] = Field(
        ..., description="Optimization method"
    )
    objective: Literal[
        "sharpe", "sortino", "calmar", "profit_factor", "total_return"
    ] = Field(..., description="Objective function to optimize")

    # Data configuration
    symbol: str = Field(..., description="Trading symbol (e.g., EURUSD)")
    timeframe: str = Field(..., description="Timeframe (e.g., H1, D1)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(10000.0, description="Initial capital")
    data_source: str = Field("mt5", description="Data source (mt5 or dukascopy)")

    # Parameter space
    parameters: list[ParameterRange] = Field(
        ..., description="Parameter ranges to optimize"
    )

    # Method-specific settings
    n_iter: int | None = Field(100, description="Number of iterations (random search)")
    n_initial_points: int | None = Field(
        10, description="Initial random points (Bayesian)"
    )
    population_size: int | None = Field(50, description="Population size (genetic)")
    generations: int | None = Field(30, description="Number of generations (genetic)")
    mutation_rate: float | None = Field(0.1, description="Mutation rate (genetic)")
    crossover_rate: float | None = Field(0.8, description="Crossover rate (genetic)")

    # Execution settings
    n_jobs: int = Field(1, description="Number of parallel jobs")
    engine_type: Literal["event_driven", "vectorised"] = Field(
        "vectorised", description="Backtest engine type"
    )
    unsupervised: UnsupervisedConfigRequest | None = Field(
        default=None,
        description="Optional unsupervised-analysis configuration",
    )


class PositionSizingRequest(BaseModel):
    """Request for Position Sizing simulation."""

    win_rate: float = Field(..., ge=0.0, le=1.0, description="Win rate (0.0 - 1.0)")
    reward_risk_ratio: float = Field(..., gt=0.0, description="Reward to Risk Ratio")
    risk_per_trade: float = Field(
        ..., gt=0.0, le=1.0, description="Risk per trade (e.g. 0.01 for 1%)"
    )
    num_trades: int = Field(..., gt=0, description="Number of trades")
    initial_balance: float = Field(10000.0, gt=0, description="Initial balance")


class OptimizationResponse(BaseModel):
    """Response after starting an optimization."""

    optimization_id: int = Field(..., description="Optimization run ID")
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = Field(
        ..., description="Current status"
    )
    method: str = Field(..., description="Optimization method used")
    total_combinations: int = Field(..., description="Total parameter combinations")
    message: str = Field(..., description="Status message")


class OptimizationRunDetails(BaseModel):
    """Detailed information about an optimization run."""

    optimization_id: int
    strategy_name: str
    strategy_version: str
    optimization_type: str
    optimization_method: str
    start_date: str
    end_date: str
    symbols: list[str] | None
    timeframes: list[str] | None
    parameter_space: dict[str, Any]
    objective_function: str
    total_combinations: int
    completed_combinations: int | None
    n_jobs: int
    status: str
    best_backtest_id: int | None
    best_score: float | None
    best_parameters: dict[str, Any] | None
    unsupervised_status: str | None = None
    unsupervised_config: dict[str, Any] | None = None
    unsupervised_report: dict[str, Any] | None = None
    created_at: str
    completed_at: str | None


class OptimizationResultItem(BaseModel):
    """Individual optimization result."""

    result_id: int
    parameters: dict[str, Any]
    score: float
    rank: int
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    profit_factor: float
    unsupervised_report: dict[str, Any] | None = None


class WalkForwardRequest(BaseModel):
    """Request to start walk-forward analysis."""

    strategy_id: int = Field(..., description="Strategy ID to optimize")
    # method: Literal["grid", "random", "bayesian"] = Field("grid", description="Optimization method")
    objective: Literal[
        "sharpe", "sortino", "calmar", "profit_factor", "total_return"
    ] = Field(..., description="Objective function to optimize")

    # Data configuration
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    initial_capital: float = Field(10000.0, description="Initial capital")
    data_source: str = Field("mt5", description="Data source")

    # Sliding Window configuration
    train_period: int = Field(..., description="Training window size (bars)")
    test_period: int = Field(..., description="Testing window size (bars)")

    # Parameter space
    parameters: list[ParameterRange] = Field(..., description="Parameter ranges")

    # Execution
    n_jobs: int = Field(-1, description="Number of parallel jobs")
    unsupervised: UnsupervisedConfigRequest | None = Field(
        default=None,
        description="Optional unsupervised-analysis configuration",
    )


class WalkForwardWindow(BaseModel):
    """Walk-forward analysis window result."""

    window_id: int
    window_number: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    best_parameters: dict[str, Any]
    train_return: float
    train_sharpe: float
    train_drawdown: float
    test_return: float
    test_sharpe: float
    test_drawdown: float


class WalkForwardResponse(BaseModel):
    """Response from Walk-Forward Optimization."""

    task_id: int
    windows: list[WalkForwardWindow]
    overall_return: float
    overall_sharpe: float
    overall_drawdown: float
    stability_score: float
    status: str = "completed"


class MonteCarloRequest(BaseModel):
    """Request to start Monte Carlo simulation."""

    backtest_id: int = Field(..., description="Backtest ID to analyze")
    simulation_type: Literal["shuffle_trades", "resample_returns", "bootstrap"] = Field(
        ..., description="Simulation method"
    )
    num_simulations: int = Field(1000, description="Number of simulations")
    block_size: int | None = Field(10, description="Block size for bootstrap")
    random_seed: int | None = None
    initial_balance: float = 10000.0


class ParametricMonteCarloRequest(BaseModel):
    """Request to run parametric Monte Carlo simulation."""

    win_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Win rate probability (0.0-1.0)"
    )
    reward_risk_ratio: float = Field(..., gt=0.0, description="Reward to Risk Ratio")
    risk_per_trade: float = Field(
        ..., gt=0.0, le=1.0, description="Risk per trade (0.01 = 1%)"
    )
    num_trades: int = Field(1000, gt=0, description="Number of trades per simulation")
    num_simulations: int = Field(1000, gt=0, description="Number of simulations")
    initial_balance: float = Field(10000.0, gt=0, description="Initial account balance")
    random_seed: int | None = Field(None, description="Random seed for reproducibility")


class MonteCarloResponse(BaseModel):
    """Monte Carlo simulation results."""

    simulation_id: int
    backtest_id: int
    simulation_type: str
    num_simulations: int

    # Summary statistics (optional until simulation completes)
    mean_return: float | None = None
    median_return: float | None = None
    std_return: float | None = None

    # Confidence intervals
    ci_95_lower: float | None = None
    ci_95_upper: float | None = None
    ci_99_lower: float | None = None
    ci_99_upper: float | None = None

    # Risk metrics
    probability_of_profit: float | None = None
    probability_of_ruin: float | None = None
    expected_shortfall_95: float | None = None

    # Percentiles
    percentile_5: float | None = None
    percentile_25: float | None = None
    percentile_50: float | None = None
    percentile_75: float | None = None
    percentile_95: float | None = None

    # Original metrics
    original_return: float | None = None
    original_sharpe: float | None = None
    original_max_dd: float | None = None

    created_at: str


class ConsecutiveLosingRequest(BaseModel):
    """Request for Consecutive Losing simulation."""

    win_rates: list[float] = Field(
        ..., description="List of win rates (e.g. [0.3, 0.5])"
    )
    rrrs: list[float] = Field(
        ..., description="List of Risk:Reward ratios (e.g. [3.0, 1.0])"
    )
    num_trades: int = Field(1000, gt=0)
    num_simulations: int = Field(200, gt=0)


class ConsecutiveLosingScenario(BaseModel):
    """Result scenario for consecutive losing simulation."""

    scenario_label: str
    win_rate: float
    rrr: float
    min_losses: int
    q1_losses: float
    median_losses: float
    q3_losses: float
    max_losses: int
    mean_losses: float
    std_losses: float


class ConsecutiveLosingResponse(BaseModel):
    """Response containing multiple consecutive losing scenarios."""

    scenarios: list[ConsecutiveLosingScenario]


class ProfitTargetRequest(BaseModel):
    """Request to calculate probability of reaching a profit target."""

    initial_balance: float = Field(1000, gt=0)
    target_balance: float = Field(200000, gt=0)
    num_trades: int = Field(750, gt=0)
    win_rate: float = Field(0.76, gt=0, le=1)
    num_simulations: int = Field(500, gt=0)


class ProfitTargetResult(BaseModel):
    """Result for a specific RRR and Risk configuration."""

    rrr: float
    risk_pct: float
    success_rate: float


class ProfitTargetResponse(BaseModel):
    """Response validation for Profit Target simulation."""

    results: list[ProfitTargetResult]


class ManualPairInput(BaseModel):
    """Input model for manual WinRate/RRR pairs."""

    win_rate: float = Field(..., gt=0, le=1)
    rrr: float = Field(..., gt=0)


class RandomWinRateRequest(BaseModel):
    """Request for Random Win Rate simulation."""

    initial_equity: float = Field(1000, gt=0)
    risk_per_trade: float = Field(0.01, gt=0, le=1)
    trades_per_run: int = Field(100, gt=0)
    simulations: int = Field(200, gt=0)
    manual_pairs: list[ManualPairInput] | None = None


class RandomWinRatePair(BaseModel):
    """Statistics for a WinRate/RRR pair used in simulation."""

    win_rate: float
    rrr: float
    expectancy: float
    usage_count: int
    usage_pct: float


class DistributionStats(BaseModel):
    """Statistical distribution metrics."""

    min_val: float
    q1_val: float
    median_val: float
    q3_val: float
    max_val: float
    mean_val: float
    std_val: float


class RandomWinRateResult(BaseModel):
    """Result wrapper for Random Win Rate simulation."""

    pairs: list[RandomWinRatePair]
    drawdown_stats: DistributionStats
    equity_stats: DistributionStats
    return_stats: DistributionStats


class RandomWinRateResponse(BaseModel):
    """Response containing Random Win Rate simulation results."""

    result: RandomWinRateResult


class RobustnessRequest(BaseModel):
    """Request parameters for Robustness check."""

    backtest_id: str
    simulations: int = Field(100, gt=0)
    simulation_type: str = Field("shuffle")  # shuffle, bootstrap
    skip_probability: float = Field(0.0, ge=0.0, le=1.0)
    deterioration_pct: float = Field(0.0, ge=0.0, le=1.0)


class RobustnessStats(BaseModel):
    """Summary statistics from Robustness simulation."""

    original_profit: float
    min_profit: float
    max_profit: float
    mean_profit: float
    worst_case_drawdown: float
    risk_of_ruin: float  # Percentage 0-100


class RobustnessResponse(BaseModel):
    """Response containing Robustness simulation results."""

    original_equity: list[float]
    simulation_equities: list[list[float]]  # Sample of curves (e.g. max 50)
    stats: RobustnessStats


class MultiEntryRequest(BaseModel):
    """Request for Multi-Entry simulation."""

    win_rate: float = Field(..., ge=0.0, le=1.0)
    initial_rrr: float = Field(..., gt=0.0)
    rrr_step: float = Field(0.0, ge=0.0)
    risk_percent: float = Field(0.01, gt=0.0, le=1.0)  # Total risk per execution
    simulations: int = Field(100, gt=0)
    initial_balance: float = Field(1000.0, gt=0)


class MultiEntryScenarioResult(BaseModel):
    """Result for a specific Multi-Entry scenario."""

    mean_equity: float
    median_equity: float
    median_drawdown: float
    profitable_pct: float
    equity_curve: list[float]  # Mean or representative curve


class MultiEntryResponse(BaseModel):
    """Response containing results for 1, 2, and 3 trade entry scenarios."""

    one_trade: MultiEntryScenarioResult
    two_trades: MultiEntryScenarioResult
    three_trades: MultiEntryScenarioResult
