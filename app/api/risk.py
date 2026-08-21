"""Risk domain public capability-aware facade."""

from typing import TYPE_CHECKING

from app.contracts.risk.approval import RISK_APPROVAL, RiskDecision

if TYPE_CHECKING:
    from app.contracts.broker.execution import OrderRequest
    from app.kernel.registry import ServiceRegistry


class RiskAPI:
    """Stable facade providing risk domain operations backed by dynamic capabilities."""

    def __init__(self, registry: ServiceRegistry) -> None:
        """Initialize RiskAPI with central service registry.

        Args:
            registry: Central ServiceRegistry tracking active capability providers.
        """
        self._registry = registry

    @property
    def is_approval_available(self) -> bool:
        """Check if pre-trade risk approval capability provider is currently active.

        Returns:
            True if risk.approval@1 is active, False otherwise.
        """
        return self._registry.is_available(RISK_APPROVAL)

    async def evaluate_order(self, order: OrderRequest) -> RiskDecision:
        """Evaluate a proposed trade order against active risk rules.

        Args:
            order: Proposed order request.

        Returns:
            RiskDecision with verdict and diagnostic reason.

        Raises:
            CapabilityUnavailableError: If risk.approval@1 provider is absent.
        """
        service = self._registry.require(RISK_APPROVAL)
        return await service.evaluate_order(order)
