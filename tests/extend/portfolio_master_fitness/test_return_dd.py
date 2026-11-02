"""Tests for ReturnDD fitness metric selector (PM-METRIC-ReturnDD)."""

from __future__ import annotations

from app.extend.portfolio_master_fitness.base import PlTypes, StatsKey, ValueTypes
from app.extend.portfolio_master_fitness.return_dd import ReturnDD


class TestReturnDD:
    """Test suite for PM-METRIC-ReturnDD."""

    def test_donor_attributes_and_instance(self) -> None:
        """Verify instance properties match donor ReturnDD.java specification."""
        metric = ReturnDD()
        assert metric.name == "Return / Drawdown ratio"
        assert metric.value_type == ValueTypes.Maximize
        assert metric.target_value == 0.0
        assert metric.range_min == -20.0
        assert metric.range_max == 20.0
        assert metric.stats_key == StatsKey.RETURN_DD_RATIO
        assert metric.pl_type == PlTypes.Money
        assert metric.maximize is True

    def test_compute_present(self) -> None:
        """Assert present ReturnDDRatio values are extracted without modification."""
        stats = {"ReturnDDRatio": 12.5}
        assert ReturnDD.compute(stats) == 12.5
        assert stats == {"ReturnDDRatio": 12.5}

        stats_neg = {"ReturnDDRatio": -4.0}
        assert ReturnDD.compute(stats_neg) == -4.0

        # Instance compute
        metric = ReturnDD()
        assert metric.compute(stats) == 12.5

    def test_compute_missing_and_empty(self) -> None:
        """Assert empty and missing mappings return 0.0 without substitutions."""
        assert ReturnDD.compute({}) == 0.0

        stats_other = {"NetProfit": 99.0}
        assert ReturnDD.compute(stats_other) == 0.0
        assert stats_other == {"NetProfit": 99.0}

        # Invalid string value
        assert ReturnDD.compute({"ReturnDDRatio": "invalid"}) == 0.0

    def test_print_formatting(self) -> None:
        """Assert print formats values as monetary/ratio strings."""
        metric = ReturnDD()
        assert metric.print(3.45) == "$3.45"
        assert ReturnDD.print(-1.2) == "-$1.20"

    def test_results_group_compatibility(self) -> None:
        """Assert compute functions with ResultsGroup mock object."""

        class MockStats:
            ReturnDDRatio = 2.85

        class MockPortfolio:
            def stats(self, sample_type: int = 0) -> MockStats:
                del sample_type
                return MockStats()

        class MockResultsGroup:
            def portfolio(self) -> MockPortfolio:
                return MockPortfolio()

        res = MockResultsGroup()
        assert ReturnDD.compute(res) == 2.85
