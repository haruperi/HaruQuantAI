"""Durable catalogue retention of canonical backtest evidence (FEAT-API-27).

The Simulator hands complete terminal evidence to an optional completion
sink exactly once per finished canonical job. This module is the gateway's
implementation of that sink: it records one catalogue run row, serializes
the owner's performance report, attaches the immutable report artifact, and
completes the row. Nothing here computes evidence — every value is copied
from the owner projection the Simulator produced.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from app.composition.logging import get_logger
from app.kernel.time import format_utc_timestamp

if TYPE_CHECKING:  # pragma: no cover - typing-only import
    from app.services.api.widgets.simulator.registry import (
        SimulationWorkbenchRegistry,
    )

logger = get_logger(__name__)


def _text(value: object) -> str | None:
    """Return one optional catalogue text value.

    Args:
        value: Raw projection value.

    Returns:
        Stripped text, or ``None`` when the value carries nothing.
    """
    if value is None:
        return None
    text = str(value)
    return text or None


def _quality_status(projection: Mapping[str, Any]) -> str | None:
    """Return the owner-declared dataset quality status.

    Args:
        projection: Compact owner run projection.

    Returns:
        Owner quality status text, or ``None`` when the owner declared none.
    """
    quality = projection.get("quality")
    if isinstance(quality, Mapping):
        return _text(quality.get("status"))
    return _text(quality)


def build_catalogue_run_values(
    projection: Mapping[str, Any],
    *,
    created_at: str,
    origin: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Project one owner run projection into exact catalogue row values.

    Args:
        projection: Compact owner run projection enriched by the job
            registry with ``job_id`` and ``principal_id``.
        created_at: Canonical UTC creation timestamp.
        origin: Gateway-owned origin columns for a run the gateway itself
            started (``origin_kind``, ``batch_id``, ``session_id``).

    Returns:
        Exact ``api_simulation_results`` column values for the queued row.
    """
    run_id = str(projection["run_id"])
    job_id = _text(projection.get("job_id"))
    symbol = _text(projection.get("symbol"))
    values: dict[str, object] = {
        "run_id": run_id,
        "principal_id": str(projection["principal_id"]),
        "origin_kind": "canonical_job",
        "origin_id": job_id,
        "job_id": job_id,
        "batch_id": _text(projection.get("batch_id")),
        "session_id": None,
        "strategy_id": _text(projection.get("strategy_id")),
        "strategy_version": _text(projection.get("strategy_version")),
        "strategy_label": _text(projection.get("strategy_label")),
        "symbols": json.dumps([symbol] if symbol else []),
        "timeframe": _text(projection.get("timeframe")),
        "measurement_start": _text(projection.get("start")),
        "measurement_end": _text(projection.get("end")),
        "status": "queued",
        "result_ref": None,
        "report_id": None,
        "report_ref": None,
        "artifact_manifest_ref": None,
        "quality_status": None,
        "evidence_class": "canonical",
        "created_at": created_at,
        "completed_at": None,
        "name": None,
        "alias": None,
        "description": None,
        "tags": "[]",
        "run_reason": None,
        "archive_state": "active",
        "updated_at": created_at,
    }
    values.update(origin or {})
    return values


def _unwrap(response: object) -> Mapping[str, object]:
    """Return the owner attachment projection carried by one response.

    Args:
        response: Simulator standard response or raw owner mapping.

    Returns:
        Immutable attachment projection.
    """
    data = getattr(response, "data", response)
    return cast("Mapping[str, object]", data)


CATALOGUE_REPORT_MAX_BYTES = 8_000_000


