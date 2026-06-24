"""Simple, deterministic, bar-by-bar backtesting for bundled HaruQuant strategies."""

from app.services.data import load_ohlcv_csv, validate_bars
from app.services.simulator.engine import FeatureProvider, SimpleBacktestEngine
from app.services.simulator.models import (
    BacktestConfig,
    BacktestEvent,
    BacktestMetrics,
    BacktestResult,
    ClosedTrade,
    EquityPoint,
    FillReason,
    IntrabarConflictPolicy,
)

__all__ = [
    "BacktestConfig",
    "BacktestEvent",
    "BacktestMetrics",
    "BacktestResult",
    "ClosedTrade",
    "EquityPoint",
    "FeatureProvider",
    "FillReason",
    "IntrabarConflictPolicy",
    "SimpleBacktestEngine",
    "load_ohlcv_csv",
    "validate_bars",
]
