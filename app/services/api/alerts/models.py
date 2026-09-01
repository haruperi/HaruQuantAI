"""Bounded channel-neutral critical operational alert contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, Protocol

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.kernel.identity import validate_id
from app.kernel.redaction import is_sensitive_key

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_MAX_MAPPING_ITEMS = 8
_MAX_TEXT_LENGTH = 256
_MAX_SUMMARY_LENGTH = 512


class CriticalAlertTrigger(StrEnum):
    """Closed authoritative trigger set for critical operational alerts."""

    RISK_KILL_SWITCH_ACTIVATED = "risk.kill_switch_activated"
    TRADING_BROKER_STATE_UNKNOWN = "trading.broker_state_unknown"


class CriticalAlertError(RuntimeError):
    """Bounded critical-alert boundary failure."""

    def __init__(self, code: str, details: str) -> None:
        """Initialize one safe critical-alert error.

        Args:
            code: Stable uppercase failure code.
            details: Bounded non-sensitive explanation.
        """
        self.code = _required_text(code, "code", limit=64)
        self.details = _required_text(details, "details", limit=_MAX_TEXT_LENGTH)
        super().__init__(f"{self.code}: {self.details}")


def _required_text(value: str, field_name: str, *, limit: int) -> str:
    """Validate one required bounded string.

    Args:
        value: Candidate text.
        field_name: Field name for deterministic errors.
        limit: Maximum allowed character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the value is blank, padded, or too long.
    """
    if not value or value != value.strip() or len(value) > limit:
        message = f"{field_name} must be trimmed and at most {limit} characters"
        raise ValueError(message)
    return value


def _utc(value: datetime, field_name: str) -> datetime:
    """Require one aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field_name: Field name for deterministic errors.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is naive or non-UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field_name} must be aware UTC"
        raise ValueError(message)
    return value


def _freeze_mapping(value: Mapping[str, str], field_name: str) -> Mapping[str, str]:
    """Validate and freeze one bounded redacted text mapping.

    Args:
        value: Candidate mapping.
        field_name: Field name for deterministic errors.

    Returns:
        Immutable validated mapping.

    Raises:
        ValueError: If the mapping is unbounded or contains sensitive fields.
    """
    if len(value) > _MAX_MAPPING_ITEMS:
        message = f"{field_name} exceeds {_MAX_MAPPING_ITEMS} entries"
        raise ValueError(message)
    frozen: dict[str, str] = {}
    for key, item in value.items():
        checked_key = _required_text(key, f"{field_name} key", limit=64)
        if is_sensitive_key(checked_key):
            message = f"{field_name} contains a protected key"
            raise ValueError(message)
        frozen[checked_key] = _required_text(
            item,
            f"{field_name} value",
            limit=_MAX_TEXT_LENGTH,
        )
    return MappingProxyType(frozen)


