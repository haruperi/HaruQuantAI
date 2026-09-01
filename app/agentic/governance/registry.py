"""Firm mandate validation and the immutable evaluated role registry.

Startup fails closed: an absent, expired, hash-mismatched, or internally
inconsistent mandate blocks the package, and a roster that grants a role more
authority than its mandate covers is rejected before any model or tool call.

Titles carry no authority here. A coordinator or department lead resolves to
exactly the permission classes and tools its manifest declares and its mandate
covers, so no leadership role can acquire an implicit capability.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from types import MappingProxyType

from app.agentic.governance.models import (
    FORBIDDEN_PERMISSION_CLASSES,
    FirmMandate,
    RoleManifest,
)
from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.kernel.time import utc_now

logger = get_logger(__name__)

# A registered tool identity must name its receiver domain, so a broker-bound
# identity can be rejected structurally rather than by naming convention alone.
_FORBIDDEN_TOOL_PREFIXES: frozenset[str] = frozenset({"brokers.", "broker."})

# Operations no registered Agentic tool may name, regardless of receiver.
_FORBIDDEN_TOOL_TOKENS: frozenset[str] = frozenset(
    {
        "clear_kill_switch",
        "place_order",
        "cancel_order",
        "close_position",
        "modify_position",
        "approve_own",
        "override_mandate",
        "deploy",
    },
)


class RoleRegistry:
    """Immutable validated resolution of role identities to manifests.

    The registry is constructed only through `get_role_registry`, which runs
    the complete startup validation first. Holding an instance therefore proves
    the roster was validated against its mandate.
    """

    def __init__(
        self,
        mandate: FirmMandate,
        manifests: Mapping[str, RoleManifest],
    ) -> None:
        """Store the validated mandate and manifest map.

        Args:
            mandate: Validated firm mandate.
            manifests: Validated role identity to manifest map.
        """
        self._mandate = mandate
        self._manifests: Mapping[str, RoleManifest] = MappingProxyType(dict(manifests))

    def _get_mandate(self) -> FirmMandate:
        """Return the validated mandate.

        Returns:
            The immutable firm mandate.
        """
        return self._mandate

    def _list_roles(self) -> tuple[str, ...]:
        """Return every registered role identity.

        Returns:
            Ordered registered role identities.
        """
        return tuple(sorted(self._manifests))

    def _list_enabled_roles(self) -> tuple[str, ...]:
        """Return every enabled registered role identity.

        Returns:
            Ordered enabled role identities.
        """
        return tuple(
            sorted(
                role_id
                for role_id, manifest in self._manifests.items()
                if manifest.enabled
            ),
        )

    def _resolve(self, role_id: str) -> RoleManifest:
        """Resolve one enabled role manifest.

        Args:
            role_id: Stable role identity.

        Returns:
            The registered enabled manifest.

        Raises:
            ValueError: If the role is unregistered or disabled.
        """
        manifest = self._manifests.get(role_id)
        if manifest is None:
            message = f"unregistered Agentic role: {role_id}"
            raise ValueError(message)
        if not manifest.enabled:
            message = f"disabled Agentic role: {role_id}"
            raise ValueError(message)
        return manifest


def _validate_mandate_window(mandate: FirmMandate, at_time: datetime) -> None:
    """Validate that the mandate is currently in force.

    Args:
        mandate: Candidate firm mandate.
        at_time: Evaluation time.

    Raises:
        ValueError: If the mandate is not yet effective or has expired.
    """
    if at_time < mandate.effective_at:
        message = f"firm mandate {mandate.mandate_id} is not yet effective"
        raise ValueError(message)
    if at_time >= mandate.expires_at:
        message = f"firm mandate {mandate.mandate_id} has expired"
        raise ValueError(message)


def _validate_mandate_integrity(mandate: FirmMandate) -> None:
    """Validate the mandate content digest against its declared material.

    Args:
        mandate: Candidate firm mandate.

    Raises:
        ValueError: If the recomputed digest does not match `content_hash`.
    """
    material = mandate.model_dump(mode="json", exclude={"content_hash", "signature"})
    recomputed = canonical_digest(material)
    if recomputed != mandate.content_hash:
        message = f"firm mandate {mandate.mandate_id} content hash mismatch"
        raise ValueError(message)


def _validate_tool_identity(tool: str) -> None:
    """Reject a tool identity that names a prohibited capability.

    Args:
        tool: Candidate registered tool identity.

    Raises:
        ValueError: If the identity names a broker or critical capability.
    """
    lowered = tool.lower()
    if any(lowered.startswith(prefix) for prefix in _FORBIDDEN_TOOL_PREFIXES):
        message = f"tool {tool} targets Brokers; Agentic has no Brokers dependency"
        raise ValueError(message)
    if any(token in lowered for token in _FORBIDDEN_TOOL_TOKENS):
        message = f"tool {tool} names a capability never registered for an agent"
        raise ValueError(message)


def validate_firm_mandate(
    mandate: FirmMandate,
    at_time: datetime | None = None,
) -> FirmMandate:
    """Validate one firm mandate for completeness, integrity, and validity.

    Args:
        mandate: Candidate firm mandate.
        at_time: Optional evaluation time; current UTC when omitted.

    Returns:
        The validated mandate.

    Raises:
        ValueError: If the mandate is expired, tampered, or internally invalid.
    """
    logger.info(
        "Validating firm mandate %s version %s", mandate.mandate_id, mandate.version
    )
    evaluation_time = at_time if at_time is not None else utc_now()
    _validate_mandate_window(mandate, evaluation_time)
    _validate_mandate_integrity(mandate)
    for tool in mandate.tool_scopes:
        _validate_tool_identity(tool)
    if mandate.limits_profile_id.strip() != mandate.limits_profile_id:
        message = "limits_profile_id must be trimmed"
        raise ValueError(message)
    logger.info("Firm mandate %s validated", mandate.mandate_id)
    return mandate


def _validate_manifest_against_mandate(
    manifest: RoleManifest,
    mandate: FirmMandate,
) -> None:
    """Validate that a manifest claims no authority beyond its mandate.

    Args:
        manifest: Candidate role manifest.
        mandate: Validated firm mandate.

    Raises:
        ValueError: If the manifest exceeds or contradicts the mandate.
    """
    if manifest.owning_feature not in mandate.enabled_features:
        message = (
            f"role {manifest.role_id} owns {manifest.owning_feature}, "
            "which the mandate does not enable"
        )
        raise ValueError(message)
    if manifest.model_profile_id not in mandate.model_profiles:
        message = (
            f"role {manifest.role_id} pins unapproved model profile "
            f"{manifest.model_profile_id}"
        )
        raise ValueError(message)
    if (
        manifest.permitted_fallback is not None
        and manifest.permitted_fallback not in mandate.model_profiles
    ):
        message = (
            f"role {manifest.role_id} declares unapproved fallback profile "
            f"{manifest.permitted_fallback}"
        )
        raise ValueError(message)
    for tool in manifest.tools:
        _validate_tool_identity(tool)
        if tool not in mandate.tool_scopes:
            message = f"role {manifest.role_id} requests unregistered tool {tool}"
            raise ValueError(message)
        granted = mandate.tool_scopes[tool]
        if granted in FORBIDDEN_PERMISSION_CLASSES:
            message = f"tool {tool} declares forbidden permission class {granted}"
            raise ValueError(message)
        if granted not in manifest.permission_classes:
            message = (
                f"role {manifest.role_id} requests tool {tool} requiring {granted}, "
                "which the role does not hold"
            )
            raise ValueError(message)


def _validate_manifest_integrity(manifest: RoleManifest) -> None:
    """Validate the manifest digest against its declared material.

    Args:
        manifest: Candidate role manifest.

    Raises:
        ValueError: If the recomputed digest does not match `manifest_hash`.
    """
    material = manifest.model_dump(
        mode="json",
        exclude={"manifest_hash", "composite_instruction_hash"},
    )
    recomputed = canonical_digest(material)
    if recomputed != manifest.manifest_hash:
        message = f"role manifest {manifest.role_id} hash mismatch"
        raise ValueError(message)


def _validate_composite_instruction(manifest: RoleManifest) -> None:
    """Validate the composed instruction digest.

    The composite instruction is derived from the verified base prompt, the
    manifest digest, and the optional bounded role instruction. Recomputing it
    here means a mutated prompt or manifest cannot reach agent construction.

    Args:
        manifest: Candidate role manifest.

    Raises:
        ValueError: If the recomputed composite digest does not match.
    """
    recomputed = canonical_digest(
        {
            "base_prompt_hash": manifest.base_prompt_hash,
            "manifest_hash": manifest.manifest_hash,
            "role_instruction": manifest.role_instruction,
        },
    )
    if recomputed != manifest.composite_instruction_hash:
        message = f"role manifest {manifest.role_id} composite instruction mismatch"
        raise ValueError(message)


def get_role_registry(
    mandate: FirmMandate,
    manifests: Iterable[RoleManifest],
    at_time: datetime | None = None,
) -> RoleRegistry:
    """Validate the complete roster and return the immutable role registry.

    Args:
        mandate: Candidate firm mandate.
        manifests: Candidate role manifests.
        at_time: Optional evaluation time; current UTC when omitted.

    Returns:
        The validated immutable role registry.

    Raises:
        ValueError: If the mandate or any manifest fails startup validation.
    """
    validated_mandate = validate_firm_mandate(mandate, at_time)
    resolved: dict[str, RoleManifest] = {}
    seen_packages: dict[str, str] = {}
    for manifest in manifests:
        if manifest.role_id in resolved:
            message = f"duplicate Agentic role identity: {manifest.role_id}"
            raise ValueError(message)
        if manifest.agent_package in seen_packages:
            message = (
                f"agent package {manifest.agent_package} is claimed by both "
                f"{seen_packages[manifest.agent_package]} and {manifest.role_id}"
            )
            raise ValueError(message)
        _validate_manifest_integrity(manifest)
        _validate_composite_instruction(manifest)
        _validate_manifest_against_mandate(manifest, validated_mandate)
        resolved[manifest.role_id] = manifest
        seen_packages[manifest.agent_package] = manifest.role_id

    enabled = {manifest.role_id for manifest in resolved.values() if manifest.enabled}
    unknown_enabled = sorted(set(validated_mandate.enabled_roles) - set(resolved))
    if unknown_enabled:
        message = f"mandate enables unregistered roles: {', '.join(unknown_enabled)}"
        raise ValueError(message)
    ungoverned = sorted(enabled - set(validated_mandate.enabled_roles))
    if ungoverned:
        message = f"roles enabled outside the mandate: {', '.join(ungoverned)}"
        raise ValueError(message)

    logger.info(
        "Agentic role registry validated with %d registered and %d enabled roles",
        len(resolved),
        len(enabled),
    )
    return RoleRegistry(validated_mandate, resolved)


def get_registry_mandate(registry: RoleRegistry) -> FirmMandate:
    """Return the validated mandate backing one registry.

    Args:
        registry: Validated role registry.

    Returns:
        The immutable firm mandate.
    """
    return registry._get_mandate()  # noqa: SLF001 - module owns the registry class


def list_registered_roles(registry: RoleRegistry) -> tuple[str, ...]:
    """Return every registered role identity.

    Args:
        registry: Validated role registry.

    Returns:
        Ordered registered role identities.
    """
    return registry._list_roles()  # noqa: SLF001 - module owns the registry class


def list_enabled_roles(registry: RoleRegistry) -> tuple[str, ...]:
    """Return every enabled registered role identity.

    Args:
        registry: Validated role registry.

    Returns:
        Ordered enabled role identities.
    """
    return registry._list_enabled_roles()  # noqa: SLF001 - module owns the class


def resolve_role_manifest(registry: RoleRegistry, role_id: str) -> RoleManifest:
    """Resolve one enabled role manifest through the registry.

    Args:
        registry: Validated role registry.
        role_id: Stable role identity.

    Returns:
        The registered enabled manifest.

    Raises:
        ValueError: If the role is unregistered or disabled.
    """
    return registry._resolve(role_id)  # noqa: SLF001 - module owns the registry class


def normalize_prompt_text(text: str) -> str:
    """Normalize prompt text to a platform-independent form before hashing.

    A prompt artefact checked out with CRLF endings would otherwise hash
    differently from the same file with LF endings, so an integrity check that
    passed on one platform would fail on another. Normalization makes the
    recorded hash portable.

    Args:
        text: Raw prompt artefact text.

    Returns:
        Text with normalized line endings and no trailing whitespace.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def verify_prompt_artifact(manifest: RoleManifest, prompt_path: Path) -> str:
    """Load one package-local prompt artefact and verify its content hash.

    An unverified, missing, or mutated prompt fails closed here, before any
    agent definition is constructed and before any model or tool call.

    Args:
        manifest: Registered role manifest declaring the expected digest.
        prompt_path: Package-local `prompt.md` location.

    Returns:
        The normalized verified prompt text.

    Raises:
        ValueError: If the artefact is missing, empty, or its digest does not
            match the manifest.
    """
    logger.debug("Verifying prompt artefact for role %s", manifest.role_id)
    if not prompt_path.is_file():
        message = f"prompt artefact missing for role {manifest.role_id}"
        raise ValueError(message)
    normalized = normalize_prompt_text(prompt_path.read_text(encoding="utf-8"))
    if not normalized.strip():
        message = f"prompt artefact is empty for role {manifest.role_id}"
        raise ValueError(message)
    digest = canonical_digest(normalized)
    if digest != manifest.base_prompt_hash:
        message = (
            f"prompt artefact hash mismatch for role {manifest.role_id}; "
            "the prompt was mutated or the manifest is stale"
        )
        raise ValueError(message)
    return normalized
