"""DATA-owned bounded audit query and page contracts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final, Literal

from pydantic import ConfigDict, field_validator, model_validator

from app.services.data.contracts._base import DataContractModel, TracedOpenContract
from app.services.data.contracts.validation import validate_request_id
from app.utils import AuditEvent, logger

AUDIT_QUERY_HARD_MAX_LIMIT: Final = 1_000


def _text(value: str) -> str:
    """Validate one non-empty trimmed DATA query value."""
    logger.debug("Validating DATA audit query text")
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _utc(value: datetime) -> datetime:
    """Validate one aware UTC DATA query timestamp."""
    logger.debug("Validating DATA audit query timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


class AuditEventQuery(DataContractModel):
    """Receiver-owned bounded authorized audit event query."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["data.audit_event_query.v1"] = "data.audit_event_query.v1"
    start: datetime
    end: datetime
    domain: str | None = None
    action: str | None = None
    principal_id: str | None = None
    correlation_id: str | None = None
    cursor: str | None = None
    limit: int
    request_id: str

    @field_validator("start", "end")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one query timestamp."""
        logger.debug("Validating DATA audit query time")
        return _utc(value)

    @field_validator("domain", "action", "principal_id", "correlation_id", "cursor")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one optional audit query filter."""
        logger.debug("Validating optional DATA audit query filter")
        return None if value is None else _text(value)

    @field_validator("limit")
    @classmethod
    def _validate_limit(cls, value: int) -> int:
        """Validate the hard audit page bound."""
        logger.debug("Validating DATA audit query limit")
        if not 0 < value <= AUDIT_QUERY_HARD_MAX_LIMIT:
            raise ValueError("limit is outside the audit query hard bound")
        return value

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate the query trace identifier."""
        logger.debug("Validating DATA audit query request ID")
        validate_request_id(value)
        return value

    @model_validator(mode="after")
    def _validate_range(self) -> AuditEventQuery:
        """Validate ordered query bounds."""
        logger.debug("Validating DATA audit query range")
        if self.start >= self.end:
            raise ValueError("start must precede end")
        return self


class AuditEventPage(DataContractModel):
    """Receiver-owned deterministically ordered audit event page."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["data.audit_event_page.v1"] = "data.audit_event_page.v1"
    events: tuple[AuditEvent, ...]
    next_cursor: str | None = None
    request_id: str

    @field_validator("next_cursor")
    @classmethod
    def _validate_cursor(cls, value: str | None) -> str | None:
        """Validate one optional opaque cursor."""
        logger.debug("Validating DATA audit page cursor")
        return None if value is None else _text(value)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate the page trace identifier."""
        logger.debug("Validating DATA audit page request ID")
        validate_request_id(value)
        return value

    @model_validator(mode="after")
    def _validate_order(self) -> AuditEventPage:
        """Require deterministic timestamp and event identity order."""
        logger.debug("Validating DATA audit page order")
        ordered = tuple(
            sorted(self.events, key=lambda event: (event.timestamp, event.event_id))
        )
        if self.events != ordered:
            raise ValueError("events must be ordered by timestamp and event_id")
        return self


class AuditPersistenceResult(TracedOpenContract):
    """Represent an idempotent durable audit-event persistence outcome."""

    event_id: str
    persisted: bool
    idempotent: bool
    request_id: str

    @field_validator("event_id")
    @classmethod
    def _validate_event_id(cls, value: str) -> str:
        """Validate the persisted audit-event identifier."""
        return _text(value)

    @field_validator("request_id")
    @classmethod
    def _validate_persistence_request_id(cls, value: str) -> str:
        """Validate the persistence trace identifier."""
        return _text(value)


__all__ = [
    "AUDIT_QUERY_HARD_MAX_LIMIT",
    "AuditEventPage",
    "AuditEventQuery",
    "AuditPersistenceResult",
]
