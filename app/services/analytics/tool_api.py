"""High-level read-only analytics tool API.

This module is the architecture-approved public tool boundary for analytics.
It delegates to existing report, metric, benchmark, and scorecard builders and
keeps the surface low-risk, read-only, JSON-safe, and usable before UI/API
modules exist.
"""

from __future__ import annotations

from typing import Any, cast

from app.services.analytics.benchmarks import calculate_benchmark_metrics
from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.services.analytics.metrics.aggregate import (
    calculate_analytics_for_subset,
    calculate_trade_metrics,
)
from app.services.analytics.metrics.drawdown import calculate_drawdown_metrics
from app.services.analytics.metrics.equity import calculate_equity_metrics
from app.services.analytics.metrics.risk import calculate_risk_metrics
from app.services.analytics.reports import (
    build_analytics_report as _build_analytics_report,
)
from app.services.analytics.reports import (
    build_portfolio_analytics_report,
    calculate_prop_firm_compliance,
    calculate_statistical_validation,
    compare_analytics_reports,
)
from app.services.analytics.scorecards import evaluate_strategy_quality
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.logger import logger

BuildAnalyticsReportRequest = dict[str, Any]
BuildPortfolioAnalyticsReportRequest = dict[str, Any]
AnalyticsReport = dict[str, Any]
PortfolioAnalyticsReport = dict[str, Any]
AnalyticsComparison = dict[str, Any]
ComplianceProfile = dict[str, Any]
ComplianceEvidence = dict[str, Any]

DEFAULT_CONFIGURATION_SOURCES: dict[str, str] = {
    "annualization": "MetricConfig.annualization_periods",
    "risk_free_rate": "MetricConfig.risk_free_rate",
    "breakeven_tolerance": "MetricConfig.breakeven_epsilon",
    "minimum_sample_size": "MetricConfig.min_sample_size",
    "bootstrap_count_limits": "docs/adr/ADR-ANALYTICS-LIMITS.md",
    "dashboard_limits": "AnalyticsLimits.max_dashboard_points",
    "fx_stale_rate_limits": "caller-supplied validated fx_conversions",
    "confidence_alpha_levels": "statistical tool arguments",
}


def get_analytics_overview(
    request: BuildAnalyticsReportRequest,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate comprehensive analytics across all, long, and short subsets.

    Args:
        request: Canonical or adapter-compatible trading result payload.
        request_id: Optional trace identifier.

    Returns:
        Standard analytics response containing all/long/short subset evidence.
    """
    logger.debug("get_analytics_overview: executed.")
    meta = build_metadata(
        tool_name="get_analytics_overview",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    if not isinstance(request, dict):
        return response_from_exception(
            exception=ValidationError("request must be a dictionary."),
            metadata=meta,
        )
    trades = request.get("trades", [])
    if not isinstance(trades, list):
        return response_from_exception(
            exception=ValidationError("request.trades must be a list when supplied."),
            metadata=meta,
        )

    try:
        from app.services.analytics.contracts import MetricConfig

        config = MetricConfig(metadata={"request_id": request_id})
        long_trades = [
            trade
            for trade in trades
            if isinstance(trade, dict)
            and str(trade.get("direction", trade.get("side", ""))).lower()
            in {"long", "buy"}
        ]
        short_trades = [
            trade
            for trade in trades
            if isinstance(trade, dict)
            and str(trade.get("direction", trade.get("side", ""))).lower()
            in {"short", "sell"}
        ]
        data = {
            "all": calculate_analytics_for_subset(trades, config).value,
            "long": calculate_analytics_for_subset(long_trades, config).value,
            "short": calculate_analytics_for_subset(short_trades, config).value,
            "default_configuration_sources": DEFAULT_CONFIGURATION_SOURCES,
            "non_binding_analytics_evidence": True,
            "forbidden_claims": (
                "final_approval",
                "promotion",
                "live_readiness",
                "prop_firm_enforcement",
                "risk_limit_approval",
                "portfolio_allocation_authority",
            ),
        }
        return success_response(
            message="Successfully calculated analytics overview.",
            data=data,
            metadata=meta,
        )
    except Exception as exc:  # noqa: BLE001
        return response_from_exception(exception=exc, metadata=meta)


def build_analytics_report(
    request: BuildAnalyticsReportRequest,
    request_id: str | None = None,
) -> StandardResponse:
    """Build a versioned low-risk, read-only analytics report.

    Args:
        request: Canonical or adapter-compatible trading result payload.
        request_id: Optional trace identifier.

    Returns:
        Standard response with metadata, side-effect flags, timing, and errors.
    """
    logger.debug("tool_api.build_analytics_report: executed.")
    response = _build_analytics_report(request, request_id=request_id)
    if response["status"] == "success" and isinstance(response.get("data"), dict):
        data = cast("dict[str, Any]", response["data"])
        data.setdefault("default_configuration_sources", DEFAULT_CONFIGURATION_SOURCES)
        data.setdefault("non_binding_analytics_evidence", True)
        data.setdefault(
            "forbidden_claims",
            (
                "final_approval",
                "promotion",
                "live_readiness",
                "prop_firm_enforcement",
                "risk_limit_approval",
                "portfolio_allocation_authority",
            ),
        )
    return response


__all__ = [
    "AnalyticsComparison",
    "AnalyticsReport",
    "BuildAnalyticsReportRequest",
    "BuildPortfolioAnalyticsReportRequest",
    "ComplianceEvidence",
    "ComplianceProfile",
    "PortfolioAnalyticsReport",
    "build_analytics_report",
    "build_portfolio_analytics_report",
    "calculate_benchmark_metrics",
    "calculate_drawdown_metrics",
    "calculate_equity_metrics",
    "calculate_prop_firm_compliance",
    "calculate_risk_metrics",
    "calculate_statistical_validation",
    "calculate_trade_metrics",
    "compare_analytics_reports",
    "evaluate_strategy_quality",
    "get_analytics_overview",
]
