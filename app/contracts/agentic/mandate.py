"""Public domain contract for Agentic mandate enforcement."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.contracts.common.wire_model import WireModel, as_utc


class BudgetEnvelope(WireModel):
    """Finite resource budget envelope for Agentic operations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_input_tokens: int = 0
    max_output_tokens: int = 0
    max_model_calls: int = 0
    max_tool_calls: int = 0
    max_cost: float = 0.0
    deadline_at: datetime | None = None
    schema_version: int = 1

    @field_validator(
        "max_input_tokens",
        "max_output_tokens",
        "max_model_calls",
        "max_tool_calls",
        mode="before",
    )
    @classmethod
    def _validate_integers(cls, v: object) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            msg = f"Budget count must be an integer, got {type(v).__name__}"
            raise TypeError(msg)
        if v < 0:
            msg = f"Budget count cannot be negative: {v}"
            raise ValueError(msg)
        return v

    @field_validator("max_cost", mode="before")
    @classmethod
    def _validate_cost(cls, v: object) -> float:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            msg = f"max_cost must be a float or int, got {type(v).__name__}"
            raise TypeError(msg)
        fval = float(v)
        if fval < 0.0:
            msg = f"max_cost cannot be negative: {fval}"
            raise ValueError(msg)
        if not math.isfinite(fval):
            msg = f"max_cost must be finite: {fval}"
            raise ValueError(msg)
        return fval

    @field_validator("deadline_at", mode="after")
    @classmethod
    def _validate_deadline(cls, v: datetime | None) -> datetime | None:
        if v is not None:
            return as_utc(v)
        return None


SYSTEM_PROHIBITED_AUTHORITIES: frozenset[str] = frozenset(
    {
        "broker_credentials",
        "order_construction",
        "risk_approval",
        "kill_switch_clear",
        "live_deployment",
        "receiver_authority",
    }
)


class FirmMandate(WireModel):
    """Immutable firm mandate defining bounded operational authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mandate_id: str
    version: int = 1
    issuer: str
    issued_at: datetime
    effective_at: datetime
    expires_at: datetime
    objectives: tuple[str, ...] = ()
    asset_scopes: tuple[str, ...] = ()
    account_scopes: tuple[str, ...] = ()
    environments: tuple[str, ...] = ()
    enabled_features: tuple[str, ...] = ()
    enabled_roles: tuple[str, ...] = ()
    budgets: BudgetEnvelope = Field(default_factory=BudgetEnvelope)
    human_action_policy: str = "required"
    prohibited_authority: tuple[str, ...] = (
        "broker_credentials",
        "order_construction",
        "risk_approval",
        "kill_switch_clear",
        "live_deployment",
        "receiver_authority",
    )
    fallback_policy: str = "fail_closed"
    policy_refs: tuple[str, ...] = ()
    integrity_digest: str = ""
    signature_ref: str | None = None
    schema_version: int = 1

    @field_validator("issued_at", "effective_at", "expires_at", mode="after")
    @classmethod
    def _validate_timestamps(cls, v: datetime) -> datetime:
        return as_utc(v)

    @model_validator(mode="after")
    def _validate_temporal_order(self) -> FirmMandate:
        if not (self.issued_at <= self.effective_at < self.expires_at):
            msg = (
                f"Invalid temporal interval: issued_at={self.issued_at.isoformat()} "
                f"effective_at={self.effective_at.isoformat()} "
                f"expires_at={self.expires_at.isoformat()}"
            )
            raise ValueError(msg)
        return self


def compute_mandate_digest(mandate: FirmMandate | dict[str, object]) -> str:
    """Compute deterministic SHA-256 integrity digest over canonical mandate fields.

    Args:
        mandate: FirmMandate instance or dictionary of fields.

    Returns:
        Hex-encoded SHA-256 digest string.
    """
    raw: dict[str, object] = (
        mandate.model_dump() if isinstance(mandate, FirmMandate) else dict(mandate)
    )

    raw.pop("integrity_digest", None)
    raw.pop("signature_ref", None)

    def _normalize(val: object) -> object:
        if isinstance(val, WireModel):
            return _normalize(val.model_dump())
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=UTC).isoformat()
            return val.astimezone(UTC).isoformat()
        if isinstance(val, (list, tuple)):
            return [_normalize(x) for x in val]
        if isinstance(val, dict):
            return {k: _normalize(v) for k, v in sorted(val.items())}
        return val

    normalized = {k: _normalize(v) for k, v in sorted(raw.items())}
    canonical_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class ValidateMandateRequest(WireModel):
    """Request to validate mandate integrity and time effectiveness."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    op: Literal["VALIDATE"] = "VALIDATE"
    mandate: FirmMandate