class CriticalOperationalAlert(BaseModel):
    """Immutable bounded alert derived from one authoritative safety source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.critical_operational_alert.v1"] = (
        "api.critical_operational_alert.v1"
    )
    alert_id: str
    trigger: CriticalAlertTrigger
    severity: Literal["critical"] = "critical"
    title: str
    summary: str
    scope: Mapping[str, str]
    source_schema_id: str
    source_id: str
    source_version: str
    occurred_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str
    redaction_applied: Literal[True] = True

    @field_validator("alert_id")
    @classmethod
    def _validate_alert_id(cls, value: str) -> str:
        """Validate deterministic SHA-256 alert identity.

        Args:
            value: Candidate alert identifier.

        Returns:
            Validated identifier.

        Raises:
            ValueError: If the identifier is not lowercase SHA-256.
        """
        if _SHA256_PATTERN.fullmatch(value) is None:
            raise ValueError("alert_id must be lowercase SHA-256")
        return value

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        """Validate fixed bounded alert title.

        Args:
            value: Candidate title.

        Returns:
            Validated title.
        """
        return _required_text(value, "title", limit=_MAX_TEXT_LENGTH)

    @field_validator("summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        """Validate bounded alert summary.

        Args:
            value: Candidate summary.

        Returns:
            Validated summary.
        """
        return _required_text(value, "summary", limit=_MAX_SUMMARY_LENGTH)

    @field_validator("source_schema_id", "source_id", "source_version")
    @classmethod
    def _validate_source_text(cls, value: str) -> str:
        """Validate bounded source identity text.

        Args:
            value: Candidate source text.

        Returns:
            Validated source text.
        """
        return _required_text(value, "source identity", limit=_MAX_TEXT_LENGTH)

    @field_validator("request_id", "workflow_id", "correlation_id")
    @classmethod
    def _validate_trace(cls, value: str, info: object) -> str:
        """Validate canonical trace identity.

        Args:
            value: Candidate trace identifier.
            info: Pydantic field metadata.

        Returns:
            Validated trace identifier.
        """
        field_name = str(getattr(info, "field_name", "trace_id"))
        prefix = {
            "request_id": "req",
            "workflow_id": "wf",
            "correlation_id": "cor",
        }[field_name]
        return validate_id(value, expected_prefix=prefix)

    @field_validator("occurred_at")
    @classmethod
    def _validate_occurred_at(cls, value: datetime) -> datetime:
        """Validate authoritative source time.

        Args:
            value: Candidate source time.

        Returns:
            Validated UTC time.
        """
        return _utc(value, "occurred_at")

    @field_validator("scope", mode="after")
    @classmethod
    def _validate_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate bounded alert scope.

        Args:
            value: Candidate scope mapping.

        Returns:
            Immutable validated scope.
        """
        return _freeze_mapping(value, "scope")

    @field_serializer("scope")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable scope through the HTTP boundary.

        Args:
            value: Immutable validated scope.

        Returns:
            JSON-compatible mapping copy.
        """
        return dict(value)

    @model_validator(mode="after")
    def _validate_fixed_title(self) -> CriticalOperationalAlert:
        """Validate that title is fixed by trigger.

        Returns:
            Validated alert.

        Raises:
            ValueError: If the title does not match the closed trigger.
        """
        expected = {
            CriticalAlertTrigger.RISK_KILL_SWITCH_ACTIVATED: (
                "Risk kill switch activated"
            ),
            CriticalAlertTrigger.TRADING_BROKER_STATE_UNKNOWN: ("Broker state unknown"),
        }[self.trigger]
        if self.title != expected:
            raise ValueError("alert title must match its trigger")
        return self


class CriticalAlertDeliveryResult(BaseModel):
    """Visible immutable result of one critical-alert sink attempt."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.critical_alert_delivery_result.v1"] = (
        "api.critical_alert_delivery_result.v1"
    )
    delivery_id: str
    alert_id: str
    status: Literal["delivered", "failed"]
    attempted_at: datetime
    failure_code: Literal["ALERT_DELIVERY_FAILED"] | None
    request_id: str
    workflow_id: str
    correlation_id: str

    @field_validator("delivery_id", "alert_id")
    @classmethod
    def _validate_hash_id(cls, value: str) -> str:
        """Validate deterministic SHA-256 identity.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.

        Raises:
            ValueError: If identity is malformed.
        """
        if _SHA256_PATTERN.fullmatch(value) is None:
            raise ValueError("delivery identities must be lowercase SHA-256")
        return value

    @field_validator("request_id", "workflow_id", "correlation_id")
    @classmethod
    def _validate_trace(cls, value: str, info: object) -> str:
        """Validate canonical delivery trace identity.

        Args:
            value: Candidate trace identifier.
            info: Pydantic field metadata.

        Returns:
            Validated trace identifier.
        """
        field_name = str(getattr(info, "field_name", "trace_id"))
        prefix = {
            "request_id": "req",
            "workflow_id": "wf",
            "correlation_id": "cor",
        }[field_name]
        return validate_id(value, expected_prefix=prefix)

    @field_validator("attempted_at")
    @classmethod
    def _validate_attempted_at(cls, value: datetime) -> datetime:
        """Validate delivery attempt time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "attempted_at")

    @model_validator(mode="after")
    def _validate_outcome(self) -> CriticalAlertDeliveryResult:
        """Validate status and failure-code consistency.

        Returns:
            Validated result.

        Raises:
            ValueError: If status and failure evidence conflict.
        """
        if (self.status == "failed") != (self.failure_code is not None):
            raise ValueError("delivery status and failure_code are inconsistent")
        return self


class CriticalAlertSink(Protocol):
    """Injected channel-neutral exactly-once delivery boundary."""

    def __call__(
        self,
        alert: CriticalOperationalAlert,
        *,
        idempotency_key: str,
    ) -> None:
        """Attempt delivery of one alert.

        Args:
            alert: Validated bounded alert.
            idempotency_key: Deterministic alert identity.
        """
        ...


__all__ = (
    "CriticalAlertDeliveryResult",
    "CriticalAlertError",
    "CriticalAlertSink",
    "CriticalAlertTrigger",
    "CriticalOperationalAlert",
)
