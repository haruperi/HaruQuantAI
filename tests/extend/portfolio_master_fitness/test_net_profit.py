"""Tests for NetProfit fitness metric selector (PM-METRIC-NetProfit)."""

from __future__ import annotations

from app.extend.portfolio_master_fitness.net_profit import NetProfit


class TestNetProfit:
    """Test suite for PM-METRIC-NetProfit."""

    def test_compute_present(self) -> None:
        """Assert present NetProfit values are extracted without modification."""
        stats = {"NetProfit": 12.5}
        assert NetProfit.compute(stats) == 12.5
        assert stats == {"NetProfit": 12.5}

        stats_neg = {"NetProfit": -4.0}
        assert NetProfit.compute(stats_neg) == -4.0

    def test_compute_missing_and_empty(self) -> None:
        """Assert empty and missing mappings return 0.0 without substitutions."""
        assert NetProfit.compute({}) == 0.0

        stats_other = {"ReturnDDRatio": 99.0}
        assert NetProfit.compute(stats_other) == 0.0
        assert stats_other == {"ReturnDDRatio": 99.0}
