"""Copyable indicator layout with a simple moving-average example.

- Copy into a category folder; rename the file, class, and metadata.
- Replace the example calculation with your indicator's calculation.
- Keep the sections in this order; optional examples are commented out.
- Return named, aligned series with NaN during warmup.
- Keep generation disabled until numerical and contract checks pass.
- This runnable example appears in indicator discovery for manual use and copying.
"""

from __future__ import annotations

from typing import ClassVar, override

from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.average import sma_kernel

# Logger: use the application's logger without configuring logging here.
logger = get_logger(__name__)


class IndicatorTemplate(BaseIndicator):
    """Example moving average; copy and customize before use."""

    # Metadata: what the catalog, chart, and generator need to know.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.custom.indicator_template",
        version="1.0.0",
        name="Indicator Template (Moving Average Example)",
        description="Example arithmetic mean of closing prices over a window",
        category="custom",
        tags=("example", "moving-average"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Closing prices"),),
        outputs=(
            OutputPort("value", PortType.SERIES, "Average closing price", unit="price"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=14,  # Default setting; method below is authoritative.
        dependencies=(),  # Registered block IDs, not Python imports.
        is_generation_eligible=False,  # Enable only after qualification.
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 200, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings, with readable labels and bounds.
    period: int = Field(
        default=14,
        ge=1,
        le=200,
        title="Period",
        description="Number of bars in the moving average window",
    )

    # Only when needed: validate relationships between parameters.
    # Add imports: from typing import Self; from pydantic import model_validator
    # lower: float = Field(default=20.0, ge=0.0, le=100.0, title="Lower Level")
    # upper: float = Field(default=80.0, ge=0.0, le=100.0, title="Upper Level")
    #
    # @model_validator(mode="after")
    # def validate_levels(self) -> Self:
    #     """Reject reversed or equal levels."""
    #     if self.lower >= self.upper:
    #         raise ValueError("Lower level must be below upper level")
    #     return self
    # Add descriptions and matching search metadata when adopting these fields.

    # Required inputs: override this method for settings-dependent feeds too.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Only when needed: choose inputs from a setting (replace required_inputs).
    # Add import: from typing import Literal
    # source: Literal["close", "high"] = Field(default="close", title="Source")
    #
    # @override
    # def required_inputs(self) -> tuple[str, ...]:
    #     """Return the selected price feed."""
    #     return (self.source,)
    # In calculate: values = sma_kernel(getattr(bars, self.source), self.period)
    # Declare both selectable ports and matching source search metadata;
    # required_market_inputs represents the default source, ("close",).

    # Required history: first usable value across all declared outputs.
    @override
    def required_history(self) -> int:
        """Return bars needed for usable outputs, assuming valid input values."""
        return self.period

    # Only when needed: extra smoothing changes history (replace method above).
    # smoothing: int = Field(default=3, ge=1, le=50, title="Smoothing Period")
    #
    # @override
    # def required_history(self) -> int:
    #     """Include the second smoothing window in output warmup."""
    #     return self.period + self.smoothing - 1
    # Smooth only the valid first-stage values, preserving leading NaNs.
    # Update calculate, parameter descriptions/search metadata, and the default
    # history metadata together when adopting this example.

    # Calculation: log, check inputs, calculate, and return named series.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Calculate the example moving average without changing input data.

        Args:
            bars: Aligned market data containing closing prices.

        Returns:
            Exactly the declared 'value' output, aligned with input bars.
            The first period - 1 values are NaN; short inputs remain all NaN.

        Raises:
            ValueError: If the required closing prices are unavailable.
        """
        logger.debug(
            "FR-indicator-template-logging: calculation requested period=%d bars=%d",
            self.period,
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        # Verify known numerical results, short inputs, output names/lengths,
        # invalid settings/feeds, prefix causality, and unchanged input arrays.
        # Verify this diagnostic label, period, and bar count in focused tests.
        values = sma_kernel(bars.close, self.period)
        return {"value": IndicatorSeries(values, name="Example Moving Average")}


# Only when needed: a private helper below the class.
# Add import: import numpy as np
# def _finite_values(series: IndicatorSeries) -> bool:
#     """Return whether a computed series has no unavailable values."""
#     return bool(np.all(np.isfinite(series.values)))
# Warmup NaNs are expected: use this only on an already warmed-up slice.
# Put numerical kernels shared by multiple indicators in app/extend/calculators.

# Conditions: use shared comparisons/compositions for rising, falling, levels,
# and crossings. Do not copy those functions into each indicator module.
# Only when needed: a specialized condition can live here beside its indicator.
# Example: a three-point trough with a minimum recovery relative to the decline.
# Add import: from math import isfinite
# def _has_recovered_trough(
#     before: float, trough: float, after: float, recovery_ratio: float
# ) -> bool:
#     """Detect a trough whose recovery meets a fraction of its decline."""
#     logger.debug("FR-indicator-trough: specialized condition requested")
#     if not all(isfinite(v) for v in (before, trough, after, recovery_ratio)):
#         raise ValueError("Trough inputs must be finite")
#     if recovery_ratio <= 0.0:
#         raise ValueError("Recovery ratio must be positive")
#     decline = before - trough
#     recovery = after - trough
#     return decline > 0.0 and recovery >= decline * recovery_ratio
# Expose a specialized condition only through an explicit catalog descriptor
# with declared inputs, validated parameters, help text, and qualification tests.

# Editor templates and structure/behavior checks should follow this reference.
# This file documents the standard; it does not install those checks.

# Public exports: expose only this module's indicator class.
__all__ = ["IndicatorTemplate"]
