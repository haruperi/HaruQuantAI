"""Tests for PortfolioMasterFitness catalog and descriptors."""

from __future__ import annotations

import pytest
from app.extend.portfolio_master_fitness.catalog import (
    PortfolioMasterFitnessCatalog,
    PortfolioMasterFitnessDescriptor,
)
from app.extend.portfolio_master_fitness.net_profit import NetProfit
from app.extend.portfolio_master_fitness.pct_stagnation import PctStagnation
from app.extend.portfolio_master_fitness.return_dd import ReturnDD


class TestPortfolioMasterFitnessCatalog:
    """Test suite for PortfolioMasterFitnessCatalog."""

    def test_descriptors(self) -> None:
        """Assert all 3 descriptors match normative specifications."""
        descriptors = PortfolioMasterFitnessCatalog.descriptors()
        assert len(descriptors) == 3

        np_desc = PortfolioMasterFitnessCatalog.get_descriptor("NetProfit")
        assert np_desc == PortfolioMasterFitnessDescriptor(
            metric_id="NetProfit",
            label="Net Profit (Return)",
            stats_key="NetProfit",
            maximize=True,
            default_target=0.0,
            range_min=-10000.0,
            range_max=10000.0,
        )

        st_desc = PortfolioMasterFitnessCatalog.get_descriptor("PctStagnation")
        assert st_desc == PortfolioMasterFitnessDescriptor(
            metric_id="PctStagnation",
            label="% Stagnation",
            stats_key="StagnationPct",
            maximize=False,
            default_target=0.0,
            range_min=0.0,
            range_max=100.0,
        )

        dd_desc = PortfolioMasterFitnessCatalog.get_descriptor("ReturnDD")
        assert dd_desc == PortfolioMasterFitnessDescriptor(
            metric_id="ReturnDD",
            label="Return / Drawdown ratio",
            stats_key="ReturnDDRatio",
            maximize=True,
            default_target=0.0,
            range_min=-20.0,
            range_max=20.0,
        )

    def test_fitness_class_lookup_and_factory(self) -> None:
        """Assert class retrieval and factory instantiation."""
        assert PortfolioMasterFitnessCatalog.get_fitness_class("NetProfit") is NetProfit
        assert (
            PortfolioMasterFitnessCatalog.get_fitness_class("PctStagnation")
            is PctStagnation
        )
        assert PortfolioMasterFitnessCatalog.get_fitness_class("ReturnDD") is ReturnDD

        instance = PortfolioMasterFitnessCatalog.create_fitness("NetProfit")
        assert isinstance(instance, NetProfit)

        with pytest.raises(
            ValueError,
            match=r"^Unknown portfolio master fitness metric: NonExistent$",
        ):
            PortfolioMasterFitnessCatalog.get_fitness_class("NonExistent")

    def test_unknown_metric(self) -> None:
        """Assert unknown metric raises ValueError."""
        with pytest.raises(
            ValueError,
            match=r"^Unknown portfolio master fitness metric: UnknownMetric$",
        ):
            PortfolioMasterFitnessCatalog.get_descriptor("UnknownMetric")

        with pytest.raises(
            ValueError,
            match=r"^Unknown portfolio master fitness metric: UnknownMetric$",
        ):
            PortfolioMasterFitnessCatalog.compute("UnknownMetric", {})

    def test_compute_dispatch(self) -> None:
        """Assert compute delegates to individual metric selectors."""
        stats = {
            "NetProfit": 1200.0,
            "StagnationPct": 15.0,
            "ReturnDDRatio": 4.5,
        }
        assert PortfolioMasterFitnessCatalog.compute("NetProfit", stats) == 1200.0
        assert PortfolioMasterFitnessCatalog.compute("PctStagnation", stats) == 15.0
        assert PortfolioMasterFitnessCatalog.compute("ReturnDD", stats) == 4.5

    def test_print_value_dispatch(self) -> None:
        """Assert print_value formats values through metric selectors."""
        assert (
            PortfolioMasterFitnessCatalog.print_value("NetProfit", 1200.0)
            == "$1,200.00"
        )
        assert (
            PortfolioMasterFitnessCatalog.print_value("PctStagnation", 15.0) == "15.00%"
        )
        assert PortfolioMasterFitnessCatalog.print_value("ReturnDD", 4.5) == "$4.50"
