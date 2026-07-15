"""Risk-ready market-context request and evidence contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
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

MARKET_CONTEXT_SCHEMA: Final = "data.market_context_evidence.v1"

type EvidenceKind = Literal[
    "session",
    "calendar",
    "spread",
    "liquidity",
    "volatility",
    "correlation",
    "crisis",
]


def _text(value: str) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _optional_text(value: str | None) -> str | None:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _optional_text")
    return None if value is None else _text(value)


def _utc(value: datetime) -> datetime:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _utc")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


class _Contract(DataContractModel):
    """Private immutable market-context behavior."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> _Contract:
        """Validate any request identifier carried by this contract."""
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class MarketContextRequest(_Contract):
    """Bounded request for declared market-context evidence."""

    symbol: str
    account_id: str | None = None
    as_of: datetime
    max_age_seconds: int
    requested_evidence: tuple[EvidenceKind, ...]
    timezone: str
    request_id: str

    @field_validator("symbol", "timezone", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("account_id")
    @classmethod
    def _validate_account(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_account")
        return _optional_text(value)

    @field_validator("as_of")
    @classmethod
    def _validate_as_of(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_as_of")
        return _utc(value)

    @field_validator("max_age_seconds")
    @classmethod
    def _validate_age(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_age")
        if value <= 0:
            raise ValueError("max_age_seconds must be positive")
        return value

    @field_validator("requested_evidence")
    @classmethod
    def _validate_requested(
        cls, value: tuple[EvidenceKind, ...]
    ) -> tuple[EvidenceKind, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_requested")
        if not value or len(set(value)) != len(value):
            raise ValueError("requested_evidence must be non-empty and unique")
        return value


class MarketContextEvidence(_Contract):
    """Immutable normalized market-context evidence version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["data.market_context_evidence.v1"] = MARKET_CONTEXT_SCHEMA
    symbol: str
    session_state: str | None = None
    calendar_state: str | None = None
    spread: Decimal | None = None
    spread_unit: str | None = None
    liquidity: Decimal | None = None
    volatility: Decimal | None = None
    correlations: Mapping[str, Decimal]
    crisis_flags: tuple[str, ...]
    timezone: str
    as_of: datetime
    expires_at: datetime
    provenance: Mapping[str, str]
    missing_fields: tuple[str, ...]
    request_id: str

    @field_validator("symbol", "timezone", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("session_state", "calendar_state", "spread_unit")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_optional_text")
        return _optional_text(value)

    @field_validator("spread", "liquidity", "volatility")
    @classmethod
    def _validate_numeric(cls, value: Decimal | None) -> Decimal | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_numeric")
        if value is not None and not value.is_finite():
            raise ValueError("evidence numeric must be finite")
        if value is not None and value < 0:
            raise ValueError("evidence numeric must be non-negative")
        return value

    @field_validator("correlations", mode="after")
    @classmethod
    def _freeze_correlations(
        cls, value: Mapping[str, Decimal]
    ) -> Mapping[str, Decimal]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_correlations")
        validated: dict[str, Decimal] = {}
        for key, item in value.items():
            if not item.is_finite() or not Decimal(-1) <= item <= Decimal(1):
                raise ValueError("correlation must be finite and between -1 and 1")
            validated[_text(key)] = item
        return MappingProxyType(validated)

    @field_validator("crisis_flags", "missing_fields")
    @classmethod
    def _validate_texts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_texts")
        validated = tuple(_text(item) for item in value)
        if len(set(validated)) != len(validated):
            raise ValueError("evidence fields must be unique")
        return validated

    @field_validator("as_of", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("provenance", mode="after")
    @classmethod
    def _freeze_provenance(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_provenance")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_serializer("provenance", when_used="json")
    def _serialize_provenance(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_provenance")
        return dict(value)

    @model_validator(mode="after")
    def _validate_evidence(self) -> MarketContextEvidence:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_evidence")
        if self.expires_at <= self.as_of:
            raise ValueError("expires_at must follow as_of")
        if self.spread is not None and self.spread_unit is None:
            raise ValueError("spread_unit is required when spread is present")
        optional_fields = {
            "session": self.session_state,
            "calendar": self.calendar_state,
            "spread": self.spread,
            "liquidity": self.liquidity,
            "volatility": self.volatility,
        }
        for field, value in optional_fields.items():
            if value is None and field not in self.missing_fields:
                raise ValueError("missing evidence must be explicit")
        return self

    @field_serializer("spread", "liquidity", "volatility", when_used="json")
    def _serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_decimal")
        return None if value is None else str(value)

    @field_serializer("correlations", when_used="json")
    def _serialize_correlations(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_correlations")
        return {key: str(item) for key, item in value.items()}


__all__ = [
    "MARKET_CONTEXT_SCHEMA",
    "MarketContextEvidence",
    "MarketContextRequest",
]
