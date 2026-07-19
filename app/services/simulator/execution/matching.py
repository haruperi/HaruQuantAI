"""Pure deterministic order triggers, gaps, liquidity, and fill policy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict

from app.services.simulator.errors import SimulationError
from app.services.simulator.execution.pricing import ExecutionProfile, price_order
from app.utils import logger

if TYPE_CHECKING:
    from app.services.simulator.timeline import Tick
    from app.services.trading import OrderIntent

SUPPORTED_FILL_POLICIES = ("FOK", "IOC")
SAME_TICK_PRIORITY = ("STOP_LOSS", "TAKE_PROFIT", "PENDING_ACTIVATION")
_EXPECTED_PRIORITY_COUNT = len(SAME_TICK_PRIORITY)


class MatchResult(BaseModel):
    """Immutable outcome of matching one intent against one tick."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["pending", "filled", "partial", "cancelled"]
    requested_quantity: Decimal
    filled_quantity: Decimal
    cancelled_quantity: Decimal
    execution_price: Decimal | None
    stop_limit_armed: bool


def _resolve_same_tick_priority(detected: Sequence[str]) -> str | None:
    """Resolve which detected same-tick condition takes precedence.

    Args:
        detected: Conditions observed on the current tick.

    Returns:
        The winning condition, or ``None`` when nothing was detected.

    Raises:
        SimulationError: If a detected condition has no declared precedence.
    """
    logger.debug("Resolving Simulation same-tick event priority")
    if len(set(SAME_TICK_PRIORITY)) != _EXPECTED_PRIORITY_COUNT:
        raise SimulationError(
            "SIM_EVENT_PRIORITY_AMBIGUOUS", "Same-tick event priority is ambiguous"
        )
    unknown = tuple(item for item in detected if item not in SAME_TICK_PRIORITY)
    if unknown:
        raise SimulationError(
            "SIM_EVENT_PRIORITY_AMBIGUOUS",
            "A detected same-tick condition has no declared precedence",
        )
    for candidate in SAME_TICK_PRIORITY:
        if candidate in detected:
            return candidate
    return None


def evaluate_protective_exit(
    position: Mapping[str, object],
    tick: Tick,
) -> str | None:
    """Resolve the protective exit of one open position on the current tick.

    A long position exits on the bid and a short position exits on the ask, so
    the same side that would close the position decides whether its stop or
    target was crossed. When both are crossed on one tick the winner is taken
    from ``SAME_TICK_PRIORITY``, which places ``STOP_LOSS`` ahead of
    ``TAKE_PROFIT``.

    Args:
        position: Open simulated position carrying side, stop, and target.
        tick: Current canonical tick.

    Returns:
        ``"STOP_LOSS"``, ``"TAKE_PROFIT"``, or ``None`` when neither triggers.

    Raises:
        SimulationError: If a detected condition has no declared precedence.
    """
    logger.debug("Evaluating Simulation protective exit")
    side = str(position["side"])
    exit_price = tick.bid if side == "BUY" else tick.ask
    stop_loss = position.get("stop_loss")
    take_profit = position.get("take_profit")
    detected: list[str] = []
    if isinstance(stop_loss, Decimal):
        crossed = exit_price <= stop_loss if side == "BUY" else exit_price >= stop_loss
        if crossed:
            detected.append("STOP_LOSS")
    if isinstance(take_profit, Decimal):
        crossed = (
            exit_price >= take_profit if side == "BUY" else exit_price <= take_profit
        )
        if crossed:
            detected.append("TAKE_PROFIT")
    return _resolve_same_tick_priority(detected)


def _triggered(intent: OrderIntent, tick: Tick, armed: bool) -> tuple[bool, bool]:
    """Evaluate the exact approved order trigger.

    Args:
        intent: Trading-owned order intent.
        tick: Current canonical tick.
        armed: Prior stop-limit activation state.

    Returns:
        Triggered and updated-armed flags.

    Raises:
        SimulationError: If required typed order price evidence is absent.
    """
    logger.debug("Evaluating Simulation order trigger")
    if intent.order_type == "MARKET":
        return True, armed
    side_price = tick.ask if intent.side == "BUY" else tick.bid
    if intent.order_type == "LIMIT":
        if intent.price is None:
            raise SimulationError("SIM_INVALID_CONFIG", "Limit price is missing")
        return (
            side_price <= intent.price
            if intent.side == "BUY"
            else side_price >= intent.price,
            armed,
        )
    if intent.stop_price is None:
        raise SimulationError("SIM_INVALID_CONFIG", "Stop price is missing")
    stop_hit = (
        side_price >= intent.stop_price
        if intent.side == "BUY"
        else side_price <= intent.stop_price
    )
    if intent.order_type == "STOP":
        return stop_hit, armed
    updated_armed = armed or stop_hit
    if intent.price is None:
        raise SimulationError("SIM_INVALID_CONFIG", "Stop-limit price is missing")
    limit_hit = (
        side_price <= intent.price
        if intent.side == "BUY"
        else side_price >= intent.price
    )
    return updated_armed and limit_hit, updated_armed


