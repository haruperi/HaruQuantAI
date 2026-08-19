"""Browser-facing read models assembled from run records and Research reports.

Each view is an API-owned projection. It renames nothing, recomputes nothing,
and adds only lifecycle facts the gateway itself owns: run identity, status,
timestamps, and the resolved dataset identity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

from app.services.api.widgets.research.projections import (
    STAGE_VIEWS,
    project_comparison,
    project_overview,
    project_provenance,
    project_scorecard,
    project_stage_status,
    project_stage_view,
    project_warnings,
)
from app.utils import get_logger

if TYPE_CHECKING:
    from app.services.api.widgets.research.registry import (
        ResearchExperiment,
        ResearchRun,
        ResearchWorkbenchRegistry,
    )

logger = get_logger(__name__)

type JsonValue = Any


def _iso(value: object) -> str | None:
    """Render one optional timestamp as an ISO-8601 string.

    Args:
        value: Timestamp or ``None``.

    Returns:
        ISO-8601 text, or ``None``.
    """
    if isinstance(value, str):
        return value
    return value.isoformat() if hasattr(value, "isoformat") else None


def run_summary(run: ResearchRun) -> Mapping[str, JsonValue]:
    """Project one run row for ledgers, history tables, and comparisons.

    Args:
        run: Run record.

    Returns:
        JSON-safe run summary.
    """
    scorecard = project_scorecard(run.report) if run.report is not None else {}
    report = run.report
    return {
        "run_id": run.run_id,
        "experiment_id": run.experiment_id,
        "batch_id": run.batch_id,
        "status": run.status,
        "hypothesis": run.hypothesis,
        "symbol": run.symbol,
        "timeframe": run.timeframe,
        "preset": run.preset,
        "selected_stages": list(run.selected_stages),
        "reason": run.reason,
        "force_rerun": run.force_rerun,
        "created_at": _iso(run.created_at),
        "started_at": _iso(run.started_at),
        "completed_at": _iso(run.completed_at),
        "report_id": (
            str(getattr(report, "report_id", "")) if report is not None else None
        ),
        "dataset_hash": (
            str(getattr(report, "dataset_hash", "")) if report is not None else None
        ),
        "configuration_hash": (
            str(getattr(report, "configuration_hash", ""))
            if report is not None
            else None
        ),
        "generated_at": (
            _iso(getattr(report, "generated_at", None)) if report is not None else None
        ),
        "duration_ms": (
            getattr(report, "duration_ms", None) if report is not None else None
        ),
        "score": scorecard.get("score"),
        "readiness": scorecard.get("readiness"),
        "advisory_only": True,
        "warning_count": (
            len(cast("Sequence[object]", getattr(report, "warnings", ())))
            if report is not None
            else 0
        ),
        "error": dict(run.error) if run.error else None,
    }


def run_detail(run: ResearchRun) -> Mapping[str, JsonValue]:
    """Project the complete run header a workbench keeps on every stage.

    Args:
        run: Run record.

    Returns:
        JSON-safe run detail including stage status and dataset identity.
    """
    report = run.report
    dataset = dict(run.dataset or {})
    return {
        **run_summary(run),
        "dataset": dataset.get("identity"),
        "effective_configuration": dict(run.effective_configuration or {}),
        "stage_status": dict(
            project_stage_status(
                report,
                selected_stages=run.selected_stages,
                run_status=run.status,
            )
        ),
        "stage_views": list(STAGE_VIEWS),
        "artifacts": [dict(item) for item in run.artifacts],
        "warnings": (
            project_warnings(cast("Sequence[object]", getattr(report, "warnings", ())))
            if report is not None
            else []
        ),
        "provenance": dict(project_provenance(report)),
        "overview": dict(project_overview(report)),
    }


def stage_view(run: ResearchRun, stage: str) -> Mapping[str, JsonValue]:
    """Project one navigable stage view for a run.

    Args:
        run: Run record.
        stage: Navigable stage view name.

    Returns:
        JSON-safe stage view.

    Raises:
        KeyError: If the stage view is not registered.
    """
    extra: dict[str, JsonValue] = {}
    dataset = dict(run.dataset or {})
    if stage == "data":
        extra["dataset"] = dataset.get("identity")
        extra["preview"] = dataset.get("preview") or []
        extra["effective_configuration"] = dict(run.effective_configuration or {})
    elif stage == "overview":
        extra["overview"] = dict(project_overview(run.report))
    elif stage == "provenance":
        extra["provenance"] = dict(project_provenance(run.report))
    elif stage == "artifacts":
        extra["artifacts"] = [dict(item) for item in run.artifacts]
    elif stage == "features":
        extra["effective_configuration"] = dict(run.effective_configuration or {})
    elif stage == "profile":
        extra["scorecard"] = dict(project_scorecard(run.report))
    return project_stage_view(
        run.report,
        stage=stage,
        selected_stages=run.selected_stages,
        run_status=run.status,
        extra=extra,
    )


def experiment_detail(
    experiment: ResearchExperiment,
    runs: Sequence[ResearchRun],
) -> Mapping[str, JsonValue]:
    """Project one experiment with its complete run ledger.

    Args:
        experiment: Experiment record.
        runs: Runs owned by the experiment, newest first.

    Returns:
        JSON-safe experiment detail.
    """
    summaries = [dict(run_summary(run)) for run in runs]
    return {
        **experiment.summary(
            run_count=len(summaries), latest=summaries[0] if summaries else None
        ),
        "runs": summaries,
    }


def dashboard_view(
    registry: ResearchWorkbenchRegistry, *, principal_id: str
) -> Mapping[str, JsonValue]:
    """Project the research ledger shown on the workbench entry page.

    Negative and inconclusive evidence stays visible: the counts below include
    failed, cancelled, contradicted, and inconclusive results rather than only
    the runs that happened to succeed.

    Args:
        registry: Composed workbench registry.
        principal_id: Authenticated principal identity.

    Returns:
        JSON-safe dashboard evidence.
    """
    experiments = registry.list_experiments(principal_id=principal_id)
    runs = registry.list_runs(principal_id=principal_id)
    summaries = [dict(run_summary(run)) for run in runs]
    readiness: dict[str, int] = {}
    statuses: dict[str, int] = {}
    studies = {"confirmed": 0, "contradicted": 0, "inconclusive": 0}
    warning_total = 0
    for run, summary in zip(runs, summaries, strict=True):
        statuses[str(summary["status"])] = statuses.get(str(summary["status"]), 0) + 1
        key = str(summary["readiness"] or "UNSCORED")
        readiness[key] = readiness.get(key, 0) + 1
        warning_total += int(cast("int", summary["warning_count"]))
        overview = project_overview(run.report)
        counts = cast("Mapping[str, int]", overview.get("study_counts") or {})
        for name in studies:
            studies[name] += int(counts.get(name, 0))
    experiment_summaries = []
    for experiment in experiments:
        owned = registry.list_runs(
            principal_id=principal_id, experiment_id=experiment.experiment_id
        )
        experiment_summaries.append(
            dict(
                experiment.summary(
                    run_count=len(owned),
                    latest=dict(run_summary(owned[0])) if owned else None,
                )
            )
        )
    return {
        "experiments": experiment_summaries,
        "recent_runs": summaries[:25],
        "readiness_distribution": readiness,
        "status_distribution": statuses,
        "study_counts": studies,
        "warning_total": warning_total,
        "advisory_only": True,
    }


def comparison_view(runs: Sequence[ResearchRun]) -> Mapping[str, JsonValue]:
    """Project one server-derived comparison across runs.

    Args:
        runs: Runs to compare, baseline first.

    Returns:
        JSON-safe comparison evidence.
    """
    return project_comparison(
        [{"summary": run_summary(run), "report": run.report} for run in runs]
    )


def batch_view(
    batch: Mapping[str, JsonValue], runs: Sequence[ResearchRun]
) -> Mapping[str, JsonValue]:
    """Project one automation batch with per-symbol run status.

    Args:
        batch: Batch record.
        runs: Runs queued by the batch.

    Returns:
        JSON-safe batch evidence including partial-failure visibility.
    """
    summaries = [dict(run_summary(run)) for run in runs]
    completed = sum(1 for item in summaries if item["status"] == "completed")
    failed = sum(1 for item in summaries if item["status"] == "failed")
    cancelled = sum(1 for item in summaries if item["status"] == "cancelled")
    pending = len(summaries) - completed - failed - cancelled
    rejections = list(cast("Sequence[JsonValue]", batch.get("rejections") or []))
    if pending:
        status = "running"
    elif failed or rejections:
        status = "partial" if completed else "failed"
    elif cancelled and not completed:
        status = "cancelled"
    else:
        status = "completed"
    return {
        "batch_id": batch.get("batch_id"),
        "experiment_id": batch.get("experiment_id"),
        "symbols": list(cast("Sequence[str]", batch.get("symbols") or [])),
        "trigger": batch.get("trigger"),
        "reason": batch.get("reason"),
        "created_at": batch.get("created_at"),
        "status": status,
        "counts": {
            "total": len(summaries),
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "pending": pending,
            "rejected": len(rejections),
        },
        "runs": summaries,
        "rejections": rejections,
    }


__all__ = (
    "batch_view",
    "comparison_view",
    "dashboard_view",
    "experiment_detail",
    "run_detail",
    "run_summary",
    "stage_view",
)
