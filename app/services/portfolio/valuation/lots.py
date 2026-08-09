"""Explicit lot-matching helpers."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal


def cost_basis(lots: Sequence[tuple[Decimal, Decimal]], method: str) -> Decimal:
    """Return FIFO or weighted-average cost basis for complete lots.

    Raises:
        ValueError: If the method is unsupported.
    """
    if method not in {"fifo", "weighted_average", "venue_netting"}:
        raise ValueError("unsupported lot matching method")
    quantity = sum((lot[0] for lot in lots), Decimal(0))
    return (
        Decimal(0)
        if quantity == 0
        else sum((q * p for q, p in lots), Decimal(0)) / quantity
    )


__all__ = ("cost_basis",)
