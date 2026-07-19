"""Tests for Optimization report handoff packages."""

# ruff: noqa: INP001

from app.services.optimization.evidence import (
    build_optimization_evidence,
    build_report_package,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request


def test_report_package_uses_existing_evidence() -> None:
    """Handoff preserves supplied chart values and candidate tables."""
    result = build_optimization_evidence(evidence_request())
    package = build_report_package(result)
    assert package["charts"] == result.chart_data
    assert package["tables"] == {"ranked_candidates": list(result.ranked_candidates)}
