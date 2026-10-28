"""Backward-compatible facades and containers for price building blocks."""

from __future__ import annotations

from typing import Any

from app.host.logging import get_logger
from app.include.blocks.price._common import (
    BarPrice,
    MTFPrice,
    QuotePrice,
    SessionPrice,
)
from app.include.blocks.price.ask import ask
from app.include.blocks.price.bid import bid
from app.include.blocks.price.close import bar_close
from app.include.blocks.price.close_d import close_d
from app.include.blocks.price.close_m import close_m
from app.include.blocks.price.close_w import close_w
from app.include.blocks.price.heiken_ashi_close import heiken_ashi_close
from app.include.blocks.price.heiken_ashi_high import heiken_ashi_high
from app.include.blocks.price.heiken_ashi_low import heiken_ashi_low
from app.include.blocks.price.heiken_ashi_open import heiken_ashi_open
from app.include.blocks.price.high import bar_high
from app.include.blocks.price.high_d import high_d
from app.include.blocks.price.high_m import high_m
from app.include.blocks.price.high_w import high_w
from app.include.blocks.price.low import bar_low
from app.include.blocks.price.low_d import low_d
from app.include.blocks.price.low_m import low_m
from app.include.blocks.price.low_w import low_w
from app.include.blocks.price.open import bar_open
from app.include.blocks.price.open_d import open_d
from app.include.blocks.price.open_m import open_m
from app.include.blocks.price.open_w import open_w
from app.include.blocks.price.session_close import session_close
from app.include.blocks.price.session_high import session_high
from app.include.blocks.price.session_low import session_low
from app.include.blocks.price.session_open import session_open
from app.include.blocks.price.spread import spread
from app.include.blocks.price.spread_in_pips import spread_in_pips
from app.include.blocks.price.volume import bar_volume

logger = get_logger(__name__)

__all__ = [
    "BarPrice",
    "MTFPrice",
    "Price",
    "QuotePrice",
    "SessionPrice",
]


class Price:
    """Unified convenience facade for price evaluations across charts and timeframes."""

    @staticmethod
    def open(chart: Any, shift: int = 0) -> float:
        """Get bar Open price."""
        return bar_open(chart, shift=shift)

    @staticmethod
    def high(chart: Any, shift: int = 0) -> float:
        """Get bar High price."""
        return bar_high(chart, shift=shift)

    @staticmethod
    def low(chart: Any, shift: int = 0) -> float:
        """Get bar Low price."""
        return bar_low(chart, shift=shift)

    @staticmethod
    def close(chart: Any, shift: int = 0) -> float:
        """Get bar Close price."""
        return bar_close(chart, shift=shift)

    @staticmethod
    def volume(chart: Any, shift: int = 0) -> float:
        """Get bar Volume."""
        return bar_volume(chart, shift=shift)

    @staticmethod
    def ask(chart: Any, shift: int = 0) -> float:
        """Get Ask price."""
        return ask(chart, shift=shift)

    @staticmethod
    def bid(chart: Any, shift: int = 0) -> float:
        """Get Bid price."""
        return bid(chart, shift=shift)

    @staticmethod
    def spread(chart: Any, shift: int = 0) -> float:
        """Get raw spread in points."""
        return spread(chart, shift=shift)

    @staticmethod
    def spread_in_pips(
        chart: Any, shift: int = 0, pip_size: float | None = None
    ) -> float:
        """Get spread in pips."""
        return spread_in_pips(chart, shift=shift, pip_size=pip_size)

    @staticmethod
    def open_d(chart: Any, shift: int = 0) -> float:
        """Get Daily Open price."""
        return open_d(chart, shift=shift)

    @staticmethod
    def high_d(chart: Any, shift: int = 0) -> float:
        """Get Daily High price."""
        return high_d(chart, shift=shift)

    @staticmethod
    def low_d(chart: Any, shift: int = 0) -> float:
        """Get Daily Low price."""
        return low_d(chart, shift=shift)

    @staticmethod
    def close_d(chart: Any, shift: int = 0) -> float:
        """Get Daily Close price."""
        return close_d(chart, shift=shift)

    @staticmethod
    def open_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly Open price."""
        return open_w(chart, shift=shift)

    @staticmethod
    def high_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly High price."""
        return high_w(chart, shift=shift)

    @staticmethod
    def low_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly Low price."""
        return low_w(chart, shift=shift)

    @staticmethod
    def close_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly Close price."""
        return close_w(chart, shift=shift)

    @staticmethod
    def open_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly Open price."""
        return open_m(chart, shift=shift)

    @staticmethod
    def high_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly High price."""
        return high_m(chart, shift=shift)

    @staticmethod
    def low_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly Low price."""
        return low_m(chart, shift=shift)

    @staticmethod
    def close_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly Close price."""
        return close_m(chart, shift=shift)

    @staticmethod
    def session_open(
        chart: Any,
        start_hours: int = 8,
        start_minutes: int = 30,
        shift: int = 0,
    ) -> float:
        """Get Session Open price."""
        return session_open(
            chart, start_hours=start_hours, start_minutes=start_minutes, shift=shift
        )

    @staticmethod
    def session_high(
        chart: Any,
        start_hours: int = 8,
        start_minutes: int = 30,
        *,
        end_hours: int = 15,
        end_minutes: int = 15,
        shift: int = 0,
    ) -> float:
        """Get Session High price."""
        return session_high(
            chart,
            start_hours=start_hours,
            start_minutes=start_minutes,
            end_hours=end_hours,
            end_minutes=end_minutes,
            shift=shift,
        )

    @staticmethod
    def session_low(
        chart: Any,
        start_hours: int = 8,
        start_minutes: int = 30,
        *,
        end_hours: int = 15,
        end_minutes: int = 15,
        shift: int = 0,
    ) -> float:
        """Get Session Low price."""
        return session_low(
            chart,
            start_hours=start_hours,
            start_minutes=start_minutes,
            end_hours=end_hours,
            end_minutes=end_minutes,
            shift=shift,
        )

    @staticmethod
    def session_close(
        chart: Any,
        end_hours: int = 15,
        end_minutes: int = 15,
        shift: int = 0,
    ) -> float:
        """Get Session Close price."""
        return session_close(
            chart, end_hours=end_hours, end_minutes=end_minutes, shift=shift
        )

    @staticmethod
    def heiken_ashi_open(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi Open price."""
        return heiken_ashi_open(chart, shift=shift)

    @staticmethod
    def heiken_ashi_high(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi High price."""
        return heiken_ashi_high(chart, shift=shift)

    @staticmethod
    def heiken_ashi_low(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi Low price."""
        return heiken_ashi_low(chart, shift=shift)

    @staticmethod
    def heiken_ashi_close(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi Close price."""
        return heiken_ashi_close(chart, shift=shift)