class CheckMandateScopeRequest(WireModel):
    """Request to verify operation scope against a mandate and active system rules."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    op: Literal["CHECK_SCOPE"] = "CHECK_SCOPE"
    mandate: FirmMandate
    requested_feature: str | None = None
    requested_role: str | None = None
    requested_environment: str | None = None
    requested_account: str | None = None
    requested_asset: str | None = None
    requested_budget: BudgetEnvelope | None = None
    parent_budget: BudgetEnvelope | None = None
    auth_account: str | None = None
    prohibited_authority_requested: tuple[str, ...] = ()


class InspectMandateRequest(WireModel):
    """Request to inspect mandate contents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    op: Literal["INSPECT"] = "INSPECT"
    mandate: FirmMandate


type MandateRequest = Annotated[
    ValidateMandateRequest | CheckMandateScopeRequest | InspectMandateRequest,
    Field(discriminator="op"),
]


class MandateAccepted(WireModel):
    """Successful validation decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: Literal["ACCEPTED"] = "ACCEPTED"
    mandate_ref: str
    effective_limits: dict[str, object] = Field(default_factory=dict)
    integrity_digest: str
    checked_at: datetime
    schema_version: int = 1


class MandateScopeDecision(WireModel):
    """Scope evaluation decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: Literal["ALLOWED", "DENIED"]
    requested_feature: str | None = None
    requested_role: str | None = None
    requested_environment: str | None = None
    requested_account: str | None = None
    requested_asset: str | None = None
    requested_budget: BudgetEnvelope | None = None
    reason_codes: tuple[str, ...] = ()
    effective_limits: dict[str, object] = Field(default_factory=dict)
    checked_at: datetime
    schema_version: int = 1


class MandateRefused(WireModel):
    """Typed refusal or failure outcome."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: Literal["REFUSED", "INVALID", "UNAVAILABLE"]
    reason_codes: tuple[str, ...] = ()
    checked_at: datetime
    schema_version: int = 1


class MandateView(WireModel):
    """Inspection view of a firm mandate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: Literal["VIEW"] = "VIEW"
    mandate: FirmMandate
    checked_at: datetime
    schema_version: int = 1


type MandateResponse = (
    MandateAccepted | MandateScopeDecision | MandateRefused | MandateView
)


@runtime_checkable
class EnforceMandateCapability(Protocol):
    """Public capability protocol for Mandate Enforcement."""

    async def enforce_mandate(self, request: MandateRequest) -> MandateResponse:
        """Evaluate one mandate validation, scope check, or inspection operation.

        Args:
            request: Validated mandate request.

        Returns:
            MandateAccepted, MandateScopeDecision, MandateRefused, or MandateView.
        """
        ...


__all__ = [
    "SYSTEM_PROHIBITED_AUTHORITIES",
    "BudgetEnvelope",
    "CheckMandateScopeRequest",
    "EnforceMandateCapability",
    "FirmMandate",
    "InspectMandateRequest",
    "MandateAccepted",
    "MandateRefused",
    "MandateRequest",
    "MandateResponse",
    "MandateScopeDecision",
    "MandateView",
    "ValidateMandateRequest",
    "compute_mandate_digest",
]
