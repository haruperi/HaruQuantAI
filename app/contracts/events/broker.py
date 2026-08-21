"""Broker domain event contracts."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OrderFilledEvent:
    """Emitted when a broker fills a submitted order.

    Attributes:
        order_id: Unique broker order identifier.
        symbol: Traded instrument symbol.
        quantity: Quantity filled.
        price: Average execution price.
        timestamp: Time of fill in UTC.
    """

    order_id: str
    symbol: str
    quantity: float
    price: float
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent:
    """Emitted when an order is cancelled or expired.

    Attributes:
        order_id: Broker order identifier.
        symbol: Traded instrument symbol.
        reason: Optional cancellation reason.
        timestamp: Time of cancellation in UTC.
    """

    order_id: str
    symbol: str
    reason: str | None
    timestamp: datetime
