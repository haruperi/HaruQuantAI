"""Tests for ReturnDD fitness metric selector (PM-METRIC-ReturnDD)."""

from __future__ import annotations

from app.extend.portfolio_master_fitness.return_dd import ReturnDD


class TestReturnDD:
    """Test suite for PM-METRIC-ReturnDD."""

    def test_compute_present(self) -> None:
        """Assert present ReturnDDRatio values are extracted without modification."""
        stats = {"ReturnDDRatio": 12.5}
        assert ReturnDD.compute(stats) == 12.5
        assert stats == {"ReturnDDRatio": 12.5}

        stats_neg = {"ReturnDDRatio": -4.0}
        assert ReturnDD.compute(stats_neg) == -4.0

    def test_compute_missing_and_empty(self) -> None:
        """Assert empty and missing mappings return 0.0 without substitutions."""
        assert ReturnDD.compute({}) == 0.0

        stats_other = {"NetProfit": 99.0}
        assert ReturnDD.compute(stats_other) == 0.0
        assert stats_other == {"NetProfit": 99.0}
