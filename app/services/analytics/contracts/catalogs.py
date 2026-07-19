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


def _unit_for(metric_key: str) -> str:
    """Return the catalog unit for one metric.

    Args:
        metric_key: Catalog metric key.

    Returns:
        Approved unit label.
    """
    logger.debug("Resolving Analytics metric catalog unit")
    if metric_key in _MONETARY_METRICS:
        return "currency"
    if metric_key in _COUNT_METRICS:
        return "count"
    if metric_key in _DURATION_METRICS:
        return "duration"
    return "ratio"


def _definition(metric_key: str) -> Mapping[str, object]:
    """Build one complete immutable metric definition.

    Args:
        metric_key: Catalog metric key.

    Returns:
        Complete immutable metric definition.
    """
    logger.debug("Building Analytics metric catalog definition")
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
            "formula": metric_key,
            "unit": _unit_for(metric_key),
            "inputs": ("closed_trades",),
            "scale": "absolute" if _unit_for(metric_key) != "ratio" else "ratio",
            "annualization": 252 if annualized else None,
            "sample_convention": "cataloged",
            "minimum_sample": 0 if metric_key in _COUNT_METRICS else 1,
            "undefined_behavior": "None with cataloged warning",
            "evidence_type": "metric",
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
        "benchmark_no_overlap": (
            "major",
            ("strategy_points", "benchmark_points", "overlap_points"),
        ),
        "benchmark_currency_missing": ("major", ("strategy_currency",)),
        "benchmark_duplicate_resolved": (
            "informational",
            ("duplicate_count", "policy"),
        ),
        "annualization_blocked": ("major", ("metric_key", "reason")),
        "optional_section_skipped": ("informational", ("section", "reason")),
        "section_degraded": ("warning", ("section", "reason")),
        "drawdown_unrecovered": ("informational", ("trough_at", "window_end")),
        "costs_not_supplied": ("informational", ("missing_components",)),
        "statistical_evidence_skipped": ("warning", ("reason", "observed_count")),
        "series_truncated": (
            "informational",
            ("original_count", "returned_count", "method"),
        ),
        "source_metadata_truncated": ("informational", ("field", "original_bytes")),
        "stop_loss_absent": ("warning", ("ticket",)),
        "r_multiple_mae_fallback": ("warning", ("ticket", "basis")),
        "r_multiple_basis_mixed": (
            "major",
            ("declared_stop_count", "realized_mae_count"),
        ),
        "r_multiple_undefined": ("warning", ("ticket",)),
        "curve_basis_closed_trade": ("informational", ("curve_basis", "trade_count")),
        "mae_mfe_absent": ("informational", ("missing_fields",)),
        "daily_resample_sparse": ("warning", ("daily_points", "trade_count")),
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
        "fx_evidence_missing": (
            "blocker",
            True,
            ("component_id", "source_currency", "base_currency"),
        ),
        "fx_evidence_stale": ("blocker", True, ("as_of", "freshness_limit")),
        "component_schema_incompatible": (
            "blocker",
            True,
            ("component_id", "contract_version"),
        ),
        "measurement_window_mismatch": (
            "major",
            False,
            ("expected_window", "observed_window"),
        ),
        "execution_unreconciled": ("major", False, ("record_reference",)),
        "benchmark_unavailable": ("warning", False, ("reason",)),
        "initial_balance_required": ("blocker", True, ("source_contract",)),
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
        "trading.closed_trade_ledger": MappingProxyType(
            {"v1": "accepted", "legacy": "legacy-adapted"}
        ),
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
