"""Tests for Phase 0 performance measurement summaries."""

from __future__ import annotations

from scripts.measure_phase0_baseline import summarize


def test_summary_retains_samples_and_budget_result() -> None:
    """Measured evidence keeps raw values and evaluates the median."""
    result = summarize([3.0, 1.0, 2.0, 5.0, 4.0, 6.0, 7.0], 4.0)

    assert result["samples"] == [3.0, 1.0, 2.0, 5.0, 4.0, 6.0, 7.0]
    assert result["median"] == 4.0
    assert result["p95"] == 7.0
    assert result["budget_result"] == "PASS"
