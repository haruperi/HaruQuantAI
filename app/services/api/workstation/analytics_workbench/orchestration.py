"""Analytics Workbench orchestration composition (FEAT-API-28).

The gateway is read-mostly: it reads the durable Simulation catalogue,
the attached immutable Analytics report artifact, and the canonical
Simulation result, then delegates every calculation — projection,
comparison, pagination — to the owning domains. Annotations and archive
transitions affect catalogue metadata only.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from app.services.api.workstation.simulation_workbench.persistence import (
    annotate_simulation_result_record,
    archive_simulation_result_record,
    read_simulation_result_record,
    read_simulation_results_page,
)
from app.services.api.workstation.simulation_workbench.schemas import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_TRADE_PAGE_SIZE,
)
from app.utils import format_utc_timestamp, generate_id, get_logger, utc_now

logger = get_logger(__name__)

type _ReportReader = Callable[[str, str], str]
type _ResultReader = Callable[[str], Mapping[str, object] | None]
type _ProjectionBuilder = Callable[..., object]
type _Comparator = Callable[..., object]


@dataclass(frozen=True, slots=True)
class _AnalyticsContext:
    """Injected composition dependencies for the dispatch handlers."""

    report_reader: _ReportReader
    result_reader: _ResultReader
    projection_builder: _ProjectionBuilder
    comparator: _Comparator


def _identities(kwargs: dict[str, object]) -> tuple[str, str]:
    """Extract the principal and request identities from handler kwargs.

    Args:
        kwargs: Caller keyword arguments.

    Returns:
        Principal identity and canonical request identity.
    """
    principal_id = str(kwargs.pop("principal_id", ""))
    request_id = str(kwargs.pop("request_id", "") or generate_id("req"))
    return principal_id, request_id


def _require_run(
    run_id: str, principal_id: str, *, request_id: str
) -> Mapping[str, object]:
    """Read one owned catalogue row or raise the uniform not-found.

    Args:
        run_id: Canonical run identity.
        principal_id: Authenticated principal.
        request_id: Canonical operation request identifier.

    Returns:
        Owned catalogue row.

    Raises:
        KeyError: When the run is unknown or foreign-owned.
    """
    rows = read_simulation_result_record(run_id, principal_id, request_id=request_id)
    if not rows:
        raise KeyError("ANALYTICS_RUN_NOT_FOUND")
    return rows[0]


def _list_runs(_context: _AnalyticsContext, **kwargs: object) -> object:
    """Read one descending catalogue page.

    Returns:
        Catalogue rows ordered by creation descending.
    """
    principal_id, request_id = _identities(kwargs)
    limit = min(int(str(kwargs.get("limit", DEFAULT_PAGE_SIZE))), MAX_PAGE_SIZE)
    offset = max(int(str(kwargs.get("offset", 0))), 0)
    return read_simulation_results_page(
        principal_id, limit=limit, offset=offset, request_id=request_id
    )


def _get_run(_context: _AnalyticsContext, run_id: str, **kwargs: object) -> object:
    """Read one owned catalogue row.

    Returns:
        Catalogue row projection.

    Raises:
        KeyError: When the run is unknown or foreign-owned.
    """
    principal_id, request_id = _identities(kwargs)
    return _require_run(run_id, principal_id, request_id=request_id)


def _require_evidence(
    context: _AnalyticsContext, run_id: str, principal_id: str, *, request_id: str
) -> tuple[Mapping[str, object], str, Mapping[str, object]]:
    """Load the owned row, attached report, and canonical result.

    Returns:
        Catalogue row, report JSON text, and result mapping.

    Raises:
        KeyError: When the run or its evidence is missing.
    """
    row = _require_run(run_id, principal_id, request_id=request_id)
    report_ref = row.get("report_ref")
    if not report_ref:
        raise KeyError("ANALYTICS_REPORT_NOT_ATTACHED")
    result = context.result_reader(run_id)
    if result is None:
        raise KeyError("ANALYTICS_SIMULATION_RESULT_UNAVAILABLE")
    return row, context.report_reader(run_id, str(report_ref)), result


def _read_report(context: _AnalyticsContext, run_id: str, **kwargs: object) -> object:
    """Read the attached immutable Analytics report artifact.

    Returns:
        Serialized report JSON text.

    Raises:
        KeyError: When the run or its report evidence is missing.
    """
    principal_id, request_id = _identities(kwargs)
    _, report_json, _ = _require_evidence(
        context, run_id, principal_id, request_id=request_id
    )
    return report_json


def _build_workbench(
    context: _AnalyticsContext, run_id: str, **kwargs: object
) -> object:
    """Delegate the workbench projection once to Analytics.

    Returns:
        Standard response containing the workbench payload.

    Raises:
        KeyError: When the run or its evidence is missing.
    """
    principal_id, request_id = _identities(kwargs)
    _, report_json, result = _require_evidence(
        context, run_id, principal_id, request_id=request_id
    )
    return context.projection_builder(report_json, result, request_id=request_id)


def _page_trades(context: _AnalyticsContext, run_id: str, **kwargs: object) -> object:
    """Paginate the canonical Simulation trade ledger.

    Returns:
        One bounded trade page with explicit total count.

    Raises:
        KeyError: When the run or its result evidence is missing.
    """
    principal_id, request_id = _identities(kwargs)
    _, _, result = _require_evidence(
        context, run_id, principal_id, request_id=request_id
    )
    trades = cast("Sequence[Mapping[str, object]]", result.get("closed_trades", ()))
    side = str(kwargs.get("side", "all"))
    if side != "all":
        wanted = "BUY" if side == "buy" else "SELL"
        trades = tuple(trade for trade in trades if str(trade.get("type")) == wanted)
    page_size = min(
        int(str(kwargs.get("page_size", DEFAULT_PAGE_SIZE))), MAX_TRADE_PAGE_SIZE
    )
    page = max(int(str(kwargs.get("page", 1))), 1)
    start = (page - 1) * page_size
    return {
        "run_id": run_id,
        "page": page,
        "page_size": page_size,
        "total_count": len(trades),
        "trades": tuple(trades[start : start + page_size]),
    }


def _get_trade(
    context: _AnalyticsContext, run_id: str, ticket: str, **kwargs: object
) -> object:
    """Read one trade from the canonical Simulation result.

    Returns:
        Exact trade record.

    Raises:
        KeyError: When the run or trade is missing.
    """
    principal_id, request_id = _identities(kwargs)
    _, _, result = _require_evidence(
        context, run_id, principal_id, request_id=request_id
    )
    for trade in cast(
        "Sequence[Mapping[str, object]]", result.get("closed_trades", ())
    ):
        if str(trade.get("ticket")) == ticket:
            return trade
    raise KeyError("ANALYTICS_TRADE_NOT_FOUND")


def _compare(
    context: _AnalyticsContext, payload: Mapping[str, object], **kwargs: object
) -> object:
    """Delegate the multi-run comparison to Analytics.

    Returns:
        Owner comparison evidence.

    Raises:
        KeyError: When any run is unknown or lacks report evidence.
    """
    principal_id, request_id = _identities(kwargs)
    reports = []
    for run_id in cast("Sequence[str]", payload.get("run_ids", ())):
        row = _require_run(str(run_id), principal_id, request_id=request_id)
        report_ref = row.get("report_ref")
        if not report_ref:
            raise KeyError("ANALYTICS_REPORT_NOT_ATTACHED")
        reports.append(context.report_reader(str(run_id), str(report_ref)))
    return context.comparator(reports, request_id=request_id)


def _annotate(
    _context: _AnalyticsContext,
    run_id: str,
    payload: Mapping[str, object],
    **kwargs: object,
) -> object:
    """Apply metadata-only annotations to one run.

    Returns:
        Annotation result projection.

    Raises:
        KeyError: When the run is unknown or foreign-owned.
    """
    principal_id, request_id = _identities(kwargs)
    row = _require_run(run_id, principal_id, request_id=request_id)
    changed = annotate_simulation_result_record(
        run_id,
        principal_id,
        name=cast("str | None", payload.get("name", row.get("name"))),
        alias=cast("str | None", payload.get("alias", row.get("alias"))),
        description=cast(
            "str | None", payload.get("description", row.get("description"))
        ),
        tags=str(payload.get("tags", row.get("tags"))),
        run_reason=cast("str | None", payload.get("run_reason", row.get("run_reason"))),
        updated_at=format_utc_timestamp(utc_now()),
        request_id=request_id,
    )
    return {"run_id": run_id, "updated": changed == 1}


def _archive(_context: _AnalyticsContext, run_id: str, **kwargs: object) -> object:
    """Archive one run's catalogue metadata; evidence is never deleted.

    Returns:
        Archive result projection.

    Raises:
        KeyError: When the run is unknown or foreign-owned.
    """
    principal_id, request_id = _identities(kwargs)
    _require_run(run_id, principal_id, request_id=request_id)
    changed = archive_simulation_result_record(
        run_id,
        principal_id,
        updated_at=format_utc_timestamp(utc_now()),
        request_id=request_id,
    )
    return {"run_id": run_id, "archived": changed == 1}


def build_analytics_workbench_source(
    *,
    report_reader: _ReportReader,
    result_reader: _ResultReader,
    projection_builder: _ProjectionBuilder,
    comparator: _Comparator,
) -> Callable[..., object]:
    """Build the dispatch source covering every Analytics Workbench read.

    Args:
        report_reader: Callable ``(run_id, report_ref) -> report_json``.
        result_reader: Callable ``run_id -> canonical Simulation result
            mapping`` or ``None``.
        projection_builder: Analytics ``build_analytics_workbench_payload``.
        comparator: Analytics ``compare_performance_reports``.

    Returns:
        Callable dispatching one allowlisted Analytics Workbench operation.
    """
    context = _AnalyticsContext(
        report_reader=report_reader,
        result_reader=result_reader,
        projection_builder=projection_builder,
        comparator=comparator,
    )
    routed: dict[str, Callable[..., object]] = {
        "list_runs": _list_runs,
        "get_run": _get_run,
        "report": _read_report,
        "workbench": _build_workbench,
        "trades": _page_trades,
        "trade": _get_trade,
        "compare": _compare,
        "annotate": _annotate,
        "archive": _archive,
    }

    def dispatch(operation: str, *args: object, **kwargs: object) -> object:
        """Execute one Analytics Workbench operation.

        Returns:
            Operation result.

        Raises:
            KeyError: When a resource is unknown or foreign-owned.
            ValueError: If the operation is unsupported.
        """
        handler = routed.get(operation)
        if handler is None:
            message = "unsupported Analytics workbench operation"
            raise ValueError(message)
        return handler(context, *args, **kwargs)

    return dispatch


def _unavailable(*args: object, **kwargs: object) -> object:
    """Fail closed until composition injects the reader.

    Raises:
        RuntimeError: Always, until the composition task wires the reader.
    """
    del args, kwargs
    raise RuntimeError("ANALYTICS_WORKBENCH_RUNTIME_UNAVAILABLE")


def build_analytics_workbench_source_bundle() -> Mapping[str, object]:
    """Build the default uncomposed composition source bundle.

    Returns:
        Opaque composition source consumed by the application factory;
        readers remain fail-closed until the composition task wires them.
    """
    logger.info("Building Analytics workbench composition source")
    return {
        "source": build_analytics_workbench_source(
            report_reader=cast("_ReportReader", _unavailable),
            result_reader=cast("_ResultReader", _unavailable),
            projection_builder=cast("_ProjectionBuilder", _unavailable),
            comparator=cast("_Comparator", _unavailable),
        ),
    }


__all__ = (
    "build_analytics_workbench_composition",
    "build_analytics_workbench_source",
    "build_analytics_workbench_source_bundle",
)


def _unavailable_projection(*args: object, **kwargs: object) -> object:
    """Fail closed until report deserialization is composed.

    Raises:
        RuntimeError: Always, until the deserialization seam is wired.
    """
    del args, kwargs
    raise RuntimeError("ANALYTICS_WORKBENCH_RUNTIME_UNAVAILABLE")


def build_analytics_workbench_composition(settings: object) -> Callable[..., object]:
    """Build the production Analytics Workbench source from runtime settings.

    Args:
        settings: API runtime settings owning the simulation artifact root.

    Returns:
        Dispatch source with catalogue-backed report and result readers.
    """
    from pathlib import Path

    typed_settings = cast("Any", settings)
    artifact_root = Path(typed_settings.simulation_artifact_root)

    def read_report_file(_run_id: str, report_ref: str) -> str:
        """Read one attached immutable report artifact.

        Returns:
            Serialized report JSON text.

        Raises:
            KeyError: When the artifact file is absent.
        """
        target = (artifact_root / report_ref).resolve()
        if artifact_root.resolve() not in target.parents:
            raise KeyError("ANALYTICS_REPORT_NOT_ATTACHED")
        if not target.is_file():
            raise KeyError("ANALYTICS_REPORT_NOT_ATTACHED")
        return target.read_text(encoding="utf-8")

    def read_canonical_result(run_id: str) -> Mapping[str, object] | None:
        """Read one canonical Simulation result as a plain mapping.

        Returns:
            Result mapping, or ``None`` when the run is unknown.
        """
        from app.services.simulator import get_simulation_result

        result = get_simulation_result(run_id, artifact_root=artifact_root)
        if result is None:
            return None
        if isinstance(result, Mapping):
            return result
        dumper = getattr(result, "model_dump", None)
        if dumper is None:
            return None
        return cast("Mapping[str, object]", dumper(mode="python"))

    return build_analytics_workbench_source(
        report_reader=read_report_file,
        result_reader=read_canonical_result,
        projection_builder=_unavailable_projection,
        comparator=_unavailable_projection,
    )
