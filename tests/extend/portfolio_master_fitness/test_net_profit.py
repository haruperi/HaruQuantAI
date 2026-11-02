"""Tests for NetProfit fitness metric selector (PM-METRIC-NetProfit)."""

from __future__ import annotations

from app.extend.portfolio_master_fitness.base import PlTypes, StatsKey, ValueTypes
from app.extend.portfolio_master_fitness.net_profit import NetProfit


class TestNetProfit:
    """Test suite for PM-METRIC-NetProfit."""

    def test_donor_attributes_and_instance(self) -> None:
        """Verify instance properties match donor NetProfit.java specification."""
        metric = NetProfit()
        assert metric.name == "Net Profit (Return)"
        assert metric.value_type == ValueTypes.Maximize
        assert metric.target_value == 0.0
        assert metric.range_min == -10000.0
        assert metric.range_max == 10000.0
        assert metric.stats_key == StatsKey.NET_PROFIT
        assert metric.pl_type == PlTypes.Money
        assert metric.maximize is True

    def test_compute_present(self) -> None:
        """Assert present NetProfit values are extracted without modification."""
        stats = {"NetProfit": 12.5}
        assert NetProfit.compute(stats) == 12.5
        assert stats == {"NetProfit": 12.5}

        stats_neg = {"NetProfit": -4.0}
        assert NetProfit.compute(stats_neg) == -4.0

        # Instance compute
        metric = NetProfit()
        assert metric.compute(stats) == 12.5

    def test_compute_missing_and_empty(self) -> None:
        """Assert empty and missing mappings return 0.0 without substitutions."""
        assert NetProfit.compute({}) == 0.0

        stats_other = {"ReturnDDRatio": 99.0}
        assert NetProfit.compute(stats_other) == 0.0
        assert stats_other == {"ReturnDDRatio": 99.0}

        # Invalid string value
        assert NetProfit.compute({"NetProfit": "invalid"}) == 0.0

    def test_print_formatting(self) -> None:
        """Assert print formats values as monetary strings."""
        metric = NetProfit()
        assert metric.print(1500.0) == "$1,500.00"
        assert NetProfit.print(-250.5) == "-$250.50"

    def test_results_group_compatibility(self) -> None:
        """Assert compute functions with ResultsGroup mock object."""

        class MockStats:
            NetProfit = 450.0

        class MockPortfolio:
            def stats(self, sample_type: int = 0) -> MockStats:
                del sample_type
                return MockStats()

        class MockResultsGroup:
            def portfolio(self) -> MockPortfolio:
                return MockPortfolio()

        res = MockResultsGroup()
        assert NetProfit.compute(res) == 450.0
