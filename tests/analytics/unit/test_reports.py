"""Unit tests for Analytics barrier reports."""

from decimal import Decimal
from types import SimpleNamespace

from app.services.analytics.contracts import ClosedTradeLedger
from app.services.analytics.reports import (
    WorstDayDistribution,
    build_barrier_section,
    build_worst_day_distribution,
)
from app.services.risk import get_drawdown_mode


def _reports() -> tuple[object, object]:
    """Build bounded Optimization report fixtures."""
    first = SimpleNamespace(
        mandate_version="v1",
        mode=get_drawdown_mode("STATIC"),
        paths=10,
        seed=1,
        probability_target=Decimal("0.4"),
        probability_daily_breach=Decimal("0.1"),
        probability_drawdown_breach=Decimal("0.2"),
        probability_expired=Decimal("0.3"),
        median_termination_day=Decimal(3),
    )
    joint = SimpleNamespace(
        paths=10,
        seed=1,
        account_ids=("a", "b"),
        surviving_accounts_distribution={
            0: Decimal("0.2"),
            1: Decimal("0.4"),
            2: Decimal("0.4"),
        },
        probability_none_survive=Decimal("0.2"),
        measured_correlation={"a:b": Decimal("0.8")},
    )
    return first, joint


def test_worst_day_reports_percentiles_not_mean() -> None:
    """Report ordered tail percentiles instead of a mean summary."""
    distribution = build_worst_day_distribution(
        ClosedTradeLedger(
            daily_pnl=(Decimal(-100), Decimal(-10), Decimal(-50), Decimal(200))
        ),
        percentiles=(Decimal("0.5"), Decimal("0.95")),
    )
    assert distribution.percentiles["0.5"] == Decimal(30)
    assert distribution.percentiles["0.5"] != Decimal(40)


def test_barrier_section_skips_on_absent_input() -> None:
    """Skip barrier reporting rather than fabricating missing evidence."""
    section = build_barrier_section(None, None, None, mandate_version="v1")
    assert section.status == "skipped"
    assert section.metrics == ()


def test_barrier_section_contains_mode_sensitivity() -> None:
    """Include Optimization barrier and mode-sensitivity evidence."""
    first, joint = _reports()
    worst = WorstDayDistribution(
        percentiles={"0.95": Decimal(100)},
        observations=4,
        maximum_loss=Decimal(100),
    )
    section = build_barrier_section(
        first,
        joint,
        worst,
        mandate_version="v1",
        mode_sensitivity={get_drawdown_mode("STATIC"): first},
    )
    assert section.status == "completed"
    assert any(
        item.metric_key == "drawdown_mode_sensitivity" for item in section.metrics
    )
