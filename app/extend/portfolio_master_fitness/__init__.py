"""Portfolio Master fitness extension package."""

from app.extend.portfolio_master_fitness.catalog import (
    PortfolioMasterFitnessCatalog,
    PortfolioMasterFitnessDescriptor,
)
from app.extend.portfolio_master_fitness.net_profit import NetProfit
from app.extend.portfolio_master_fitness.pct_stagnation import PctStagnation
from app.extend.portfolio_master_fitness.return_dd import ReturnDD

__all__ = [
    "NetProfit",
    "PctStagnation",
    "PortfolioMasterFitnessCatalog",
    "PortfolioMasterFitnessDescriptor",
    "ReturnDD",
]
