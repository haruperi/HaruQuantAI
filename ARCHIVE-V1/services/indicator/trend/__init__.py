"""Trend indicator tools exposed to HaruQuant agents."""

# ema.py tools
from app.services.indicator.trend.ema import ema

# sma.py tools
from app.services.indicator.trend.sma import sma

# wma.py tools
from app.services.indicator.trend.wma import wma
from app.services.utils.logger import logger

__all__ = [
    # ema.py tools
    "ema",
    # sma.py tools
    "sma",
    # wma.py tools
    "wma",
]
