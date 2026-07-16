"""Exact FX conversion request, leg, and evidence contracts."""

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

FX_CONVERSION_EVIDENCE_SCHEMA: Final = "data.fx_conversion_evidence.v1"
CURRENCY_CODE_LENGTH = 3


def _text(value: str) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _currency(value: str) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _currency")
    validated = _text(value)
    if len(validated) != CURRENCY_CODE_LENGTH or validated != validated.upper():
        raise ValueError("currency must be a three-letter uppercase code")
    return validated


def _utc(value: datetime) -> datetime:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _utc")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


def _freeze_text_mapping(value: Mapping[str, str]) -> Mapping[str, str]:
    """Freeze one DATA contract value against mutation."""
    logger.debug("Running DATA function: _freeze_text_mapping")
    return MappingProxyType({_text(key): _text(item) for key, item in value.items()})


class _Contract(DataContractModel):
    """Private immutable FX-contract behavior."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> _Contract:
        """Validate any request identifier carried by this contract."""
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class FXConversionRequest(_Contract):
    """Bounded explicit FX conversion-path request."""

    source_currency: str
    target_currency: str
    as_of: datetime
    max_age_seconds: int
    allowed_intermediates: tuple[str, ...]
    max_legs: int
    path_policy_id: str
    path_policy_version: str
    request_id: str

    @field_validator("source_currency", "target_currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_currency")
        return _currency(value)

    @field_validator("allowed_intermediates")
    @classmethod
    def _validate_intermediates(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_intermediates")
        validated = tuple(_currency(item) for item in value)
        if len(set(validated)) != len(validated):
            raise ValueError("allowed_intermediates must be unique")
        return validated

    @field_validator("as_of")
    @classmethod
    def _validate_as_of(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_as_of")
        return _utc(value)

    @field_validator("max_age_seconds", "max_legs")
    @classmethod
    def _validate_positive(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_positive")
        if value <= 0:
            raise ValueError("bound must be positive")
        return value

    @field_validator("path_policy_id", "path_policy_version", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @model_validator(mode="after")
    def _validate_request(self) -> FXConversionRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request")
        if self.source_currency == self.target_currency:
            raise ValueError("source and target currencies must differ")
        if self.source_currency in self.allowed_intermediates:
            raise ValueError("source currency cannot be an intermediate")
        if self.target_currency in self.allowed_intermediates:
            raise ValueError("target currency cannot be an intermediate")
        if self.max_legs > len(self.allowed_intermediates) + 1:
            raise ValueError("max_legs exceeds the declared path space")
        return self


class FXRateLeg(_Contract):
    """One exact provenance-bound rate leg."""

    source_currency: str
    target_currency: str
    rate: Decimal
    source_id: str
    provider_symbol: str
    as_of: datetime
    provenance: Mapping[str, str]

    @field_validator("source_currency", "target_currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_currency")
        return _currency(value)

    @field_validator("rate")
    @classmethod
    def _validate_rate(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_rate")
        if not value.is_finite() or value <= 0:
            raise ValueError("rate must be finite and positive")
        return value

    @field_validator("source_id", "provider_symbol")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("as_of")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("provenance", mode="after")
    @classmethod
    def _validate_provenance(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_provenance")
        return _freeze_text_mapping(value)

    @field_serializer("provenance", when_used="json")
    def _serialize_provenance(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_provenance")
        return dict(value)

    @model_validator(mode="after")
    def _validate_leg(self) -> FXRateLeg:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_leg")
        if self.source_currency == self.target_currency:
            raise ValueError("rate leg cannot convert a currency to itself")
        return self

    @field_serializer("rate", when_used="json")
    def _serialize_rate(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_rate")
        return str(value)


class FXConversionEvidence(_Contract):
    """Immutable ordered FX conversion evidence version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["data.fx_conversion_evidence.v1"] = FX_CONVERSION_EVIDENCE_SCHEMA
    source_currency: str
    target_currency: str
    legs: tuple[FXRateLeg, ...]
    composite_rate: Decimal
    as_of: datetime
    expires_at: datetime
    path_policy_id: str
    path_policy_version: str
    provenance: Mapping[str, str]
    request_id: str

    @field_validator("source_currency", "target_currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_currency")
        return _currency(value)

    @field_validator("composite_rate")
    @classmethod
    def _validate_rate(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_rate")
        if not value.is_finite() or value <= 0:
            raise ValueError("composite_rate must be finite and positive")
        return value

    @field_validator("as_of", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("path_policy_id", "path_policy_version", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("provenance", mode="after")
    @classmethod
    def _validate_provenance(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_provenance")
        return _freeze_text_mapping(value)

    @field_serializer("provenance", when_used="json")
    def _serialize_provenance(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_provenance")
        return dict(value)

    @model_validator(mode="after")
    def _validate_evidence(self) -> FXConversionEvidence:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_evidence")
        if not self.legs:
            raise ValueError("conversion evidence requires at least one leg")
        if self.expires_at <= self.as_of:
            raise ValueError("expires_at must follow as_of")
        if self.legs[0].source_currency != self.source_currency:
            raise ValueError("first leg must begin with source_currency")
        if self.legs[-1].target_currency != self.target_currency:
            raise ValueError("last leg must end with target_currency")
        visited = {self.source_currency}
        product = Decimal(1)
        previous = self.source_currency
        for leg in self.legs:
            if leg.source_currency != previous:
                raise ValueError("rate legs must form a continuous path")
            if leg.target_currency in visited:
                raise ValueError("rate path must be acyclic")
            if leg.as_of > self.as_of:
                raise ValueError("leg evidence cannot be newer than evidence as_of")
            visited.add(leg.target_currency)
            previous = leg.target_currency
            product *= leg.rate
        if product != self.composite_rate:
            raise ValueError("composite_rate must equal the exact leg product")
        return self

    @field_serializer("composite_rate", when_used="json")
    def _serialize_rate(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_rate")
        return str(value)


__all__ = [
    "FX_CONVERSION_EVIDENCE_SCHEMA",
    "FXConversionEvidence",
    "FXConversionRequest",
    "FXRateLeg",
]
