"""Order scope matching, history order inspection, and price/time calculations.

Description:
    Provides domain types and pure utility functions for trade scope filtering,
    time-series bar offset calculation, pip size determination, price
    normalization, and donor-faithful order identification (OrderFunctions)
    conforming to StrategyQuant SQ.Functions.OrderFunctions snippet specifications.

Purpose:
    FEAT-FUNCTIONS: StrategyQuant donor-faithful functions and domain utilities.

Key Capabilities:
    - FR-FUNCTIONS-ORDER-FILTER: Multi-attribute matching and order identification.
    - FR-FUNCTIONS-PRICE-NORM: Tick grid alignment conforming to symbol specs.
    - FR-FUNCTIONS-BARS-SINCE: Count chart bar intervals between events.

Python API Usage:
    from app.extend.functions.order_functions import OrderFunctions, TradeFilter

CLI Usage:
    uv run pytest tests/extend/test_functions.py --no-cov
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from itertools import pairwise
from typing import Any

from app.core.data.contracts import SymbolInfo
from app.core.host.logging import get_logger
from app.core.trading.connection.contracts import OrderInfo, PositionInfo

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TradeFilter:
    """Explicit trading scope; None means any symbol/magic, direction 0 means either.

    Comments match by substring. A magic of zero matches zero exactly.
    Resolve strategy aliases such as Current before constructing this filter.
    """

    symbol: str | None
    direction: int = 0
    magic: int | None = None
    comment: str = ""
    ticket: int | None = None

    def __post_init__(self) -> None:
        """Validate the direction selector."""
        if type(self.direction) is not int or self.direction not in (-1, 0, 1):
            raise ValueError("direction must be -1, 0, or 1")

    def matches(self, item: PositionInfo | OrderInfo) -> bool:
        """Match one canonical position or working order without backend filtering."""
        kind = item.position_type if isinstance(item, PositionInfo) else item.order_type
        direction = 1 if kind in (0, 2, 4, 6) else -1
        return (
            (self.symbol is None or item.symbol == self.symbol)
            and (self.direction in (0, direction))
            and (self.magic is None or item.magic == self.magic)
            and (not self.comment or self.comment in item.comment)
            and (self.ticket is None or item.ticket == self.ticket)
        )


def aware_timestamp(value: datetime) -> float:
    """Validate an explicit evaluation timestamp and return epoch seconds."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("evaluation timestamps must include a timezone")
    return value.timestamp()


def bars_since(timestamp: float, bar_times: Sequence[datetime], as_of: datetime) -> int:
    """Count actual bar starts strictly after an event, bounded by evaluation time.

    Bars must be oldest first and cover the event. Missing history is an error.
    """
    end = aware_timestamp(as_of)
    starts = [aware_timestamp(value) for value in bar_times]
    if not starts or any(a >= b for a, b in pairwise(starts)):
        raise ValueError("bar times must be nonempty and strictly oldest first")
    if starts[-1] > end:
        raise ValueError("bar times must not extend past evaluation time")
    if timestamp > end:
        return -1
    if timestamp < starts[0]:
        raise ValueError("bar history does not cover the trade timestamp")
    count = sum(timestamp < start <= end for start in starts)
    logger.debug(
        "FR-FUNCTIONS-BARS-SINCE: Calculated %d bars since timestamp=%s as_of=%s",
        count,
        timestamp,
        as_of,
    )
    return count


def pip_size(price: float | None, tick_size: float) -> float:
    """Use an explicit pip size, falling back to the instrument tick size."""
    value = tick_size if price is None else price
    if not math.isfinite(value) or value <= 0:
        raise ValueError("pip size must be finite and positive")
    return value


