"""Canonical immutable Strategy-to-Risk TradeIntent contract."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.utils import logger


class TradeIntent(BaseModel):
    """Non-executable deterministic strategy proposal version 1."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.trade_intent.v1"] = "strategy.trade_intent.v1"
    intent_id: str
    decision_id: str
    idempotency_key: str
    strategy_id: str
    strategy_version: str
    strategy_sequence: int
    symbol: str
    side: Literal["BUY", "SELL"]
    intent_type: Literal["OPEN", "CLOSE", "REDUCE", "INCREASE", "MODIFY", "CANCEL"]
    requested_sizing_mode: str | None
    quantity_hint: Decimal | None
    notional_hint: Decimal | None
    signal_timestamp: datetime
    decision_timestamp: datetime
    parent_intent_id: str | None
    stop_loss: Decimal | None
    take_profit: Decimal | None
    expiration: datetime | None
    allow_partial_fills: bool
    min_fill_size: Decimal | None
    rationale_ref: str | None
    lineage: Mapping[str, str]

    @field_validator(
        "intent_id",
        "decision_id",
        "idempotency_key",
        "strategy_id",
        "strategy_version",
        "symbol",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required TradeIntent text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank.
        """
        logger.debug("Validating TradeIntent text")
        if not value or value != value.strip():
            raise ValueError("TradeIntent text must be non-empty and trimmed")
        return value

    @field_validator("lineage", mode="after")
    @classmethod
    def _freeze_lineage(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze required TradeIntent lineage.

        Args:
            value: Lineage mapping.

        Returns:
            Immutable lineage.

        Raises:
            ValueError: If lineage is empty or contains blank text.
        """
        logger.debug("Freezing TradeIntent lineage")
        if not value or any(
            not key.strip() or not item.strip() for key, item in value.items()
        ):
            raise ValueError("TradeIntent lineage must contain non-empty text")
        return MappingProxyType(dict(value))

    @field_serializer("lineage", when_used="json")
    def _serialize_lineage(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable TradeIntent lineage.

        Args:
            value: Immutable lineage.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing TradeIntent lineage")
        return dict(value)

    @model_validator(mode="after")
    def _validate_intent(self) -> TradeIntent:
        """Validate precision, timestamps, sizing, and partial fills.

        Returns:
            The validated intent.

        Raises:
            ValueError: If proposal invariants conflict.
        """
        logger.debug("Validating TradeIntent relationships")
        if self.strategy_sequence < 0:
            raise ValueError("strategy_sequence must be non-negative")
        if (
            self.signal_timestamp.tzinfo is None
            or self.decision_timestamp.tzinfo is None
        ):
            raise ValueError("TradeIntent timestamps must be aware UTC")
        if self.signal_timestamp > self.decision_timestamp:
            raise ValueError("signal_timestamp cannot follow decision_timestamp")
        for value in (
            self.quantity_hint,
            self.notional_hint,
            self.stop_loss,
            self.take_profit,
            self.min_fill_size,
        ):
            if value is not None and (not value.is_finite() or value <= 0):
                raise ValueError("TradeIntent decimals must be finite and positive")
        if self.min_fill_size is not None and not self.allow_partial_fills:
            raise ValueError("min_fill_size requires allow_partial_fills")
        return self


__all__ = ["TradeIntent"]
