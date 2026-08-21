"""Broker order execution capability contract."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


class OrderSide(StrEnum):
    """Trade order direction."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    """Trade order pricing type."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class OrderRequest:
    """Standardized broker order submission request.

    Attributes:
        symbol: Target financial instrument symbol.
        side: Order direction (BUY or SELL).
        order_type: Execution type (MARKET, LIMIT, STOP).
        quantity: Order volume / lot size.
        price: Limit or trigger price (if applicable).
        client_order_id: Unique client-side idempotency identifier.
    """

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None
    client_order_id: str | None = None


@dataclass(frozen=True, slots=True)
class OrderResult:
    """Execution receipt returned by the broker adapter.

    Attributes:
        order_id: Unique broker-assigned order ID.
        client_order_id: Client-side tracking ID.
        symbol: Traded instrument symbol.
        status: Execution status (e.g., 'FILLED', 'REJECTED', 'PENDING').
        filled_quantity: Total quantity filled.
        average_price: Average fill price.
        timestamp: Execution timestamp in UTC.
        message: Optional diagnostic or rejection message.
    """

    order_id: str
    client_order_id: str | None
    symbol: str
    status: str
    filled_quantity: float
    average_price: float
    timestamp: datetime
    message: str | None = None


@runtime_checkable
class BrokerExecution(Protocol):
    """Protocol for broker order routing and execution."""

    async def submit_order(self, request: OrderRequest) -> OrderResult:
        """Submit a trade order to the broker.

        Args:
            request: Order submission parameters.

        Returns:
            Execution result details.
        """
        ...

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an active open order.

        Args:
            order_id: Target broker order identifier.

        Returns:
            True if cancellation succeeded, False otherwise.
        """
        ...


BROKER_EXECUTION = CapabilityKey[BrokerExecution](
    name="broker.execution",
    major=1,
)
