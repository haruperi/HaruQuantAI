"""Read-only normalized broker-account evidence contracts."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Final, Literal

from pydantic import (
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.data.contracts._base import DataContractModel
from app.services.data.contracts._validation import validate_request_id
from app.utils import logger

ACCOUNT_SNAPSHOT_SCHEMA: Final = "data.account_state_snapshot.v1"


def _text(value: str) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _utc(value: datetime) -> datetime:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _utc")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


def _finite(value: Decimal | None) -> Decimal | None:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _finite")
    if value is not None and not value.is_finite():
        raise ValueError("numeric value must be finite")
    return value


class _Contract(DataContractModel):
    """Private immutable broker-evidence behavior."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> _Contract:
        """Validate any request identifier carried by this contract."""
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class AccountBalance(_Contract):
    """Exact balance evidence for one asset."""

    asset: str
    total: Decimal
    available: Decimal

    @field_validator("asset")
    @classmethod
    def _validate_asset(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_asset")
        return _text(value)

    @field_validator("total", "available")
    @classmethod
    def _validate_amount(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_amount")
        validated = _finite(value)
        if validated is None:
            raise ValueError("amount is required")
        return validated

    @model_validator(mode="after")
    def _validate_balance(self) -> AccountBalance:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_balance")
        if self.total < 0 or self.available < 0 or self.available > self.total:
            raise ValueError("balance amounts are inconsistent")
        return self

    @field_serializer("total", "available", when_used="json")
    def _serialize_amount(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_amount")
        return str(value)


class AccountPosition(_Contract):
    """Normalized immutable open-position evidence."""

    position_id: str
    symbol: str
    side: Literal["LONG", "SHORT"]
    quantity: Decimal
    entry_price: Decimal | None = None

    @field_validator("position_id", "symbol")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("quantity", "entry_price")
    @classmethod
    def _validate_numeric(cls, value: Decimal | None) -> Decimal | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_numeric")
        return _finite(value)

    @model_validator(mode="after")
    def _validate_position(self) -> AccountPosition:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_position")
        if self.quantity <= 0:
            raise ValueError("position quantity must be positive")
        if self.entry_price is not None and self.entry_price <= 0:
            raise ValueError("entry_price must be positive")
        return self

    @field_serializer("quantity", "entry_price", when_used="json")
    def _serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_decimal")
        return None if value is None else str(value)


class AccountOrder(_Contract):
    """Normalized immutable open-order evidence."""

    order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    state: str
    quantity: Decimal
    price: Decimal | None = None

    @field_validator("order_id", "symbol", "state")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("quantity", "price")
    @classmethod
    def _validate_numeric(cls, value: Decimal | None) -> Decimal | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_numeric")
        return _finite(value)

    @model_validator(mode="after")
    def _validate_order(self) -> AccountOrder:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_order")
        if self.quantity <= 0:
            raise ValueError("order quantity must be positive")
        if self.price is not None and self.price <= 0:
            raise ValueError("order price must be positive")
        return self

    @field_serializer("quantity", "price", when_used="json")
    def _serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_decimal")
        return None if value is None else str(value)


class AccountSnapshotRequest(_Contract):
    """Bounded request for a fresh read-only account snapshot."""

    source_id: str
    account_id: str
    max_age_seconds: int
    request_id: str

    @field_validator("source_id", "account_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("max_age_seconds")
    @classmethod
    def _validate_age(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_age")
        if value <= 0:
            raise ValueError("max_age_seconds must be positive")
        return value


class AccountStateSnapshot(_Contract):
    """Immutable normalized account-state evidence version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["data.account_state_snapshot.v1"] = ACCOUNT_SNAPSHOT_SCHEMA
    account_id: str
    currency: str
    balances: tuple[AccountBalance, ...]
    equity: Decimal
    margin_used: Decimal | None = None
    margin_available: Decimal | None = None
    positions: tuple[AccountPosition, ...]
    orders: tuple[AccountOrder, ...]
    connected: bool
    trading_allowed: bool
    source_id: str
    snapshot_at: datetime
    expires_at: datetime
    request_id: str

    @field_validator("account_id", "currency", "source_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("equity", "margin_used", "margin_available")
    @classmethod
    def _validate_numeric(cls, value: Decimal | None) -> Decimal | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_numeric")
        return _finite(value)

    @field_validator("snapshot_at", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_snapshot(self) -> AccountStateSnapshot:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_snapshot")
        if self.expires_at <= self.snapshot_at:
            raise ValueError("expires_at must follow snapshot_at")
        if self.margin_used is not None and self.margin_used < 0:
            raise ValueError("margin_used must be non-negative")
        if self.margin_available is not None and self.margin_available < 0:
            raise ValueError("margin_available must be non-negative")
        if self.trading_allowed and not self.connected:
            raise ValueError("trading cannot be allowed while disconnected")
        position_ids = tuple(position.position_id for position in self.positions)
        order_ids = tuple(order.order_id for order in self.orders)
        if len(set(position_ids)) != len(position_ids):
            raise ValueError("position identifiers must be unique")
        if len(set(order_ids)) != len(order_ids):
            raise ValueError("order identifiers must be unique")
        return self

    @field_serializer("equity", "margin_used", "margin_available", when_used="json")
    def _serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_decimal")
        return None if value is None else str(value)


__all__ = [
    "ACCOUNT_SNAPSHOT_SCHEMA",
    "AccountBalance",
    "AccountOrder",
    "AccountPosition",
    "AccountSnapshotRequest",
    "AccountStateSnapshot",
]
