"""Shared batch and streaming calculations for indicators and trading execution.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
"""

from __future__ import annotations

from app.extend.calculators.average import (
    AverageCalculator,
    AverageType,
    ema_kernel,
    lwma_kernel,
    sma_kernel,
    smma_kernel,
    tema_kernel,
)
from app.extend.calculators.base import AbstractCalculator, CalculatorError
from app.extend.calculators.extrema import HighestCalculator, LowestCalculator
from app.extend.calculators.rsi import RSICalculator, rsi_kernel
from app.extend.calculators.std_dev import StdDevCalculator
from app.extend.calculators.sum import SumCalculator

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
    "ema_kernel",
    "lwma_kernel",
    "rsi_kernel",
    "sma_kernel",
    "smma_kernel",
    "tema_kernel",
]
