"""Tests for PctStagnation fitness metric selector (PM-METRIC-PctStagnation)."""

from __future__ import annotations

from app.extend.portfolio_master_fitness.pct_stagnation import PctStagnation


class TestPctStagnation:
    """Test suite for PM-METRIC-PctStagnation."""

    def test_compute_present(self) -> None:
        """Assert present StagnationPct values are extracted without modification."""
        stats = {"StagnationPct": 12.5}
        assert PctStagnation.compute(stats) == 12.5
        assert stats == {"StagnationPct": 12.5}

        stats_neg = {"StagnationPct": -4.0}
        assert PctStagnation.compute(stats_neg) == -4.0

    def test_compute_missing_and_empty(self) -> None:
        """Assert empty and missing mappings return 0.0 without substitutions."""
        assert PctStagnation.compute({}) == 0.0

        stats_other = {"NetProfit": 99.0}
        assert PctStagnation.compute(stats_other) == 0.0
        assert stats_other == {"NetProfit": 99.0}
