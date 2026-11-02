"""Session OHLC calculator matching StrategyQuant X SessionOHLCCalculator logic.

Description:
    Implements StrategyQuant-faithful session OHLC calculation engine
    for extracting intra-session Open, High, Low, and Close price points.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-SESSION-CALCULATOR: Intra-session OHLC aggregation and indexing.
Python API Usage:
    from app.extend.blocks.price.session_ohlc_calculator import (
        CLOSE,
        HIGH,
        LOW,
        OPEN,
        SessionOHLCCalculator,
    )
    calc = SessionOHLCCalculator(output_type=OPEN, start_hours=8, chart=chart)
    val = calc.get()
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.price._common import SessionPrice

logger = get_logger(__name__)

OPEN: int = 1
HIGH: int = 2
LOW: int = 3
CLOSE: int = 4

__all__ = ["CLOSE", "HIGH", "LOW", "OPEN", "SessionOHLCCalculator"]


class SessionOHLCCalculator:
    """Incremental session OHLC calculator."""

    OPEN: int = OPEN
    HIGH: int = HIGH
    LOW: int = LOW
    CLOSE: int = CLOSE

    def __init__(
        self,
        output_type: int = OPEN,
        start_hours: int = 8,
        start_minutes: int = 30,
        *,
        end_hours: int = 15,
        end_minutes: int = 15,
        days_shift: int = 0,
        chart: Any = None,
    ) -> None:
        """Initialize calculator with session window and target price type."""
        self.output_type = output_type
        self.start_hours = start_hours
        self.start_minutes = start_minutes
        self.end_hours = end_hours
        self.end_minutes = end_minutes
        self.days_shift = days_shift
        self.chart = chart
        self._session_price: SessionPrice | None = None

        if isinstance(chart, SessionPrice):
            self._session_price = chart
        elif (
            chart is not None
            and hasattr(chart, "prices")
            and hasattr(chart, "timestamps")
        ):
            # BarData context
            self._session_price = SessionPrice(
                timestamps=chart.timestamps,
                open_data=chart.open,
                high_data=chart.high,
                low_data=chart.low,
                close_data=chart.close,
                start_hour=start_hours,
                start_minute=start_minutes,
                end_hour=end_hours,
                end_minute=end_minutes,
            )

        logger.debug(
            "FR-PRICE-SESSION-CALCULATOR: Init(type=%d, start=%02d:%02d, "
            "end=%02d:%02d, shift=%d)",
            output_type,
            start_hours,
            start_minutes,
            end_hours,
            end_minutes,
            days_shift,
        )

    def get(self) -> float:
        """Evaluate and retrieve the target session price at specified shift."""
        if self._session_price is None:
            if isinstance(self.chart, SessionPrice):
                self._session_price = self.chart
            else:
                return 0.0

        val = 0.0
        if self.output_type == OPEN:
            val = self._session_price.open(self.days_shift)
        elif self.output_type == HIGH:
            val = self._session_price.high(self.days_shift)
        elif self.output_type == LOW:
            val = self._session_price.low(self.days_shift)
        elif self.output_type == CLOSE:
            val = self._session_price.close(self.days_shift)

        logger.debug(
            "FR-PRICE-SESSION-CALCULATOR: Get(type=%d, shift=%d) = %f",
            self.output_type,
            self.days_shift,
            val,
        )
        return val
