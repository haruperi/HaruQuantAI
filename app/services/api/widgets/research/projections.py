"""API-owned read-model projections over the registered Research report.

Research owns every scientific conclusion in these projections. This module
only reshapes the already-registered ``ResearchReport v1`` evidence into the
stage-addressable views a workbench navigates, and never recomputes a score,
classification, readiness verdict, or statistic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, cast

from app.composition.logging import get_logger
from app.kernel.serialization import to_json_safe

logger = get_logger(__name__)

type JsonValue = Any


@dataclass(frozen=True, slots=True)
class _HydratedReport:
    """Attribute-compatible form of one persisted report projection."""

    report_id: str
    schema_id: str
    contract_version: str
    hypothesis: str
    evidence: Mapping[str, JsonValue]
    seeds: Mapping[str, JsonValue]
    configuration_hash: str
    dataset_hash: str
    source_references: tuple[JsonValue, ...]
    warnings: tuple[JsonValue, ...]
    generated_at: JsonValue
    dependency_versions: Mapping[str, JsonValue]
    duration_ms: JsonValue
    advisory_only: bool


#: UI stage vocabulary, in navigation order.
STAGE_VIEWS: Final[tuple[str, ...]] = (
    "overview",
    "data",
    "features",
    "validation",
    "metrics",
    "studies",
    "seasonality",
    "market-structure",
    "modeling",
    "profile",
    "intelligence",
    "stress",
    "artifacts",
    "provenance",
)

#: Research evidence keys each navigable stage view is derived from.
_STAGE_SOURCES: Final[Mapping[str, tuple[str, ...]]] = {
    "overview": (),
    "data": ("data",),
    "features": ("features",),
    "validation": ("leakage", "statistics"),
    "metrics": ("metrics",),
    "studies": ("studies",),
    "seasonality": ("seasonality",),
    "market-structure": ("market_structure",),
    "modeling": ("modeling",),
    "profile": ("profiles",),
    "intelligence": (),
    "stress": (),
    "artifacts": (),
    "provenance": (),
}

#: Research stages that back each navigable stage view.
_STAGE_REQUIREMENTS: Final[Mapping[str, tuple[str, ...]]] = {
    "data": ("data",),
    "features": ("features",),
    "validation": ("leakage", "statistics"),
    "metrics": ("metrics",),
    "studies": ("studies",),
    "seasonality": ("seasonality",),
    "market-structure": ("market_structure",),
    "modeling": ("modeling",),
    "profile": ("profiles",),
}


def _json(value: object) -> JsonValue:
    """Convert one owner value into detached JSON-safe evidence.

    Args:
        value: Owner-supplied evidence of any registered shape.

    Returns:
        JSON-safe detached copy.
    """
    return to_json_safe(value)


def project_warning(warning: object) -> Mapping[str, JsonValue]:
    """Project one Research warning into browser-safe evidence.

    Args:
        warning: Research warning dataclass or already-projected mapping.

    Returns:
        JSON-safe warning evidence carrying code, message, and severity.
    """
    if isinstance(warning, Mapping):
        return {
            "code": str(warning.get("code", "UNKNOWN")),
            "message": str(warning.get("message", "")),
            "severity": str(warning.get("severity", "warning")),
            "field_path": warning.get("field_path"),
            "details": _json(warning.get("details") or {}),
        }
    typed = cast("Any", warning)
    return {
        "code": str(getattr(typed, "code", "UNKNOWN")),
        "message": str(getattr(typed, "message", "")),
        "severity": str(getattr(typed, "severity", "warning")),
        "field_path": getattr(typed, "field_path", None),
        "details": _json(getattr(typed, "details", {}) or {}),
    }


def project_warnings(warnings: Sequence[object]) -> list[Mapping[str, JsonValue]]:
    """Project a warning sequence into browser-safe evidence.

    Args:
        warnings: Research warnings from a report or stage.

    Returns:
        JSON-safe warning list preserving owner order.
    """
    return [dict(project_warning(item)) for item in warnings]


def _evidence(report: object) -> Mapping[str, JsonValue]:
    """Return the registered report evidence mapping.

    Args:
        report: Registered ``ResearchReport`` value.

    Returns:
        Evidence mapping, empty when the report carries none.
    """
    evidence = getattr(report, "evidence", None)
    if isinstance(evidence, Mapping):
        return cast("Mapping[str, JsonValue]", evidence)
    return {}


def _stage_evidence(report: object, stage: str) -> Mapping[str, JsonValue] | None:
    """Return one Research stage's evidence when it was executed.

    Args:
        report: Registered ``ResearchReport`` value.
        stage: Research stage key.

    Returns:
        Stage evidence mapping, or ``None`` when the stage did not run.
    """
    value = _evidence(report).get(stage)
    if isinstance(value, Mapping):
        return cast("Mapping[str, JsonValue]", value)
    return None


def project_scorecard(report: object) -> Mapping[str, JsonValue]:
    """Project the Research-owned scorecard evidence.

    Args:
        report: Registered ``ResearchReport`` value.

    Returns:
        Score, readiness, reasons, and score rows exactly as Research
        published them, or an explicit unavailable state.
    """
    profiles = _stage_evidence(report, "profiles")
    if profiles is None:
        return {
            "available": False,
            "score": None,
            "readiness": None,
            "reasons": [],
            "score_rows": [],
        }
    return {
        "available": True,
        "score": profiles.get("score"),
        "readiness": profiles.get("readiness"),
        "reasons": _json(profiles.get("reasons") or []),
        "score_rows": _json(profiles.get("score_rows") or []),
        "stage_count": profiles.get("stage_count"),
        "advisory_only": profiles.get("advisory_only", True),
        "snapshot_id": profiles.get("snapshot_id"),
        "schema_version": profiles.get("schema_version"),
    }


def _study_counts(report: object) -> Mapping[str, int]:
    """Count study classifications published by Research.

    Args:
        report: Registered ``ResearchReport`` value.

    Returns:
        Counts of confirmed, contradicted, and inconclusive studies.
    """
    studies = _stage_evidence(report, "studies")
    counts = {"confirmed": 0, "contradicted": 0, "inconclusive": 0}
    if studies is None:
        return counts
    for result in cast("Sequence[Mapping[str, JsonValue]]", studies.get("results", [])):
        classification = str(result.get("classification", "inconclusive"))
        if classification in counts:
            counts[classification] += 1
    return counts


def project_stage_status(
    report: object | None,
    *,
    selected_stages: Sequence[str],
    run_status: str,
) -> Mapping[str, Mapping[str, JsonValue]]:
    """Derive one explicit state per navigable stage view.

    Every state is server-derived so the browser never guesses whether a stage
    is missing because it was deselected, because the run has not reached it,
    or because Research could not produce it.

    Args:
        report: Terminal report, or ``None`` while the run has no result.
        selected_stages: Research stages the run requested.
        run_status: Current run lifecycle status.

    Returns:
        Mapping from stage view name to its state and reason.
    """
    selected = set(selected_stages)
    states: dict[str, Mapping[str, JsonValue]] = {}
    for view in STAGE_VIEWS:
        required = _STAGE_REQUIREMENTS.get(view, ())
        if not required:
            # Always-available views: overview, artifacts, provenance and the
            # two evidence surfaces Research exposes outside the run stages.
            states[view] = {
                "state": "completed" if report is not None else run_status,
                "reason": None,
            }
            continue
        if not set(required) & selected:
            states[view] = {"state": "not_selected", "reason": "STAGE_NOT_SELECTED"}
            continue
        if report is None:
            states[view] = {"state": run_status, "reason": None}
            continue
        produced = [stage for stage in required if _stage_evidence(report, stage)]
        if not produced:
            states[view] = {
                "state": "unavailable",
                "reason": "STAGE_PRODUCED_NO_EVIDENCE",
            }
        elif len(produced) < len(required):
            states[view] = {"state": "partial", "reason": "STAGE_PARTIALLY_AVAILABLE"}
        else:
            states[view] = {"state": "completed", "reason": None}
    return states


def project_stage_view(
    report: object | None,
    *,
    stage: str,
    selected_stages: Sequence[str],
    run_status: str,
    extra: Mapping[str, JsonValue] | None = None,
) -> Mapping[str, JsonValue]:
    """Project one navigable stage view over registered report evidence.

    Args:
        report: Terminal report, or ``None`` when no result exists yet.
        stage: Navigable stage view name.
        selected_stages: Research stages the run requested.
        run_status: Current run lifecycle status.
        extra: Additional gateway-owned evidence merged into the view.

    Returns:
        Stage view carrying state, evidence, and warnings.

    Raises:
        KeyError: If the stage view is not registered.
    """
    if stage not in _STAGE_SOURCES:
        raise KeyError(stage)
    status = project_stage_status(
        report, selected_stages=selected_stages, run_status=run_status
    )[stage]
    evidence: dict[str, JsonValue] = {}
    warnings: list[Mapping[str, JsonValue]] = []
    if report is not None:
        for source in _STAGE_SOURCES[stage]:
            stage_evidence = _stage_evidence(report, source)
            if stage_evidence is None:
                continue
            evidence[source] = _json(stage_evidence)
            warnings.extend(
                project_warnings(
                    cast(
                        "Sequence[object]",
                        stage_evidence.get("warnings", []),
                    )
                )
            )
    if extra:
        evidence.update({key: _json(value) for key, value in extra.items()})
    return {
        "stage": stage,
        "state": status["state"],
        "reason": status["reason"],
        "evidence": evidence,
        "warnings": warnings,
    }


def project_overview(report: object | None) -> Mapping[str, JsonValue]:
    """Project the composite overview evidence for one completed run.

    Args:
        report: Terminal report, or ``None`` when no result exists yet.

    Returns:
        Overview evidence assembled entirely from Research-owned fields.
    """
    if report is None:
        return {"available": False}
    structure = _stage_evidence(report, "market_structure")
    seasonality = _stage_evidence(report, "seasonality")
    modeling = _stage_evidence(report, "modeling")
    scorecard = project_scorecard(report)
    return {
        "available": True,
        "hypothesis": str(getattr(report, "hypothesis", "")),
        "selected_stages": _json(_evidence(report).get("selected_stages") or []),
        "scorecard": scorecard,
        "study_counts": dict(_study_counts(report)),
        "structure": (
            {
                "score": structure.get("score"),
                "verdict": structure.get("verdict"),
                "strategy_fit": _json(structure.get("strategy_fit") or {}),
            }
            if structure is not None
            else None
        ),
        "sessions": _json((seasonality or {}).get("sessions") or []),
        "modeling_insights": _json((modeling or {}).get("insights") or {}),
        "warnings": project_warnings(
            cast("Sequence[object]", getattr(report, "warnings", ()))
        ),
    }


def project_provenance(report: object | None) -> Mapping[str, JsonValue]:
    """Project reproducibility evidence for one run.

    Args:
        report: Terminal report, or ``None`` when no result exists yet.

    Returns:
        Hashes, seeds, dependency versions, and source references.
    """
    if report is None:
        return {"available": False}
    return {
        "available": True,
        "report_id": str(getattr(report, "report_id", "")),
        "schema_id": str(getattr(report, "schema_id", "")),
        "contract_version": str(getattr(report, "contract_version", "")),
        "dataset_hash": str(getattr(report, "dataset_hash", "")),
        "configuration_hash": str(getattr(report, "configuration_hash", "")),
        "seeds": _json(getattr(report, "seeds", {})),
        "dependency_versions": _json(getattr(report, "dependency_versions", {})),
        "source_references": _json(getattr(report, "source_references", ())),
        "selected_stages": _json(_evidence(report).get("selected_stages") or []),
        "generated_at": _json(getattr(report, "generated_at", None)),
        "duration_ms": getattr(report, "duration_ms", None),
        "advisory_only": bool(getattr(report, "advisory_only", True)),
        "warnings": project_warnings(
            cast("Sequence[object]", getattr(report, "warnings", ()))
        ),
    }


def project_report(report: object) -> Mapping[str, JsonValue]:
    """Project the complete registered report for the diagnostic viewer.

    Args:
        report: Registered ``ResearchReport`` value.

    Returns:
        JSON-safe copy of the whole registered report.
    """
    return {
        "report_id": str(getattr(report, "report_id", "")),
        "schema_id": str(getattr(report, "schema_id", "")),
        "contract_version": str(getattr(report, "contract_version", "")),
        "hypothesis": str(getattr(report, "hypothesis", "")),
        "evidence": _json(_evidence(report)),
        "seeds": _json(getattr(report, "seeds", {})),
        "configuration_hash": str(getattr(report, "configuration_hash", "")),
        "dataset_hash": str(getattr(report, "dataset_hash", "")),
        "source_references": _json(getattr(report, "source_references", ())),
        "warnings": project_warnings(
            cast("Sequence[object]", getattr(report, "warnings", ()))
        ),
        "generated_at": _json(getattr(report, "generated_at", None)),
        "dependency_versions": _json(getattr(report, "dependency_versions", {})),
        "duration_ms": getattr(report, "duration_ms", None),
        "advisory_only": bool(getattr(report, "advisory_only", True)),
    }


def hydrate_report(report: Mapping[str, JsonValue]) -> object:
    """Restore attribute access for one persisted report projection.

    Args:
        report: Mapping previously produced by :func:`project_report`.

    Returns:
        Frozen report value compatible with all workbench projections.
    """
    evidence = report.get("evidence")
    seeds = report.get("seeds")
    dependency_versions = report.get("dependency_versions")
    return _HydratedReport(
        report_id=str(report.get("report_id", "")),
        schema_id=str(report.get("schema_id", "")),
        contract_version=str(report.get("contract_version", "")),
        hypothesis=str(report.get("hypothesis", "")),
        evidence=cast(
            "Mapping[str, JsonValue]", evidence if isinstance(evidence, Mapping) else {}
        ),
        seeds=cast(
            "Mapping[str, JsonValue]", seeds if isinstance(seeds, Mapping) else {}
        ),
        configuration_hash=str(report.get("configuration_hash", "")),
        dataset_hash=str(report.get("dataset_hash", "")),
        source_references=tuple(report.get("source_references") or ()),
        warnings=tuple(report.get("warnings") or ()),
        generated_at=report.get("generated_at"),
        dependency_versions=cast(
            "Mapping[str, JsonValue]",
            dependency_versions if isinstance(dependency_versions, Mapping) else {},
        ),
        duration_ms=report.get("duration_ms"),
        advisory_only=bool(report.get("advisory_only", True)),
    )


def _metric_map(report: object | None) -> Mapping[str, JsonValue]:
    """Return the flat metric mapping Research published, if any.

    Args:
        report: Terminal report, or ``None``.

    Returns:
        Metric family mapping, empty when metrics did not run.
    """
    if report is None:
        return {}
    metrics = _stage_evidence(report, "metrics")
    if metrics is None:
        return {}
    values = metrics.get("metrics")
    if isinstance(values, Mapping):
        return cast("Mapping[str, JsonValue]", values)
    return {}


def _study_map(report: object | None) -> Mapping[str, str]:
    """Return study classifications keyed by study name.

    Args:
        report: Terminal report, or ``None``.

    Returns:
        Mapping from study name to Research-owned classification.
    """
    if report is None:
        return {}
    studies = _stage_evidence(report, "studies")
    if studies is None:
        return {}
    return {
        str(result.get("study", f"study_{index}")): str(
            result.get("classification", "inconclusive")
        )
        for index, result in enumerate(
            cast("Sequence[Mapping[str, JsonValue]]", studies.get("results", []))
        )
    }


def _numeric(value: object) -> float | None:
    """Coerce one evidence value into a comparable number.

    Args:
        value: Candidate metric value.

    Returns:
        Float value, or ``None`` when the value is not numeric.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, Mapping):
        return _numeric(value.get("value"))
    return None


