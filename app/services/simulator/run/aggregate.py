"""Exact aggregate account ledger for portfolio simulation."""

from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.services.simulator.errors import SimulationError

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.simulator.reporting import SimulationResult


class PortfolioAggregateLedger:
    """Maintain exact component attribution for one portfolio account."""

    def __init__(self, initial_balance: Decimal) -> None:
        """Initialize an empty aggregate ledger.

        Args:
            initial_balance: Exact portfolio opening balance.

        Raises:
            SimulationError: If the opening balance is invalid.
        """
        logger.info("Initializing portfolio aggregate account ledger")
        if not initial_balance.is_finite() or initial_balance <= 0:
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN",
                "Portfolio aggregate balance is invalid",
            )
        self._initial_balance = initial_balance
        self._allocated_balance = Decimal(0)
        self._net_profit = Decimal(0)
        self._components: dict[str, Decimal] = {}

    def record_component(
        self,
        component_id: str,
        allocated_balance: Decimal,
        result: SimulationResult,
    ) -> None:
        """Record one completed component in the aggregate ledger.

        Args:
            component_id: Unique portfolio component identity.
            allocated_balance: Exact opening capital allocated to the component.
            result: Completed component result.

        Raises:
            SimulationError: If identity, allocation, or accounting is invalid.
        """
        logger.info("Recording component %s in aggregate ledger", component_id)
        net_profit = result.accounting.net_profit
        if (
            component_id in self._components
            or not allocated_balance.is_finite()
            or allocated_balance <= 0
            or result.initial_balance != allocated_balance
            or not net_profit.is_finite()
        ):
            raise SimulationError(
                "SIM_AGGREGATE_UNRECONCILED",
                "Portfolio component accounting is incompatible",
            )
        self._components[component_id] = net_profit
        self._allocated_balance += allocated_balance
        self._net_profit += net_profit

    def snapshot(self, expected_component_count: int) -> MappingProxyType[str, object]:
        """Return an immutable reconciled aggregate account snapshot.

        Args:
            expected_component_count: Exact number of requested components.

        Returns:
            Immutable aggregate balance and component evidence.

        Raises:
            SimulationError: If allocation or component count does not reconcile.
        """
        logger.info("Reconciling portfolio aggregate account ledger")
        if (
            len(self._components) != expected_component_count
            or self._allocated_balance != self._initial_balance
        ):
            raise SimulationError(
                "SIM_AGGREGATE_UNRECONCILED",
                "Portfolio aggregate allocation does not reconcile",
            )
        return MappingProxyType(
            {
                "initial_balance": self._initial_balance,
                "allocated_balance": self._allocated_balance,
                "net_profit": self._net_profit,
                "equity": self._initial_balance + self._net_profit,
                "component_net_profit": MappingProxyType(dict(self._components)),
            }
        )


__all__ = ["PortfolioAggregateLedger"]
