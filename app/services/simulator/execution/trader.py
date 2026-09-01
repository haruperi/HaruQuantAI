"""Simulation-scoped facade implementing Trading's injected async sim port."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from app.composition.logging import get_logger
from app.services.simulator.errors import (
    SimulationError,
    async_operation_guard,
    operation_guard,
    unwrap_simulation_response,
)

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.simulator.execution.engine import EventDrivenExecutionEngine

    ExecutionReceipt = Any
    OrderIntent = Any


class SimTrader:
    """Explicit per-run simulated order and state facade."""

    def __init__(self, engine: EventDrivenExecutionEngine) -> None:
        """Bind the facade to exactly one active simulation engine.

        Args:
            engine: Isolated engine for one run.
        """
        logger.info("Binding SimTrader to one execution engine")
        self._engine = engine

    @async_operation_guard(
        operation="simulation.execution.sim_trader.submit_order",
        risk_level="medium",
        read_only=False,
    )
    async def submit_order(self, intent: OrderIntent) -> ExecutionReceipt:
        """Submit a Trading-owned sim intent through the injected async port.

        The route and the Risk-approved volume are verified here, before the
        engine is reached, so no non-`sim` intent and no re-sized order can
        mutate simulated state.

        Args:
            intent: Approved Trading order intent.

        Returns:
            Immediate immutable acceptance receipt.

        Raises:
            SimulationError: `SIM_INVALID_CONFIG` for a non-`sim` route,
                `SIM_INVALID_VOLUME` when the approved volume was altered, or a
                matching or accounting code raised by the engine.
        """
        logger.info("Submitting Trading intent through SimTrader")
        if str(intent.route) != "sim":
            raise SimulationError(
                "SIM_INVALID_CONFIG", "Only sim-route intents are accepted"
            )
        if intent.approved_volume != intent.risk_approved_volume:
            raise SimulationError(
                "SIM_INVALID_VOLUME", "Approved volume was altered after Risk approval"
            )
        return unwrap_simulation_response(
            self._engine.submit_order(intent),
            operation="simulation.execution.sim_trader.submit_order",
        )

    @operation_guard(
        operation="simulation.execution.sim_trader.close_position",
        risk_level="medium",
        read_only=False,
    )
    def close_position(
        self, position_id: str, quantity: Decimal
    ) -> Mapping[str, object]:
        """Close an existing simulated position.

        Args:
            position_id: Existing position identity.
            quantity: Approved closing quantity.

        Returns:
            Immutable close evidence.

        Raises:
            SimulationError: `SIM_POSITION_NOT_FOUND` when the position is
                unknown, or `SIM_INVALID_VOLUME` for an invalid quantity.
        """
        logger.info("Closing position through SimTrader")
        return unwrap_simulation_response(
            self._engine.close_position(position_id, quantity),
            operation="simulation.execution.sim_trader.close_position",
        )

    @operation_guard(
        operation="simulation.execution.sim_trader.cancel_pending_order",
        risk_level="medium",
        read_only=False,
    )
    def cancel_pending_order(self, client_order_id: str) -> ExecutionReceipt:
        """Cancel one resting simulated order.

        Args:
            client_order_id: Trading-owned resting order identity.

        Returns:
            Trading-owned cancelled receipt carrying no fill.

        Raises:
            SimulationError: `SIM_ORDER_NOT_FOUND` when no such order rests.
        """
        logger.info("Cancelling pending order through SimTrader")
        return unwrap_simulation_response(
            self._engine.cancel_pending_order(client_order_id),
            operation="simulation.execution.sim_trader.cancel_pending_order",
        )

    @operation_guard(
        operation="simulation.execution.sim_trader.modify_pending_order",
        risk_level="medium",
        read_only=False,
    )
    def modify_pending_order(
        self,
        client_order_id: str,
        *,
        price: Decimal | None = None,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
    ) -> ExecutionReceipt:
        """Revise the levels of one resting simulated order.

        Args:
            client_order_id: Trading-owned resting order identity.
            price: Replacement limit or stop trigger price.
            stop_loss: Replacement protective stop level.
            take_profit: Replacement protective target level.

        Returns:
            Trading-owned accepted receipt carrying no fill.

        Raises:
            SimulationError: `SIM_ORDER_NOT_FOUND` when no such order rests, or
                `SIM_INVALID_CONFIG` when no level was supplied.
        """
        logger.info("Modifying pending order through SimTrader")
        return unwrap_simulation_response(
            self._engine.modify_pending_order(
                client_order_id,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
            ),
            operation="simulation.execution.sim_trader.modify_pending_order",
        )

    @operation_guard(
        operation="simulation.execution.sim_trader.snapshot",
        risk_level="medium",
        read_only=True,
    )
    def snapshot(self) -> Mapping[str, object]:
        """Return immutable read-only simulated state.

        Returns:
            Engine-owned immutable projection.

        Raises:
            SimulationError: `SIM_ACCOUNT_INVARIANT_BROKEN` when account state
                cannot be verified.
        """
        logger.debug("Reading state through SimTrader")
        return unwrap_simulation_response(
            self._engine.snapshot(),
            operation="simulation.execution.sim_trader.snapshot",
        )


__all__ = ["SimTrader"]
