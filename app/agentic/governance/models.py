"""Firm mandate and role manifest contracts.

The mandate is the immutable, versioned operating envelope for one Agentic
deployment. The role manifest is the immutable declaration of one registered
specialized role. Neither may be authored or amended by an agent.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FEATURE_ID = re.compile(r"FEAT-AGT-(0[1-9]|1[0-9]|2[0-2])\Z")
_AGENT_PACKAGE = re.compile(r"agents/[a-z][a-z0-9_]*/[a-z][a-z0-9_]*\Z")

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64

MandateEnvironment = Literal["development", "sandbox", "paper", "live"]

# Permission classes an agent may hold. `controlled_mutation` and `critical`
# are deliberately absent: they are never granted to an agent.
PermissionClass = Literal[
    "read_evidence",
    "compute_deterministic",
    "write_working",
    "write_staging",
    "submit_proposal",
]

# Classes that must never appear in a mandate or manifest. Presence is a
# registry validation failure, not a runtime check.
FORBIDDEN_PERMISSION_CLASSES: frozenset[str] = frozenset(
    {"controlled_mutation", "critical"},
)

# Every mandate denies these regardless of what it declares.
UNIVERSAL_PROHIBITIONS: tuple[str, ...] = (
    "broker_credential_access",
    "broker_native_mutation",
    "mandate_modification",
    "kill_switch_clearing",
    "self_approval",
    "approval_delegation",
    "production_code_mutation",
    "hot_loading",
    "unbounded_discussion",
    "unbounded_spend",
    "unverified_evidence_use",
    "receipt_as_fill",
)

# Scope wildcards would make an account or environment bound meaningless.
_WILDCARDS: frozenset[str] = frozenset({"*", "all", "any", ""})


def _text(value: str, field: str, *, limit: int = _MAX_TEXT) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.
        limit: Maximum permitted character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > limit:
        message = f"{field} must not exceed {limit} characters"
        raise ValueError(message)
    return value


def _utc(value: datetime, field: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Safe field label for validation.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the value is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field} must be aware UTC"
        raise ValueError(message)
    return value


def _hash(value: str, field: str) -> str:
    """Validate lowercase SHA-256 hexadecimal.

    Args:
        value: Candidate digest.
        field: Safe field label for validation.

    Returns:
        Validated digest.

    Raises:
        ValueError: If the digest shape is invalid.
    """
    if _SHA256.fullmatch(value) is None:
        message = f"{field} must be lowercase SHA-256 hexadecimal"
        raise ValueError(message)
    return value


def _tuple(
    value: tuple[str, ...], field: str, *, required: bool = True
) -> tuple[str, ...]:
    """Validate a bounded ordered tuple of trimmed entries.

    Args:
        value: Candidate entries.
        field: Safe field label for validation.
        required: Whether at least one entry is required.

    Returns:
        Validated entries.

    Raises:
        ValueError: If the tuple is empty when required, oversized, or duplicated.
    """
    if required and not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    validated = tuple(_text(item, field, limit=_MAX_SHORT_TEXT) for item in value)
    if len(set(validated)) != len(validated):
        message = f"{field} must not repeat an entry"
        raise ValueError(message)
    return validated


def _scope_mapping(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze a governed scope mapping.

    A wildcard value would defeat the purpose of declaring a scope, so it is
    rejected rather than normalized.

    Args:
        value: Candidate scope mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only scope mapping.

    Raises:
        ValueError: If the mapping is empty, oversized, or wildcard-scoped.
    """
    logger.debug("Validating Agentic governance scope %s", field)
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} keys"
        raise ValueError(message)
    frozen: dict[str, str] = {}
    for key, item in sorted(value.items()):
        safe_key = _text(key, field, limit=_MAX_SHORT_TEXT)
        safe_value = _text(item, field, limit=_MAX_SHORT_TEXT)
        if safe_value.strip().lower() in _WILDCARDS:
            message = f"{field} must not declare a wildcard scope"
            raise ValueError(message)
        frozen[safe_key] = safe_value
    return MappingProxyType(frozen)


