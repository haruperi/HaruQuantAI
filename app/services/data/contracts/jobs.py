"""Public bounded backfill and scheduler contracts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import ConfigDict, field_validator, model_validator

from app.services.data.contracts._base import DataContractModel
from app.services.data.contracts._validation import validate_request_id
from app.utils import logger


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
    """Private immutable job-contract behavior."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> _Contract:
        """Validate any request identifier carried by this contract."""
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class BackfillChunkRequest(_Contract):
    """One bounded, version-identified backfill unit."""

    job_id: str
    source_id: str
    symbol: str
    data_kind: Literal["ohlcv", "tick", "spread"]
    timeframe: str | None = None
    start: datetime
    end: datetime
    schema_version: str
    normalization_version: str
    max_records: int
    request_id: str

    @field_validator(
        "job_id",
        "source_id",
        "symbol",
        "schema_version",
        "normalization_version",
        "request_id",
    )
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
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("max_records")
    @classmethod
    def _validate_bound(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_bound")
        if value <= 0:
            raise ValueError("max_records must be positive")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> BackfillChunkRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request")
        if self.start >= self.end:
            raise ValueError("start must precede end")
        if self.data_kind == "ohlcv" and self.timeframe is None:
            raise ValueError("OHLCV backfill requires a timeframe")
        return self


class BackfillChunkResult(_Contract):
    """Durable chunk commit and checkpoint evidence."""

    job_id: str
    chunk_id: str
    idempotency_key: str
    committed_start: datetime
    committed_end: datetime
    record_count: int
    content_hash: str
    checkpoint: str
    committed: bool
    request_id: str

    @field_validator(
        "job_id",
        "chunk_id",
        "idempotency_key",
        "content_hash",
        "checkpoint",
        "request_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("committed_start", "committed_end")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value <= 0:
            raise ValueError("record_count must be positive")
        return value

    @model_validator(mode="after")
    def _validate_result(self) -> BackfillChunkResult:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_result")
        if self.committed_start >= self.committed_end:
            raise ValueError("committed_start must precede committed_end")
        if not self.committed:
            raise ValueError("a chunk result requires durable commit evidence")
        return self


class RecoveryReport(_Contract):
    """Evidence-based recovery classification for interrupted jobs."""

    recovered_job_ids: tuple[str, ...]
    blocked_job_ids: tuple[str, ...]
    recovered_at: datetime
    request_id: str

    @field_validator("recovered_job_ids", "blocked_job_ids")
    @classmethod
    def _validate_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_ids")
        validated = tuple(_text(item) for item in value)
        if len(set(validated)) != len(validated):
            raise ValueError("job identifiers must be unique")
        return validated

    @field_validator("recovered_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_request_id")
        return _text(value)

    @model_validator(mode="after")
    def _validate_report(self) -> RecoveryReport:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_report")
        if set(self.recovered_job_ids) & set(self.blocked_job_ids):
            raise ValueError("a job cannot be both recovered and blocked")
        return self


class JobDefinition(_Contract):
    """Persistable schedule definition without a timer or runtime handle."""

    job_id: str
    source_id: str
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...]
    data_kinds: tuple[Literal["ohlcv", "tick", "spread"], ...]
    start: datetime
    end: datetime | None = None
    interval_seconds: int | None = None
    enabled: bool
    created_at: datetime
    request_id: str

    @field_validator("job_id", "source_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("symbols", "timeframes")
    @classmethod
    def _validate_text_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text_tuple")
        validated = tuple(_text(item) for item in value)
        if not validated or len(set(validated)) != len(validated):
            raise ValueError("values must be non-empty and unique")
        return validated

    @field_validator("data_kinds")
    @classmethod
    def _validate_kinds(
        cls, value: tuple[Literal["ohlcv", "tick", "spread"], ...]
    ) -> tuple[Literal["ohlcv", "tick", "spread"], ...]:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_kinds")
        if not value or len(set(value)) != len(value):
            raise ValueError("data_kinds must be non-empty and unique")
        return value

    @field_validator("start", "end", "created_at")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return None if value is None else _utc(value)

    @model_validator(mode="after")
    def _validate_definition(self) -> JobDefinition:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_definition")
        if self.end is not None and self.start >= self.end:
            raise ValueError("start must precede end")
        if self.interval_seconds is not None and self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.end is None and self.interval_seconds is None:
            raise ValueError("open-ended jobs require interval_seconds")
        if "ohlcv" in self.data_kinds and not self.timeframes:
            raise ValueError("OHLCV jobs require timeframes")
        return self


class ScheduleJobRequest(_Contract):
    """Explicit scheduler lifecycle command."""

    action: Literal["create", "start", "stop", "run_once"]
    job_id: str
    definition: JobDefinition | None = None
    request_id: str

    @field_validator("job_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @model_validator(mode="after")
    def _validate_action(self) -> ScheduleJobRequest:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_action")
        if self.action == "create":
            if self.definition is None or self.definition.job_id != self.job_id:
                raise ValueError("create requires a matching job definition")
        elif self.definition is not None:
            raise ValueError("only create accepts a job definition")
        return self


class JobRunResult(_Contract):
    """Completed run evidence; success cannot be timer-only."""

    job_id: str
    run_id: str
    state: Literal["succeeded", "failed", "blocked"]
    started_at: datetime
    finished_at: datetime
    committed_chunks: int
    record_count: int
    last_checkpoint: str | None = None
    error_code: str | None = None
    request_id: str

    @field_validator("job_id", "run_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("last_checkpoint", "error_code")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_optional_text")
        return _optional_text(value)

    @field_validator("started_at", "finished_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return _utc(value)

    @field_validator("committed_chunks", "record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_count")
        if value < 0:
            raise ValueError("run counters must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_result(self) -> JobRunResult:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_result")
        if self.started_at >= self.finished_at:
            raise ValueError("started_at must precede finished_at")
        if self.state == "succeeded":
            if (
                self.committed_chunks <= 0
                or self.record_count <= 0
                or self.last_checkpoint is None
                or self.error_code is not None
            ):
                raise ValueError(
                    "success requires committed work and checkpoint evidence"
                )
        elif self.error_code is None:
            raise ValueError("failed and blocked runs require a safe error code")
        return self


class JobStatusRequest(_Contract):
    """Request for one persisted job's evidence-based status."""

    job_id: str
    request_id: str

    @field_validator("job_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)


class JobStatus(_Contract):
    """Persisted lifecycle, lease, checkpoint, and recovery evidence."""

    job_id: str
    state: Literal["created", "running", "stopped", "failed", "blocked"]
    enabled: bool
    last_run_status: Literal["succeeded", "failed", "blocked"] | None = None
    last_checkpoint: str | None = None
    last_error: str | None = None
    next_run_at: datetime | None = None
    lease_state: Literal["none", "held", "expired"]
    recovery_state: Literal["clean", "required", "recovered", "blocked"]
    request_id: str

    @field_validator("job_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_text")
        return _text(value)

    @field_validator("last_checkpoint", "last_error")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_optional_text")
        return _optional_text(value)

    @field_validator("next_run_at")
    @classmethod
    def _validate_time(cls, value: datetime | None) -> datetime | None:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_time")
        return None if value is None else _utc(value)

    @model_validator(mode="after")
    def _validate_status(self) -> JobStatus:
        """Validate one DATA value or contract invariant."""
        logger.debug("Running DATA function: _validate_status")
        if self.state == "running" and self.lease_state != "held":
            raise ValueError("running status requires a held lease")
        if self.last_run_status == "succeeded" and self.last_checkpoint is None:
            raise ValueError("successful status requires checkpoint evidence")
        if self.last_run_status in {"failed", "blocked"} and self.last_error is None:
            raise ValueError("failed status requires a safe last error")
        if self.recovery_state == "blocked" and self.state != "blocked":
            raise ValueError("blocked recovery requires blocked lifecycle state")
        return self


__all__ = [
    "BackfillChunkRequest",
    "BackfillChunkResult",
    "JobDefinition",
    "JobRunResult",
    "JobStatus",
    "JobStatusRequest",
    "RecoveryReport",
    "ScheduleJobRequest",
]
