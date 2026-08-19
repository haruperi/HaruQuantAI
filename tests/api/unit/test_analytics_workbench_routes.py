"""Route and orchestration tests for the Analytics Workbench gateway."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.api.identity import build_auth_context
from app.services.api.workstation.analytics_workbench.orchestration import (
    build_analytics_workbench_source,
)
from app.services.api.workstation.analytics_workbench.routes import (
    _analytics_workbench_source,
    _annotate_run,
    _archive_run,
    _compare_runs,
    _get_periods,
    _get_trade,
    _get_trades,
    _get_workbench,
    _list_runs,
)
from app.services.api.workstation.analytics_workbench.schemas import (
    AnalyticsAnnotationRequest,
    AnalyticsArchiveRequest,
    AnalyticsCompareRequest,
)
from app.utils import generate_id
from fastapi import HTTPException

_RESULT: dict[str, object] = {
    "schema_id": "simulation.result.v1",
    "run_id": "run-1",
    "closed_trades": (
        {"ticket": "t-1", "type": "BUY", "exit_time": "2026-01-02T00:00:00Z"},
        {"ticket": "t-2", "type": "SELL", "exit_time": "2026-01-03T00:00:00Z"},
        {"ticket": "t-3", "type": "BUY", "exit_time": "2026-01-04T00:00:00Z"},
    ),
}


def _context(*permissions: str) -> Any:
    """Return an authenticated principal carrying the given permissions."""
    return build_auth_context(
        principal={
            "principal_id": "user-analytics",
            "principal_type": "USER",
            "roles": ("researcher",),
            "permissions": permissions,
            "scopes": (),
            "tenant_or_environment": "development",
            "runtime_profile": "simulation",
        },
        trace={
            "issued_at": datetime.now(UTC),
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
        },
    )


class _FakeStore:
    """In-memory catalogue rows standing in for persistence reads."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict[str, object]] = {}

    def add(self, run_id: str, principal_id: str, **extra: object) -> None:
        self.rows[(run_id, principal_id)] = {
            "run_id": run_id,
            "principal_id": principal_id,
            "status": "completed",
            "report_ref": f"{run_id}/analytics-report.json",
            "result_ref": f"{run_id}/result.json",
            "artifact_manifest_ref": f"{run_id}/manifest.json",
            "name": None,
            "alias": None,
            "description": None,
            "tags": "[]",
            "run_reason": None,
            **extra,
        }


def _read_report(run_id: str, report_ref: str) -> str:
    """Replay one attached report read."""
    del run_id, report_ref
    return '{"report": true}'


def _make_result_reader(result: object):
    """Build one result reader bound to the faked evidence."""

    def read_result(run_id: str) -> object:
        """Replay one canonical result read."""
        del run_id
        return result

    return read_result


def _build_projection(*args: object, **kwargs: object) -> dict[str, str]:
    """Replay one delegated projection."""
    del args, kwargs
    return {"payload": "workbench"}


def _build_periods(*args: object, **kwargs: object) -> dict[str, object]:
    """Replay one delegated period aggregation."""
    del args
    return {
        "rows": (),
        "dimension": kwargs.get("dimension"),
        "context": kwargs.get("context"),
    }


def _compare_reports(reports: object, **kwargs: object) -> dict[str, int]:
    """Replay one delegated comparison."""
    del kwargs
    return {"comparison": len(reports)}  # type: ignore[arg-type]


def _source(
    store: _FakeStore,
    monkeypatch: pytest.MonkeyPatch,
    *,
    result: object = _RESULT,
) -> Any:
    """Build one dispatch source over the fake store."""
    from app.services.api.workstation.analytics_workbench import orchestration

    def read_run(run_id: str, principal_id: str, *, request_id: str) -> tuple:
        row = store.rows.get((run_id, principal_id))
        return (row,) if row else ()

    def page_runs(
        principal_id: str, *, limit: int, offset: int, request_id: str
    ) -> tuple:
        rows = tuple(
            row for (_, owner), row in store.rows.items() if owner == principal_id
        )
        return rows[offset : offset + limit]

    def annotate_run(
        run_id: str,
        principal_id: str,
        *,
        name: str | None,
        alias: str | None,
        description: str | None,
        tags: str,
        run_reason: str | None,
        updated_at: str,
        request_id: str,
    ) -> int:
        row = store.rows.get((run_id, principal_id))
        if row is None:
            return 0
        row.update(
            {
                "name": name,
                "alias": alias,
                "description": description,
                "tags": tags,
                "run_reason": run_reason,
            }
        )
        return 1

    def archive_run(
        run_id: str, principal_id: str, *, updated_at: str, request_id: str
    ) -> int:
        row = store.rows.get((run_id, principal_id))
        if row is None:
            return 0
        row["archive_state"] = "archived"
        return 1

    monkeypatch.setattr(orchestration, "read_simulation_result_record", read_run)
    monkeypatch.setattr(orchestration, "read_simulation_results_page", page_runs)
    monkeypatch.setattr(
        orchestration, "annotate_simulation_result_record", annotate_run
    )
    monkeypatch.setattr(orchestration, "archive_simulation_result_record", archive_run)

    return build_analytics_workbench_source(
        report_reader=_read_report,
        result_reader=_make_result_reader(result),
        projection_builder=_build_projection,
        comparator=_compare_reports,
        period_builder=_build_periods,
    )


