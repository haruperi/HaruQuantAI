"""Report-ready transformations of existing Optimization evidence."""

from __future__ import annotations

from app.services.optimization.evidence.contracts import (
    OptimizationResult,  # noqa: TC001
)
from app.utils import logger


def build_report_package(result: OptimizationResult) -> dict[str, object]:
    """Package existing result tables and chart data without recomputation.

    Args:
        result: Validated Optimization result version one.

    Returns:
        JSON-safe report package containing only existing evidence.
    """
    logger.info("Building Optimization report handoff package")
    return {
        "contract_version": result.contract_version,
        "schema_id": result.schema_id,
        "search_id": result.search_id,
        "reproducibility_hash": result.reproducibility_hash,
        "decision": result.final_decision.value,
        "tables": {"ranked_candidates": list(result.ranked_candidates)},
        "charts": dict(result.chart_data),
        "warnings": result.warnings,
        "audit_references": result.audit_references,
    }


__all__ = ["build_report_package"]
