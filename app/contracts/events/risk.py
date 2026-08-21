"""Risk domain event contracts."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RiskLimitBreachedEvent:
    """Emitted when a pre-trade or post-trade risk limit rule is violated.

    Attributes:
        rule_name: Identifier of the breached risk rule.
        symbol: Instrument symbol involved.
        reason: Diagnostic description of the violation.
        timestamp: Time of violation in UTC.
    """

    rule_name: str
    symbol: str
    reason: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class OrderProposalEvent:
    """Pipeline interceptor event for validating and modifying proposed orders.

    Attributes:
        symbol: Target financial instrument symbol.
        side: Order direction (BUY/SELL).
        quantity: Proposed order quantity.
        price: Optional limit price.
        is_approved: Whether the proposal is allowed to proceed.
        rejection_reason: Reason if rejected by any policy.
    """

    symbol: str
    side: str
    quantity: float
    price: float | None = None
    is_approved: bool = True
    rejection_reason: str | None = None