def normalize_price(value: float, spec: SymbolInfo) -> float:
    """Validate a price and align it to the instrument tick grid."""
    if not math.isfinite(value) or value < 0:
        raise ValueError("prices must be finite and nonnegative")
    step = spec.price.tick_step
    if not math.isfinite(step) or step <= 0:
        raise ValueError("symbol tick step must be positive")
    grid = Decimal(str(step))
    rounded = float(round(Decimal(str(value)) / grid) * grid)
    if value > 0 and rounded <= 0:
        raise ValueError("positive price is smaller than the symbol tick step")
    logger.debug(
        "FR-FUNCTIONS-PRICE-NORM: Normalized price %s -> %s (tick_step=%s)",
        value,
        rounded,
        step,
    )
    return rounded


def _extract_strategy_name(target: Any) -> str:
    """Extract strategy name from strategy or order object."""
    val = getattr(target, "strategy_name", getattr(target, "StrategyName", ""))
    if callable(val):
        return str(val())
    fn = getattr(target, "get_strategy_name", getattr(target, "getStrategyName", None))
    if callable(fn):
        return str(fn())
    return str(val)


def _extract_symbol(order: Any) -> str:
    """Extract symbol string from order object."""
    val = getattr(order, "symbol", getattr(order, "Symbol", ""))
    if callable(val):
        return str(val())
    fn = getattr(order, "get_symbol", getattr(order, "getSymbol", None))
    if callable(fn):
        return str(fn())
    return str(val)


def _extract_direction(order: Any) -> int:
    """Extract direction int (-1, 0, 1) from order object."""
    d = getattr(order, "direction", getattr(order, "Direction", None))
    if d is not None:
        return int(d() if callable(d) else d)
    fn = getattr(order, "get_direction", getattr(order, "getDirection", None))
    if callable(fn):
        return int(fn())
    kind = getattr(order, "position_type", getattr(order, "order_type", None))
    if kind is not None:
        return 1 if kind in (0, 2, 4, 6) else -1
    return 0


def _extract_magic(order: Any) -> int:
    """Extract magic number from order object."""
    m = getattr(
        order,
        "magic",
        getattr(order, "magic_number", getattr(order, "MagicNumber", None)),
    )
    if m is not None:
        return int(m() if callable(m) else m)
    fn = getattr(order, "get_magic_number", getattr(order, "getMagicNumber", None))
    if callable(fn):
        return int(fn())
    return 0


def _extract_comment(order: Any) -> str:
    """Extract comment string from order object."""
    c = getattr(order, "comment", getattr(order, "Comment", ""))
    if callable(c):
        return str(c())
    fn = getattr(order, "get_comment", getattr(order, "getComment", None))
    if callable(fn):
        return str(fn())
    return str(c)


def _extract_current_chart_symbol(strategy: Any) -> str:
    """Extract symbol from strategy market data primary chart."""
    md = getattr(strategy, "market_data", getattr(strategy, "MarketData", None))
    if md is not None:
        chart_fn = getattr(md, "chart", getattr(md, "Chart", None))
        if callable(chart_fn):
            chart = chart_fn(0)
            return str(getattr(chart, "symbol", getattr(chart, "Symbol", "")))
    return ""


def _match_symbol(order: Any, strategy: Any, symbol: str) -> bool:
    """Return True if order symbol matches requested symbol specification."""
    if symbol == "Any":
        return True
    order_sym = _extract_symbol(order)
    if symbol == "Current":
        chart_sym = _extract_current_chart_symbol(strategy)
        return not chart_sym or order_sym == chart_sym
    return not symbol or order_sym == symbol


def _get_trader_orders(trader: Any, is_open: bool) -> Sequence[Any]:
    """Extract order sequence from trader candidate."""
    method_name = "get_open_orders" if is_open else "get_history_orders"
    fn = getattr(trader, method_name, None)
    if callable(fn):
        return list(fn(True) if is_open else fn())
    orders = getattr(trader, "open_orders" if is_open else "history_orders", None)
    if orders is not None:
        return list(orders)
    return []


