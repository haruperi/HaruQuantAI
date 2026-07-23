"""Integration evidence for canonical Analytics report construction."""

# ruff: noqa: INP001

from app.utils import logger
from tests.analytics._support import _report


def test_build_performance_report_from_simulation_result() -> None:
    """A documented Simulation ledger fixture builds a complete report."""
    logger.debug("Testing Analytics Simulation-to-report workflow")
    report, _ = _report()
    assert report.schema_id == "analytics.performance_report.v1"
    assert {section.section_key for section in report.sections}.issuperset(
        {"trades", "pnl", "equity_returns", "drawdown"}
    )
