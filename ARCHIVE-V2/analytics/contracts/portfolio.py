"""Portfolio state contracts module.

Defines AccountSnapshot, Position, and PortfolioSnapshot.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any, Literal

from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.utils.normalization import normalize_timestamp
from app.utils.standard import SENSITIVE_KEY_PATTERN, canonical_json
from pydantic import BaseModel, Field, field_validator, model_validator

_SCHEMA_VERSION_MIN_PARTS = 2

_TRACE_FIELDS: frozenset[str] = frozenset(
    {"created_at", "request_id", "workflow_id", "correlation_id"}
)


class Contract(BaseModel):
    """Local base model for analytics portfolio contracts."""

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


class AccountSnapshot(Contract):
    """Snapshot of account cash, margin, and equity metrics.

    Attributes:
        equity: Current net asset equity value.
        balance: Cash balance (excluding floating PnL).
        margin: Used/allocated margin amount.
        free_margin: Available margin for new positions.
        currency: Account denomination currency code.
        leverage: Account leverage multiplier.
        timestamp: UTC ISO 8601 timestamp of this snapshot.
        provider_metadata: Adapter-specific supplemental account fields.
    """

    equity: float = Field(..., description="Current net asset equity value.")
    balance: float = Field(..., description="Account cash balance.")
    margin: float = Field(..., ge=0.0, description="Used/allocated margin amount.")
    free_margin: float = Field(
        ..., description="Available margin for opening positions."
    )
    currency: str = Field(..., description="Account denomination currency code.")
    leverage: int = Field(..., gt=0, description="Account leverage multiplier.")
    timestamp: str = Field(..., description="UTC ISO 8601 calculation timestamp.")
    provider_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Adapter-specific supplemental account metadata.",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_snap_time(cls, v: str) -> str:
        """Validate and normalize snapshot timestamp.

        Args:
            v: The timestamp string to validate.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        try:
            return normalize_timestamp(v).isoformat()
        except (ValueError, TypeError) as e:
            msg = f"Invalid timestamp: {v}"
            raise ValueError(msg) from e


class Position(Contract):
    """Canonical representation of an open trading position."""

    position_id: str = Field(..., description="Durable unique position ID.")
    symbol: str = Field(..., description="Symbol name.")
    side: Literal["buy", "sell"] = Field(..., description="Position direction.")
    quantity: float = Field(..., gt=0.0, description="Position size in lots.")
    average_price: float = Field(..., gt=0.0, description="Average entry price level.")
    unrealized_pnl: float = Field(..., description="Floating profit or loss value.")
    realized_pnl: float = Field(default=0.0, description="Realized transaction PnL.")
    margin: float = Field(default=0.0, ge=0.0, description="Allocated margin size.")
    provider_position_id: str = Field(
        ..., description="Broker ticket reference identifier."
    )
    opened_at: str = Field(..., description="UTC position open timestamp.")
    updated_at: str = Field(..., description="UTC last update timestamp.")

    @field_validator("opened_at", "updated_at")
    @classmethod
    def validate_pos_times(cls, v: str) -> str:
        """Validate and normalize position lifecycle timestamps.

        Args:
            v: Raw timestamp string.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            msg = f"Invalid position timestamp: {v}"
            raise ValueError(msg) from e


class PortfolioSnapshot(Contract):
    """Standardized composite snapshot of the entire portfolio state."""

    account: AccountSnapshot = Field(..., description="Account snapshot metrics.")
    positions: list[Position] = Field(
        default_factory=list, description="List of currently active positions."
    )
    pending_exposure: float = Field(
        default=0.0, description="Value of unfilled order exposure."
    )
    risk_budget: float = Field(
        default=0.0, ge=0.0, description="Allocated risk budget utilization."
    )
    correlation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Calculated asset correlation details.",
    )
    freshness_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Freshness validation timestamps map.",
    )
