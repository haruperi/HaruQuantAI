"""Audit trail contracts module.

Defines AuditEvent.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any, Literal

from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.utils.standard import SENSITIVE_KEY_PATTERN, canonical_json
from pydantic import BaseModel, Field, field_validator, model_validator

_SCHEMA_VERSION_MIN_PARTS = 2

_TRACE_FIELDS: frozenset[str] = frozenset(
    {"created_at", "request_id", "workflow_id", "correlation_id"}
)


class Contract(BaseModel):
    """Local base model for analytics audit contracts."""

    schema_version: str = Field(default="1.0.0")
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    request_id: str | None = None
    workflow_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata_structure(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata namespacing and secret safety."""
        for key in value:
            if not isinstance(key, str):
                raise TypeError("Metadata keys must be strings.")
            if "." not in key and ":" not in key:
                raise ValueError("Metadata keys must be namespaced.")
            if SENSITIVE_KEY_PATTERN.search(key):
                raise ValueError("Metadata key matches sensitive key pattern.")
        try:
            canonical_json(value)
        except (TypeError, ValueError) as exc:
            msg = f"Metadata is not deterministically serializable: {exc}"
            raise ValueError(msg) from exc
        return value

    @model_validator(mode="after")
    def validate_trace_identifiers(self) -> Contract:
        """Validate trace identifier fields."""
        for name in ("request_id", "workflow_id", "correlation_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                msg = f"{name} must be a non-empty string or None."
                raise ValueError(msg)
        return self

    def to_json(self) -> str:
        """Serialize this contract to deterministic canonical JSON."""
        try:
            return canonical_json(self.model_dump())
        except (TypeError, ValueError) as exc:
            msg = f"Failed to serialize contract: {exc}"
            raise ValidationError(msg) from exc

    def content_hash(self) -> str:
        """Calculate a stable SHA256 hash over business-data fields only."""
        payload = {
            key: value
            for key, value in self.model_dump().items()
            if key not in _TRACE_FIELDS
        }
        try:
            serialized = canonical_json(payload)
        except (TypeError, ValueError) as exc:
            msg = f"Failed to compute content hash: {exc}"
            raise ValidationError(msg) from exc
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def contract_hash(self) -> str:
        """Calculate SHA256 hash over the full serialized contract."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def check_compatibility(self, target_version: str) -> bool:
        """Check whether this contract version is compatible with a target."""
        try:
            current_parts = [int(part) for part in self.schema_version.split(".")]
            target_parts = [int(part) for part in target_version.split(".")]
            return (
                len(current_parts) >= _SCHEMA_VERSION_MIN_PARTS
                and len(target_parts) >= _SCHEMA_VERSION_MIN_PARTS
                and current_parts[0] == target_parts[0]
                and current_parts[1] >= target_parts[1]
            )
        except ValueError:
            return False


class AuditEvent(Contract):
    """The canonical audit log record contract.

    The event timestamp is carried by ``Contract.created_at``, which is
    set at construction time to UTC now. Consumers building audit timelines
    should read ``created_at`` as the authoritative event time.

    Attributes:
        event_id: Unique audit event identifier.
        event_type: Dotted category string (e.g. ``risk.policy_change``).
        severity: Event severity level.
        actor: User, service account, or agent initiating the action.
        subject: Target entity being modified or queried.
        action: Specific operation performed (e.g. ``approve``, ``execute``).
        evidence: References to verification payloads or data hashes.
        redacted_payload_hash: SHA256 hash of the fully redacted operation
            details, suitable for audit record integrity checks.
    """

    event_id: str = Field(..., description="Unique audit event ID.")
    event_type: str = Field(
        ...,
        description=("Audit event category (e.g. risk.policy_change, trading.fill)."),
    )
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Audit event severity level."
    )
    actor: str = Field(
        ...,
        description="The user, service account, or agent initiating action.",
    )
    subject: str = Field(
        ..., description="The target entity being modified or queried."
    )
    action: str = Field(
        ...,
        description=(
            "The specific operation performed (e.g. approve, reject, execute)."
        ),
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="References to verification payloads or data hashes.",
    )
    redacted_payload_hash: str | None = Field(
        default=None,
        description="SHA256 hash of the fully redacted operation details.",
    )
