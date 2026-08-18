"""Unit coverage for the Analytics workbench projection (FEAT-ANLT-11)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.analytics import (
    build_analytics_workbench_payload,
    build_performance_report,
)

from tests.analytics._support import NOW, _configured, _source_with_profit, unwrap


def _two_trade_source() -> dict[str, object]:
    """Build one deterministic two-trade producer-neutral source.

    Returns:
        Source evidence with one winning and one losing round trip.
    """
    source = _source_with_profit(Decimal(25))
    trades = source["closed_trades"]
    first = trades[0]  # type: ignore[index]
    second = {
        **first,
        "ticket": "ticket-2",
        "exit_price": Decimal("1.10"),
        "profit": Decimal(-5),
        "commission": Decimal(-1),
    }
    source["closed_trades"] = (first, second)
    return source


def _report_from(source: dict[str, object]) -> Any:
    """Build one validated report from producer-neutral source evidence."""
    from app.utils import generate_id

    return unwrap(
        build_performance_report(
            source,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=_configured(),
        )
    )


_SIMULATION_RESULT: dict[str, object] = {
    "contract_version": "v1",
    "schema_id": "simulation.result.v1",
    "run_id": "run-workbench",
    "status": "completed",
}


def test_two_trade_projection_is_deterministic() -> None:
    """Identical owner evidence projects to identical payloads."""
    report = _report_from(_two_trade_source())
    first = unwrap(build_analytics_workbench_payload(report, _SIMULATION_RESULT))
    second = unwrap(build_analytics_workbench_payload(report, dict(_SIMULATION_RESULT)))
    assert first == second
    assert first.payload_id == f"workbench-{report.report_id}"
    assert first.summary.status == "completed"
    assert first.summary.total_count == len(first.summary.items)
    assert first.summary.items
    assert first.non_binding is True
    assert first.lineage["simulation_run_id"] == "run-workbench"


def test_drawdown_and_monthly_sections_stay_unavailable() -> None:
    """Missing owner evidence is never substituted with zero values."""
    payload = unwrap(
        build_analytics_workbench_payload(
            _report_from(_two_trade_source()), _SIMULATION_RESULT
        )
    )
    for section in (payload.drawdown_curve, payload.monthly_returns):
        assert section.status == "unavailable"
        assert section.reason == "authoritative_evidence_unavailable"
        assert section.items == ()
        assert section.sample_count == 0


def test_equity_curve_truncation_is_explicit() -> None:
    """A small bound truncates the equity series with visible evidence."""
    payload = unwrap(
        build_analytics_workbench_payload(
            _report_from(_two_trade_source()),
            _SIMULATION_RESULT,
            max_points=1,
        )
    )
    assert payload.equity_curve.status == "completed"
    assert payload.equity_curve.truncated is True
    assert payload.equity_curve.sample_count == 1
    assert payload.equity_curve.total_count > 1
    assert any(row["key"] == "equity_curve" for row in payload.truncation)


def test_non_canonical_simulation_evidence_fails_closed() -> None:
    """A non-canonical Simulation mapping is refused."""
    response = build_analytics_workbench_payload(
        _report_from(_two_trade_source()),
        {"schema_id": "something.else", "run_id": "run-x"},
    )
    assert getattr(response, "status", None) == "error"


def test_summary_rows_preserve_owner_source_contexts() -> None:
    """Projected rows keep the owner's all/long/short context labels."""
    payload = unwrap(
        build_analytics_workbench_payload(
            _report_from(_two_trade_source()), _SIMULATION_RESULT
        )
    )
    contexts = {str(row["source_context"]) for row in payload.summary.items}
    assert "all" in contexts
    assert all(context for context in contexts)
