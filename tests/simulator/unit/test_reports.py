"""Unit tests for deterministic Simulation report rendering."""

from pathlib import Path

from app.services.simulator.errors import unwrap_simulation_response
from app.services.simulator.reporting import build_json_report, build_markdown_report

from tests.simulator.unit.test_reporting_contracts import _result


def test_json_report_is_deterministic() -> None:
    """Serialize identical results to byte-identical JSON."""
    assert unwrap_simulation_response(
        build_json_report(_result()), operation="test.reports.build_json_report"
    ) == unwrap_simulation_response(
        build_json_report(_result()), operation="test.reports.build_json_report"
    )


def test_markdown_report_discloses_shortcuts() -> None:
    """Include explicit assumptions and limitations in Markdown."""
    report = unwrap_simulation_response(
        build_markdown_report(_result()), operation="test.reports.build_markdown_report"
    )
    assert "No queue-position model." in report
    assert "Bid and ask are provider evidence." in report


def test_markdown_report_matches_reviewed_golden_artifact() -> None:
    """Keep the canonical human-facing report byte-stable."""
    golden_path = Path(__file__).parents[1] / "fixtures" / "golden" / "report.md"
    assert unwrap_simulation_response(
        build_markdown_report(_result()), operation="test.reports.build_markdown_report"
    ) == golden_path.read_text(encoding="utf-8")
