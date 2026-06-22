"""Analytics catalog and schema support models.

This module defines the small, read-only catalog records used by the Analytics
service to classify official tools, metric definitions, and schema behaviour.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects on import.

Exports:
    AnalyticsMetadata, AnalyticsConfig, AnalyticsRequest, AnalyticsResult,
    MetricDefinition, ToolDefinition, MetricDefinitionCatalog,
    OFFICIAL_ANALYTICS_TOOL_CATALOG, METRIC_DEFINITION_CATALOG,
    SCHEMA_COMPATIBILITY_MATRIX, WARNING_SEVERITY_LEVELS,
    validate_metric_catalog.

Side effects:
    None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.utils.errors import ValidationError

CapabilityStability = Literal[
    "stable",
    "approved_experimental",
    "deprecated",
    "internal_support_only",
]
MetricRole = Literal[
    "calculated_fact",
    "diagnostic_estimate",
    "warning_evidence",
    "scorecard_input",
    "non_binding_review_context",
]
SchemaStatus = Literal[
    "accepted",
    "deprecated",
    "legacy_adapted",
    "rejected",
    "unsupported_future",
]


@dataclass(frozen=True, slots=True)
class AnalyticsMetadata:
    """Trace and reproducibility metadata for analytics payloads.

    Args:
        request_id: Optional request trace identifier.
        workflow_id: Optional workflow trace identifier.
        schema_version: Version of the analytics schema.
        analytics_engine_version: Version of the analytics engine.
        source_context: Source lineage or run context.

    Side effects:
        None.
    """

    request_id: str | None = None
    workflow_id: str | None = None
    schema_version: str = "1.3.1"
    analytics_engine_version: str = "1.0.0"
    source_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnalyticsConfig:
    """Deterministic analytics configuration.

    Args:
        annualization_periods: Period count used for annualised ratios.
        breakeven_epsilon: Absolute PnL tolerance for breakeven classification.
        monetary_precision_mode: Monetary precision mode used in reports.
        derived_ratio_tolerance: Deterministic tolerance for float ratios.
        max_dashboard_points: Maximum points returned in dashboard series.
        risk_free_rate: Annual risk-free rate used in Sharpe / Sortino.
        min_sample_size: Minimum trades for reliable metric calculation.

    Side effects:
        None.
    """

    annualization_periods: int = 252
    breakeven_epsilon: float = 1e-9
    monetary_precision_mode: str = "float64_with_tolerance"
    derived_ratio_tolerance: float = 1e-9
    max_dashboard_points: int = 500
    risk_free_rate: float = 0.0
    min_sample_size: int = 30


@dataclass(frozen=True, slots=True)
class AnalyticsRequest:
    """Canonical analytics request wrapper.

    Args:
        payload: Input payload to analyse.
        config: Deterministic analytics configuration.
        metadata: Trace and reproducibility metadata.

    Side effects:
        None.
    """

    payload: dict[str, Any]
    config: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    metadata: AnalyticsMetadata = field(default_factory=AnalyticsMetadata)


@dataclass(frozen=True, slots=True)
class AnalyticsResult:
    """Canonical analytics result wrapper.

    Args:
        status: Result status string.
        data: JSON-safe analytics payload.
        warnings: Warning objects emitted during calculation.
        quality_flags: Quality flags emitted during calculation.
        metadata: Trace and reproducibility metadata.

    Side effects:
        None.
    """

    status: Literal["completed", "partial", "failed"]
    data: dict[str, Any]
    warnings: list[dict[str, Any]] = field(default_factory=list)
    quality_flags: list[dict[str, Any]] = field(default_factory=list)
    metadata: AnalyticsMetadata = field(default_factory=AnalyticsMetadata)


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Approved definition for a metric exposed by analytics.

    Args:
        name: Stable metric name matching the MDC key.
        formula: Human-readable formula string.
        units: Metric units (e.g. ``"percent"``, ``"ratio"``, ``"currency"``).
        required_inputs: Required input field names.
        optional_inputs: Optional input field names.
        accepted_aliases: Accepted source-field aliases.
        return_scale: Scale label (e.g. ``"fraction"``, ``"percent"``).
        annualization_basis: Annualisation basis or ``None``.
        sample_convention: ``"sample"`` or ``"population"`` convention.
        minimum_sample_size: Minimum sample size before the metric is reliable.
        undefined_behavior: How undefined values must be represented.
        golden_fixture: Expected fixture behaviour for regression tests.
        role: How the metric may be used by reports and scorecards.
        confidence: Confidence label for derived or proxy metrics.

    Side effects:
        None.
    """

    name: str
    formula: str
    units: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    accepted_aliases: tuple[str, ...] = ()
    return_scale: str = "scalar"
    annualization_basis: str | None = None
    sample_convention: str = "sample"
    minimum_sample_size: int = 1
    undefined_behavior: str = (
        "return None and emit structured warning metadata"
    )
    golden_fixture: str = "covered by analytics unit tests"
    role: MetricRole = "calculated_fact"
    confidence: Literal["normal", "degraded"] = "normal"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Public analytics tool catalog entry.

    Args:
        name: Stable public tool name.
        input_schema: Human-readable input schema summary.
        output_schema: Human-readable output schema summary.
        errors: Stable error codes used by the tool.
        side_effects: Side-effect summary.
        stability: Stability classification.
        agent_api_safe: Whether the tool is safe for agent/API use.
        tests: Test files or usage scripts covering the tool.

    Side effects:
        None.
    """

    name: str
    input_schema: str
    output_schema: str
    errors: tuple[str, ...]
    side_effects: str
    stability: CapabilityStability
    agent_api_safe: bool
    tests: tuple[str, ...]


MetricDefinitionCatalog = dict[str, MetricDefinition]

# ---------------------------------------------------------------------------
# Metric Definition Catalog
# ---------------------------------------------------------------------------
METRIC_DEFINITION_CATALOG: MetricDefinitionCatalog = {
    # ── Return metrics ───────────────────────────────────────────────────────
    "total_return": MetricDefinition(
        name="total_return",
        formula=(
            "((ending_equity - initial_equity) / initial_equity) * 100"
        ),
        units="percent",
        required_inputs=("equity_curve",),
        accepted_aliases=("return_on_initial_capital",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior=(
            "return None and emit warning when initial equity is missing,"
            " non-positive, or zero"
        ),
        golden_fixture="10000 → 11000 equals 10.0 %",
    ),
    "return_on_initial_capital": MetricDefinition(
        name="return_on_initial_capital",
        formula="(net_profit / initial_capital) * 100",
        units="percent",
        required_inputs=("equity_curve",),
        accepted_aliases=("total_return",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior=(
            "return None and emit warning when initial capital is missing"
            " or non-positive"
        ),
        golden_fixture="10 000 capital, 500 profit → 5.0 %",
    ),
    "total_return_usd": MetricDefinition(
        name="total_return_usd",
        formula="ending_equity - initial_equity",
        units="currency",
        required_inputs=("equity_curve",),
        return_scale="currency",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when equity curve has fewer than two points"
        ),
    ),
    "cagr": MetricDefinition(
        name="cagr",
        formula=(
            "((final_value / initial_value) ** (1.0 / years) - 1.0) * 100"
        ),
        units="percent",
        required_inputs=("initial_value", "final_value", "years"),
        return_scale="percent",
        annualization_basis="years elapsed",
        minimum_sample_size=1,
        undefined_behavior=(
            "return None when initial_value, final_value, or years is"
            " non-positive"
        ),
        golden_fixture="10 000 → 12 000 over 2 years ≈ 9.54 %",
    ),
    "annualized_return": MetricDefinition(
        name="annualized_return",
        formula=(
            "((geometric_mean + 1) ** periods_per_year - 1) * 100"
        ),
        units="percent",
        required_inputs=("returns",),
        optional_inputs=("periods_per_year",),
        return_scale="percent",
        annualization_basis="configured periods (AnalyticsConfig.annualization_periods)",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when returns list is empty or periods_per_year <= 0"
        ),
    ),
    "compound_monthly_growth_rate": MetricDefinition(
        name="compound_monthly_growth_rate",
        formula=(
            "((final_value / initial_value) ** (1.0 / months) - 1.0) * 100"
        ),
        units="percent",
        required_inputs=("initial_value", "final_value", "months"),
        return_scale="percent",
        annualization_basis="months elapsed",
        minimum_sample_size=1,
        undefined_behavior=(
            "return None when initial_value, final_value, or months"
            " is non-positive"
        ),
    ),
    "buy_and_hold_cagr": MetricDefinition(
        name="buy_and_hold_cagr",
        formula=(
            "CAGR(price_values[0], price_values[-1], years)"
        ),
        units="percent",
        required_inputs=("price_values", "years"),
        return_scale="percent",
        annualization_basis="years elapsed",
        minimum_sample_size=2,
        undefined_behavior=(
            "return None when price series has fewer than two points or"
            " years is non-positive"
        ),
    ),
    "buy_and_hold_return": MetricDefinition(
        name="buy_and_hold_return",
        formula=(
            "((price_values[-1] - price_values[0]) / price_values[0]) * 100"
        ),
        units="percent",
        required_inputs=("price_values",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior=(
            "return None when price series has fewer than two points or"
            " first price is non-positive"
        ),
    ),
    # ── Trade count metrics ──────────────────────────────────────────────────
    "total_trades": MetricDefinition(
        name="total_trades",
        formula="count(closed_trades)",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=0,
        undefined_behavior="return 0 when no trades are supplied",
    ),
    "winning_trades": MetricDefinition(
        name="winning_trades",
        formula="count(t for t in closed_trades if pnl(t) > epsilon)",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=0,
        undefined_behavior="return 0 when no closed trades exist",
    ),
    "losing_trades": MetricDefinition(
        name="losing_trades",
        formula="count(t for t in closed_trades if pnl(t) < -epsilon)",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=0,
        undefined_behavior="return 0 when no closed trades exist",
    ),
    "breakeven_trades": MetricDefinition(
        name="breakeven_trades",
        formula=(
            "count(t for t in closed_trades if abs(pnl(t)) <= epsilon)"
        ),
        units="count",
        required_inputs=("trades",),
        optional_inputs=("breakeven_epsilon",),
        return_scale="count",
        minimum_sample_size=0,
        undefined_behavior="return 0 when no closed trades exist",
    ),
    "long_trades": MetricDefinition(
        name="long_trades",
        formula="count(t for t in closed_trades if direction(t) in (long,buy))",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=0,
        undefined_behavior="return 0 when no closed trades exist",
    ),
    "short_trades": MetricDefinition(
        name="short_trades",
        formula=(
            "count(t for t in closed_trades if direction(t) in"
            " (short,sell))"
        ),
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=0,
        undefined_behavior="return 0 when no closed trades exist",
    ),
    # ── Win / loss rate metrics ──────────────────────────────────────────────
    "win_rate": MetricDefinition(
        name="win_rate",
        formula="winning_closed_trades / closed_trades",
        units="fraction",
        required_inputs=("trades",),
        accepted_aliases=("win_rate_fraction",),
        return_scale="fraction",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
        golden_fixture="6 wins from 10 closed trades → 0.6",
    ),
    "win_rate_fraction": MetricDefinition(
        name="win_rate_fraction",
        formula="winning_closed_trades / closed_trades",
        units="fraction",
        required_inputs=("trades",),
        accepted_aliases=("win_rate",),
        return_scale="fraction",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    "loss_rate": MetricDefinition(
        name="loss_rate",
        formula="losing_closed_trades / closed_trades",
        units="fraction",
        required_inputs=("trades",),
        return_scale="fraction",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    # ── PnL summary metrics ──────────────────────────────────────────────────
    "net_profit": MetricDefinition(
        name="net_profit",
        formula="sum(pnl(t) for t in closed_trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    "gross_profit": MetricDefinition(
        name="gross_profit",
        formula=(
            "sum(pnl(t) for t in closed_trades if pnl(t) > 0)"
        ),
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no winning trades exist",
    ),
    "gross_loss": MetricDefinition(
        name="gross_loss",
        formula=(
            "sum(pnl(t) for t in closed_trades if pnl(t) < 0)"
        ),
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no losing trades exist",
    ),
    "avg_win": MetricDefinition(
        name="avg_win",
        formula="mean(pnl(t) for t in closed_trades if pnl(t) > 0)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no winning trades exist",
    ),
    "avg_loss": MetricDefinition(
        name="avg_loss",
        formula="mean(pnl(t) for t in closed_trades if pnl(t) < 0)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no losing trades exist",
    ),
    "avg_win_loss": MetricDefinition(
        name="avg_win_loss",
        formula="avg_win / abs(avg_loss)",
        units="ratio",
        required_inputs=("trades",),
        return_scale="ratio",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when avg_loss is zero or no losing trades exist"
        ),
    ),
    "largest_win": MetricDefinition(
        name="largest_win",
        formula="max(pnl(t) for t in closed_trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    "largest_loss": MetricDefinition(
        name="largest_loss",
        formula="min(pnl(t) for t in closed_trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    "median_win": MetricDefinition(
        name="median_win",
        formula="median(pnl(t) for t in winning_closed_trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no winning trades exist",
    ),
    "median_loss": MetricDefinition(
        name="median_loss",
        formula="median(pnl(t) for t in losing_closed_trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no losing trades exist",
    ),
    "expectancy": MetricDefinition(
        name="expectancy",
        formula="mean(pnl(t) for t in closed_trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    # ── Consecutive streak metrics ───────────────────────────────────────────
    "max_consecutive_wins": MetricDefinition(
        name="max_consecutive_wins",
        formula="max length of consecutive winning trade streaks",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=1,
        undefined_behavior="return 0 when no closed trades exist",
    ),
    "max_consecutive_losses": MetricDefinition(
        name="max_consecutive_losses",
        formula="max length of consecutive losing trade streaks",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=1,
        undefined_behavior="return 0 when no closed trades exist",
    ),
    "avg_consecutive_wins": MetricDefinition(
        name="avg_consecutive_wins",
        formula="mean length of all winning streaks",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no winning streaks exist",
    ),
    "avg_consecutive_losses": MetricDefinition(
        name="avg_consecutive_losses",
        formula="mean length of all losing streaks",
        units="count",
        required_inputs=("trades",),
        return_scale="count",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no losing streaks exist",
    ),
    # ── Time-in-trade metrics ────────────────────────────────────────────────
    "avg_time_in_trade": MetricDefinition(
        name="avg_time_in_trade",
        formula=(
            "mean((close_time - open_time).total_seconds() / 3600"
            " for t in closed_trades)"
        ),
        units="hours",
        required_inputs=("trades",),
        return_scale="hours",
        minimum_sample_size=1,
        undefined_behavior=(
            "return 0.0 when no closed trades have parseable timestamps"
        ),
    ),
    "median_time_in_trade": MetricDefinition(
        name="median_time_in_trade",
        formula="median trade duration in hours",
        units="hours",
        required_inputs=("trades",),
        return_scale="hours",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    "max_time_in_trade": MetricDefinition(
        name="max_time_in_trade",
        formula="max trade duration in hours",
        units="hours",
        required_inputs=("trades",),
        return_scale="hours",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    "min_time_in_trade": MetricDefinition(
        name="min_time_in_trade",
        formula="min trade duration in hours",
        units="hours",
        required_inputs=("trades",),
        return_scale="hours",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    # ── R-multiple metrics ───────────────────────────────────────────────────
    "r_multiple": MetricDefinition(
        name="r_multiple",
        formula="net_pnl / initial_risk",
        units="R",
        required_inputs=("net_pnl", "initial_risk"),
        optional_inputs=("profit_loss", "risk"),
        accepted_aliases=("r_multiples", "get_r_multiples"),
        return_scale="R",
        minimum_sample_size=1,
        undefined_behavior=(
            "skip values without non-zero initial_risk; emit degraded"
            " warning when proxy fallback is used"
        ),
        golden_fixture="100 profit over 50 risk equals 2.0 R",
    ),
    "r_multiple_proxy_profit_loss": MetricDefinition(
        name="r_multiple_proxy_profit_loss",
        formula="profit_loss / 1.0 when explicit initial_risk is unavailable",
        units="R proxy",
        required_inputs=("profit_loss",),
        return_scale="R",
        minimum_sample_size=1,
        undefined_behavior=(
            "emit DEGRADED_CONFIDENCE warning; mark affected metric as"
            " confidence=degraded"
        ),
        role="diagnostic_estimate",
        confidence="degraded",
    ),
    "expectancy_r": MetricDefinition(
        name="expectancy_r",
        formula="mean(r_multiple(t) for t in trades)",
        units="R",
        required_inputs=("trades",),
        accepted_aliases=("r_expectancy",),
        return_scale="R",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no R-multiples can be computed",
    ),
    "avg_r_multiple": MetricDefinition(
        name="avg_r_multiple",
        formula="mean(r_multiples)",
        units="R",
        required_inputs=("trades",),
        return_scale="R",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no R-multiples can be computed",
    ),
    "median_r_multiple": MetricDefinition(
        name="median_r_multiple",
        formula="median(r_multiples)",
        units="R",
        required_inputs=("trades",),
        return_scale="R",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no R-multiples can be computed",
    ),
    "max_r_multiple": MetricDefinition(
        name="max_r_multiple",
        formula="max(r_multiples)",
        units="R",
        required_inputs=("trades",),
        return_scale="R",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no R-multiples can be computed",
    ),
    "min_r_multiple": MetricDefinition(
        name="min_r_multiple",
        formula="min(r_multiples)",
        units="R",
        required_inputs=("trades",),
        return_scale="R",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no R-multiples can be computed",
    ),
    # ── Profit / factor / ratio metrics ─────────────────────────────────────
    "profit_factor": MetricDefinition(
        name="profit_factor",
        formula="gross_profit / abs(gross_loss)",
        units="ratio",
        required_inputs=("trades",),
        return_scale="ratio",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 for no trades; return sentinel 999.0 when"
            " gross_loss is zero; emit warning metadata"
        ),
        role="scorecard_input",
        golden_fixture="600 profit, 300 loss → 2.0",
    ),
    "payoff_ratio": MetricDefinition(
        name="payoff_ratio",
        formula="avg_win / abs(avg_loss)",
        units="ratio",
        required_inputs=("trades",),
        return_scale="ratio",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when avg_loss is zero or no losing trades exist"
        ),
    ),
    "edge_ratio": MetricDefinition(
        name="edge_ratio",
        formula="win_rate * payoff_ratio - (1 - win_rate)",
        units="ratio",
        required_inputs=("trades",),
        return_scale="ratio",
        minimum_sample_size=2,
        undefined_behavior="return 0.0 when no trades exist",
    ),
    "sqn": MetricDefinition(
        name="sqn",
        formula="sqrt(n) * mean_pnl / std_pnl",
        units="dimensionless",
        required_inputs=("trades",),
        return_scale="scalar",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when fewer than 2 closed trades or zero std"
        ),
        role="scorecard_input",
        golden_fixture="100 trades, mean 10, std 20 → SQN ≈ 5.0",
    ),
    "t_statistic": MetricDefinition(
        name="t_statistic",
        formula="mean_pnl / (std_pnl / sqrt(n))",
        units="dimensionless",
        required_inputs=("trades",),
        return_scale="scalar",
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when fewer than 2 closed trades or zero variance"
        ),
    ),
    "kelly_criterion": MetricDefinition(
        name="kelly_criterion",
        formula="win_rate - (1 - win_rate) / payoff_ratio",
        units="fraction",
        required_inputs=("trades",),
        return_scale="fraction",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when payoff_ratio <= 0 or no closed trades"
        ),
    ),
    # ── Drawdown metrics ─────────────────────────────────────────────────────
    "max_drawdown": MetricDefinition(
        name="max_drawdown",
        formula="max peak-to-valley percentage decline from returns",
        units="percent",
        required_inputs=("returns",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when equity curve has no drawdown or insufficient"
            " data"
        ),
        role="scorecard_input",
    ),
    "max_strategy_drawdown": MetricDefinition(
        name="max_strategy_drawdown",
        formula="max(peak - equity) for each point in equity_curve",
        units="currency",
        required_inputs=("equity_curve",),
        return_scale="currency",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when no drawdown exists in the equity curve"
        ),
    ),
    "max_strategy_drawdown_percent": MetricDefinition(
        name="max_strategy_drawdown_percent",
        formula="max((peak - equity) / peak) * 100",
        units="percent",
        required_inputs=("equity_curve",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when no drawdown exists or peak is non-positive"
        ),
        role="scorecard_input",
    ),
    "avg_drawdown": MetricDefinition(
        name="avg_drawdown",
        formula="mean(drawdown_series[drawdown_series > 0]) * 100",
        units="percent",
        required_inputs=("equity_curve",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior="return 0.0 when no underwater periods exist",
    ),
    "calmar_ratio": MetricDefinition(
        name="calmar_ratio",
        formula="annualized_return / max_drawdown",
        units="ratio",
        required_inputs=("annualized_return", "max_drawdown"),
        return_scale="ratio",
        annualization_basis=(
            "configured periods (AnalyticsConfig.annualization_periods)"
        ),
        minimum_sample_size=2,
        undefined_behavior="return 0.0 when max_drawdown is zero",
    ),
    "ulcer_index": MetricDefinition(
        name="ulcer_index",
        formula="sqrt(mean(drawdown_series ** 2)) * 100",
        units="percent",
        required_inputs=("equity_curve",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior="return 0.0 when equity curve is empty",
    ),
    "pain_index": MetricDefinition(
        name="pain_index",
        formula="mean(drawdown_series) * 100",
        units="percent",
        required_inputs=("equity_curve",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior="return 0.0 when equity curve is empty",
    ),
    "recovery_factor": MetricDefinition(
        name="recovery_factor",
        formula="net_profit / max_drawdown",
        units="ratio",
        required_inputs=("net_profit", "max_drawdown"),
        return_scale="ratio",
        minimum_sample_size=1,
        undefined_behavior=(
            "return 0.0 when max_drawdown is zero or non-positive"
        ),
    ),
    # ── Risk metrics ─────────────────────────────────────────────────────────
    "sharpe_ratio": MetricDefinition(
        name="sharpe_ratio",
        formula="mean(excess_returns) / std(excess_returns)",
        units="ratio",
        required_inputs=("returns",),
        optional_inputs=("risk_free_rate",),
        return_scale="ratio",
        annualization_basis=(
            "configured periods (AnalyticsConfig.annualization_periods)"
        ),
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 for insufficient variance or fewer than 2 returns"
        ),
        role="scorecard_input",
        golden_fixture=(
            "daily returns with mean 0.001, std 0.01 → Sharpe ≈ 0.1"
        ),
    ),
    "annualized_sharpe_ratio": MetricDefinition(
        name="annualized_sharpe_ratio",
        formula="sharpe_ratio * sqrt(annualization_periods)",
        units="ratio",
        required_inputs=("returns",),
        optional_inputs=("risk_free_rate", "periods"),
        return_scale="ratio",
        annualization_basis=(
            "configured periods (AnalyticsConfig.annualization_periods)"
        ),
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 for insufficient variance or fewer than 2 returns"
        ),
    ),
    "sortino_ratio": MetricDefinition(
        name="sortino_ratio",
        formula="mean(excess_returns) / downside_deviation",
        units="ratio",
        required_inputs=("returns",),
        optional_inputs=("risk_free_rate", "target"),
        return_scale="ratio",
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when downside deviation is zero or insufficient"
            " data"
        ),
    ),
    "volatility": MetricDefinition(
        name="volatility",
        formula="std(returns) * 100",
        units="percent",
        required_inputs=("returns",),
        return_scale="percent",
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when fewer than 2 returns or zero variance"
        ),
    ),
    "annualized_volatility": MetricDefinition(
        name="annualized_volatility",
        formula="volatility * sqrt(annualization_periods)",
        units="percent",
        required_inputs=("returns",),
        optional_inputs=("periods",),
        return_scale="percent",
        annualization_basis=(
            "configured periods (AnalyticsConfig.annualization_periods)"
        ),
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when fewer than 2 returns or zero variance"
        ),
    ),
    "downside_volatility": MetricDefinition(
        name="downside_volatility",
        formula="sqrt(sum((r - target)^2 for r < target) / (n - 1)) * 100",
        units="percent",
        required_inputs=("returns",),
        optional_inputs=("target",),
        return_scale="percent",
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when fewer than 2 below-target returns"
        ),
    ),
    "value_at_risk": MetricDefinition(
        name="value_at_risk",
        formula=(
            "abs(sorted_returns[int(n * (1 - confidence))]) * 100"
        ),
        units="percent",
        required_inputs=("returns",),
        optional_inputs=("confidence",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior="return 0.0 when returns list is empty",
    ),
    "conditional_var": MetricDefinition(
        name="conditional_var",
        formula=(
            "mean(abs(r) for r in sorted_returns[:tail_idx]) * 100"
        ),
        units="percent",
        required_inputs=("returns",),
        optional_inputs=("confidence",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when returns list is empty or tail is empty"
        ),
    ),
    "expected_shortfall": MetricDefinition(
        name="expected_shortfall",
        formula="conditional_var at specified confidence level",
        units="percent",
        required_inputs=("returns",),
        optional_inputs=("confidence",),
        accepted_aliases=("conditional_var",),
        return_scale="percent",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when returns list is empty or tail is empty"
        ),
    ),
    # ── Benchmark comparison metrics ─────────────────────────────────────────
    "beta": MetricDefinition(
        name="beta",
        formula="cov(strategy, benchmark) / var(benchmark)",
        units="dimensionless",
        required_inputs=("strategy_returns", "benchmark_returns"),
        return_scale="scalar",
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 1.0 when benchmark variance is zero or fewer than 2"
            " aligned returns"
        ),
    ),
    "alpha": MetricDefinition(
        name="alpha",
        formula=(
            "(E[R_s] - [R_f + beta * (E[R_b] - R_f)]) * annualization_periods"
            " * 100"
        ),
        units="percent",
        required_inputs=("strategy_returns", "benchmark_returns"),
        optional_inputs=("risk_free_rate",),
        return_scale="percent",
        annualization_basis=(
            "configured periods (AnalyticsConfig.annualization_periods)"
        ),
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when no aligned returns are available"
        ),
    ),
    "information_ratio": MetricDefinition(
        name="information_ratio",
        formula=(
            "(mean(strategy - benchmark) / std(strategy - benchmark))"
            " * sqrt(annualization_periods)"
        ),
        units="ratio",
        required_inputs=("strategy_returns", "benchmark_returns"),
        return_scale="ratio",
        annualization_basis=(
            "configured periods (AnalyticsConfig.annualization_periods)"
        ),
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when tracking error is zero or fewer than 2"
            " aligned returns"
        ),
    ),
    "tracking_error": MetricDefinition(
        name="tracking_error",
        formula=(
            "std(strategy_returns - benchmark_returns)"
            " * sqrt(annualization_periods) * 100"
        ),
        units="percent",
        required_inputs=("strategy_returns", "benchmark_returns"),
        return_scale="percent",
        annualization_basis=(
            "configured periods (AnalyticsConfig.annualization_periods)"
        ),
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when fewer than 2 aligned returns"
        ),
    ),
    # ── Distribution metrics ─────────────────────────────────────────────────
    "return_volatility": MetricDefinition(
        name="return_volatility",
        formula="std(returns)",
        units="fraction",
        required_inputs=("returns",),
        return_scale="fraction",
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when fewer than 2 returns or zero variance"
        ),
    ),
    "return_skewness": MetricDefinition(
        name="return_skewness",
        formula="m3(returns) / std(returns)^3",
        units="dimensionless",
        required_inputs=("returns",),
        return_scale="scalar",
        sample_convention="population",
        minimum_sample_size=3,
        undefined_behavior=(
            "return 0.0 when fewer than 3 returns or zero variance"
        ),
    ),
    "return_kurtosis": MetricDefinition(
        name="return_kurtosis",
        formula="m4(returns) / std(returns)^4 - 3",
        units="dimensionless",
        required_inputs=("returns",),
        return_scale="scalar",
        sample_convention="population",
        minimum_sample_size=4,
        undefined_behavior=(
            "return 0.0 when fewer than 4 returns or zero variance"
        ),
    ),
    # ── Efficiency metrics ───────────────────────────────────────────────────
    "capital_efficiency": MetricDefinition(
        name="capital_efficiency",
        formula="net_profit / nominal_capital_deployed",
        units="ratio",
        required_inputs=("net_profit", "nominal_capital_deployed"),
        return_scale="ratio",
        minimum_sample_size=1,
        undefined_behavior=(
            "return 0.0 when nominal_capital_deployed is non-positive"
        ),
    ),
    "return_per_unit_mae": MetricDefinition(
        name="return_per_unit_mae",
        formula="net_profit / total_mae",
        units="ratio",
        required_inputs=("trades",),
        return_scale="ratio",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when total MAE is zero",
    ),
    "return_per_unit_mfe": MetricDefinition(
        name="return_per_unit_mfe",
        formula="net_profit / total_mfe",
        units="ratio",
        required_inputs=("trades",),
        return_scale="ratio",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when total MFE is zero",
    ),
    # ── Exposure / time in market ────────────────────────────────────────────
    "percent_time_in_market": MetricDefinition(
        name="percent_time_in_market",
        formula=(
            "time_in_market_duration(trades) / period_duration_hours"
        ),
        units="fraction",
        required_inputs=("trades", "period_duration_hours"),
        return_scale="fraction",
        minimum_sample_size=1,
        undefined_behavior=(
            "return 0.0 when period_duration_hours is non-positive"
        ),
    ),
    "time_in_market_duration": MetricDefinition(
        name="time_in_market_duration",
        formula=(
            "sum of merged overlapping open/close trade intervals in hours"
        ),
        units="hours",
        required_inputs=("trades",),
        return_scale="hours",
        minimum_sample_size=1,
        undefined_behavior=(
            "return 0.0 when no closed trades have parseable timestamps"
        ),
    ),
    # ── Statistical validation metrics ───────────────────────────────────────
    "r_signal_to_noise": MetricDefinition(
        name="r_signal_to_noise",
        formula="mean(r_multiples) / std(r_multiples)",
        units="ratio",
        required_inputs=("trades",),
        return_scale="ratio",
        sample_convention="sample",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when R-multiple std is zero or fewer than 2"
        ),
    ),
    "rolling_expectancy_stability": MetricDefinition(
        name="rolling_expectancy_stability",
        formula="std(rolling_window_expectancies)",
        units="currency",
        required_inputs=("trades",),
        optional_inputs=("window",),
        return_scale="currency",
        sample_convention="sample",
        minimum_sample_size=10,
        undefined_behavior=(
            "return 0.0 when fewer trades than window size"
        ),
    ),
    "win_after_win_probability": MetricDefinition(
        name="win_after_win_probability",
        formula=(
            "count(win then win pairs) / count(win as first in pair)"
        ),
        units="fraction",
        required_inputs=("trades",),
        return_scale="fraction",
        minimum_sample_size=2,
        undefined_behavior="return 0.0 when no win-then-pair exists",
    ),
    "runs_test_zscore": MetricDefinition(
        name="runs_test_zscore",
        formula=(
            "(observed_runs - expected_runs) / sqrt(variance_runs)"
        ),
        units="dimensionless",
        required_inputs=("trades",),
        return_scale="scalar",
        minimum_sample_size=2,
        undefined_behavior=(
            "return 0.0 when only wins or only losses; variance zero"
        ),
    ),
    # ── Size metrics ─────────────────────────────────────────────────────────
    "max_gross_size_held": MetricDefinition(
        name="max_gross_size_held",
        formula="max(abs(size(t)) for t in trades)",
        units="contracts",
        required_inputs=("trades",),
        return_scale="contracts",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no trades exist",
    ),
    "max_size_held": MetricDefinition(
        name="max_size_held",
        formula="max(abs(size(t)) for t in trades)",
        units="contracts",
        required_inputs=("trades",),
        return_scale="contracts",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no trades exist",
    ),
    "max_net_size_held": MetricDefinition(
        name="max_net_size_held",
        formula=(
            "max abs value of running net (long - short) position size"
        ),
        units="contracts",
        required_inputs=("trades",),
        return_scale="contracts",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no trades exist",
    ),
    "max_long_size_held": MetricDefinition(
        name="max_long_size_held",
        formula="max(size(t) for t in long_trades)",
        units="contracts",
        required_inputs=("trades",),
        return_scale="contracts",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no long trades exist",
    ),
    "max_short_size_held": MetricDefinition(
        name="max_short_size_held",
        formula="max(size(t) for t in short_trades)",
        units="contracts",
        required_inputs=("trades",),
        return_scale="contracts",
        minimum_sample_size=1,
        undefined_behavior="return 0.0 when no short trades exist",
    ),
    # ── Cost metrics ─────────────────────────────────────────────────────────
    "slippage_paid": MetricDefinition(
        name="slippage_paid",
        formula="sum(abs(slippage(t)) for t in trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=0,
        undefined_behavior="return 0.0 when no slippage data",
    ),
    "commission_paid": MetricDefinition(
        name="commission_paid",
        formula="sum(abs(commission(t)) for t in trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=0,
        undefined_behavior="return 0.0 when no commission data",
    ),
    "swap_paid": MetricDefinition(
        name="swap_paid",
        formula="sum(abs(swap(t)) for t in trades)",
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=0,
        undefined_behavior="return 0.0 when no swap data",
    ),
    "open_position_pnl": MetricDefinition(
        name="open_position_pnl",
        formula=(
            "sum(unrealized_pnl(t) for t in trades if t.is_open)"
        ),
        units="currency",
        required_inputs=("trades",),
        return_scale="currency",
        minimum_sample_size=0,
        undefined_behavior="return 0.0 when no open trades exist",
    ),
}

OFFICIAL_ANALYTICS_TOOL_CATALOG: dict[str, ToolDefinition] = {
    "build_analytics_report": ToolDefinition(
        name="build_analytics_report",
        input_schema=(
            "TradingResult dictionary with trades and equity_curve."
        ),
        output_schema=(
            "StandardResponse containing versioned AnalyticsReport data."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_report.py",
        ),
    ),
    "build_portfolio_analytics_report": ToolDefinition(
        name="build_portfolio_analytics_report",
        input_schema=(
            "Portfolio result dictionary with component_results."
        ),
        output_schema=(
            "StandardResponse containing portfolio analytics summary."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="approved_experimental",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_report.py",
        ),
    ),
    "evaluate_strategy_quality": ToolDefinition(
        name="evaluate_strategy_quality",
        input_schema="Analytics report dictionary.",
        output_schema=(
            "StandardResponse containing non-binding scorecard context."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_scorecard.py",
        ),
    ),
    "calculate_trade_metrics": ToolDefinition(
        name="calculate_trade_metrics",
        input_schema=(
            "List/dataframe-like collection of trade records."
        ),
        output_schema=(
            "StandardResponse containing aggregate trade metrics."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_metrics.py",
        ),
    ),
    "calculate_equity_metrics": ToolDefinition(
        name="calculate_equity_metrics",
        input_schema="List/dataframe-like equity curve.",
        output_schema=(
            "StandardResponse containing equity and return metrics."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_metrics.py",
        ),
    ),
    "calculate_drawdown_metrics": ToolDefinition(
        name="calculate_drawdown_metrics",
        input_schema="List/dataframe-like equity curve.",
        output_schema=(
            "StandardResponse containing drawdown metrics."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_metrics.py",
        ),
    ),
    "calculate_risk_metrics": ToolDefinition(
        name="calculate_risk_metrics",
        input_schema="Numeric return series.",
        output_schema=(
            "StandardResponse containing risk metrics."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_metrics.py",
        ),
    ),
    "calculate_benchmark_metrics": ToolDefinition(
        name="calculate_benchmark_metrics",
        input_schema="Strategy and benchmark return series.",
        output_schema=(
            "StandardResponse containing aligned benchmark metrics."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_metrics.py",
        ),
    ),
    "calculate_statistical_validation": ToolDefinition(
        name="calculate_statistical_validation",
        input_schema="Numeric return series.",
        output_schema=(
            "StandardResponse containing statistical validation data."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; deterministic when seeded helpers are used"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_report.py",
        ),
    ),
    "calculate_prop_firm_compliance": ToolDefinition(
        name="calculate_prop_firm_compliance",
        input_schema="Analytics report dictionary.",
        output_schema=(
            "StandardResponse containing non-binding compliance context."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="approved_experimental",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_report.py",
        ),
    ),
    "build_overview_payload": ToolDefinition(
        name="build_overview_payload",
        input_schema="Validated AnalyticsReport dictionary.",
        output_schema=(
            "StandardResponse containing dashboard-ready overview payload."
        ),
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects=(
            "read-only; no writes, trades, database mutations, or network"
        ),
        stability="stable",
        agent_api_safe=True,
        tests=(
            "tests/unit/app/services/analytics/test_metrics.py",
        ),
    ),
}

SCHEMA_COMPATIBILITY_MATRIX: dict[str, SchemaStatus] = {
    "1.0.0": "legacy_adapted",
    "1.1.0": "legacy_adapted",
    "1.2.0": "deprecated",
    "1.3.1": "accepted",
    "2.0.0": "unsupported_future",
}

WARNING_SEVERITY_LEVELS = (
    "informational",
    "warning",
    "major",
    "critical",
    "blocker",
)

DECIMAL_PRECISION_POLICY = (
    "Canonical monetary sums, cost aggregation, and base-currency"
    " aggregation use float64 arithmetic with derived_ratio_tolerance"
    " documented in AnalyticsConfig.  Reports must include"
    " monetary_precision_mode in metadata."
)


def validate_metric_catalog(
    catalog: MetricDefinitionCatalog | None = None,
) -> dict[str, Any]:
    """Validate that metric catalog entries are complete and unique.

    Args:
        catalog: Optional catalog to validate.  Defaults to
            ``METRIC_DEFINITION_CATALOG``.

    Returns:
        JSON-safe validation summary with ``status``, ``metric_count``,
        and ``metrics``.

    Raises:
        ValidationError: If a catalog entry is malformed or duplicated.

    Side effects:
        None.
    """
    active = (
        METRIC_DEFINITION_CATALOG if catalog is None else catalog
    )
    if not isinstance(active, dict) or not active:
        raise ValidationError(
            "metric catalog must be a non-empty dictionary."
        )

    seen: set[str] = set()
    for key, definition in active.items():
        if key in seen:
            raise ValidationError(
                f"duplicate metric definition: {key}"
            )
        seen.add(key)
        if not isinstance(definition, MetricDefinition):
            raise ValidationError(
                f"metric definition for {key!r} is invalid."
            )
        if key != definition.name:
            raise ValidationError(
                f"metric catalog key mismatch for {key!r}."
            )
        if not definition.formula.strip():
            raise ValidationError(
                f"metric {key!r} must define a formula."
            )
        if not definition.required_inputs:
            raise ValidationError(
                f"metric {key!r} must define required inputs."
            )
        if definition.minimum_sample_size < 0:
            raise ValidationError(
                f"metric {key!r} must not use a negative minimum"
                " sample size."
            )

    return {
        "status": "valid",
        "metric_count": len(active),
        "metrics": sorted(active),
    }


# Compatibility aliases named by the implementation plan.
Request = AnalyticsRequest
Result = AnalyticsResult
Config = AnalyticsConfig
Metadata = AnalyticsMetadata
