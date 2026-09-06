# ruff: noqa: N801, N816, RUF022, RUF100  # Exact public names/order.
"""Generated MQL5-based contract vocabulary. DO NOT EDIT."""

from __future__ import annotations

from enum import IntEnum
from typing import Final


class ENUM_BOOK_TYPE(IntEnum):
    """Defines the identifier set for book type."""

    BOOK_TYPE_SELL = 1
    BOOK_TYPE_BUY = 2
    BOOK_TYPE_SELL_MARKET = 3
    BOOK_TYPE_BUY_MARKET = 4


BOOK_TYPE_SELL: Final = ENUM_BOOK_TYPE.BOOK_TYPE_SELL
BOOK_TYPE_BUY: Final = ENUM_BOOK_TYPE.BOOK_TYPE_BUY
BOOK_TYPE_SELL_MARKET: Final = ENUM_BOOK_TYPE.BOOK_TYPE_SELL_MARKET
BOOK_TYPE_BUY_MARKET: Final = ENUM_BOOK_TYPE.BOOK_TYPE_BUY_MARKET

__all__ = [
    "BOOK_TYPE_BUY",
    "BOOK_TYPE_BUY_MARKET",
    "BOOK_TYPE_SELL",
    "BOOK_TYPE_SELL_MARKET",
    "ENUM_BOOK_TYPE",
]
