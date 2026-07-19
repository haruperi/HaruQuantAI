"""Canonical Analytics PerformanceReport orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import build_warning, to_report_json_safe
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    PerformanceReport,
    ReproducibilityHashes,
)
from app.services.analytics.metrics.groups import calculate_grouped_evidence
from app.services.analytics.metrics.trades import ANNUALIZATION_POLICY
from app.services.analytics.reports.hashes import compute_reproducibility_hashes
from app.utils import ValidationError as UtilsValidationError
from app.utils import canonical_json, derive_stable_id, logger, utc_now, validate_id

REQUIRED_REPORT_SECTIONS = ("trades", "pnl", "equity_returns", "drawdown")
OPTIONAL_REPORT_SECTIONS = (
    "risk",
    "ratios",
    "benchmark",
    "distribution",
    "cost_efficiency",
    "statistical",
)


def _replace_hashes(
    report: PerformanceReport,
    hashes: ReproducibilityHashes,
) -> PerformanceReport:
    """Return an immutable report copy with completed report hashes.

    Args:
        report: Provisional report.
        hashes: Completed reproducibility hashes.

    Returns:
        Completed report copy.
    """
    logger.debug("Finalizing Analytics report reproducibility hashes")
    return PerformanceReport(
        contract_version=report.contract_version,
        schema_id=report.schema_id,
        report_id=report.report_id,
        request_id=report.request_id,
        created_at=report.created_at,
        account_currency=report.account_currency,
        sections=report.sections,
        caveats=report.caveats,
        quality_flags=report.quality_flags,
        lineage=report.lineage,
        hashes=hashes,
        precision_metadata=report.precision_metadata,
    )


def build_performance_report(
    source: Mapping[str, object],
    *,
    source_contract: str,
    request_id: str,
    initial_balance: Decimal,
    account_currency: str,
    config: AnalyticsRunConfig,
    benchmark: Mapping[str, object] | None = None,
    fx_evidence: Mapping[str, object] | None = None,
    diagnostic_partial_mode: bool = False,
) -> PerformanceReport:
    """Build a complete non-binding PerformanceReport from canonical ledger evidence.

    Args:
        source: Approved producer-neutral closed-trade ledger mapping.
        source_contract: Compatibility-matrix producer identity.
        request_id: Required caller request identity.
        initial_balance: Exact positive starting balance.
        account_currency: Ledger account currency.
        config: Required limits and calculation configuration.
        benchmark: Optional caller-supplied benchmark evidence.
        fx_evidence: Optional caller-supplied Data-owned FX evidence.
        diagnostic_partial_mode: Explicit permission for non-binding diagnostics.

    Returns:
        Canonical PerformanceReport v1.

    Raises:
        AnalyticsValidationError: If input, a required section, or output fails.
    """
    logger.info("Building canonical Analytics performance report")
    try:
        validate_id(request_id, expected_prefix="req")
    except UtilsValidationError as error:
        raise AnalyticsValidationError("request_id is invalid") from error
    result = adapt_trading_result(
        source,
        source_contract=source_contract,
        initial_balance=initial_balance,
        account_currency=account_currency,
        config=config,
        benchmark=benchmark,
        fx_evidence=fx_evidence,
    )
    sections = calculate_grouped_evidence(result, config=config)
    required_failures = tuple(
        section.section_key
        for section in sections
        if section.section_key in REQUIRED_REPORT_SECTIONS
        and section.status in {"failed", "skipped"}
    )
    if required_failures and not diagnostic_partial_mode:
        raise AnalyticsValidationError("required Analytics report section failed")
    initial_hashes = compute_reproducibility_hashes(result)
    caveats = tuple(warning for section in sections for warning in section.warnings)
    curve_warning = build_warning(
        "curve_basis_closed_trade",
        section="drawdown",
        source_context="all",
        detail={"curve_basis": result.curve_basis, "trade_count": len(result.trades)},
        max_detail_bytes=config.max_warning_detail_bytes,
    )
    caveats += (curve_warning,)
    report_id = derive_stable_id(
        "cor", f"analytics-report:{request_id}:{initial_hashes.input_hash}"
    )
    report = PerformanceReport(
        contract_version="v1",
        schema_id="analytics.performance_report.v1",
        report_id=report_id,
        request_id=request_id,
        created_at=utc_now(),
        account_currency=account_currency,
        sections=sections,
        caveats=caveats,
        quality_flags=(),
        lineage=result.lineage,
        hashes=initial_hashes,
        precision_metadata={
            "monetary": "Decimal",
            "ratio_absolute_tolerance": 1e-9,
            "annualization_days": ANNUALIZATION_POLICY["trading_days"],
            "curve_basis": result.curve_basis,
            "measurement_start": result.window_start,
            "measurement_end": result.window_end,
            "diagnostic_partial_mode": diagnostic_partial_mode,
            "optional_sections": OPTIONAL_REPORT_SECTIONS,
            "presentation_series": {"equity_curve": result.equity_curve},
        },
    )
    report = _replace_hashes(report, compute_reproducibility_hashes(result, report))
    safe = to_report_json_safe(report)
    if len(canonical_json(safe).encode("utf-8")) > config.max_response_bytes:
        raise AnalyticsValidationError("performance report exceeds configured bound")
    logger.info("Completed canonical Analytics performance report")
    return report


__all__ = [
    "OPTIONAL_REPORT_SECTIONS",
    "REQUIRED_REPORT_SECTIONS",
    "build_performance_report",
]
