"""Risk contracts module.

Defines RiskDecision, RiskRejection, PositionSizingResult, and RiskAuditEvent.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from app.services.risk.errors import RiskValidationError as ValidationError
from app.utils.standard import SENSITIVE_KEY_PATTERN, canonical_json
from pydantic import BaseModel, Field, field_validator, model_validator

if TYPE_CHECKING:
    from app.services.trading.contracts import OrderIntent

_SCHEMA_VERSION_MIN_PARTS = 2

_TRACE_FIELDS: frozenset[str] = frozenset(
    {"created_at", "request_id", "workflow_id", "correlation_id"}
)


class Contract(BaseModel):
    """Local base model for risk boundary contracts."""

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


class RiskRejection(Contract):
    """Details explaining why a strategy proposal or signal was rejected."""

    code: str = Field(..., description="Stable, deterministic risk error code.")
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Severity of the violation."
    )
    reason: str = Field(..., description="Human-readable reason for rejection.")
    violated_limit: str | None = Field(
        default=None, description="Name of the violated risk limit."
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Audit material proving violation."
    )
    remediation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Actionable steps or parameters for remediation.",
    )


class PositionSizingResult(Contract):
    """Details of the position sizing step."""

    requested_size: float = Field(
        ..., ge=0.0, description="Requested trade volume size in lots."
    )
    approved_size: float = Field(
        ..., ge=0.0, description="Approved trade volume size in lots."
    )
    sizing_method: str = Field(
        ..., description="Position calculator type (e.g. fixed_fractional, kelly)."
    )
    constraints_applied: list[str] = Field(
        default_factory=list,
        description="Limit/constraints evaluated during sizing.",
    )
    risk_contribution: float = Field(
        ...,
        ge=0.0,
        description="Calculated portfolio risk or margin contribution.",
    )


class RiskDecision(Contract):
    """The canonical outcome of the risk review process."""

    decision_id: str = Field(..., description="Unique decision ID.")
    signal_id: str = Field(
        ..., description="Target StrategySignal contract hash or ID."
    )
    approved: bool = Field(..., description="True if proposal passes all risk limits.")
    sizing: PositionSizingResult | None = Field(
        default=None, description="Applied sizing details."
    )
    rejection: RiskRejection | None = Field(
        default=None, description="Applied rejection details."
    )
    approved_order_intent: OrderIntent | None = Field(
        default=None,
        description="Approved OrderIntent produced after all risk gates pass.",
    )
    risk_signature: str | None = Field(
        default=None,
        description="Cryptographic or validation signature of decision state.",
    )

    @model_validator(mode="after")
    def validate_outcome_consistency(self) -> RiskDecision:
        """Enforce mutual exclusivity of approval and rejection states.

        A non-approved decision must carry a ``RiskRejection`` explaining
        why.  An approved decision must not carry a rejection, as that
        would produce an ambiguous audit record.

        Returns:
            The validated RiskDecision instance.

        Raises:
            ValueError: If a non-approved decision has no rejection, or if
                an approved decision carries a rejection object.
        """
        if not self.approved and self.rejection is None:
            raise ValueError("Rejection details must be provided if not approved.")
        if self.approved and self.rejection is not None:
            raise ValueError("Rejection details must not be provided if approved.")
        return self


class RiskAuditEvent(Contract):
    """Event payload generated during risk checks."""

    event_id: str = Field(..., description="Event identifier.")
    event_type: str = Field(default="risk.audit", description="Risk audit type.")
    decision_id: str = Field(..., description="Decision identifier.")
    policy_name: str = Field(..., description="Evaluated policy rule category.")
    action_taken: str = Field(
        ..., description="Outcome action (e.g. block, approve, scale)."
    )
    payload_hash: str = Field(..., description="Hash code of the evaluated signal.")
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Event severity."
    )
