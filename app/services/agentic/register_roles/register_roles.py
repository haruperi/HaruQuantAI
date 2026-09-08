"""Immutable Agentic role contribution registry."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import timezone
from decimal import Decimal
import hashlib
import json
import unicodedata
import uuid

from app.contracts.agentic.mandate import (
    BudgetEnvelope,
    CheckMandateScopeRequest,
    MandateCapability,
    MandateOutcome,
)
from app.contracts.agentic.roles import (
    RoleContribution,
    RoleEligibilityDecision,
    RoleEligibilityRequest,
    RoleRegistration,
)


def _normalize_prompt(value: str) -> str:
    """Normalize role prompt bytes deterministically."""
    return unicodedata.normalize(
        "NFC",
        value.replace("\r\n", "\n").replace("\r", "\n"),
    ).lstrip("\ufeff")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _seal(contribution: RoleContribution) -> RoleContribution:
    """Validate and seal one immutable role contribution."""
    if contribution.version < 1 or contribution.source_generation < 1:
        raise ValueError("ROLE_VERSION_INVALID")
    if not contribution.role_id.strip() or not contribution.model_profile_id.strip():
        raise ValueError("ROLE_IDENTITY_INVALID")
    if contribution.eligible_until.tzinfo is None:
        raise ValueError("ROLE_ELIGIBILITY_TIME_INVALID")
    if contribution.model_profile_id.lower() in {"latest", "best", "auto", "current"}:
        raise ValueError("ROLE_MODEL_IDENTITY_FLOATING")
    prompt = _normalize_prompt(contribution.prompt_text)
    if len(contribution.declared_tools) != len(set(contribution.declared_tools)):
        raise ValueError("ROLE_TOOLS_DUPLICATED")
    if len(contribution.conflicts) != len(set(contribution.conflicts)):
        raise ValueError("ROLE_CONFLICTS_DUPLICATED")
    prompt_hash = _hash_text(prompt)
    manifest = asdict(contribution)
    for key in ("prompt_hash", "manifest_hash", "composite_hash", "prompt_text"):
        manifest.pop(key, None)
    manifest_json = json.dumps(
        manifest,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    manifest_hash = _hash_text(manifest_json)
    composite_hash = _hash_text(prompt_hash + ":" + manifest_hash)
    if contribution.prompt_hash and contribution.prompt_hash != prompt_hash:
        raise ValueError("ROLE_PROMPT_HASH_INVALID")
    if contribution.manifest_hash and contribution.manifest_hash != manifest_hash:
        raise ValueError("ROLE_MANIFEST_HASH_INVALID")
    if contribution.composite_hash and contribution.composite_hash != composite_hash:
        raise ValueError("ROLE_COMPOSITE_HASH_INVALID")
    return replace(
        contribution,
        prompt_text=prompt,
        prompt_hash=prompt_hash,
        manifest_hash=manifest_hash,
        composite_hash=composite_hash,
    )


class RegisterRolesService:
    """Scoped immutable role registry with generation-bound disposal."""

    def __init__(self, mandate: MandateCapability) -> None:
        self._mandate = mandate
        self._roles: dict[tuple[str, int], tuple[RoleContribution, str]] = {}
        self._closed = False

    async def register_role(self, contribution: RoleContribution) -> RoleRegistration:
        self._ensure_open()
        sealed = _seal(contribution)
        key = (sealed.role_id, sealed.version)
        existing = self._roles.get(key)
        if existing is not None:
            if existing[0] != sealed:
                raise ValueError("ROLE_IDENTITY_VERSION_CONFLICT")
            return RoleRegistration(existing[0], existing[1])
        disposer = (
            f"role-disposer-{sealed.source_generation}-{uuid.uuid4().hex}"
        )
        self._roles[key] = (sealed, disposer)
        return RoleRegistration(sealed, disposer)

    async def dispose_role(self, registration: RoleRegistration) -> bool:
        self._ensure_open()
        key = (
            registration.contribution.role_id,
            registration.contribution.version,
        )
        current = self._roles.get(key)
        if current is None or current[1] != registration.disposer_id:
            return False
        if (
            current[0].source_generation
            != registration.contribution.source_generation
        ):
            return False
        del self._roles[key]
        return True

    async def resolve_role(
        self,
        request: RoleEligibilityRequest,
    ) -> RoleEligibilityDecision:
        self._ensure_open()
        candidates = [
            item[0]
            for key, item in self._roles.items()
            if key[0] == request.role_id
        ]
        if not candidates:
            return RoleEligibilityDecision(False, None, ("ROLE_NOT_REGISTERED",))
        role = max(candidates, key=lambda item: item.version)
        reasons: list[str] = []
        if role.revoked:
            reasons.append("ROLE_ELIGIBILITY_REVOKED")
        if role.evaluation_only:
            reasons.append("ROLE_EVALUATION_ONLY")
        if (
            request.now.tzinfo is None
            or request.now.astimezone(timezone.utc)
            >= role.eligible_until.astimezone(timezone.utc)
        ):
            reasons.append("ROLE_ELIGIBILITY_EXPIRED")
        if any(conflict in request.mandate.enabled_roles for conflict in role.conflicts):
            reasons.append("ROLE_CONFLICT")
        zero = BudgetEnvelope(0, 0, 0, 0, Decimal("0"))
        mandate = await self._mandate.enforce_mandate(
            CheckMandateScopeRequest(
                request.mandate,
                request.feature_id,
                role.role_id,
                request.environment,
                request.account_id,
                request.asset_id,
                zero,
            )
        )
        if getattr(mandate, "outcome", None) is not MandateOutcome.ALLOWED:
            reasons.append("ROLE_MANDATE_DENIED")
        unique_reasons = tuple(dict.fromkeys(reasons))
        return RoleEligibilityDecision(
            not unique_reasons,
            role if not unique_reasons else None,
            unique_reasons,
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("register-roles service is closed")

    def close(self) -> None:
        """Withdraw all scoped role contributions."""
        self._closed = True
        self._roles.clear()
