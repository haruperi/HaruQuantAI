"""Validated protective-order plans and coverage evidence."""

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator


class _ProtectiveOrderPlan(BaseModel):
    """Private immutable protection plan."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.protective_order_plan.v1"] = (
        "trading.protective_order_plan.v1"
    )
    plan_id: str
    position_id: str
    order_id: str
    risk_decision_id: str
    quantity: Decimal
    stop_price: Decimal
    target_price: Decimal
    oco_group_id: str
    source_sequence: int

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if any(
            not value.strip()
            for value in (
                self.plan_id,
                self.position_id,
                self.order_id,
                self.risk_decision_id,
                self.oco_group_id,
            )
        ):
            raise ValueError("protective-order identifiers must be non-empty")
        if (
            self.quantity <= 0
            or self.stop_price <= 0
            or self.target_price <= 0
            or self.source_sequence < 0
        ):
            raise ValueError("protective-order numeric values are invalid")
        if self.stop_price == self.target_price:
            raise ValueError("stop and target prices must differ")
        return self


__all__: list[str] = []
