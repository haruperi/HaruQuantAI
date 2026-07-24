"""Static Analytics metric, evidence, and compatibility catalogs."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.utils import logger

_METRIC_KEYS = (
    "trade_count",
    "win_count",
    "loss_count",
    "breakeven_count",
    "win_rate",
    "r_multiple",
    "r_multiple_basis",
    "r_multiple_potential",
    "market_presence",
    "max_win_streak",
    "max_loss_streak",
    "sum_winning_pnl",
    "sum_losing_pnl",
    "net_pnl",
    "starting_equity",
    "ending_equity",
    "period_returns",
    "cagr",
    "max_drawdown",
    "max_drawdown_duration",
    "drawdown_recovery",
    "ulcer_index",
    "pain_index",
    "volatility",
    "value_at_risk",
    "conditional_var",
    "sharpe_ratio",
    "sortino_ratio",
    "calmar_ratio",
    "profit_factor",
    "payoff_ratio",
    "expectancy",
    "benchmark_alpha",
    "benchmark_beta",
    "benchmark_correlation",
    "tracking_error",
    "information_ratio",
    "mean",
    "stdev",
    "skewness",
    "kurtosis",
    "percentiles",
    "tail_ratio",
    "histogram",
    "outliers",
    "bootstrap_confidence_interval",
    "permutation_p_value",
    "multiple_comparison_adjustment",
    "sample_adequacy",
    "total_commission",
    "total_swap",
    "total_cost_drag",
    "gross_pnl_before_costs",
    "total_mae",
    "total_mfe",
    "max_intratrade_excursion",
    "average_trade_duration",
    "trade_efficiency",
    "component_return_correlation",
    "capital_concentration_hhi",
)

_MONETARY_METRICS = frozenset(
    {
        "sum_winning_pnl",
        "sum_losing_pnl",
        "net_pnl",
        "expectancy",
        "starting_equity",
        "ending_equity",
        "total_commission",
        "total_swap",
        "total_cost_drag",
        "gross_pnl_before_costs",
        "total_mae",
        "total_mfe",
        "max_intratrade_excursion",
    }
)
_COUNT_METRICS = frozenset(
    {
        "trade_count",
        "win_count",
        "loss_count",
        "breakeven_count",
        "max_win_streak",
        "max_loss_streak",
        "histogram",
        "outliers",
    }
)
_DURATION_METRICS = frozenset(
    {
        "market_presence",
        "max_drawdown_duration",
        "drawdown_recovery",
        "average_trade_duration",
    }
)
_DAILY_METRICS = frozenset(
    {
        "period_returns",
        "volatility",
        "value_at_risk",
        "conditional_var",
        "sharpe_ratio",
        "sortino_ratio",
    }
)
_ALIGNED_METRICS = frozenset(
    {
        "benchmark_alpha",
        "benchmark_beta",
        "benchmark_correlation",
        "tracking_error",
        "information_ratio",
        "component_return_correlation",
    }
)
_SAMPLE_METRICS = frozenset(
    {
        "mean",
        "stdev",
        "skewness",
        "kurtosis",
        "percentiles",
        "tail_ratio",
        "histogram",
        "outliers",
        "bootstrap_confidence_interval",
        "permutation_p_value",
        "multiple_comparison_adjustment",
        "sample_adequacy",
    }
)
_FORMULAS: Mapping[str, str] = MappingProxyType(
    {
        "trade_count": "count of closed-trade ledger rows",
        "win_count": "count where net_trade_pnl exceeds BREAKEVEN_EPSILON",
        "loss_count": "count where net_trade_pnl is below negative BREAKEVEN_EPSILON",
        "breakeven_count": (
            "count where absolute net_trade_pnl is below BREAKEVEN_EPSILON"
        ),
        "win_rate": "win_count divided by trade_count",
        "r_multiple": (
            "direction-adjusted exit over declared-stop risk, "
            "with realized-MAE fallback"
        ),
        "r_multiple_basis": "count of applied declared_stop and realized_mae bases",
        "r_multiple_potential": "mean mfe divided by absolute mae",
        "market_presence": "duration of merged overlapping trade intervals",
        "max_win_streak": "longest exit-ordered consecutive winning run",
        "max_loss_streak": "longest exit-ordered consecutive losing run",
        "sum_winning_pnl": "sum of positive net_trade_pnl",
        "sum_losing_pnl": "sum of negative net_trade_pnl",
        "net_pnl": "sum of profit plus commission plus swap",
        "starting_equity": "caller-supplied initial_balance",
        "ending_equity": "initial_balance plus net_pnl",
        "period_returns": "daily equity divided by prior daily equity minus one",
        "cagr": "compound annual growth over the UTC measurement span",
        "max_drawdown": "maximum running-peak loss on the closed-trade equity curve",
        "max_drawdown_duration": "longest peak-to-recovery duration",
        "drawdown_recovery": "trough-to-prior-peak recovery duration",
        "ulcer_index": "square root of mean squared drawdown",
        "pain_index": "mean drawdown",
        "volatility": "sample daily-return deviation times square root of 252",
        "value_at_risk": "historical lower-tail daily-return percentile",
        "conditional_var": "mean daily return at or below historical value_at_risk",
        "sharpe_ratio": (
            "annualized mean daily excess return divided by its sample deviation"
        ),
        "sortino_ratio": "annualized mean excess return divided by downside deviation",
        "calmar_ratio": "cagr divided by max_drawdown",
        "profit_factor": "sum_winning_pnl divided by absolute sum_losing_pnl",
        "payoff_ratio": "mean winning net PnL divided by absolute mean losing net PnL",
        "expectancy": "win-weighted mean win minus loss-weighted absolute mean loss",
        "benchmark_alpha": (
            "annualized aligned strategy-on-benchmark regression intercept"
        ),
        "benchmark_beta": "aligned covariance divided by benchmark variance",
        "benchmark_correlation": "Pearson correlation of aligned returns",
        "tracking_error": "annualized sample deviation of aligned active returns",
        "information_ratio": (
            "annualized mean active return divided by active-return deviation"
        ),
        "mean": "arithmetic sample mean",
        "stdev": "sample standard deviation with ddof one",
        "skewness": "bias-corrected Fisher-Pearson standardized moment",
        "kurtosis": "bias-corrected excess kurtosis",
        "percentiles": "linear interpolation at the cataloged percentile set",
        "tail_ratio": "absolute 95th percentile divided by 5th percentile",
        "histogram": "counts in 50 deterministic equal-width bins",
        "outliers": "count outside Tukey 1.5-IQR fences",
        "bootstrap_confidence_interval": "seeded percentile-method bootstrap interval",
        "permutation_p_value": "seeded permutation estimate with add-one correction",
        "multiple_comparison_adjustment": (
            "Holm step-down adjustment of ordered p-values"
        ),
        "sample_adequacy": "observed sample count against cataloged minimum",
        "total_commission": "sum of signed commission",
        "total_swap": "sum of signed swap",
        "total_cost_drag": "total_commission plus total_swap",
        "gross_pnl_before_costs": "sum of gross profit",
        "total_mae": "sum of supplied adverse excursions",
        "total_mfe": "sum of supplied favorable excursions",
        "max_intratrade_excursion": "largest absolute supplied adverse excursion",
        "average_trade_duration": "mean exit_time minus entry_time",
        "trade_efficiency": "net_pnl divided by gross_pnl_before_costs",
        "component_return_correlation": (
            "pairwise Pearson correlation on common UTC observations"
        ),
        "capital_concentration_hhi": "sum of squared component capital shares",
    }
)
_MINIMUM_SAMPLES: Mapping[str, int] = MappingProxyType(
    {
        "value_at_risk": 30,
        "conditional_var": 30,
        "benchmark_alpha": 30,
        "benchmark_beta": 30,
        "benchmark_correlation": 30,
        "tail_ratio": 20,
        "bootstrap_confidence_interval": 30,
        "permutation_p_value": 30,
        "multiple_comparison_adjustment": 2,
        "sample_adequacy": 1,
        "component_return_correlation": 30,
        "skewness": 3,
        "kurtosis": 4,
        "outliers": 4,
        "stdev": 2,
        "period_returns": 2,
        "volatility": 2,
        "sharpe_ratio": 2,
        "sortino_ratio": 2,
        "tracking_error": 2,
        "information_ratio": 2,
    }
)


def _unit_for(metric_key: str) -> str:
    """Return the catalog unit for one metric.

    Args:
        metric_key: Catalog metric key.

    Returns:
        Approved unit label.
    """
    if metric_key in _MONETARY_METRICS:
        return "currency"
    if metric_key in _COUNT_METRICS:
        return "count"
    if metric_key in _DURATION_METRICS:
        return "duration"
    if metric_key == "bootstrap_confidence_interval":
        return "interval"
    return "ratio"


def _inputs_for(metric_key: str) -> tuple[str, ...]:
    """Return the authoritative input family for one metric.

    Args:
        metric_key: Catalog metric key.

    Returns:
        Required input family.
    """
    if metric_key in _DAILY_METRICS:
        return ("daily_equity_curve", "daily_returns")
    if metric_key in _ALIGNED_METRICS:
        return ("aligned_return_observations",)
    if metric_key in _SAMPLE_METRICS:
        return ("bounded_numeric_sample",)
    if metric_key in {
        "cagr",
        "max_drawdown",
        "max_drawdown_duration",
        "drawdown_recovery",
        "ulcer_index",
        "pain_index",
    }:
        return ("closed_trade_equity_curve",)
    if metric_key == "capital_concentration_hhi":
        return ("converted_component_starting_equity",)
    return ("closed_trade_ledger",)


def _sample_convention_for(metric_key: str) -> str:
    """Return the cataloged sample convention for one metric."""
    if metric_key in _DAILY_METRICS:
        return "UTC calendar-daily resample"
    if metric_key in _ALIGNED_METRICS:
        return "exact UTC timestamp intersection"
    if metric_key in _SAMPLE_METRICS:
        return "bounded deterministic sample"
    if "drawdown" in metric_key or metric_key in {"cagr", "ulcer_index", "pain_index"}:
        return "full closed-trade equity curve"
    return "closed trades ordered by exit_time and ticket"


def _definition(metric_key: str) -> Mapping[str, object]:
    """Build one complete immutable metric definition.

    Args:
        metric_key: Catalog metric key.

    Returns:
        Complete immutable metric definition.
    """
    annualized = metric_key in {
        "cagr",
        "volatility",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "benchmark_alpha",
        "tracking_error",
        "information_ratio",
    }
    return MappingProxyType(
        {
            "formula": _FORMULAS[metric_key],
            "unit": _unit_for(metric_key),
            "inputs": _inputs_for(metric_key),
            "scale": "absolute" if _unit_for(metric_key) != "ratio" else "ratio",
            "annualization": 252 if annualized else None,
            "sample_convention": _sample_convention_for(metric_key),
            "minimum_sample": _MINIMUM_SAMPLES.get(
                metric_key, 0 if metric_key in _COUNT_METRICS else 1
            ),
            "undefined_behavior": (
                "real zero"
                if metric_key in _COUNT_METRICS
                else "None or skipped with cataloged warning; never fabricated"
            ),
            "evidence_type": (
                "monetary"
                if metric_key in _MONETARY_METRICS
                else "interval"
                if metric_key == "bootstrap_confidence_interval"
                else "series"
                if metric_key in {"period_returns", "percentiles", "histogram"}
                else "count"
                if metric_key in _COUNT_METRICS
                else "ratio"
            ),
            "fixture": f"tests/analytics/fixtures/golden/{metric_key}.json",
        }
    )


METRIC_DEFINITION_CATALOG: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {metric_key: _definition(metric_key) for metric_key in _METRIC_KEYS}
)

_WARNING_ROWS: Mapping[str, tuple[str, tuple[str, ...]]] = MappingProxyType(
    {
        "insufficient_samples": ("warning", ("observed_count", "required_count")),
        "undefined_zero_denominator": ("warning", ("metric_key",)),
        "undefined_zero_variance": ("warning", ("metric_key", "series_name")),
        "optional_section_skipped": ("informational", ("section", "reason")),
        "drawdown_unrecovered": ("informational", ("trough_at", "window_end")),
        "statistical_evidence_skipped": ("warning", ("reason", "observed_count")),
        "r_multiple_mae_fallback": ("warning", ("ticket", "basis")),
        "r_multiple_basis_mixed": (
            "major",
            ("declared_stop_count", "realized_mae_count"),
        ),
        "r_multiple_undefined": ("warning", ("ticket",)),
        "curve_basis_closed_trade": ("informational", ("curve_basis", "trade_count")),
        "mae_mfe_absent": ("informational", ("missing_fields",)),
    }
)

_QUALITY_ROWS: Mapping[str, tuple[str, bool, tuple[str, ...]]] = MappingProxyType(
    {
        "sample_below_threshold": (
            "warning",
            False,
            ("observed_count", "required_count"),
        ),
        "required_section_failed": ("blocker", True, ("section", "reason")),
        "diagnostic_partial_report": ("blocker", True, ("failed_sections",)),
        "intratrade_exposure_unobserved": ("warning", False, ("curve_basis",)),
    }
)

EVIDENCE_CATALOG: Mapping[str, Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {
        "warnings": MappingProxyType(
            {
                code: MappingProxyType(
                    {"severity": row[0], "required_detail_keys": row[1]}
                )
                for code, row in _WARNING_ROWS.items()
            }
        ),
        "quality_flags": MappingProxyType(
            {
                code: MappingProxyType(
                    {
                        "severity": row[0],
                        "blocker": row[1],
                        "required_detail_keys": row[2],
                    }
                )
                for code, row in _QUALITY_ROWS.items()
            }
        ),
    }
)

CONTRACT_COMPATIBILITY_MATRIX: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "trading.closed_trade_ledger": MappingProxyType({"v1": "accepted"}),
        "simulation.result": MappingProxyType({"v1": "accepted"}),
        "simulation.portfolio_result": MappingProxyType({"v1": "accepted"}),
        "analytics.performance_report": MappingProxyType({"v1": "accepted"}),
        "analytics.dashboard_payload": MappingProxyType({"v1": "accepted"}),
        "analytics.portfolio_allocation_evidence": MappingProxyType({"v1": "accepted"}),
    }
)


def validate_metric_catalog(catalog: Mapping[str, Mapping[str, object]]) -> None:
    """Validate completeness of an Analytics metric catalog.

    Args:
        catalog: Candidate catalog.

    Raises:
        AnalyticsValidationError: If a metric definition is incomplete.
    """
    logger.info("Validating Analytics metric definition catalog")
    required = {
        "formula",
        "unit",
        "inputs",
        "scale",
        "annualization",
        "sample_convention",
        "minimum_sample",
        "undefined_behavior",
        "evidence_type",
        "fixture",
    }
    if not catalog:
        raise AnalyticsValidationError("metric catalog must not be empty")
    for metric_key, definition in catalog.items():
        if set(definition) != required:
            message = f"metric definition is incomplete: {metric_key}"
            raise AnalyticsValidationError(message)
        if definition["formula"] == metric_key:
            message = f"metric formula is a placeholder: {metric_key}"
            raise AnalyticsValidationError(message)
        inputs = definition["inputs"]
        if not isinstance(inputs, tuple) or not inputs:
            message = f"metric inputs are invalid: {metric_key}"
            raise AnalyticsValidationError(message)


def validate_contract_version(contract: str, version: str) -> str:
    """Classify or reject one contract compatibility version.

    Args:
        contract: Compatibility-matrix contract key.
        version: Producer compatibility version.

    Returns:
        Compatibility classification.

    Raises:
        AnalyticsValidationError: If the contract or version is unsupported.
    """
    logger.info("Validating Analytics source contract compatibility")
    versions = CONTRACT_COMPATIBILITY_MATRIX.get(contract)
    if versions is None:
        message = f"unsupported source contract: {contract}"
        raise AnalyticsValidationError(message)
    classification = versions.get(version)
    if classification is None or classification in {"unsupported", "future"}:
        message = f"unsupported contract version: {contract} {version}"
        raise AnalyticsValidationError(message)
    return classification


__all__ = [
    "CONTRACT_COMPATIBILITY_MATRIX",
    "EVIDENCE_CATALOG",
    "METRIC_DEFINITION_CATALOG",
    "validate_contract_version",
    "validate_metric_catalog",
]