def _budget_mapping(value: Mapping[str, Decimal], field: str) -> Mapping[str, Decimal]:
    """Validate and freeze a bounded budget mapping.

    Args:
        value: Candidate budget mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only budget mapping.

    Raises:
        ValueError: If the mapping is empty or a limit is invalid.
    """
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    frozen: dict[str, Decimal] = {}
    for key, item in sorted(value.items()):
        safe_key = _text(key, field, limit=_MAX_SHORT_TEXT)
        if not item.is_finite() or item < 0:
            message = f"{field} limits must be finite and non-negative"
            raise ValueError(message)
        frozen[safe_key] = item
    return MappingProxyType(frozen)


class _GovernanceModel(BaseModel):
    """Private strict immutable behaviour shared by governance contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class RoleManifest(_GovernanceModel):
    """Immutable declaration of one registered specialized role.

    A manifest binds a role to exactly one owning feature and one registered
    agent package, and pins the prompt and instruction hashes verified before
    agent construction.

    Attributes:
        role_id: Stable role identity.
        version: Exact manifest version.
        owning_feature: Canonical `FEAT-AGT-NN` owning feature.
        department: Firm department grouping.
        agent_package: Registered `agents/<department>/<agent_name>` path.
        description: Bounded role description.
        objective: Bounded role objective.
        expertise_boundary: Bounded statement of what the role does not cover.
        supported_assets: Supported asset classes.
        refusal_conditions: Declared conditions requiring refusal.
        input_schema_id: Namespaced input schema identity.
        output_schema_id: Namespaced output schema identity.
        base_prompt_hash: Package-local `prompt.md` digest.
        manifest_hash: This manifest's digest.
        composite_instruction_hash: Composed instruction digest.
        role_instruction: Optional bounded role-specific instruction.
        model_profile_id: Approved evaluated model-profile identity.
        permitted_fallback: Optional evaluated fallback profile identity.
        tools: Registered tool identities the role may request.
        permission_classes: Permission classes the role may hold.
        data_requirements: Governed evidence the role requires.
        freshness_seconds: Maximum evidence age the role accepts.
        budgets: Bounded per-role limits.
        evaluation_set_id: Versioned evaluation-set identity.
        baseline_id: Simpler baseline the role must beat.
        enabled: Whether the role is currently activated.
    """

    role_id: str
    version: str
    owning_feature: str
    department: str
    agent_package: str
    description: str
    objective: str
    expertise_boundary: str
    supported_assets: tuple[str, ...]
    refusal_conditions: tuple[str, ...]
    input_schema_id: str
    output_schema_id: str
    base_prompt_hash: str
    manifest_hash: str
    composite_instruction_hash: str
    role_instruction: str | None = None
    model_profile_id: str
    permitted_fallback: str | None = None
    tools: tuple[str, ...]
    permission_classes: tuple[PermissionClass, ...]
    data_requirements: tuple[str, ...]
    freshness_seconds: int
    budgets: Mapping[str, Decimal]
    evaluation_set_id: str
    baseline_id: str
    enabled: bool

    @field_validator(
        "role_id",
        "version",
        "department",
        "input_schema_id",
        "output_schema_id",
        "model_profile_id",
        "evaluation_set_id",
        "baseline_id",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded manifest reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "role manifest reference", limit=_MAX_SHORT_TEXT)

    @field_validator("description", "objective", "expertise_boundary")
    @classmethod
    def _validate_prose(cls, value: str) -> str:
        """Validate one bounded manifest prose field.

        Args:
            value: Candidate text.

        Returns:
            Validated text.
        """
        return _text(value, "role manifest text")

    @field_validator("owning_feature")
    @classmethod
    def _validate_owning_feature(cls, value: str) -> str:
        """Validate the canonical owning feature identity.

        Args:
            value: Candidate feature identity.

        Returns:
            Validated feature identity.

        Raises:
            ValueError: If the identity is not a canonical `FEAT-AGT-NN` value.
        """
        if _FEATURE_ID.fullmatch(value) is None:
            message = "owning_feature must be a canonical FEAT-AGT-NN identity"
            raise ValueError(message)
        return value

    @field_validator("agent_package")
    @classmethod
    def _validate_agent_package(cls, value: str) -> str:
        """Validate the registered leaf agent package path.

        Args:
            value: Candidate package path.

        Returns:
            Validated package path.

        Raises:
            ValueError: If the path is not a registered leaf agent package.
        """
        if _AGENT_PACKAGE.fullmatch(value) is None:
            message = "agent_package must be agents/<department>/<agent_name>"
            raise ValueError(message)
        return value

    @field_validator(
        "base_prompt_hash",
        "manifest_hash",
        "composite_instruction_hash",
    )
    @classmethod
    def _validate_integrity_hash(cls, value: str) -> str:
        """Validate one manifest integrity digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "role manifest digest")

    @field_validator("supported_assets", "refusal_conditions", "data_requirements")
    @classmethod
    def _validate_required_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required manifest declaration tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _tuple(value, "role manifest declaration")

    @field_validator("tools")
    @classmethod
    def _validate_tools(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the declared tool identities.

        A role legitimately holds no tools, so an empty tuple is permitted.

        Args:
            value: Candidate tool identities.

        Returns:
            Validated tool identities.
        """
        return _tuple(value, "role manifest tools", required=False)

    @field_validator("permission_classes")
    @classmethod
    def _validate_permission_classes(
        cls,
        value: tuple[PermissionClass, ...],
    ) -> tuple[PermissionClass, ...]:
        """Validate the declared permission classes.

        Args:
            value: Candidate permission classes.

        Returns:
            Validated permission classes.

        Raises:
            ValueError: If a class is absent or repeated.
        """
        if not value:
            message = "permission_classes is required"
            raise ValueError(message)
        if len(set(value)) != len(value):
            message = "permission_classes must not repeat a class"
            raise ValueError(message)
        return value

    @field_validator("role_instruction")
    @classmethod
    def _validate_role_instruction(cls, value: str | None) -> str | None:
        """Validate the optional bounded role-specific instruction.

        Args:
            value: Candidate instruction.

        Returns:
            Validated instruction, or None.
        """
        if value is None:
            return None
        return _text(value, "role_instruction")

    @field_validator("permitted_fallback")
    @classmethod
    def _validate_fallback(cls, value: str | None) -> str | None:
        """Validate the optional evaluated fallback profile.

        Args:
            value: Candidate profile identity.

        Returns:
            Validated profile identity, or None.
        """
        if value is None:
            return None
        return _text(value, "permitted_fallback", limit=_MAX_SHORT_TEXT)

    @field_validator("freshness_seconds")
    @classmethod
    def _validate_freshness(cls, value: int) -> int:
        """Validate the declared evidence freshness bound.

        Args:
            value: Candidate freshness bound.

        Returns:
            Validated freshness bound.

        Raises:
            ValueError: If the bound is not positive.
        """
        if value <= 0:
            message = "freshness_seconds must be positive"
            raise ValueError(message)
        return value

    @field_validator("budgets")
    @classmethod
    def _validate_budgets(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Validate and freeze the declared role budgets.

        Args:
            value: Candidate budget mapping.

        Returns:
            Frozen ordered budget mapping.
        """
        return _budget_mapping(value, "role manifest budgets")

    @field_serializer("budgets", mode="plain")
    def _serialize_budgets(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize role budgets without precision loss.

        Args:
            value: Frozen budget mapping.

        Returns:
            Plain ordered mapping of canonical decimal strings.
        """
        return {key: str(item) for key, item in value.items()}


class FirmMandate(_GovernanceModel):
    """Immutable versioned operating envelope for one Agentic deployment.

    Attributes:
        mandate_id: Stable mandate identity.
        version: Exact mandate version.
        content_hash: Mandate content digest.
        signature: Owner signature or trusted identity proof.
        environment: Approved mandate environment.
        effective_at: UTC validity start.
        expires_at: UTC validity end.
        owner_principal: Authenticated mandate owner.
        objectives: Permitted research and advisory objectives.
        asset_scopes: Governed asset, venue, instrument, and account scope.
        enabled_features: Canonical enabled `FEAT-AGT-NN` capabilities.
        enabled_roles: Enabled versioned role identities.
        model_profiles: Approved evaluated model-profile identities.
        tool_scopes: Registered tool identity to permission class.
        limits_profile_id: Versioned workflow limits profile.
        budgets: Bounded deployment budgets.
        approval_policy: Actions requiring explicit approval.
        retention_policy: Retention class to retention days.
        prohibited_actions: Explicit universal denials.
        fallback_policy: Behaviour when a governed precondition fails.
    """

    mandate_id: str
    version: str
    content_hash: str
    signature: str
    environment: MandateEnvironment
    effective_at: datetime
    expires_at: datetime
    owner_principal: str
    objectives: tuple[str, ...]
    asset_scopes: Mapping[str, str]
    enabled_features: tuple[str, ...]
    enabled_roles: tuple[str, ...]
    model_profiles: tuple[str, ...]
    tool_scopes: Mapping[str, str]
    limits_profile_id: str
    budgets: Mapping[str, Decimal]
    approval_policy: tuple[str, ...]
    retention_policy: Mapping[str, str]
    prohibited_actions: tuple[str, ...]
    fallback_policy: Literal["refuse", "degrade", "cancel", "safe_drain"]

    @field_validator(
        "mandate_id",
        "version",
        "owner_principal",
        "limits_profile_id",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded mandate reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "mandate reference", limit=_MAX_SHORT_TEXT)

    @field_validator("content_hash")
    @classmethod
    def _validate_content_hash(cls, value: str) -> str:
        """Validate the mandate content digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "content_hash")

    @field_validator("signature")
    @classmethod
    def _validate_signature(cls, value: str) -> str:
        """Validate the mandate signature material.

        Args:
            value: Candidate signature.

        Returns:
            Validated signature.
        """
        return _text(value, "signature", limit=_MAX_SHORT_TEXT)

    @field_validator("effective_at", "expires_at")
    @classmethod
    def _validate_validity(cls, value: datetime) -> datetime:
        """Validate one mandate validity timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "mandate validity")

    @field_validator("objectives", "enabled_roles", "model_profiles", "approval_policy")
    @classmethod
    def _validate_required_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required mandate declaration tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _tuple(value, "mandate declaration")

    @field_validator("enabled_features")
    @classmethod
    def _validate_enabled_features(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the enabled canonical feature identities.

        Args:
            value: Candidate feature identities.

        Returns:
            Validated feature identities.

        Raises:
            ValueError: If an entry is not a canonical `FEAT-AGT-NN` identity.
        """
        entries = _tuple(value, "enabled_features")
        for entry in entries:
            if _FEATURE_ID.fullmatch(entry) is None:
                message = "enabled_features entries must be FEAT-AGT-NN identities"
                raise ValueError(message)
        return entries

    @field_validator("prohibited_actions")
    @classmethod
    def _validate_prohibited_actions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate that every universal prohibition is present.

        A mandate may deny more than the universal set; it may never deny less.

        Args:
            value: Candidate prohibitions.

        Returns:
            Validated prohibitions.

        Raises:
            ValueError: If a universal prohibition is absent.
        """
        entries = _tuple(value, "prohibited_actions")
        missing = sorted(set(UNIVERSAL_PROHIBITIONS) - set(entries))
        if missing:
            message = f"prohibited_actions must deny: {', '.join(missing)}"
            raise ValueError(message)
        return entries

    @field_validator("asset_scopes")
    @classmethod
    def _validate_asset_scopes(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the governed asset scope.

        Args:
            value: Candidate scope mapping.

        Returns:
            Frozen ordered scope mapping.
        """
        return _scope_mapping(value, "asset_scopes")

    @field_validator("retention_policy")
    @classmethod
    def _validate_retention_policy(
        cls,
        value: Mapping[str, str],
    ) -> Mapping[str, str]:
        """Validate and freeze the declared retention policy.

        Args:
            value: Candidate retention mapping.

        Returns:
            Frozen ordered retention mapping.
        """
        return _scope_mapping(value, "retention_policy")

    @field_validator("tool_scopes")
    @classmethod
    def _validate_tool_scopes(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the registered tool permission map.

        Args:
            value: Candidate tool-to-permission mapping.

        Returns:
            Frozen ordered tool mapping.

        Raises:
            ValueError: If a tool declares a forbidden permission class.
        """
        frozen = _scope_mapping(value, "tool_scopes")
        for tool, permission in frozen.items():
            if permission in FORBIDDEN_PERMISSION_CLASSES:
                message = (
                    f"tool_scopes must not grant {permission} (tool {tool}); "
                    "controlled_mutation and critical are never granted to an agent"
                )
                raise ValueError(message)
        return frozen

    @field_validator("budgets")
    @classmethod
    def _validate_budgets(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Validate and freeze the declared deployment budgets.

        Args:
            value: Candidate budget mapping.

        Returns:
            Frozen ordered budget mapping.
        """
        return _budget_mapping(value, "mandate budgets")

    @field_serializer("asset_scopes", "retention_policy", "tool_scopes", mode="plain")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one mandate mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)

    @field_serializer("budgets", mode="plain")
    def _serialize_budgets(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize mandate budgets without precision loss.

        Args:
            value: Frozen budget mapping.

        Returns:
            Plain ordered mapping of canonical decimal strings.
        """
        return {key: str(item) for key, item in value.items()}

    @model_validator(mode="after")
    def _validate_mandate_consistency(self) -> Self:
        """Validate the mandate validity window and internal agreement.

        Returns:
            The validated mandate.

        Raises:
            ValueError: If the validity window or declared references disagree.
        """
        logger.debug("Validating firm mandate %s consistency", self.mandate_id)
        if self.effective_at >= self.expires_at:
            message = "effective_at must precede expires_at"
            raise ValueError(message)
        if self.environment == "live":
            # A live mandate is only meaningful alongside a separately approved
            # system configuration; the mandate itself never grants live access.
            logger.warning(
                "Firm mandate %s declares the live environment; receiver and "
                "system controls remain mandatory",
                self.mandate_id,
            )
        return self


_PLACEHOLDER_DIGEST = "0" * 64


def _compose_instruction_digest(
    base_prompt_hash: str,
    manifest_hash: str,
    role_instruction: str | None,
) -> str:
    """Derive the composite instruction digest.

    The composite binds the verified base prompt, the manifest identity, and
    the optional bounded role instruction, so mutating any one of them changes
    the digest recorded in provenance.

    Args:
        base_prompt_hash: Verified `prompt.md` digest.
        manifest_hash: Manifest digest.
        role_instruction: Optional bounded role-specific instruction.

    Returns:
        The composite instruction digest.
    """
    return canonical_digest(
        {
            "base_prompt_hash": base_prompt_hash,
            "manifest_hash": manifest_hash,
            "role_instruction": role_instruction,
        },
    )


def build_role_manifest(fields: Mapping[str, object]) -> RoleManifest:
    """Build one role manifest with its integrity digests computed.

    The caller supplies every declared field except `manifest_hash` and
    `composite_instruction_hash`, which are derived here so a manifest cannot
    be registered with a digest that does not match its own content.

    Args:
        fields: Complete manifest fields excluding the derived digests.

    Returns:
        A validated manifest carrying matching integrity digests.

    Raises:
        ValueError: If a derived digest field was supplied by the caller.
    """
    derived = {"manifest_hash", "composite_instruction_hash"}
    supplied = derived & set(fields)
    if supplied:
        message = f"derived digests must not be supplied: {', '.join(sorted(supplied))}"
        raise ValueError(message)
    logger.debug("Building role manifest %s", fields.get("role_id"))
    draft = RoleManifest.model_validate(
        {
            **fields,
            "manifest_hash": _PLACEHOLDER_DIGEST,
            "composite_instruction_hash": _PLACEHOLDER_DIGEST,
        },
    )
    manifest_hash = canonical_digest(
        draft.model_dump(mode="json", exclude=derived),
    )
    composite = _compose_instruction_digest(
        draft.base_prompt_hash,
        manifest_hash,
        draft.role_instruction,
    )
    return draft.model_copy(
        update={
            "manifest_hash": manifest_hash,
            "composite_instruction_hash": composite,
        },
    )


def build_firm_mandate(fields: Mapping[str, object], signature: str) -> FirmMandate:
    """Build one firm mandate with its content digest computed.

    Args:
        fields: Complete mandate fields excluding `content_hash` and `signature`.
        signature: Owner signature or trusted identity proof.

    Returns:
        A validated mandate carrying a matching content digest.

    Raises:
        ValueError: If a derived field was supplied by the caller.
    """
    derived = {"content_hash", "signature"}
    supplied = derived & set(fields)
    if supplied:
        message = f"derived fields must not be supplied: {', '.join(sorted(supplied))}"
        raise ValueError(message)
    logger.debug("Building firm mandate %s", fields.get("mandate_id"))
    draft = FirmMandate.model_validate(
        {**fields, "content_hash": _PLACEHOLDER_DIGEST, "signature": signature},
    )
    content_hash = canonical_digest(draft.model_dump(mode="json", exclude=derived))
    return draft.model_copy(update={"content_hash": content_hash})