def _serialize_owner_report(report: object) -> str:
    """Serialize one owner report exactly as the immutable artifact text.

    The gateway owns only the retention bound; every byte of the rendered
    report comes from the Analytics serializer.

    Args:
        report: Validated Analytics performance report.

    Returns:
        Canonical report JSON text.
    """
    from app.services.analytics import create_analytics_value, serialize_report

    config = create_analytics_value(
        "AnalyticsRunConfig",
        max_warning_detail_bytes=4_096,
        max_trades=1_000_000,
        max_equity_points=1_000_000,
        max_benchmark_points=1_000_000,
        max_statistical_observations=1_000_000,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=CATALOGUE_REPORT_MAX_BYTES,
        risk_free_rate=None,
        statistics=create_analytics_value(
            "StatisticalValidationConfig",
            seed=7,
            bootstrap_iterations=100,
            permutation_iterations=100,
            confidence=0.95,
            alpha=0.05,
        ),
    )
    return cast(
        "str",
        getattr(
            serialize_report(
                cast("Any", report), format_name="json", config=cast("Any", config)
            ),
            "data",
            "",
        ),
    )


def _default_attacher() -> Callable[..., object]:
    """Return the Simulator-owned report attachment entry point.

    Returns:
        Simulator ``attach_analytics_report_artifact``.
    """
    from app.services.simulator import attach_analytics_report_artifact

    return attach_analytics_report_artifact


def build_catalogue_completion_sink(
    registry: SimulationWorkbenchRegistry,
    *,
    attach_report: Callable[..., object] | None = None,
    serializer: Callable[[object], str] | None = None,
    provenance: Callable[[str], Mapping[str, object]] | None = None,
    clock: Callable[[], datetime] | None = None,
    request_id_factory: Callable[[], str] | None = None,
) -> Callable[[Any], None]:
    """Build the completion sink retaining canonical evidence durably.

    The immutable report artifact is attached before the catalogue row is
    registered at all, so a failed attachment leaves no half-written run
    stranded in ``queued`` and the Simulator reports the retention failure
    as the run's terminal outcome.

    Args:
        registry: Catalogue transition registry owning row transitions.
        attach_report: Simulator ``attach_analytics_report_artifact``
            returning the immutable artifact reference; the Simulator facade
            is used when absent.
        serializer: Callable rendering one owner report as artifact text;
            the bounded Analytics JSON serializer is used when absent.
        provenance: Callable resolving one job identity to its gateway-owned
            origin columns; runs carry their canonical-job origin when absent.
        clock: UTC clock used for row timestamps; real time when absent.
        request_id_factory: Canonical request-id source; generated when
            absent.

    Returns:
        Callable accepting one ``BacktestRunEvidence`` and retaining it.
    """
    from app.kernel.identity import generate_id

    now = clock or (lambda: datetime.now(UTC))
    next_request_id = request_id_factory or (lambda: generate_id("req"))

    def sink(evidence: object) -> None:
        """Record one finished canonical run in the durable catalogue.

        Args:
            evidence: Complete terminal evidence for one finished run.

        Raises:
            KeyError: If the owner projection carries no run or principal
                identity; the Simulator translates the refusal into
                ``BACKTEST_EVIDENCE_PERSISTENCE_FAILED``.
        """
        projection = cast("Mapping[str, Any]", getattr(evidence, "projection", {}))
        performance_report = getattr(evidence, "performance_report", None)
        run_id = str(projection["run_id"])
        principal_id = str(projection["principal_id"])
        timestamp = format_utc_timestamp(now())
        request_id = next_request_id()
        report_json = (serializer or _serialize_owner_report)(performance_report)
        attachment = _unwrap(
            (attach_report or _default_attacher())(
                run_id, report_json, request_id=request_id
            )
        )
        origin = provenance(str(projection.get("job_id", ""))) if provenance else None
        registry.register_run(
            build_catalogue_run_values(projection, created_at=timestamp, origin=origin),
            request_id=request_id,
        )
        report = performance_report
        registry.complete_run(
            run_id,
            principal_id,
            request_id=request_id,
            evidence={
                "result_ref": f"{run_id}/result.json",
                "report_id": _text(getattr(report, "report_id", None)),
                "report_ref": _text(attachment.get("artifact_ref")),
                "artifact_manifest_ref": f"{run_id}/manifest.json",
                "quality_status": _quality_status(projection),
                "completed_at": timestamp,
            },
        )
        logger.info("Retained canonical Simulation run %s in the catalogue", run_id)

    return sink


__all__ = ("build_catalogue_completion_sink", "build_catalogue_run_values")
