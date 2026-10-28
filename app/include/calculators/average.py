"""Moving average streaming calculators (SMA, EMA, SMMA, LWMA).

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-AVERAGE: Moving average algorithms with drift correction and intra-bar support.
"""

from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, override

from app.include.calculators.base import AbstractCalculator, CalculatorError


class AverageType(IntEnum):
    """Moving average type selector matching donor numeric identifier mapping."""

    SMA = 0
    EMA = 1
    SMMA = 2
    LWMA = 3


class AverageCalculator(AbstractCalculator):
    """Streaming moving average calculator for SMA, EMA, SMMA, and LWMA."""

    SMA: ClassVar[int] = 0
    EMA: ClassVar[int] = 1
    SMMA: ClassVar[int] = 2
    LWMA: ClassVar[int] = 3

    def __init__(
        self,
        ma_type: int | AverageType,
        period: int,
        average_precision: int = 0,
    ) -> None:
        """Initialize the moving average calculator.

        Args:
            ma_type: Average algorithm (0=SMA, 1=EMA, 2=SMMA, 3=LWMA).
            period: Window length in bars.
            average_precision: Periodic recalculation threshold percentage to
                mitigate accumulation drift in recursive SMA updates. Clamped >= 0.

        Raises:
            CalculatorError: If ma_type is outside [0, 3].
        """
        super().__init__(period)

        try:
            self.ma_type: AverageType = AverageType(int(ma_type))
        except ValueError as err:
            raise CalculatorError(
                f"Invalid MA type used: {ma_type}. Must be in range 0-3."
            ) from err

        self.average_precision: int = max(0, int(average_precision))
        self.last_value: float = 0.0
        self.current_value: float = 0.0
        self.nb_bar_last_reset: int = 0

    @override
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        """Execute moving average computation step."""
        if not is_same_bar:
            self.last_value = self.current_value

        if self.ma_type == AverageType.SMA:
            self._calculate_sma(self.current_bar, new_value)
        elif self.ma_type == AverageType.EMA:
            self._calculate_ema(self.current_bar, new_value)
        elif self.ma_type == AverageType.SMMA:
            self._calculate_smma(self.current_bar, new_value)
        elif self.ma_type == AverageType.LWMA:
            self._calculate_lwma(self.current_bar, new_value)

    def _calculate_sma(self, current_bar: int, new_value: float) -> None:
        """Compute simple moving average with optional periodic drift reset."""
        if current_bar == 0:
            self.current_value = new_value
            return

        reset_threshold = (self.period * self.average_precision) // 100
        should_use_recursive = (
            self.average_precision == 0 or self.nb_bar_last_reset < reset_threshold
        )

        if should_use_recursive:
            effective_bars = min(current_bar, self.period)
            running_sum = self.last_value * effective_bars

            if current_bar >= self.period:
                self.current_value = (
                    running_sum + new_value - self.old_buffer_value
                ) / effective_bars
            else:
                self.current_value = (running_sum + new_value) / (effective_bars + 1)

            if self.average_precision > 0:
                self.nb_bar_last_reset += 1
        else:
            self.current_value = self.average_buffer_get()
            self.nb_bar_last_reset = 0

    def _calculate_ema(self, current_bar: int, new_value: float) -> None:
        """Compute exponential moving average using 2 / (1 + Period) smoothing."""
        if current_bar == 0:
            self.current_value = new_value
        else:
            multiplier = 2.0 / (1.0 + self.period)
            self.current_value = (
                new_value * multiplier + (1.0 - multiplier) * self.last_value
            )

    def _calculate_smma(self, current_bar: int, new_value: float) -> None:
        """Compute smoothed moving average (Wilder's smoothing)."""
        if current_bar == 1:
            self.current_value = new_value
        else:
            self.current_value = (
                self.last_value * (self.period - 1) + new_value
            ) / self.period

    def _calculate_lwma(self, current_bar: int, new_value: float) -> None:
        """Compute linear weighted moving average."""
        max_bars = min(self.period, current_bar)
        if max_bars <= 0:
            self.current_value = new_value
            return

        multiplier = self.period
        divider = 0
        weighted_sum = 0.0

        for a in range(max_bars):
            divider += multiplier
            weighted_sum += self.buffer_get(a) * multiplier
            multiplier -= 1

        self.current_value = weighted_sum / divider if divider != 0 else new_value

    @override
    def get_value(self) -> float:
        """Return the current computed moving average value."""
        return self.current_value
