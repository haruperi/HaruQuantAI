"""Shared batch and streaming calculations for indicators and trading execution.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
"""

from __future__ import annotations

from app.include.calculators.average import (
    AverageCalculator,
    AverageType,
    ema_kernel,
    lwma_kernel,
    sma_kernel,
    smma_kernel,
    tema_kernel,
)
from app.include.calculators.base import AbstractCalculator, CalculatorError
from app.include.calculators.extrema import HighestCalculator, LowestCalculator
from app.include.calculators.rsi import RSICalculator, rsi_kernel
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
    "ema_kernel",
    "lwma_kernel",
    "rsi_kernel",
    "sma_kernel",
    "smma_kernel",
    "tema_kernel",
]