def project_comparison(
    runs: Sequence[Mapping[str, JsonValue]],
) -> Mapping[str, JsonValue]:
    """Build one server-derived comparison across completed runs.

    Args:
        runs: Ordered ``{"summary": ..., "report": ...}`` entries. The first
            entry is the baseline every delta is measured against.

    Returns:
        Comparison evidence covering readiness, metrics, studies, stages,
        warnings, and provenance differences.
    """
    logger.info("Projecting Research run comparison")
    baseline = runs[0]
    baseline_summary = cast("Mapping[str, JsonValue]", baseline.get("summary", {}))
    baseline_report = baseline.get("report")
    baseline_metrics = _metric_map(baseline_report)
    baseline_studies = _study_map(baseline_report)
    baseline_score = project_scorecard(baseline_report) if baseline_report else {}

    metric_names = sorted(
        {
            name
            for entry in runs
            for name in _metric_map(entry.get("report"))
            if _numeric(_metric_map(entry.get("report"))[name]) is not None
        }
    )
    study_names = sorted(
        {name for entry in runs for name in _study_map(entry.get("report"))}
    )

    entries: list[Mapping[str, JsonValue]] = []
    for entry in runs:
        report = entry.get("report")
        summary = cast("Mapping[str, JsonValue]", entry.get("summary", {}))
        scorecard = project_scorecard(report) if report is not None else {}
        metrics = _metric_map(report)
        studies = _study_map(report)
        entries.append(
            {
                "run_id": summary.get("run_id"),
                "experiment_id": summary.get("experiment_id"),
                "symbol": summary.get("symbol"),
                "timeframe": summary.get("timeframe"),
                "status": summary.get("status"),
                "created_at": summary.get("created_at"),
                "report_id": (
                    str(getattr(report, "report_id", ""))
                    if report is not None
                    else None
                ),
                "dataset_hash": (
                    str(getattr(report, "dataset_hash", ""))
                    if report is not None
                    else None
                ),
                "configuration_hash": (
                    str(getattr(report, "configuration_hash", ""))
                    if report is not None
                    else None
                ),
                "score": scorecard.get("score"),
                "readiness": scorecard.get("readiness"),
                "score_delta": (
                    None
                    if _numeric(scorecard.get("score")) is None
                    or _numeric(baseline_score.get("score")) is None
                    else cast("float", _numeric(scorecard.get("score")))
                    - cast("float", _numeric(baseline_score.get("score")))
                ),
                "stages": _json(
                    (_evidence(report).get("selected_stages") or [])
                    if report is not None
                    else []
                ),
                "warning_count": (
                    len(cast("Sequence[object]", getattr(report, "warnings", ())))
                    if report is not None
                    else 0
                ),
                "metrics": {
                    name: {
                        "value": _numeric(metrics.get(name)),
                        "delta": (
                            None
                            if _numeric(metrics.get(name)) is None
                            or _numeric(baseline_metrics.get(name)) is None
                            else cast("float", _numeric(metrics.get(name)))
                            - cast("float", _numeric(baseline_metrics.get(name)))
                        ),
                    }
                    for name in metric_names
                },
                "studies": {
                    name: {
                        "classification": studies.get(name),
                        "changed": studies.get(name) != baseline_studies.get(name),
                    }
                    for name in study_names
                },
                "seeds": (
                    _json(getattr(report, "seeds", {})) if report is not None else {}
                ),
                "dependency_versions": (
                    _json(getattr(report, "dependency_versions", {}))
                    if report is not None
                    else {}
                ),
            }
        )
    return {
        "baseline_run_id": baseline_summary.get("run_id"),
        "metric_names": metric_names,
        "study_names": study_names,
        "entries": entries,
    }


__all__ = (
    "STAGE_VIEWS",
    "hydrate_report",
    "project_comparison",
    "project_overview",
    "project_provenance",
    "project_report",
    "project_scorecard",
    "project_stage_status",
    "project_stage_view",
    "project_warning",
    "project_warnings",
)
