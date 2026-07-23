"""Source readiness, capability, provenance, licence, and plan contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal

from pydantic import (
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.data.contracts._base import FrozenContract as _Contract
from app.utils import logger

type WorkflowContext = Literal[
    "research", "backtest", "validation", "risk", "execution_bound"
]
type SourceReadiness = Literal["disabled", "staging", "production"]
type LicenseStatus = Literal["approved", "restricted", "unknown"]
type DataKind = Literal["bars", "ticks", "spreads", "volume"]


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


def _unique_texts(values: tuple[str, ...]) -> tuple[str, ...]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _unique_texts")
    validated = tuple(_text(value) for value in values)
    if len(set(validated)) != len(validated):
        raise ValueError("values must be unique")
    return validated


class SourceLicensePolicy(_Contract):
    """Declared workflow, export, retention, and attribution policy."""

    source_id: str
    status: LicenseStatus
    permitted_workflows: tuple[WorkflowContext, ...]
    export_allowed: bool
    retention_days: int | None = None
    attribution_required: bool
    attribution_text: str | None = None

    @field_validator("source_id")
    @classmethod
    def _validate_source_id(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_source_id")
        return _text(value)

    @field_validator("permitted_workflows")
    @classmethod
    def _validate_workflows(
        cls, value: tuple[WorkflowContext, ...]
    ) -> tuple[WorkflowContext, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_workflows")
        if len(set(value)) != len(value):
            raise ValueError("permitted_workflows must be unique")
        return value

    @field_validator("retention_days")
    @classmethod
    def _validate_retention(cls, value: int | None) -> int | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_retention")
        if value is not None and value < 0:
            raise ValueError("retention_days must be non-negative")
        return value

    @field_validator("attribution_text")
    @classmethod
    def _validate_attribution(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_attribution")
        return _optional_text(value)

    @model_validator(mode="after")
    def _validate_attribution_relation(self) -> SourceLicensePolicy:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_attribution_relation")
        if self.attribution_required and self.attribution_text is None:
            raise ValueError("attribution_text is required")
        if self.status == "unknown" and self.permitted_workflows:
            raise ValueError("unknown license status cannot permit workflows")
        if self.status != "approved" and self.export_allowed:
            raise ValueError("only an approved license may permit export")
        return self


class SourceDescriptor(_Contract):
    """Versioned source capability and readiness declaration."""

    source_id: str
    readiness: SourceReadiness
    capabilities: tuple[str, ...]
    requires_credentials: bool
    requires_network: bool
    supports_writes: bool
    schema_version: str
    timezone: str
    revision: str
    license_policy: SourceLicensePolicy
    identity_mapping_revision: str
    promotion_evidence: tuple[str, ...] = ()

    @field_validator(
        "source_id",
        "schema_version",
        "timezone",
        "revision",
        "identity_mapping_revision",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("capabilities", "promotion_evidence")
    @classmethod
    def _validate_text_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text_tuple")
        return _unique_texts(value)

    @model_validator(mode="after")
    def _validate_descriptor(self) -> SourceDescriptor:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_descriptor")
        if not self.capabilities:
            raise ValueError("capabilities must not be empty")
        if self.license_policy.source_id != self.source_id:
            raise ValueError("license policy source does not match descriptor")
        if self.readiness == "production" and not self.promotion_evidence:
            raise ValueError("production readiness requires promotion evidence")
        return self


class SourceReadRequest(_Contract):
    """Bounded provider-native source read request."""

    source_id: str
    provider_symbol: str
    data_kind: DataKind
    timeframe: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    limit: int
    request_id: str

    @field_validator("source_id", "provider_symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("timeframe")
    @classmethod
    def _validate_timeframe(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_timeframe")
        return _optional_text(value)

    @field_validator("start", "end")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return None if value is None else _utc(value)

    @field_validator("limit")
    @classmethod
    def _validate_limit(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_limit")
        if value <= 0:
            raise ValueError("limit must be positive")
        return value

    @model_validator(mode="after")
    def _validate_range(self) -> SourceReadRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_range")
        if (self.start is None) != (self.end is None):
            raise ValueError("start and end must be supplied together")
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("start must precede end")
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("bar reads require timeframe")
        return self


class RawSourceBatch(_Contract):
    """Provider-neutral raw records plus source revision evidence."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    source_id: str
    provider_symbol: str
    data_kind: DataKind
    records: tuple[Mapping[str, object], ...]
    retrieved_at: datetime
    revision: str
    request_id: str

    @field_validator("source_id", "provider_symbol", "revision", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("retrieved_at")
    @classmethod
    def _validate_retrieved_at(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_retrieved_at")
        return _utc(value)

    @field_validator("records", mode="after")
    @classmethod
    def _freeze_records(
        cls, value: tuple[Mapping[str, object], ...]
    ) -> tuple[Mapping[str, object], ...]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_records")
        return tuple(MappingProxyType(dict(record)) for record in value)

    @field_serializer("records", when_used="json")
    def _serialize_records(
        self, value: tuple[Mapping[str, object], ...]
    ) -> tuple[dict[str, object], ...]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_records")
        return tuple(dict(record) for record in value)


class SourceIdentityRequest(_Contract):
    """Resolve one canonical or friendly source identity."""

    source_id: str
    identity: str
    request_id: str

    @field_validator("source_id", "identity", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)


class SourceIdentity(_Contract):
    """Exact provider identity plus versioned mapping evidence."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    source_id: str
    canonical_symbol: str
    friendly_name: str
    provider_symbol: str
    mapping_revision: str
    provenance: Mapping[str, str]
    request_id: str

    @field_validator(
        "source_id",
        "canonical_symbol",
        "friendly_name",
        "provider_symbol",
        "mapping_revision",
        "request_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("provenance", mode="after")
    @classmethod
    def _freeze_provenance(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_provenance")
        frozen = MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )
        if not frozen:
            raise ValueError("identity provenance must not be empty")
        return frozen

    @field_serializer("provenance", when_used="json")
    def _serialize_provenance(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_provenance")
        return dict(value)


class SourcePlan(_Contract):
    """Explicit deterministic requested and fallback source plan."""

    requested_source: str
    ordered_sources: tuple[str, ...]
    attempted_sources: tuple[str, ...] = ()
    request_id: str

    @field_validator("requested_source", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("ordered_sources", "attempted_sources")
    @classmethod
    def _validate_sources(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_sources")
        return _unique_texts(value)

    @model_validator(mode="after")
    def _validate_plan(self) -> SourcePlan:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_plan")
        if not self.ordered_sources or self.ordered_sources[0] != self.requested_source:
            raise ValueError("ordered_sources must begin with requested_source")
        if any(source not in self.ordered_sources for source in self.attempted_sources):
            raise ValueError("attempted source is outside the explicit plan")
        return self


class SourcePromotionRequest(_Contract):
    """Authenticated evidence package for one readiness transition."""

    source_id: str
    target_readiness: SourceReadiness
    evidence: tuple[str, ...]
    request_id: str

    @field_validator("source_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("evidence")
    @classmethod
    def _validate_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_evidence")
        validated = _unique_texts(value)
        if not validated:
            raise ValueError("promotion evidence must not be empty")
        return validated


__all__ = [
    "RawSourceBatch",
    "SourceDescriptor",
    "SourceIdentity",
    "SourceIdentityRequest",
    "SourceLicensePolicy",
    "SourcePlan",
    "SourcePromotionRequest",
    "SourceReadRequest",
]