def test_uncomposed_source_fails_closed() -> None:
    """The gateway dependency refuses service until composed."""
    with pytest.raises(HTTPException) as raised:
        _analytics_workbench_source()
    assert raised.value.status_code == 503
    assert raised.value.detail == "ANALYTICS_WORKBENCH_RUNTIME_UNAVAILABLE"


def test_reads_require_permission_and_404_foreign_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Authorization precedes access; foreign runs are uniform 404s."""
    store = _FakeStore()
    store.add("run-1", "user-analytics")
    source = _source(store, monkeypatch)
    with pytest.raises(HTTPException) as raised:
        _get_workbench("run-1", _context(), source)
    assert raised.value.status_code == 403
    with pytest.raises(HTTPException) as raised:
        _get_workbench(
            "run-1", _context("simulation:read"), _source(_FakeStore(), monkeypatch)
        )
    assert raised.value.status_code == 404
    assert raised.value.detail == "ANALYTICS_RUN_NOT_FOUND"


def test_trades_paginate_with_side_filter_and_totals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Trade pagination is bounded and reports the true total."""
    store = _FakeStore()
    store.add("run-1", "user-analytics")
    source = _source(store, monkeypatch)
    page = _get_trades(
        "run-1", _context("simulation:read"), source, page=1, page_size=2
    )
    assert page["total_count"] == 3
    assert len(page["trades"]) == 2
    buys = _get_trades(
        "run-1", _context("simulation:read"), source, page=1, page_size=10, side="buy"
    )
    assert buys["total_count"] == 2
    assert {trade["ticket"] for trade in buys["trades"]} == {"t-1", "t-3"}


def test_trade_detail_returns_the_exact_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One trade is addressable by ticket."""
    store = _FakeStore()
    store.add("run-1", "user-analytics")
    source = _source(store, monkeypatch)
    trade = _get_trade("run-1", "t-2", _context("simulation:read"), source)
    assert trade["ticket"] == "t-2"
    with pytest.raises(HTTPException) as raised:
        _get_trade("run-1", "t-x", _context("simulation:read"), source)
    assert raised.value.status_code == 404
    assert raised.value.detail == "ANALYTICS_TRADE_NOT_FOUND"


def test_period_query_dimensions_are_exact_enums(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only the frozen period dimensions and contexts are accepted."""
    store = _FakeStore()
    store.add("run-1", "user-analytics")
    source = _source(store, monkeypatch)
    payload = _get_periods(
        "run-1", _context("simulation:read"), source, dimension="week", context="long"
    )
    assert payload["dimension"] == "week"
    assert payload["context"] == "long"


def test_comparison_delegates_to_the_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Comparison evidence comes only from the Analytics owner."""
    store = _FakeStore()
    store.add("run-1", "user-analytics")
    store.add("run-2", "user-analytics")
    source = _source(store, monkeypatch)
    result = _compare_runs(
        AnalyticsCompareRequest(run_ids=("run-1", "run-2")),
        _context("simulation:read"),
        source,
    )
    assert result == {"comparison": 2}


def test_annotations_and_archive_are_metadata_only_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Writes need permission, idempotency, and never delete evidence."""
    store = _FakeStore()
    store.add("run-1", "user-analytics")
    source = _source(store, monkeypatch)
    context = _context("simulation:read", "simulation:run")
    with pytest.raises(HTTPException) as raised:
        _annotate_run(
            "run-1",
            AnalyticsAnnotationRequest(name="Renamed"),
            context,
            source,
        )
    assert raised.value.status_code == 422
    annotated = _annotate_run(
        "run-1",
        AnalyticsAnnotationRequest(name="Renamed"),
        context,
        source,
        idempotency_key=generate_id("req"),
    )
    assert annotated == {"run_id": "run-1", "updated": True}
    archived = _archive_run(
        "run-1",
        AnalyticsArchiveRequest(archive_state="archived"),
        context,
        source,
        idempotency_key=generate_id("req"),
    )
    assert archived == {"run_id": "run-1", "archived": True}
    assert store.rows[("run-1", "user-analytics")]["report_ref"] == (
        "run-1/analytics-report.json"
    )


def test_run_listing_is_principal_scoped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Listing returns only the caller's catalogue rows."""
    store = _FakeStore()
    store.add("run-1", "user-analytics")
    store.add("run-2", "someone-else")
    payload = _list_runs(_context("simulation:read"), _source(store, monkeypatch))
    assert [row["run_id"] for row in payload["runs"]] == ["run-1"]
