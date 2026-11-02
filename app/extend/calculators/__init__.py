"""Shared batch and streaming calculations for indicators and trading execution.

Description:
    Root package for StrategyQuant-faithful incremental rolling window
    calculators and high-performance NumPy batch kernels.
Purpose:
    FEAT-CALCULATORS: Stateful streaming window calculators and batch kernels.
Key Capabilities:
    - FR-CALC-EXPORTS: Canonical calculator exports and rolling algorithms.
Python API Usage:
    from app.extend.calculators import (
        AverageCalculator,
        HighestCalculator,
        LowestCalculator,
        RSICalculator,
        StdDevCalculator,
        SumCalculator,
    )
CLI Usage:
    uv run pytest tests/extend/calculators/test_calculators.py --no-cov
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
from app.extend.calculators.highest import (
    HighestCalculator,
    rolling_highest,
    time_window_highest,
)
from app.extend.calculators.lowest import (
    LowestCalculator,
    rolling_lowest,
    time_window_lowest,
)
from app.extend.calculators.rsi import RSICalculator, rsi_kernel
from app.extend.calculators.std_dev import (
    StdDevCalculator,
    centered_deviation,
    std_dev_kernel,
)
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
    "centered_deviation",
    "ema_kernel",
    "lwma_kernel",
    "rolling_highest",
    "rolling_lowest",
    "rsi_kernel",
    "sma_kernel",
    "smma_kernel",
    "std_dev_kernel",
    "tema_kernel",
    "time_window_highest",
    "time_window_lowest",
]
