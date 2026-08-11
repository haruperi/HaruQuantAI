"""Canonical immutable TradePlan v1 transport."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import canonical_digest, get_logger, to_json_safe

logger = get_logger(__name__)


class _TradePlan(BaseModel):
    """Private planning artifact that remains distinct from TradeIntent."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.trade_plan.v1"] = "strategy.trade_plan.v1"
    plan_id: str
    plan_version: int
    status: Literal[
        "DRAFT",
        "READY_FOR_RISK",
        "APPROVED",
        "REJECTED",
        "RELEASED",
        "MANAGED",
        "CLOSED",
        "ABORTED",
    ]
    strategy_id: str
    strategy_version: str
    symbol: str
    direction: Literal["BUY", "SELL"]
    entry_rule: str
    entry_price: Decimal | None
    invalidation_rule: str
    stop_price: Decimal
    target_price: Decimal
    exit_plan_ref: str
    operating_envelope_ref: str
    requested_size_basis: str
    planned_rationale: str
    author_type: Literal["STRATEGY", "PLAYER"]
    parent_plan_id: str | None = None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("TradePlan timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _relationships(self) -> _TradePlan:
        texts = (
            self.plan_id,
            self.strategy_id,
            self.strategy_version,
            self.symbol,
            self.entry_rule,
            self.invalidation_rule,
            self.exit_plan_ref,
            self.operating_envelope_ref,
            self.requested_size_basis,
            self.planned_rationale,
        )
        if any(not item.strip() for item in texts):
            raise ValueError("TradePlan text must be non-empty")
        if self.plan_version < 1:
            raise ValueError("plan_version must be positive")
        for price in (self.entry_price, self.stop_price, self.target_price):
            if price is not None and (not price.is_finite() or price <= 0):
                raise ValueError("TradePlan prices must be finite and positive")
        if self.plan_version > 1 and self.parent_plan_id is None:
            raise ValueError("amended plans require a parent_plan_id")
        return self


def build_trade_plan(
    *,
    plan_version: int,
    status: str,
    strategy_id: str,
    strategy_version: str,
    symbol: str,
    direction: str,
    entry_rule: str,
    entry_price: Decimal | None,
    invalidation_rule: str,
    stop_price: Decimal,
    target_price: Decimal,
    exit_plan_ref: str,
    operating_envelope_ref: str,
    requested_size_basis: str,
    planned_rationale: str,
    author_type: str,
    created_at: datetime,
    parent_plan_id: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic JSON-safe TradePlan v1 mapping."""
    fields = {
        "plan_version": plan_version,
        "status": status,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "symbol": symbol,
        "direction": direction,
        "entry_rule": entry_rule,
        "entry_price": entry_price,
        "invalidation_rule": invalidation_rule,
        "stop_price": stop_price,
        "target_price": target_price,
        "exit_plan_ref": exit_plan_ref,
        "operating_envelope_ref": operating_envelope_ref,
        "requested_size_basis": requested_size_basis,
        "planned_rationale": planned_rationale,
        "author_type": author_type,
        "created_at": created_at,
        "parent_plan_id": parent_plan_id,
    }
    material = fields | {
        "contract_version": "v1",
        "schema_id": "strategy.trade_plan.v1",
    }
    plan_id = f"plan-{canonical_digest(material)}"
    logger.info("Building TradePlan %s", plan_id)
    model = _TradePlan(plan_id=plan_id, **fields)
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_trade_plan(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict TradePlan v1 mapping."""
    logger.info("Parsing TradePlan contract")
    return dict(
        to_json_safe(_TradePlan.model_validate(dict(value)).model_dump(mode="json"))
    )


__all__ = ["build_trade_plan", "parse_trade_plan"]
