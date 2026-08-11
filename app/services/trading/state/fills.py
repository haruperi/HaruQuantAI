"""Deterministic fill aggregation without invented execution evidence."""

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.trading.contracts import TradingError


class _FillAggregate(BaseModel):
    """Private immutable fill aggregate."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    order_id: str
    ordered_quantity: Decimal
    filled_quantity: Decimal = Decimal(0)
    average_fill_price: Decimal | None = None
    fill_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if (
            self.ordered_quantity <= 0
            or not 0 <= self.filled_quantity <= self.ordered_quantity
        ):
            raise ValueError("fill quantities are outside the order boundary")
        if len(set(self.fill_ids)) != len(self.fill_ids):
            raise ValueError("fill identities must be unique")
        return self


def create_fill_aggregate(**values: object) -> object:
    """Create one validated empty or recovered fill aggregate.

    Args:
        **values: Field values for _FillAggregate schema.

    Returns:
        Validated _FillAggregate instance.
    """
    return _FillAggregate.model_validate(values)


def apply_order_fill(
    aggregate: object, *, fill_id: str, quantity: Decimal, price: Decimal
) -> object:
    """Apply one unique positive fill and recompute its weighted average.

    Args:
        aggregate: Existing _FillAggregate instance.
        fill_id: Unique fill identifier string.
        quantity: Fill quantity Decimal.
        price: Fill execution price Decimal.

    Returns:
        New _FillAggregate instance with updated filled quantity and average price.

    Raises:
        TradingError: If aggregate is invalid, fill is duplicated, or fill
            parameters are invalid.
    """
    if not isinstance(aggregate, _FillAggregate) or fill_id in aggregate.fill_ids:
        raise TradingError("VERSION_CONFLICT", "Fill is invalid or duplicated")
    if quantity <= 0 or price <= 0:
        raise TradingError(
            "VALIDATION_FAILED", "Fill quantity and price must be positive"
        )
    total = aggregate.filled_quantity + quantity
    if total > aggregate.ordered_quantity:
        raise TradingError("VALIDATION_FAILED", "Fill exceeds residual quantity")
    prior = (aggregate.average_fill_price or Decimal(0)) * aggregate.filled_quantity
    average = (prior + price * quantity) / total
    return _FillAggregate.model_validate(
        {
            **aggregate.model_dump(),
            "filled_quantity": total,
            "average_fill_price": average,
            "fill_ids": (*aggregate.fill_ids, fill_id),
        }
    )


def get_fill_residual(aggregate: object) -> Decimal:
    """Return the exact unfilled order quantity.

    Args:
        aggregate: Target _FillAggregate instance.

    Returns:
        Exact Decimal residual quantity.

    Raises:
        TradingError: If aggregate is not a valid _FillAggregate.
    """
    if not isinstance(aggregate, _FillAggregate):
        raise TradingError("INVALID_REQUEST", "Fill aggregate is invalid")
    return aggregate.ordered_quantity - aggregate.filled_quantity


__all__ = ["apply_order_fill", "create_fill_aggregate", "get_fill_residual"]
