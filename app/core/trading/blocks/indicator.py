"""Foundational single-class BaseIndicator contract."""

from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar

from pydantic import ConfigDict

from app.core.trading.blocks.base import BaseBlock
from app.core.trading.blocks.metadata import BlockSpec
from app.core.trading.blocks.series import BarData, IndicatorSeries


class BaseIndicator(BaseBlock):
    """Abstract base class for all canonical single-class quantitative indicators.

    Parameters are declared as validated Pydantic fields on the class.
    Indicator metadata is declared via `spec: ClassVar[BlockSpec]`.
    Calculation is batch-first via `calculate(bars)`.
    """

    spec: ClassVar[BlockSpec]
    model_config = ConfigDict(strict=True, allow_inf_nan=False)

    def required_history(self) -> int:
        """Return minimum history bars needed before first valid output."""
        return getattr(self.spec, "required_history_lookback", 1)

    def required_inputs(self) -> tuple[str, ...]:
        """Resolve market dependencies for this validated parameter selection."""
        return self.spec.required_market_inputs

    @abstractmethod
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Execute batch indicator calculation over historical bars.

        Args:
            bars: Shared calculation context providing OHLCV price series.

        Returns:
            Dictionary of named output series aligned 1-to-1 with input rows.
        """

    def supports_incremental(self) -> bool:
        """Return whether indicator supports streaming bar updates."""
        return getattr(self.spec, "supports_incremental", False)


__all__ = ["BaseIndicator"]
