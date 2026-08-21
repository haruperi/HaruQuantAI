"""Pre-trade risk evaluation and approval capability contract."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.broker.execution import OrderRequest


class RiskVerdict(StrEnum):
    """Risk approval decision outcome."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


@dataclass(frozen=True, slots=True)
class RiskDecision:
    """Outcome of pre-trade risk evaluation.

    Attributes:
        verdict: Approval status.
        reason: Diagnostic reason for approval or rejection.
        modified_order: Adjusted order if verdict is MODIFIED.
    """

    verdict: RiskVerdict
    reason: str
    modified_order: OrderRequest | None = None


@runtime_checkable
class RiskApproval(Protocol):
    """Protocol for evaluating pre-trade risk policies."""

    async def evaluate_order(self, order: OrderRequest) -> RiskDecision:
        """Evaluate a proposed trade order against active risk rules.

        Args:
            order: Proposed order request.

        Returns:
            Risk decision and justification.
        """
        ...


RISK_APPROVAL = CapabilityKey[RiskApproval](
    name="risk.approval",
    major=1,
)
