"""Canonical immutable StopValidation v1 transport."""

# mypy: disable-error-code="arg-type"
# ruff: noqa: DOC201

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest, to_json_safe

logger = get_logger(__name__)


class _StopValidation(BaseModel):
    """Private stop-loss validation request/evidence artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.stop_validation.v1"] = "risk.stop_validation.v1"
    validation_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    entry_price: Decimal
    stop_price: Decimal
    tick_size: Decimal
    min_stop_distance: Decimal
    contract_value: Decimal
    quantity: Decimal
    invalidation_price: Decimal | None = None
    previous_stop_price: Decimal | None = None
    allow_widening: bool = False
    evaluated_at: datetime

    @field_validator("evaluated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("StopValidation timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _relationships(self) -> _StopValidation:
        if not self.symbol.strip() or not self.validation_id.strip():
            raise ValueError("StopValidation identity text must be non-empty")
        for price in (self.entry_price, self.stop_price):
            if not price.is_finite() or price <= 0:
                raise ValueError("StopValidation prices must be finite and positive")
        if not self.tick_size.is_finite() or self.tick_size <= 0:
            raise ValueError("tick_size must be finite and positive")
        if not self.min_stop_distance.is_finite() or self.min_stop_distance < 0:
            raise ValueError("min_stop_distance must be finite and non-negative")
        if not self.contract_value.is_finite() or self.contract_value <= 0:
            raise ValueError("contract_value must be finite and positive")
        if not self.quantity.is_finite() or self.quantity <= 0:
            raise ValueError("quantity must be finite and positive")
        if self.invalidation_price is not None and (
            not self.invalidation_price.is_finite() or self.invalidation_price <= 0
        ):
            raise ValueError("invalidation_price must be finite and positive")
        if self.previous_stop_price is not None and (
            not self.previous_stop_price.is_finite() or self.previous_stop_price <= 0
        ):
            raise ValueError("previous_stop_price must be finite and positive")
        return self


def build_stop_validation(
    *,
    symbol: str,
    side: str,
    entry_price: Decimal,
    stop_price: Decimal,
    tick_size: Decimal,
    min_stop_distance: Decimal,
    contract_value: Decimal,
    quantity: Decimal,
    evaluated_at: datetime,
    invalidation_price: Decimal | None = None,
    previous_stop_price: Decimal | None = None,
    allow_widening: bool = False,
) -> dict[str, Any]:
    """Build a deterministic JSON-safe StopValidation v1 mapping."""
    fields = {
        "symbol": symbol,
        "side": side,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "tick_size": tick_size,
        "min_stop_distance": min_stop_distance,
        "contract_value": contract_value,
        "quantity": quantity,
        "evaluated_at": evaluated_at,
        "invalidation_price": invalidation_price,
        "previous_stop_price": previous_stop_price,
        "allow_widening": allow_widening,
    }
    material = fields | {
        "contract_version": "v1",
        "schema_id": "risk.stop_validation.v1",
    }
    validation_id = f"stopval-{canonical_digest(material)}"
    logger.info("Building StopValidation %s", validation_id)
    model = _StopValidation(validation_id=validation_id, **fields)
    return dict(to_json_safe(model.model_dump(mode="json")))


def parse_stop_validation(value: Mapping[str, object]) -> dict[str, Any]:
    """Parse a strict StopValidation v1 mapping."""
    logger.info("Parsing StopValidation contract")
    return dict(
        to_json_safe(
            _StopValidation.model_validate(dict(value)).model_dump(mode="json")
        )
    )


__all__ = ["build_stop_validation", "parse_stop_validation"]
