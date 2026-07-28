"""Simulation-scoped facade implementing Trading's injected async sim port."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from app.services.simulator.errors import (
    SimulationError,
    async_operation_guard,
    operation_guard,
    unwrap_simulation_response,
)
from app.utils import get_logger

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.simulator.execution.engine import EventDrivenExecutionEngine
    from app.services.trading import ExecutionReceipt, OrderIntent


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
