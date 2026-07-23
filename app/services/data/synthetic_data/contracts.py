"""Contracts for deterministic bounded synthetic market-data generation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from pydantic import field_serializer, field_validator, model_validator

from app.services.data.contracts._base import TracedOpenContract
from app.services.data.time_sessions.utc import require_utc

type PrecisionPolicy = Literal[
    "decimal_string",
    "float_research_only",
    "source_native_decimal",
    "reject_on_missing_metadata",
]


def _text(value: str) -> str:
    """Validate one required trimmed string."""
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


class SyntheticRequest(TracedOpenContract):
    """Bounded deterministic synthetic market-record request."""

    symbol: str
    data_kind: Literal["bars", "ticks"]
    timeframe: str | None = None
    start: datetime
    record_count: int
    method: Literal["gbm"]
    seed: int | None = None
    parameters: Mapping[str, Decimal]
    precision_policy: PrecisionPolicy
    request_id: str

    @field_validator("symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required request field."""
        return _text(value)

    @field_validator("timeframe")
    @classmethod
    def _validate_timeframe(cls, value: str | None) -> str | None:
        """Validate the optional timeframe."""
        return None if value is None else _text(value)

    @field_validator("start")
    @classmethod
    def _validate_start(cls, value: datetime) -> datetime:
        """Validate the generation start as aware UTC."""
        return require_utc(value)

    @field_validator("record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate the positive record bound."""
        if value <= 0:
            raise ValueError("record_count must be positive")
        return value

    @field_validator("parameters", mode="after")
    @classmethod
    def _freeze_parameters(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Validate and freeze exact generation parameters."""
        validated: dict[str, Decimal] = {}
        for key, item in value.items():
            if not item.is_finite():
                raise ValueError("synthetic parameter must be finite")
            validated[_text(key)] = item
        return MappingProxyType(validated)

    @model_validator(mode="after")
    def _validate_synthetic_request(self) -> SyntheticRequest:
        """Validate kind, timeframe, and precision relationships."""
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("synthetic bars require timeframe")
        if self.precision_policy == "float_research_only":
            raise ValueError("synthetic governed output requires exact precision")
        return self

    @field_serializer("parameters", when_used="json")
    def _serialize_parameters(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize generation parameters deterministically."""
        return {key: str(item) for key, item in value.items()}


__all__ = ["SyntheticRequest"]