class OrderFunctions:
    """Strategy order identification and lookup matching donor OrderFunctions.java."""

    @classmethod
    def identify(  # noqa: PLR0917
        cls,
        order: Any,
        strategy: Any,
        symbol: str,
        direction: int,
        magic_number: int,
        comment: str = "",
    ) -> bool:
        """Check whether order matches strategy, symbol, direction, magic, and comment.

        Args:
            order: Order candidate.
            strategy: Strategy context.
            symbol: 'Any', 'Current', or specific symbol name.
            direction: 0 for either, 1 for Long, -1 for Short.
            magic_number: 0 for any, otherwise exact magic number.
            comment: Substring filter, or empty for any.

        Returns:
            True if order meets all criteria, False otherwise.
        """
        strat_name = _extract_strategy_name(strategy)
        order_strat_name = _extract_strategy_name(order)
        if strat_name and order_strat_name and order_strat_name != strat_name:
            return False

        if not _match_symbol(order, strategy, symbol):
            return False

        if direction != 0 and _extract_direction(order) != direction:
            return False

        if magic_number != 0 and _extract_magic(order) != magic_number:
            return False

        if comment and comment not in _extract_comment(order):
            return False

        logger.debug(
            "FR-FUNCTIONS-ORDER-FILTER: order matches strategy %s (symbol=%s)",
            strat_name,
            symbol,
        )
        return True

    @classmethod
    def find_live_order(
        cls,
        strategy: Any,
        symbol: str,
        direction: int,
        magic_number: int,
        comment: str = "",
    ) -> Any | None:
        """Find first open order matching criteria in strategy trader.

        Args:
            strategy: Strategy context containing Trader.
            symbol: Target symbol ('Any', 'Current', or exact).
            direction: 0 for either, 1 for Long, -1 for Short.
            magic_number: Magic number filter (0 for any).
            comment: Comment substring filter.

        Returns:
            Matching order or None.
        """
        trader = getattr(strategy, "trader", getattr(strategy, "Trader", None))
        if trader is None:
            return None

        for order in _get_trader_orders(trader, is_open=True):
            if cls.identify(order, strategy, symbol, direction, magic_number, comment):
                return order
        return None

    @classmethod
    def find_history_order(
        cls,
        strategy: Any,
        symbol: str,
        direction: int,
        magic_number: int,
        comment: str = "",
    ) -> Any | None:
        """Find first (oldest) history order matching criteria in strategy trader.

        Args:
            strategy: Strategy context containing Trader.
            symbol: Target symbol ('Any', 'Current', or exact).
            direction: 0 for either, 1 for Long, -1 for Short.
            magic_number: Magic number filter (0 for any).
            comment: Comment substring filter.

        Returns:
            Matching order or None.
        """
        trader = getattr(strategy, "trader", getattr(strategy, "Trader", None))
        if trader is None:
            return None

        for order in _get_trader_orders(trader, is_open=False):
            if cls.identify(order, strategy, symbol, direction, magic_number, comment):
                return order
        return None

    @classmethod
    def find_last_history_order(
        cls,
        strategy: Any,
        symbol: str,
        direction: int,
        magic_number: int,
        comment: str = "",
    ) -> Any | None:
        """Find last (newest) history order matching criteria in strategy trader.

        Args:
            strategy: Strategy context containing Trader.
            symbol: Target symbol ('Any', 'Current', or exact).
            direction: 0 for either, 1 for Long, -1 for Short.
            magic_number: Magic number filter (0 for any).
            comment: Comment substring filter.

        Returns:
            Matching order or None.
        """
        trader = getattr(strategy, "trader", getattr(strategy, "Trader", None))
        if trader is None:
            return None

        for order in reversed(_get_trader_orders(trader, is_open=False)):
            if cls.identify(order, strategy, symbol, direction, magic_number, comment):
                return order
        return None


__all__ = [
    "OrderFunctions",
    "TradeFilter",
    "aware_timestamp",
    "bars_since",
    "normalize_price",
    "pip_size",
]
