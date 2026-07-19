"""Deterministic SHA-256 identities for Analytics evidence."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import to_report_json_safe
from app.services.analytics.contracts.models import (
    PerformanceReport,
    ReproducibilityHashes,
    TradingResult,
)
from app.utils import ValidationError as UtilsValidationError
from app.utils import canonical_json, logger


def _digest(value: object) -> str:
    """Hash one canonical JSON-safe evidence value.

    Args:
        value: Evidence to serialize and hash.

    Returns:
        Lowercase SHA-256 digest.

    Raises:
        AnalyticsValidationError: If evidence cannot be serialized canonically.
    """
    logger.debug("Hashing canonical Analytics evidence")
    try:
        safe = to_report_json_safe(value)
        return hashlib.sha256(canonical_json(safe).encode("utf-8")).hexdigest()
    except (AnalyticsValidationError, UtilsValidationError, TypeError) as error:
        raise AnalyticsValidationError("Analytics evidence cannot be hashed") from error


def _report_hash_payload(report: PerformanceReport) -> Mapping[str, object]:
    """Build the deterministic report payload excluding creation time and self-hash.

    Args:
        report: Validated Analytics report.

    Returns:
        Report mapping eligible for deterministic hashing.
    """
    logger.debug("Building deterministic Analytics report hash payload")
    return {
        "contract_version": report.contract_version,
        "schema_id": report.schema_id,
        "report_id": report.report_id,
        "request_id": report.request_id,
        "account_currency": report.account_currency,
        "sections": report.sections,
        "caveats": report.caveats,
        "quality_flags": report.quality_flags,
        "lineage": report.lineage,
        "hashes": {
            "input_hash": report.hashes.input_hash,
            "configuration_hash": report.hashes.configuration_hash,
            "trade_ledger_hash": report.hashes.trade_ledger_hash,
            "equity_curve_hash": report.hashes.equity_curve_hash,
            "benchmark_hash": report.hashes.benchmark_hash,
        },
        "precision_metadata": report.precision_metadata,
        "non_binding": report.non_binding,
    }


def compute_reproducibility_hashes(
    result: TradingResult,
    report: PerformanceReport | None = None,
) -> ReproducibilityHashes:
    """Compute canonical input, configuration, ledger, curve, and report hashes.

    Args:
        result: Canonical Analytics calculation input.
        report: Optional completed report whose nondeterministic time is excluded.

    Returns:
        Complete deterministic reproducibility hashes.
    """
    logger.info("Computing Analytics reproducibility hashes")
    input_payload = {
        "contract_version": result.contract_version,
        "schema_id": result.schema_id,
        "source_contract": result.source_contract,
        "source_contract_version": result.source_contract_version,
        "source_schema_id": result.source_schema_id,
        "source_id": result.source_id,
        "phase": result.phase,
        "window_start": result.window_start,
        "window_end": result.window_end,
        "account_currency": result.account_currency,
        "initial_balance": result.initial_balance,
        "strategy_id": result.strategy_id,
        "strategy_version": result.strategy_version,
        "symbols": result.symbols,
        "timeframe": result.timeframe,
        "quality_metadata": result.quality_metadata,
        "source_metadata": result.source_metadata,
    }
    configuration_payload = {
        "configuration_sources": result.lineage.configuration_sources,
        "transformations": result.lineage.transformations,
        "source_metadata": result.source_metadata,
    }
    return ReproducibilityHashes(
        input_hash=_digest(input_payload),
        configuration_hash=_digest(configuration_payload),
        trade_ledger_hash=_digest(result.trades),
        equity_curve_hash=_digest(
            {"curve": result.equity_curve, "daily": result.daily_equity_curve}
        ),
        benchmark_hash=_digest(result.benchmark)
        if result.benchmark is not None
        else None,
        report_hash=_digest(_report_hash_payload(report))
        if report is not None
        else None,
    )


def _compute_portfolio_hashes(
    payload: Mapping[str, object],
) -> ReproducibilityHashes:
    """Compute deterministic identities for internal portfolio composition.

    Args:
        payload: Validated portfolio aggregation evidence.

    Returns:
        Portfolio reproducibility hashes.
    """
    logger.debug("Computing internal Analytics portfolio hashes")
    component_ids = payload["component_report_ids"]
    sections = payload["sections"]
    return ReproducibilityHashes(
        input_hash=_digest(payload),
        configuration_hash=_digest(
            {"base_currency": payload["base_currency"], "fx": payload["fx"]}
        ),
        trade_ledger_hash=_digest(component_ids),
        equity_curve_hash=_digest(sections),
        benchmark_hash=None,
        report_hash=_digest(payload),
    )


__all__ = ["compute_reproducibility_hashes"]
