"""Unit tests for PortfolioMasterFitness base framework and helpers."""

from __future__ import annotations

from app.extend.portfolio_master_fitness.base import (
    PlTypes,
    PortfolioMasterFitness,
    StatsKey,
    ValueTypes,
)


class DummyPortfolioStats:
    def __init__(self, key: str, value: float) -> None:
        setattr(self, key, value)


class DummyPortfolio:
    def __init__(self, stats_obj: object) -> None:
        self._stats = stats_obj

    def stats(self, sample_type: int = 0) -> object:
        del sample_type
        return self._stats


class DummyResultsGroup:
    def __init__(self, portfolio: DummyPortfolio) -> None:
        self._portfolio = portfolio

    def portfolio(self) -> DummyPortfolio:
        return self._portfolio


class TestPortfolioMasterFitnessBase:
    """Test suite for PortfolioMasterFitness base class and helper types."""

    def test_value_types(self) -> None:
        """Verify ValueTypes constant values."""
        assert ValueTypes.Maximize == 1
        assert ValueTypes.Minimize == 2
        assert ValueTypes.Approximate == 3

    def test_stats_key_constants(self) -> None:
        """Verify StatsKey string identifiers."""
        assert StatsKey.NET_PROFIT == "NetProfit"
        assert StatsKey.STAGNATION_PERIOD_PCT == "StagnationPct"
        assert StatsKey.RETURN_DD_RATIO == "ReturnDDRatio"

    def test_pl_types_formatting(self) -> None:
        """Verify PlTypes formatting across percent, money, pips, and fallback."""
        assert PlTypes.print_pl(15.25, PlTypes.Percent) == "15.25%"
        assert PlTypes.print_pl(1250.5, PlTypes.Money) == "$1,250.50"
        assert PlTypes.print_pl(-500.25, PlTypes.Money) == "-$500.25"
        assert PlTypes.print_pl(12.3, PlTypes.Pips) == "12.3 pips"
        assert PlTypes.print_pl(42.0, 99) == "42.00"
        # Donor compatibility alias
        assert PlTypes.printPL(10.0, PlTypes.Percent) == "10.00%"

    def test_base_fitness_initialization_and_properties(self) -> None:
        """Verify default and custom initialization of PortfolioMasterFitness."""
        base = PortfolioMasterFitness(
            name="CustomMetric",
            value_type=ValueTypes.Minimize,
            target_value=5.0,
            range_min=-50.0,
            range_max=50.0,
            stats_key="CustomKey",
            pl_type=PlTypes.Percent,
        )
        assert base.name == "CustomMetric"
        assert base.value_type == ValueTypes.Minimize
        assert base.target_value == 5.0
        assert base.range_min == -50.0
        assert base.range_max == 50.0
        assert base.stats_key == "CustomKey"
        assert base.pl_type == PlTypes.Percent
        assert base.maximize is False

        default_base = PortfolioMasterFitness("Default")
        assert default_base.maximize is True

    def test_compute_with_mappings(self) -> None:
        """Verify compute extracting values from mappings."""
        fitness = PortfolioMasterFitness(
            name="Test",
            stats_key="Profit",
            pl_type=PlTypes.Money,
        )
        assert fitness.compute({"Profit": 100.5}) == 100.5
        assert fitness.compute({"Profit": "250.25"}) == 250.25
        assert fitness.compute({"Profit": "invalid"}) == 0.0
        assert fitness.compute({}) == 0.0

    def test_compute_with_results_group_objects(self) -> None:
        """Verify compute handling ResultsGroup-like portfolio objects."""
        fitness = PortfolioMasterFitness(
            name="Test",
            stats_key="NetProfit",
            pl_type=PlTypes.Money,
        )
        stats = DummyPortfolioStats("NetProfit", 550.0)
        res = DummyResultsGroup(DummyPortfolio(stats))
        assert fitness.compute(res) == 550.0

        # Mapping-based stats object inside portfolio()
        res_map = DummyResultsGroup(DummyPortfolio({"NetProfit": 300.0}))
        assert fitness.compute(res_map) == 300.0

        # Result with direct attribute
        class DirectObj:
            NetProfit = 750.0

        assert fitness.compute(DirectObj()) == 750.0

        # Unsupported object returns 0.0
        assert fitness.compute(object()) == 0.0

    def test_print_formatting(self) -> None:
        """Verify print method uses assigned pl_type."""
        fitness = PortfolioMasterFitness(
            name="TestMoney",
            pl_type=PlTypes.Money,
        )
        assert fitness.print(1000.0) == "$1,000.00"
