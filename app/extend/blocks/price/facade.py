"""Backward-compatible facades and containers for price building blocks.

Description:
    Provides an object-oriented and namespace-bound API facade over discrete
    StrategyQuant-faithful single-bar, quote, multi-timeframe, session, and
    Heiken Ashi price building blocks.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-FACADE: Centralized namespace for price evaluation across timeframes.
Python API Usage:
    from app.extend.blocks.price import Price, Prices
    close_val = Price.close(chart, shift=0)
    open_d_val = Prices.open_d(chart, shift=1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.price._common import (
    BarPrice,
    MTFPrice,
    QuotePrice,
    SessionPrice,
)
from app.extend.blocks.price.ask import ask
from app.extend.blocks.price.bid import bid
from app.extend.blocks.price.close import bar_close
from app.extend.blocks.price.close_d import close_d
from app.extend.blocks.price.close_m import close_m
from app.extend.blocks.price.close_w import close_w
from app.extend.blocks.price.heiken_ashi_close import heiken_ashi_close
from app.extend.blocks.price.heiken_ashi_high import heiken_ashi_high
from app.extend.blocks.price.heiken_ashi_low import heiken_ashi_low
from app.extend.blocks.price.heiken_ashi_open import heiken_ashi_open
from app.extend.blocks.price.high import bar_high
from app.extend.blocks.price.high_d import high_d
from app.extend.blocks.price.high_m import high_m
from app.extend.blocks.price.high_w import high_w
from app.extend.blocks.price.low import bar_low
from app.extend.blocks.price.low_d import low_d
from app.extend.blocks.price.low_m import low_m
from app.extend.blocks.price.low_w import low_w
from app.extend.blocks.price.open import bar_open
from app.extend.blocks.price.open_d import open_d
from app.extend.blocks.price.open_m import open_m
from app.extend.blocks.price.open_w import open_w
from app.extend.blocks.price.session_close import session_close
from app.extend.blocks.price.session_high import session_high
from app.extend.blocks.price.session_low import session_low
from app.extend.blocks.price.session_open import session_open
from app.extend.blocks.price.spread import spread
from app.extend.blocks.price.spread_in_pips import spread_in_pips
from app.extend.blocks.price.volume import bar_volume

logger = get_logger(__name__)

__all__ = [
    "BarPrice",
    "MTFPrice",
    "Price",
    "Prices",
    "QuotePrice",
    "SessionPrice",
]


class Price:
    """Unified convenience facade for price evaluations across charts and timeframes."""

    @staticmethod
    def open(chart: Any, shift: int = 0) -> float:
        """Get bar Open price."""
        logger.debug("FR-PRICE-FACADE: Price.open(shift=%d)", shift)
        return bar_open(chart, shift=shift)

    @staticmethod
    def high(chart: Any, shift: int = 0) -> float:
        """Get bar High price."""
        logger.debug("FR-PRICE-FACADE: Price.high(shift=%d)", shift)
        return bar_high(chart, shift=shift)

    @staticmethod
    def low(chart: Any, shift: int = 0) -> float:
        """Get bar Low price."""
        logger.debug("FR-PRICE-FACADE: Price.low(shift=%d)", shift)
        return bar_low(chart, shift=shift)

    @staticmethod
    def close(chart: Any, shift: int = 0) -> float:
        """Get bar Close price."""
        logger.debug("FR-PRICE-FACADE: Price.close(shift=%d)", shift)
        return bar_close(chart, shift=shift)

    @staticmethod
    def volume(chart: Any, shift: int = 0) -> float:
        """Get bar Volume."""
        logger.debug("FR-PRICE-FACADE: Price.volume(shift=%d)", shift)
        return bar_volume(chart, shift=shift)

    @staticmethod
    def ask(chart: Any, shift: int = 0) -> float:
        """Get Ask price."""
        logger.debug("FR-PRICE-FACADE: Price.ask(shift=%d)", shift)
        return ask(chart, shift=shift)

    @staticmethod
    def bid(chart: Any, shift: int = 0) -> float:
        """Get Bid price."""
        logger.debug("FR-PRICE-FACADE: Price.bid(shift=%d)", shift)
        return bid(chart, shift=shift)

    @staticmethod
    def spread(chart: Any, shift: int = 0) -> float:
        """Get raw spread in points."""
        logger.debug("FR-PRICE-FACADE: Price.spread(shift=%d)", shift)
        return spread(chart, shift=shift)

    @staticmethod
    def spread_in_pips(
        chart: Any, shift: int = 0, pip_size: float | None = None
    ) -> float:
        """Get spread in pips."""
        logger.debug("FR-PRICE-FACADE: Price.spread_in_pips(shift=%d)", shift)
        if pip_size is None:
            return spread_in_pips(chart, shift=shift)
        return spread_in_pips(chart, shift=shift, pip_size=pip_size)

    @staticmethod
    def open_d(chart: Any, shift: int = 0) -> float:
        """Get Daily Open price."""
        logger.debug("FR-PRICE-FACADE: Price.open_d(shift=%d)", shift)
        return open_d(chart, shift=shift)

    @staticmethod
    def high_d(chart: Any, shift: int = 0) -> float:
        """Get Daily High price."""
        logger.debug("FR-PRICE-FACADE: Price.high_d(shift=%d)", shift)
        return high_d(chart, shift=shift)

    @staticmethod
    def low_d(chart: Any, shift: int = 0) -> float:
        """Get Daily Low price."""
        logger.debug("FR-PRICE-FACADE: Price.low_d(shift=%d)", shift)
        return low_d(chart, shift=shift)

    @staticmethod
    def close_d(chart: Any, shift: int = 0) -> float:
        """Get Daily Close price."""
        logger.debug("FR-PRICE-FACADE: Price.close_d(shift=%d)", shift)
        return close_d(chart, shift=shift)

    @staticmethod
    def open_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly Open price."""
        logger.debug("FR-PRICE-FACADE: Price.open_w(shift=%d)", shift)
        return open_w(chart, shift=shift)

    @staticmethod
    def high_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly High price."""
        logger.debug("FR-PRICE-FACADE: Price.high_w(shift=%d)", shift)
        return high_w(chart, shift=shift)

    @staticmethod
    def low_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly Low price."""
        logger.debug("FR-PRICE-FACADE: Price.low_w(shift=%d)", shift)
        return low_w(chart, shift=shift)

    @staticmethod
    def close_w(chart: Any, shift: int = 0) -> float:
        """Get Weekly Close price."""
        logger.debug("FR-PRICE-FACADE: Price.close_w(shift=%d)", shift)
        return close_w(chart, shift=shift)

    @staticmethod
    def open_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly Open price."""
        logger.debug("FR-PRICE-FACADE: Price.open_m(shift=%d)", shift)
        return open_m(chart, shift=shift)

    @staticmethod
    def high_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly High price."""
        logger.debug("FR-PRICE-FACADE: Price.high_m(shift=%d)", shift)
        return high_m(chart, shift=shift)

    @staticmethod
    def low_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly Low price."""
        logger.debug("FR-PRICE-FACADE: Price.low_m(shift=%d)", shift)
        return low_m(chart, shift=shift)

    @staticmethod
    def close_m(chart: Any, shift: int = 0) -> float:
        """Get Monthly Close price."""
        logger.debug("FR-PRICE-FACADE: Price.close_m(shift=%d)", shift)
        return close_m(chart, shift=shift)

    @staticmethod
    def session_open(
        chart: Any,
        start_hours: int = 8,
        start_minutes: int = 30,
        shift: int = 0,
    ) -> float:
        """Get Session Open price."""
        logger.debug(
            "FR-PRICE-FACADE: Price.session_open(start=%02d:%02d, shift=%d)",
            start_hours,
            start_minutes,
            shift,
        )
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
        logger.debug(
            "FR-PRICE-FACADE: Price.session_high(start=%02d:%02d, end=%02d:%02d, "
            "shift=%d)",
            start_hours,
            start_minutes,
            end_hours,
            end_minutes,
            shift,
        )
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
        logger.debug(
            "FR-PRICE-FACADE: Price.session_low(start=%02d:%02d, end=%02d:%02d, "
            "shift=%d)",
            start_hours,
            start_minutes,
            end_hours,
            end_minutes,
            shift,
        )
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
        logger.debug(
            "FR-PRICE-FACADE: Price.session_close(end=%02d:%02d, shift=%d)",
            end_hours,
            end_minutes,
            shift,
        )
        return session_close(
            chart, end_hours=end_hours, end_minutes=end_minutes, shift=shift
        )

    @staticmethod
    def heiken_ashi_open(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi Open price."""
        logger.debug("FR-PRICE-FACADE: Price.heiken_ashi_open(shift=%d)", shift)
        return heiken_ashi_open(chart, shift=shift)

    @staticmethod
    def heiken_ashi_high(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi High price."""
        logger.debug("FR-PRICE-FACADE: Price.heiken_ashi_high(shift=%d)", shift)
        return heiken_ashi_high(chart, shift=shift)

    @staticmethod
    def heiken_ashi_low(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi Low price."""
        logger.debug("FR-PRICE-FACADE: Price.heiken_ashi_low(shift=%d)", shift)
        return heiken_ashi_low(chart, shift=shift)

    @staticmethod
    def heiken_ashi_close(chart: Any, shift: int = 0) -> float:
        """Get Heiken Ashi Close price."""
        logger.debug("FR-PRICE-FACADE: Price.heiken_ashi_close(shift=%d)", shift)
        return heiken_ashi_close(chart, shift=shift)


# Facade alias matching other block namespaces (e.g. Actions, Types)
Prices = Price
