"""Public contract for immutable Agentic role contributions and eligibility."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.contracts.agentic.mandate import FirmMandate


@dataclass(frozen=True, slots=True)
class RoleContribution:
    role_id: str
    version: int
    prompt_text: str
    input_schema: str
    output_schema: str
    declared_tools: tuple[str, ...]
    model_profile_id: str
    limits_ref: str
    conflicts: tuple[str, ...]
    refusal_policy_ref: str
    evaluation_ref: str
    eligible_until: datetime
    evaluation_only: bool = False
    revoked: bool = False
    source_generation: int = 1
    prompt_hash: str = ""
    manifest_hash: str = ""
    composite_hash: str = ""


@dataclass(frozen=True, slots=True)
class RoleRegistration:
    contribution: RoleContribution
    disposer_id: str


@dataclass(frozen=True, slots=True)
class RoleEligibilityRequest:
    role_id: str
    mandate: FirmMandate
    feature_id: str
    environment: str
    account_id: str
    asset_id: str
    now: datetime


@dataclass(frozen=True, slots=True)
class RoleEligibilityDecision:
    eligible: bool
    contribution: RoleContribution | None
    reason_codes: tuple[str, ...]


@runtime_checkable
class RolesCapability(Protocol):
    async def register_role(self, contribution: RoleContribution) -> RoleRegistration: ...
    async def dispose_role(self, registration: RoleRegistration) -> bool: ...
    async def resolve_role(self, request: RoleEligibilityRequest) -> RoleEligibilityDecision: ...


__all__ = [
    "RoleContribution", "RoleEligibilityDecision", "RoleEligibilityRequest", "RoleRegistration",
    "RolesCapability",
]
