"""Public contract for immutable Agentic mandate validation and scope checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
import hashlib
import json
import unicodedata
from typing import Protocol, runtime_checkable


class MandateOperation(StrEnum):
    VALIDATE = "VALIDATE"
    CHECK_SCOPE = "CHECK_SCOPE"
    INSPECT = "INSPECT"


class MandateOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class BudgetEnvelope:
    max_input_tokens: int
    max_output_tokens: int
    max_model_calls: int
    max_tool_calls: int
    max_cost: Decimal
    deadline_at: datetime | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in ("max_input_tokens", "max_output_tokens", "max_model_calls", "max_tool_calls"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not self.max_cost.is_finite() or self.max_cost < 0:
            raise ValueError("max_cost must be finite and non-negative")
        if self.deadline_at is not None and self.deadline_at.tzinfo is None:
            raise ValueError("deadline_at must be timezone-aware")


@dataclass(frozen=True)
class FirmMandate:
    mandate_id: str
    version: int
    issuer: str
    issued_at: datetime
    effective_at: datetime
    expires_at: datetime
    objectives: tuple[str, ...]
    asset_scopes: tuple[str, ...]
    account_scopes: tuple[str, ...]
    environments: tuple[str, ...]
    enabled_features: tuple[str, ...]
    enabled_roles: tuple[str, ...]
    budgets: BudgetEnvelope
    human_action_policy: tuple[str, ...]
    prohibited_authority: tuple[str, ...]
    fallback_policy: tuple[str, ...]
    policy_refs: tuple[str, ...]
    integrity_digest: str
    signature_ref: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.mandate_id.strip() or not self.issuer.strip():
            raise ValueError("mandate_id and issuer are required")
        if self.version < 1 or self.schema_version != 1:
            raise ValueError("unsupported mandate version")
        if not self.signature_ref.strip():
            raise ValueError("signature_ref is required")
        if any(value.tzinfo is None for value in (self.issued_at, self.effective_at, self.expires_at)):
            raise ValueError("mandate timestamps must be timezone-aware")
        if not self.issued_at <= self.effective_at < self.expires_at:
            raise ValueError("mandate time interval is invalid")
        for field_name in (
            "objectives", "asset_scopes", "account_scopes", "environments", "enabled_features",
            "enabled_roles", "human_action_policy", "prohibited_authority", "fallback_policy", "policy_refs",
        ):
            values = getattr(self, field_name)
            if len(values) != len(set(values)) or any(not item.strip() for item in values):
                raise ValueError(f"{field_name} must contain unique non-blank values")


def _canonical(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite decimal is not canonical")
        return format(value, "f")
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, tuple | list):
        return [_canonical(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in value.items()}
    return value


def mandate_digest(mandate: FirmMandate) -> str:
    """Return canonical SHA-256 digest excluding only the digest field itself."""
    payload = asdict(mandate)
    payload.pop("integrity_digest", None)
    canonical = json.dumps(_canonical(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class ValidateMandateRequest:
    mandate: FirmMandate
    operation: MandateOperation = MandateOperation.VALIDATE


@dataclass(frozen=True)
class CheckMandateScopeRequest:
    mandate: FirmMandate
    feature_id: str
    role_id: str
    environment: str
    account_id: str
    asset_id: str
    requested_budget: BudgetEnvelope
    parent_remaining_budget: BudgetEnvelope | None = None
    operation: MandateOperation = MandateOperation.CHECK_SCOPE


@dataclass(frozen=True)
class InspectMandateRequest:
    mandate: FirmMandate
    operation: MandateOperation = MandateOperation.INSPECT


MandateRequest = ValidateMandateRequest | CheckMandateScopeRequest | InspectMandateRequest


@dataclass(frozen=True)
class MandateAccepted:
    outcome: MandateOutcome
    mandate_ref: str
    effective_limits: BudgetEnvelope
    integrity_digest: str
    checked_at: datetime
    schema_version: int = 1


@dataclass(frozen=True)
class MandateScopeDecision:
    outcome: MandateOutcome
    feature_id: str
    role_id: str
    environment: str
    account_id: str
    asset_id: str
    requested_budget: BudgetEnvelope
    reason_codes: tuple[str, ...]
    effective_limits: BudgetEnvelope | None
    checked_at: datetime
    schema_version: int = 1


MandateView = FirmMandate
MandateResult = MandateAccepted | MandateScopeDecision | MandateView


@runtime_checkable
class MandateCapability(Protocol):
    async def enforce_mandate(self, request: MandateRequest) -> MandateResult:
        ...


__all__ = [
    "BudgetEnvelope", "CheckMandateScopeRequest", "FirmMandate", "InspectMandateRequest",
    "MandateAccepted", "MandateCapability", "MandateOperation", "MandateOutcome",
    "MandateRequest", "MandateResult", "MandateScopeDecision", "MandateView",
    "ValidateMandateRequest", "mandate_digest",
]
