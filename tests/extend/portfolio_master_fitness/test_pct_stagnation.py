"""Tests for PctStagnation fitness metric selector (PM-METRIC-PctStagnation)."""

from __future__ import annotations

from app.extend.portfolio_master_fitness.base import PlTypes, StatsKey, ValueTypes
from app.extend.portfolio_master_fitness.pct_stagnation import PctStagnation


class TestPctStagnation:
    """Test suite for PM-METRIC-PctStagnation."""

    def test_donor_attributes_and_instance(self) -> None:
        """Verify instance properties match donor PctStagnation.java specification."""
        metric = PctStagnation()
        assert metric.name == "% Stagnation"
        assert metric.value_type == ValueTypes.Minimize
        assert metric.target_value == 0.0
        assert metric.range_min == 0.0
        assert metric.range_max == 100.0
        assert metric.stats_key == StatsKey.STAGNATION_PERIOD_PCT
        assert metric.pl_type == PlTypes.Percent
        assert metric.maximize is False

    def test_compute_present(self) -> None:
        """Assert present StagnationPct values are extracted without modification."""
        stats = {"StagnationPct": 12.5}
        assert PctStagnation.compute(stats) == 12.5
        assert stats == {"StagnationPct": 12.5}

        stats_neg = {"StagnationPct": -4.0}
        assert PctStagnation.compute(stats_neg) == -4.0

        # Instance compute
        metric = PctStagnation()
        assert metric.compute(stats) == 12.5

    def test_compute_missing_and_empty(self) -> None:
        """Assert empty and missing mappings return 0.0 without substitutions."""
        assert PctStagnation.compute({}) == 0.0

        stats_other = {"NetProfit": 99.0}
        assert PctStagnation.compute(stats_other) == 0.0
        assert stats_other == {"NetProfit": 99.0}

        # Invalid string value
        assert PctStagnation.compute({"StagnationPct": "invalid"}) == 0.0

    def test_print_formatting(self) -> None:
        """Assert print formats values as percentage strings."""
        metric = PctStagnation()
        assert metric.print(23.45) == "23.45%"
        assert PctStagnation.print(0.0) == "0.00%"

    def test_results_group_compatibility(self) -> None:
        """Assert compute functions with ResultsGroup mock object."""

        class MockStats:
            StagnationPct = 14.2

        class MockPortfolio:
            def stats(self, sample_type: int = 0) -> MockStats:
                del sample_type
                return MockStats()

        class MockResultsGroup:
            def portfolio(self) -> MockPortfolio:
                return MockPortfolio()

        res = MockResultsGroup()
        assert PctStagnation.compute(res) == 14.2
