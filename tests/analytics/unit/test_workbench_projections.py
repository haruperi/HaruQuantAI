"""Unit coverage for the Analytics workbench projection (FEAT-ANLT-11)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from app.services.analytics import (
    build_analytics_period_tables,
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
        "entry_time": NOW + timedelta(hours=1),
        "exit_time": NOW + timedelta(hours=2),
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


def _ledger_result(source: dict[str, object]) -> dict[str, object]:
    """Build a canonical Simulation mapping carrying the source ledger.

    Args:
        source: Producer-neutral source evidence.

    Returns:
        Canonical result mapping whose closed-trade ledger mirrors the
        report's own trades plus owner excursion values.
    """
    return {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "run_id": "run-workbench",
        "status": "completed",
        "closed_trades": [
            {**dict(trade), "mae": Decimal("-0.005"), "mfe": Decimal("0.008")}
            for trade in source["closed_trades"]  # type: ignore[union-attr]
        ],
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


def test_equity_derived_sections_carry_owner_series() -> None:
    """Drawdown, returns, VAMI, and monthly rows project from owner evidence."""
    payload = unwrap(
        build_analytics_workbench_payload(
            _report_from(_two_trade_source()), _SIMULATION_RESULT
        )
    )
    for section in (
        payload.drawdown_curve,
        payload.returns_series,
        payload.vami,
        payload.monthly_returns,
    ):
        assert section.status == "completed"
        assert section.items
    drawdowns = [Decimal(str(row["drawdown"])) for row in payload.drawdown_curve.items]
    assert all(value <= 0 for value in drawdowns)
    months = [str(row["month"]) for row in payload.monthly_returns.items]
    assert months == sorted(months)


def test_trade_ledger_sections_require_the_canonical_ledger() -> None:
    """Missing ledger evidence is never substituted with zero values."""
    payload = unwrap(
        build_analytics_workbench_payload(
            _report_from(_two_trade_source()), _SIMULATION_RESULT
        )
    )
    for section in (
        payload.period_tables,
        payload.trade_calendar,
        payload.streaks,
        payload.excursions,
        payload.duration,
    ):
        assert section.status == "unavailable"
        assert section.reason == "authoritative_evidence_unavailable"
        assert section.items == ()
        assert section.sample_count == 0


def test_trade_ledger_sections_project_owner_rows() -> None:
    """Ledger-backed sections carry owner counts, sums, and durations."""
    source = _two_trade_source()
    payload = unwrap(
        build_analytics_workbench_payload(_report_from(source), _ledger_result(source))
    )
    streak_outcomes = [str(row["outcome"]) for row in payload.streaks.items]
    assert streak_outcomes == ["win", "loss"]
    streak_counts = [int(row["streak"]) for row in payload.streaks.items]
    assert streak_counts == [1, -1]
    calendar_count = sum(
        int(row["trade_count"]) for row in payload.trade_calendar.items
    )
    assert calendar_count == 2
    period_count = sum(int(row["trade_count"]) for row in payload.period_tables.items)
    assert period_count == 2
    durations = [int(row["duration_seconds"]) for row in payload.duration.items]
    assert durations == [0, 3600]
    excursions = payload.excursions.items
    assert all(row["mae"] is not None and row["mfe"] is not None for row in excursions)


def test_period_tables_honour_dimension_and_context() -> None:
    """The dedicated period projection filters by dimension and context."""
    source = _two_trade_source()
    report = _report_from(source)
    long_rows = unwrap(
        build_analytics_period_tables(report, _ledger_result(source), context="long")
    )
    assert sum(int(row["trade_count"]) for row in long_rows) == 2
    short_rows = unwrap(
        build_analytics_period_tables(report, _ledger_result(source), context="short")
    )
    assert short_rows == ()


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