def _available_quantity(
    intent: OrderIntent,
    tick: Tick,
    profile: ExecutionProfile,
) -> Decimal:
    """Resolve fillable quantity from explicit liquidity evidence.

    Args:
        intent: Approved order intent.
        tick: Current tick volume evidence.
        profile: Explicit liquidity policy.

    Returns:
        Available quantity in the intent unit.

    Raises:
        SimulationError: If bounded liquidity evidence is missing.
    """
    logger.debug("Resolving Simulation tick liquidity")
    if profile.liquidity_mode == "unbounded":
        return intent.approved_volume
    if tick.volume is None or tick.volume_unit != intent.quantity_unit:
        raise SimulationError(
            "SIM_LIQUIDITY_UNAVAILABLE", "Compatible tick liquidity is unavailable"
        )
    return tick.volume * profile.participation_rate


def match_order(
    intent: OrderIntent,
    tick: Tick,
    profile: ExecutionProfile,
    *,
    stop_limit_armed: bool = False,
) -> MatchResult:
    """Match one approved order under deterministic trigger and fill rules.

    Args:
        intent: Trading-owned sim-route intent.
        tick: Current canonical tick.
        profile: Explicit execution profile.
        stop_limit_armed: Prior stop-limit activation state.

    Returns:
        Immutable match outcome.

    Raises:
        SimulationError: If policy, session, price, gap, or liquidity fails.
    """
    logger.info("Matching Simulation order %s", intent.client_order_id)
    _resolve_same_tick_priority(())
    policy = intent.time_in_force
    if policy not in SUPPORTED_FILL_POLICIES:
        raise SimulationError(
            "SIM_UNSUPPORTED_FILL_POLICY", "Fill policy is unsupported"
        )
    triggered, armed = _triggered(intent, tick, stop_limit_armed)
    if not triggered:
        return MatchResult(
            status="pending",
            requested_quantity=intent.approved_volume,
            filled_quantity=Decimal(0),
            cancelled_quantity=Decimal(0),
            execution_price=None,
            stop_limit_armed=armed,
        )
    execution_price = price_order(intent, tick, profile)
    trigger_price = (
        intent.stop_price if intent.order_type in {"STOP", "STOP_LIMIT"} else None
    )
    if trigger_price is not None:
        gap_points = abs(execution_price - trigger_price) / profile.point_value
        if gap_points > profile.maximum_gap_points:
            raise SimulationError(
                "SIM_GAP_UNCROSSABLE", "Trigger gap exceeds approved maximum"
            )
    available = min(intent.approved_volume, _available_quantity(intent, tick, profile))
    if policy == "FOK" and available < intent.approved_volume:
        return MatchResult(
            status="cancelled",
            requested_quantity=intent.approved_volume,
            filled_quantity=Decimal(0),
            cancelled_quantity=intent.approved_volume,
            execution_price=None,
            stop_limit_armed=armed,
        )
    filled = available
    cancelled = intent.approved_volume - filled
    status: Literal["filled", "partial", "cancelled"]
    if filled == intent.approved_volume:
        status = "filled"
    elif filled > 0:
        status = "partial"
    else:
        status = "cancelled"
    return MatchResult(
        status=status,
        requested_quantity=intent.approved_volume,
        filled_quantity=filled,
        cancelled_quantity=cancelled,
        execution_price=execution_price if filled > 0 else None,
        stop_limit_armed=armed,
    )


__all__ = [
    "SAME_TICK_PRIORITY",
    "SUPPORTED_FILL_POLICIES",
    "MatchResult",
    "evaluate_protective_exit",
    "match_order",
]
