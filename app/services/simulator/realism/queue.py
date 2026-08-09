"""Deterministic price-level queue fill model."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

from app.services.simulator.realism.contracts import QueueFillResult, QueueModel


def simulate_queue_fill(
    model: QueueModel, *, traded_volume: Decimal
) -> QueueFillResult:
    """Apply traded volume and modeled cancellations to one queue position.

    Args:
        model: Validated queue model.
        traded_volume: Finite non-negative volume at the price level.

    Returns:
        Deterministic fill projection.

    Raises:
        ValueError: If traded volume is invalid.
    """
    if not traded_volume.is_finite() or traded_volume < 0:
        raise ValueError("traded_volume must be finite and non-negative")
    cancelled_ahead = model.quantity_ahead * model.cancellation_rate
    effective_ahead = max(Decimal(0), model.quantity_ahead - cancelled_ahead)
    available = max(Decimal(0), traded_volume - effective_ahead)
    filled = min(model.order_quantity, available)
    remaining = model.order_quantity - filled
    remaining_ahead = max(Decimal(0), effective_ahead - traded_volume)
    raw_probability = (
        Decimal(1)
        if filled == model.order_quantity
        else min(Decimal(1), traded_volume / (effective_ahead + model.order_quantity))
    )
    probability = min(model.maximum_fill_probability, raw_probability).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_EVEN
    )
    return QueueFillResult(
        filled_quantity=filled,
        remaining_quantity=remaining,
        remaining_ahead=remaining_ahead,
        fill_probability=probability,
    )


__all__ = ["simulate_queue_fill"]
