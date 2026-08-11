"""Approved public trend-indicator API."""

from app.services.indicators.trend.aroon import aroon
from app.services.indicators.trend.bollinger_bands import bollinger_bands
from app.services.indicators.trend.directional import adx
from app.services.indicators.trend.ema import ema
from app.services.indicators.trend.ema_slope import ema_slope
from app.services.indicators.trend.hull_ma import hull_ma
from app.services.indicators.trend.linear_regression_trend import (
    linear_regression_trend,
)
from app.services.indicators.trend.macd import macd
from app.services.indicators.trend.sma import sma
from app.services.indicators.trend.strength import measure_trend_strength
from app.services.indicators.trend.structural_levels import project_structural_levels
from app.services.indicators.trend.supertrend import supertrend
from app.services.indicators.trend.wma import wma
from app.services.indicators.trend.zigzag import zigzag

__all__ = [
    "adx",
    "aroon",
    "bollinger_bands",
    "ema",
    "ema_slope",
    "hull_ma",
    "linear_regression_trend",
    "macd",
    "measure_trend_strength",
    "project_structural_levels",
    "sma",
    "supertrend",
    "wma",
    "zigzag",
]
