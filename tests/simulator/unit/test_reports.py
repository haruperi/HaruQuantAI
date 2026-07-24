"""Unit tests for deterministic Simulation report rendering."""
# ruff: noqa: INP001

from pathlib import Path

from app.services.simulator.reporting import build_json_report, build_markdown_report
from tests.simulator.unit.test_reporting_contracts import _result


def test_json_report_is_deterministic() -> None:
    """Serialize identical results to byte-identical JSON."""
    assert build_json_report(_result()) == build_json_report(_result())


def test_markdown_report_discloses_shortcuts() -> None:
    """Include explicit assumptions and limitations in Markdown."""
    report = build_markdown_report(_result())
    assert "No queue-position model." in report
    assert "Bid and ask are provider evidence." in report


def test_markdown_report_matches_reviewed_golden_artifact() -> None:
    """Keep the canonical human-facing report byte-stable."""
    golden_path = Path(__file__).parents[1] / "fixtures" / "golden" / "report.md"
    assert build_markdown_report(_result()) == golden_path.read_text(encoding="utf-8")
