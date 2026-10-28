"""Streaming rolling-window calculation kernels for indicators and trading execution.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
"""

from __future__ import annotations

from app.include.calculators.average import AverageCalculator, AverageType
from app.include.calculators.base import AbstractCalculator, CalculatorError
from app.include.calculators.extrema import HighestCalculator, LowestCalculator
from app.include.calculators.rsi import RSICalculator
from app.include.calculators.std_dev import StdDevCalculator
from app.include.calculators.sum import SumCalculator

__all__ = [
    "AbstractCalculator",
    "AverageCalculator",
    "AverageType",
    "CalculatorError",
    "HighestCalculator",
    "LowestCalculator",
    "RSICalculator",
    "StdDevCalculator",
    "SumCalculator",
]
