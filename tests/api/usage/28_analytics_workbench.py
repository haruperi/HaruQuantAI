"""Standalone Analytics Workbench API feature usage."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest
from app.services.api import build_analytics_workbench_source
from app.services.api.widgets.analytics.schemas import (
    AnalyticsAnnotationRequest,
    AnalyticsArchiveRequest,
    AnalyticsCompareRequest,
    AnalyticsPeriodsQuery,
    AnalyticsTradesQuery,
)

_RESULT: dict[str, object] = {
    "schema_id": "simulation.result.v1",
    "run_id": "run-usage",
    "closed_trades": tuple(
        {"ticket": f"t-{index}", "type": "BUY", "exit_time": "2026-01-02T00:00:00Z"}
        for index in range(3)
    ),
}


def _store_rows() -> dict[tuple[str, str], dict[str, object]]:
    """Build the caller-side fake catalogue used by this program."""
    return {
        ("run-usage", "principal-usage"): {
            "run_id": "run-usage",
            "principal_id": "principal-usage",
            "status": "completed",
            "report_ref": "run-usage/analytics-report.json",
            "result_ref": "run-usage/result.json",
            "artifact_manifest_ref": "run-usage/manifest.json",
            "name": None,
            "alias": None,
            "description": None,
            "tags": "[]",
            "run_reason": None,
        }
    }


def _read_report(run_id: str, report_ref: str) -> str:
    """Replay one attached report read."""
    del run_id, report_ref
    return '{"report": true}'


def _read_result(run_id: str) -> object:
    """Replay one canonical result read."""
    del run_id
    return _RESULT


def _build_projection(*args: object, **kwargs: object) -> dict[str, str]:
    """Replay one delegated projection."""
    del args, kwargs
    return {"payload": "workbench"}


def _compare(reports: object, **kwargs: object) -> dict[str, int]:
    """Replay one delegated comparison."""
    del kwargs
    return {"comparison": len(reports)}  # type: ignore[arg-type]


def main() -> None:
    """Exercise the feature's public contracts and dispatch surface."""
    assert AnalyticsPeriodsQuery().dimension == "month"
    assert AnalyticsTradesQuery().page_size == 50
    assert AnalyticsCompareRequest(run_ids=("a", "b")).metric == "summary"
    assert AnalyticsAnnotationRequest(name="N").name == "N"
    assert AnalyticsArchiveRequest(archive_state="archived").archive_state == "archived"

    rows = _store_rows()
    from app.services.api.widgets.analytics import orchestration

    def read_run(run_id: str, principal_id: str, *, request_id: str) -> tuple:
        row = rows.get((run_id, principal_id))
        return (row,) if row else ()

    def page_runs(
        principal_id: str, *, limit: int, offset: int, request_id: str
    ) -> tuple:
        return tuple(row for (_, owner), row in rows.items() if owner == principal_id)[
            offset : offset + limit
        ]

    def annotate_run(*args: object, **kwargs: object) -> int:
        del args, kwargs
        return 1

    def archive_run(*args: object, **kwargs: object) -> int:
        del args, kwargs
        return 1

    def _build_periods(*args: object, **kwargs: object) -> dict[str, object]:
        """Replay one delegated period aggregation."""
        del args
        return {
            "rows": (),
            "dimension": kwargs.get("dimension"),
            "context": kwargs.get("context"),
        }

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(orchestration, "read_simulation_result_record", read_run)
    monkeypatch.setattr(orchestration, "read_simulation_results_page", page_runs)
    monkeypatch.setattr(
        orchestration, "annotate_simulation_result_record", annotate_run
    )
    monkeypatch.setattr(orchestration, "archive_simulation_result_record", archive_run)
    try:
        source = build_analytics_workbench_source(
            report_reader=_read_report,
            result_reader=_read_result,
            projection_builder=_build_projection,
            comparator=_compare,
            period_builder=_build_periods,
        )
        listed = source("list_runs", principal_id="principal-usage")
        report = source("report", "run-usage", principal_id="principal-usage")
        workbench = source("workbench", "run-usage", principal_id="principal-usage")
        trades = source(
            "trades",
            "run-usage",
            principal_id="principal-usage",
            page=1,
            page_size=2,
            side="buy",
        )
        trade = source("trade", "run-usage", "t-1", principal_id="principal-usage")
        comparison = source(
            "compare",
            {"run_ids": ("run-usage", "run-usage")},
            principal_id="principal-usage",
        )
        annotation = source(
            "annotate",
            "run-usage",
            {"name": "Renamed"},
            principal_id="principal-usage",
        )
        archive = source("archive", "run-usage", principal_id="principal-usage")
        print(
            {
                "feature": "analytics-workbench",
                "runs_listed": len(listed),
                "report_read": report == '{"report": true}',
                "workbench": workbench == {"payload": "workbench"},
                "trades_total": trades["total_count"],
                "trade_ticket": trade["ticket"],
                "comparison_runs": comparison["comparison"],
                "annotation": annotation["updated"] is True,
                "archive": archive["archived"] is True,
            }
        )
    finally:
        monkeypatch.undo()


if __name__ == "__main__":
    main()
