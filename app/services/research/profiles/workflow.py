"""Deterministic advisory Edge Lab profile orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.services.research.contracts import (
    EdgeLabConfig,
    ResearchReport,
    ResearchWarning,
)
from app.services.research.data import prepare_research_dataset
from app.services.research.metrics import (
    build_core_metric_profile,
    build_default_registry,
)
from app.utils import ValidationError, canonical_digest, logger

if TYPE_CHECKING:
    from app.services.analytics import PerformanceReport
    from app.services.data import MarketDataset

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_IMPLEMENTED_STAGES = frozenset({"data", "metrics"})


def _warning_value(warning: ResearchWarning) -> Mapping[str, JSONValue]:
    """Project one internal warning into bounded report evidence.

    Args:
        warning: Validated Research warning.

    Returns:
        JSON-compatible warning evidence.
    """
    return {
        "code": warning.code,
        "message": warning.message,
        "severity": warning.severity,
        "field_path": warning.field_path,
        "details": warning.details,
    }


def run_edge_lab_profile(
    dataset: MarketDataset,
    *,
    hypothesis: str,
    config: EdgeLabConfig,
    performance: PerformanceReport | None = None,
) -> ResearchReport:
    """Run implemented deterministic stages and build an advisory report.

    Args:
        dataset: Canonical Data-owned market evidence.
        hypothesis: Explicit researcher-supplied hypothesis.
        config: Complete bounded Research configuration.
        performance: Optional Analytics evidence supplied by the orchestrator.

    Returns:
        Immutable advisory ``ResearchReport v1``.

    Raises:
        ValidationError: If the hypothesis, stage selection, or input is invalid.
    """
    logger.info("Running bounded Research Edge Lab profile")
    if not hypothesis or hypothesis != hypothesis.strip():
        raise ValidationError("RES_INPUT_INVALID", "INVALID_HYPOTHESIS")
    selected = set(config.selected_stages)
    if "data" not in selected:
        raise ValidationError("RES_STAGE_DEPENDENCY_INVALID", "DATA_STAGE_REQUIRED")
    unsupported = selected - _IMPLEMENTED_STAGES
    if unsupported:
        logger.warning(
            "Rejecting %d unavailable Research stages",
            len(unsupported),
        )
        raise ValidationError(
            "RES_STAGE_UNAVAILABLE",
            "UNAVAILABLE_SELECTED_STAGE",
        )

    prepared = prepare_research_dataset(
        dataset,
        cleaning=config.cleaning,
        enrichment=config.enrichment,
        limits=config.limits,
    )
    warnings = list(prepared.quality.warnings)
    evidence: dict[str, JSONValue] = {
        "selected_stages": list(config.selected_stages),
        "data": {
            "record_count": len(prepared.data),
            "checks": list(prepared.quality.checks),
            "cleaning_actions": list(prepared.quality.cleaning_actions),
        },
    }
    if "metrics" in selected:
        metric_profile = build_core_metric_profile(
            prepared,
            registry=build_default_registry(),
            limits=config.limits,
        )
        evidence["metrics"] = metric_profile.metrics
        warnings.extend(metric_profile.warnings)
    if performance is not None:
        evidence["performance_report_ref"] = performance.report_id

    report_material = {
        "hypothesis": hypothesis,
        "dataset_hash": prepared.dataset_hash,
        "configuration_hash": prepared.configuration_hash,
        "selected_stages": list(config.selected_stages),
    }
    report_hash = canonical_digest(report_material)
    return ResearchReport(
        contract_version="v1",
        schema_id="research.report.v1",
        report_id=f"research-report-{report_hash[:24]}",
        hypothesis=hypothesis,
        evidence=evidence,
        seeds={
            "statistics": config.statistics.seed,
            "modeling": config.modeling.seed,
        },
        configuration_hash=prepared.configuration_hash,
        dataset_hash=prepared.dataset_hash,
        source_references=prepared.source_references,
        warnings=tuple(warnings),
        generated_at=dataset.available_at,
        dependency_versions={
            "data": dataset.normalization_version,
            "research": "v1",
        },
        duration_ms=0.0,
        advisory_only=True,
    )


__all__ = ("run_edge_lab_profile",)
