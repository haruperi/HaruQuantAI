"""Canonical market requests, datasets, quality, and availability contracts."""

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
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord
from app.utils import logger

MARKET_DATASET_SCHEMA: Final = "data.market_dataset.v1"
NORMALIZATION_VERSION = "v1"
QUALITY_SAMPLE_LIMIT: Final = 1000
PRECISION_POLICIES = (
    "decimal_string",
    "float_research_only",
    "source_native_decimal",
    "reject_on_missing_metadata",
)
WORKFLOW_CONTEXTS = (
    "research",
    "backtest",
    "validation",
    "risk",
    "execution_bound",
)

type WorkflowContext = Literal[
    "research", "backtest", "validation", "risk", "execution_bound"
]
type PrecisionPolicy = Literal[
    "decimal_string",
    "float_research_only",
    "source_native_decimal",
    "reject_on_missing_metadata",
]
type DataKind = Literal["bars", "ticks", "spreads", "volume"]
type CanonicalRecord = OHLCVRecord | TickRecord | SpreadRecord


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


class _Contract(DataContractModel):
    """Private immutable market-contract behavior."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> _Contract:
        """Validate any request identifier carried by this contract."""
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class QualityIssue(_Contract):
    """One bounded redacted quality diagnostic."""

    code: str
    severity: Literal["info", "warning", "error", "critical"]
    message: str
    field: str | None = None
    affected_count: int | None = None
    samples: tuple[str, ...] = ()
    blocking_workflows: tuple[WorkflowContext, ...] = ()

    @field_validator("code", "message")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("field")
    @classmethod
    def _validate_field(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_field")
        return _optional_text(value)

    @field_validator("affected_count")
    @classmethod
    def _validate_count(cls, value: int | None) -> int | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value is not None and value < 0:
            raise ValueError("affected_count must be non-negative")
        return value

    @field_validator("samples")
    @classmethod
    def _validate_samples(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_samples")
        return tuple(_text(item) for item in value)

    @field_validator("blocking_workflows")
    @classmethod
    def _validate_workflows(
        cls, value: tuple[WorkflowContext, ...]
    ) -> tuple[WorkflowContext, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_workflows")
        if len(set(value)) != len(value):
            raise ValueError("blocking_workflows must be unique")
        return value


class DataQualityReport(_Contract):
    """Bounded quality evidence for one normalized dataset."""

    quality_status: Literal["passed", "passed_with_warnings", "failed", "not_checked"]
    quality_score: Decimal
    issues: tuple[QualityIssue, ...] = ()
    warnings: tuple[str, ...] = ()
    record_count: int
    checked_count: int
    truncated: bool
    sample_limit: int
    schema_version: str
    generated_at: datetime

    @field_validator("quality_score")
    @classmethod
    def _validate_score(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_score")
        if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
            raise ValueError("quality_score must be finite and between zero and one")
        return value

    @field_validator("record_count", "checked_count", "sample_limit")
    @classmethod
    def _validate_count(cls, value: int, info: object) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        field_name = str(getattr(info, "field_name", "count"))
        if value < 0 or (field_name == "sample_limit" and value == 0):
            message = f"{field_name} is outside its valid range"
            raise ValueError(message)
        return value

    @field_validator("warnings")
    @classmethod
    def _validate_warnings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_warnings")
        return tuple(_text(item) for item in value)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_schema")
        return _text(value)

    @field_validator("generated_at")
    @classmethod
    def _validate_generated_at(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_generated_at")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_report(self) -> DataQualityReport:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_report")
        if self.checked_count > self.record_count:
            raise ValueError("checked_count must not exceed record_count")
        if sum(len(issue.samples) for issue in self.issues) > self.sample_limit:
            raise ValueError("quality issue samples exceed sample_limit")
        if self.quality_status == "failed" and not self.issues:
            raise ValueError("failed quality status requires an issue")
        return self

    @field_serializer("quality_score", when_used="json")
    def _serialize_score(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_score")
        return str(value)


class MarketDataset(_Contract):
    """Immutable normalized provider-neutral market dataset version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["data.market_dataset.v1"] = MARKET_DATASET_SCHEMA
    normalization_version: str
    data_kind: Literal["bars", "ticks", "spreads"]
    symbol: str
    timeframe: str | None = None
    records: tuple[CanonicalRecord, ...]
    start: datetime
    end: datetime
    available_at: datetime
    record_count: int
    quality_report: DataQualityReport
    source_metadata: Mapping[str, str]
    license_metadata: Mapping[str, str]
    cache_status: Literal["miss", "hit", "stale_warning", "not_used"]
    workflow_context: WorkflowContext
    precision_policy: PrecisionPolicy
    request_id: str

    @field_validator("normalization_version", "symbol", "request_id")
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

    @field_validator("start", "end", "available_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("source_metadata", "license_metadata", mode="after")
    @classmethod
    def _freeze_metadata(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_metadata")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_serializer("source_metadata", "license_metadata", when_used="json")
    def _serialize_metadata(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_metadata")
        return dict(value)

    @model_validator(mode="after")
    def _validate_dataset(self) -> MarketDataset:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_dataset")
        _validate_dataset_counts(self)
        _validate_dataset_record_type(self)
        _validate_dataset_times(self)
        _validate_dataset_policy(self)
        return self


def _validate_dataset_counts(dataset: MarketDataset) -> None:
    """Validate dataset bounds and record-count relationships."""
    logger.debug("Running DATA function: _validate_dataset_counts")
    if dataset.start > dataset.end:
        raise ValueError("start must not follow end")
    if dataset.record_count != len(dataset.records):
        raise ValueError("record_count must equal the number of records")
    if dataset.quality_report.record_count != dataset.record_count:
        raise ValueError("quality report count must match dataset count")


def _validate_dataset_record_type(dataset: MarketDataset) -> None:
    """Validate the declared kind against canonical record types."""
    logger.debug("Running DATA function: _validate_dataset_record_type")
    if dataset.data_kind == "bars" and dataset.timeframe is None:
        raise ValueError("bar datasets require timeframe")
    invalid = (
        (
            dataset.data_kind == "bars"
            and any(not isinstance(record, OHLCVRecord) for record in dataset.records)
        )
        or (
            dataset.data_kind == "ticks"
            and any(not isinstance(record, TickRecord) for record in dataset.records)
        )
        or (
            dataset.data_kind == "spreads"
            and any(not isinstance(record, SpreadRecord) for record in dataset.records)
        )
    )
    if invalid:
        raise ValueError("record type does not match data_kind")


def _validate_dataset_times(dataset: MarketDataset) -> None:
    """Validate deterministic ordering and evidence availability."""
    logger.debug("Running DATA function: _validate_dataset_times")
    if dataset.records:
        timestamps = tuple(record.timestamp for record in dataset.records)
        if timestamps != tuple(sorted(timestamps)):
            raise ValueError("records must be ordered by timestamp")
        if timestamps[0] != dataset.start or timestamps[-1] != dataset.end:
            raise ValueError("dataset bounds must match record timestamps")
        if (
            max(record.available_at for record in dataset.records)
            > dataset.available_at
        ):
            raise ValueError("dataset available_at precedes record evidence")
    if dataset.available_at < dataset.end:
        raise ValueError("available_at must not precede end")


def _validate_dataset_policy(dataset: MarketDataset) -> None:
    """Validate workflow-specific precision restrictions."""
    logger.debug("Running DATA function: _validate_dataset_policy")
    if (
        dataset.workflow_context != "research"
        and dataset.precision_policy == "float_research_only"
    ):
        raise ValueError("float research precision is restricted to research")


class MarketDataRequest(_Contract):
    """Typed bounded market-data retrieval request."""

    source_id: str
    symbol: str
    data_kind: Literal["bars", "ticks", "spreads"]
    timeframe: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    limit: int
    use_cache: bool
    cache_ttl_seconds: int | None = None
    quality_failure_behavior: Literal["fail", "warn"]
    workflow_context: WorkflowContext
    precision_policy: PrecisionPolicy
    fallback_sources: tuple[str, ...] = ()
    source_timezone: str | None = None
    request_id: str

    @field_validator("source_id", "symbol", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("timeframe", "source_timezone")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_optional_text")
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

    @field_validator("cache_ttl_seconds")
    @classmethod
    def _validate_ttl(cls, value: int | None) -> int | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_ttl")
        if value is not None and value < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        return value

    @field_validator("fallback_sources")
    @classmethod
    def _validate_fallbacks(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_fallbacks")
        return _unique_texts(value)

    @model_validator(mode="after")
    def _validate_request(self) -> MarketDataRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request")
        if (self.start is None) != (self.end is None):
            raise ValueError("start and end must be supplied together")
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("start must precede end")
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("bar requests require timeframe")
        if self.source_id in self.fallback_sources:
            raise ValueError("fallback_sources must not repeat source_id")
        if (
            self.workflow_context != "research"
            and self.precision_policy == "float_research_only"
        ):
            raise ValueError("float research precision is restricted to research")
        return self


class DataRange(_Contract):
    """One measured inclusive data range."""

    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_range(self) -> DataRange:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_range")
        if self.start > self.end:
            raise ValueError("start must not follow end")
        return self


class DataGap(DataRange):
    """One measured missing data range."""


class DataAvailability(_Contract):
    """Measured indexed availability without materialized records."""

    source_id: str
    symbol: str
    data_kind: DataKind
    timeframe: str | None = None
    ranges: tuple[DataRange, ...]
    gaps: tuple[DataGap, ...]
    completeness: Decimal
    record_count: int
    source_revision: str
    source_readiness: Literal["disabled", "staging", "production"]
    provenance: Mapping[str, str]
    request_id: str

    @field_validator("source_id", "symbol", "source_revision", "request_id")
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

    @field_validator("completeness")
    @classmethod
    def _validate_completeness(cls, value: Decimal) -> Decimal:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_completeness")
        if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
            raise ValueError("completeness must be finite and between zero and one")
        return value

    @field_validator("record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("record_count must be non-negative")
        return value

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
    def _validate_availability(self) -> DataAvailability:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_availability")
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("bar availability requires timeframe")
        starts = tuple(item.start for item in self.ranges)
        if starts != tuple(sorted(starts)):
            raise ValueError("ranges must be ordered")
        gap_starts = tuple(item.start for item in self.gaps)
        if gap_starts != tuple(sorted(gap_starts)):
            raise ValueError("gaps must be ordered")
        return self

    @field_serializer("completeness", when_used="json")
    def _serialize_completeness(self, value: Decimal) -> str:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_completeness")
        return str(value)


class SyntheticRequest(_Contract):
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
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("timeframe")
    @classmethod
    def _validate_timeframe(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_timeframe")
        return _optional_text(value)

    @field_validator("start")
    @classmethod
    def _validate_start(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_start")
        return _utc(value)

    @field_validator("record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value <= 0:
            raise ValueError("record_count must be positive")
        return value

    @field_validator("parameters", mode="after")
    @classmethod
    def _freeze_parameters(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Freeze one DATA contract value against mutation."""
        logger.debug("Running DATA function: _freeze_parameters")
        validated: dict[str, Decimal] = {}
        for key, item in value.items():
            if not item.is_finite():
                raise ValueError("synthetic parameter must be finite")
            validated[_text(key)] = item
        return MappingProxyType(validated)

    @model_validator(mode="after")
    def _validate_synthetic_request(self) -> SyntheticRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_synthetic_request")
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("synthetic bars require timeframe")
        if self.precision_policy == "float_research_only":
            raise ValueError("synthetic governed output requires exact precision")
        return self

    @field_serializer("parameters", when_used="json")
    def _serialize_parameters(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize one DATA contract value deterministically."""
        logger.debug("Running DATA function: _serialize_parameters")
        return {key: str(item) for key, item in value.items()}


__all__ = [
    "MARKET_DATASET_SCHEMA",
    "NORMALIZATION_VERSION",
    "PRECISION_POLICIES",
    "QUALITY_SAMPLE_LIMIT",
    "WORKFLOW_CONTEXTS",
    "DataAvailability",
    "DataGap",
    "DataQualityReport",
    "DataRange",
    "MarketDataRequest",
    "MarketDataset",
    "QualityIssue",
    "SyntheticRequest",
]
