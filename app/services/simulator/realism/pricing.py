"""Decimal slippage and market-impact calculations."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

from app.services.simulator.errors import SimulationError
from app.services.simulator.realism.contracts import (
    LatencyProfile,
    RealisticExecutionResult,
)


def price_realistic_execution(
    *,
    side: Literal["BUY", "SELL"],
    base_price: Decimal,
    quantity: Decimal,
    point_value: Decimal,
    price_quantum: Decimal,
    fixed_slippage_points: Decimal,
    impact_points_per_unit: Decimal,
    maximum_total_points: Decimal,
    latency: LatencyProfile,
) -> RealisticExecutionResult:
    """Apply bounded adverse slippage and linear market impact.

    Args:
        side: Order direction.
        base_price: Current venue price.
        quantity: Positive requested quantity.
        point_value: Positive value of one price point.
        price_quantum: Positive price quantization unit.
        fixed_slippage_points: Explicit non-negative slippage.
        impact_points_per_unit: Explicit non-negative linear impact coefficient.
        maximum_total_points: Hard total adverse-movement ceiling.
        latency: Validated latency profile.

    Returns:
        Deterministic realistic execution result.

    Raises:
        SimulationError: If evidence is invalid or the approved ceiling is exceeded.
    """
    values = (
        base_price,
        quantity,
        point_value,
        price_quantum,
        fixed_slippage_points,
        impact_points_per_unit,
        maximum_total_points,
    )
    if (
        any(not value.is_finite() for value in values)
        or min(base_price, quantity, point_value, price_quantum) <= 0
    ):
        raise SimulationError(
            "SIM_INVALID_PRICE", "Realism pricing evidence is invalid"
        )
    if min(fixed_slippage_points, impact_points_per_unit, maximum_total_points) < 0:
        raise SimulationError(
            "SIM_INVALID_CONFIG", "Realism settings must be non-negative"
        )
    impact = quantity * impact_points_per_unit
    total = fixed_slippage_points + impact
    if total > maximum_total_points:
        raise SimulationError(
            "SIM_SLIPPAGE_EXCEEDED", "Realism movement exceeds maximum"
        )
    adjustment = total * point_value
    execution_price = (
        base_price + adjustment if side == "BUY" else base_price - adjustment
    )
    if execution_price <= 0:
        raise SimulationError("SIM_INVALID_PRICE", "Realism produced an invalid price")
    total_latency = sum(
        (
            latency.market_ms,
            latency.client_ms,
            latency.network_ms,
            latency.broker_ms,
            latency.venue_ms,
            latency.report_ms,
            latency.processing_ms,
        ),
        Decimal(0),
    )
    return RealisticExecutionResult(
        execution_price=execution_price.quantize(
            price_quantum, rounding=ROUND_HALF_EVEN
        ),
        slippage_points=fixed_slippage_points,
        impact_points=impact,
        total_latency_ms=total_latency,
    )


__all__ = ["price_realistic_execution"]
