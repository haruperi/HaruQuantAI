"""Pure helpers shared by the bundled MQL5 strategy translations."""

from __future__ import annotations

from collections.abc import Sequence

from app.services.indicators import pips_to_price
from app.services.strategy import (
    Direction,
    MarketContext,
    PositionSnapshot,
    QuoteSnapshot,
)


def require_quote(context: MarketContext) -> QuoteSnapshot:
    """Return an executable quote or fail loudly; translations cannot invent prices."""
    if context.quote is None:
        raise ValueError("This translated MQL5 strategy requires MarketContext.quote.")
    return context.quote


def pip_value(context: MarketContext, pips: float, multiplier: float) -> float:
    """Convert an MQL-style pip input using the supplied instrument point size."""
    return pips_to_price(pips, require_quote(context).point_size, multiplier)



def by_direction(
    positions: Sequence[PositionSnapshot], direction: Direction
) -> tuple[PositionSnapshot, ...]:
    return tuple(position for position in positions if position.direction is direction)


def entry_price(position: PositionSnapshot) -> float:
    """Return the reconciled opening price required by MQL basket calculations."""
    if position.entry_price is None:
        raise ValueError(f"Position {position.position_id!r} has no entry_price.")
    return position.entry_price


def average_entry(positions: Sequence[PositionSnapshot]) -> float:
    values = [entry_price(position) for position in positions]
    if not values:
        raise ValueError("Cannot average an empty position set.")
    return sum(values) / len(values)
