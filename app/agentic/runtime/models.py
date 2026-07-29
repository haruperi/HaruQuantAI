"""Provider-neutral evaluated model profiles.

A profile pins exactly one evaluated model. It carries a credential
*reference* resolved by the composition root, never a secret value, and it
never names a floating alias, so a governed workflow cannot silently change
model behind an unchanged profile identifier.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from decimal import Decimal
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

_MAX_SHORT_TEXT = 200

# Floating aliases would permit a silent provider substitution (FR-AGENTIC-008).
_FLOATING_ALIASES = frozenset({"current", "latest", "newest", "preview", "stable"})

# Shapes that indicate a caller passed real secret material where only a
# reference belongs. Agentic holds no provider credential of any kind.
_SECRET_PREFIXES = ("sk-", "sk_", "ghp_", "aws_", "bearer ")
_LONG_OPAQUE = re.compile(r"[A-Za-z0-9+/_-]{40,}\Z")

StructuredOutputMode = Literal["json_schema", "tool_call", "none"]
EvaluationState = Literal["evaluated", "shadow", "disabled"]

# The ordered gates a candidate profile must pass before activation
# (`FR-AGENTIC-009`; `docs/dev/agentic_firm/14_google_adk_and_model_providers.md`).
REQUIRED_UPGRADE_GATES: tuple[str, ...] = (
    "schema_compatibility",
    "tool_compatibility",
    "context_and_output_limits",
    "safety_and_refusal_regression",
    "injection_regression",
    "privacy_and_retention",
    "latency",
    "cost",
    "shadow_comparison",
)


def _text(value: str, field: str, *, limit: int = _MAX_SHORT_TEXT) -> str:
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


def _positive(value: int, field: str) -> int:
    """Validate a positive bound.

    Args:
        value: Candidate bound.
        field: Safe field label for validation.

    Returns:
        Validated bound.

    Raises:
        ValueError: If the bound is not positive.
    """
    if value <= 0:
        message = f"{field} must be positive"
        raise ValueError(message)
    return value


class _RuntimeModel(BaseModel):
    """Private strict immutable behaviour shared by runtime contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class ModelProfile(_RuntimeModel):
    """One evaluated provider-neutral model profile.

    Attributes:
        profile_id: Stable profile identity.
        version: Exact profile version.
        provider: Provider identity.
        model_identifier: Exact pinned model identifier.
        region: Data-processing region.
        credential_ref: Composition-root credential reference, never a secret.
        structured_output_mode: Structured-output mechanism.
        max_context_tokens: Maximum assembled context tokens.
        max_output_tokens: Maximum output tokens for one call.
        max_latency_ms: Maximum acceptable call latency.
        max_cost_per_call: Maximum acceptable cost for one call.
        retention_policy: Provider data-retention policy identity.
        training_use_permitted: Whether provider training use is permitted.
        fallback_profile_id: Optional evaluated fallback profile.
        cost_per_1k_input: Price per 1000 input tokens, when priced.
        cost_per_1k_output: Price per 1000 output tokens, when priced.
        evaluation_state: Current evaluation state.
        enabled: Whether the profile may be invoked.
    """

    profile_id: str
    version: str
    provider: str
    model_identifier: str
    region: str
    credential_ref: str
    structured_output_mode: StructuredOutputMode
    max_context_tokens: int
    max_output_tokens: int
    max_latency_ms: int
    max_cost_per_call: Decimal
    retention_policy: str
    training_use_permitted: bool
    fallback_profile_id: str | None = None
    cost_per_1k_input: Decimal | None = None
    cost_per_1k_output: Decimal | None = None
    evaluation_state: EvaluationState
    enabled: bool

    @field_validator(
        "profile_id",
        "version",
        "provider",
        "region",
        "retention_policy",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded profile reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "model profile reference")

    @field_validator("model_identifier")
    @classmethod
    def _validate_model_identifier(cls, value: str) -> str:
        """Validate that the identifier pins one exact model.

        Args:
            value: Candidate model identifier.

        Returns:
            Validated model identifier.

        Raises:
            ValueError: If the identifier is a floating alias.
        """
        identifier = _text(value, "model_identifier")
        lowered = identifier.lower()
        if "*" in lowered or lowered.rsplit("-", 1)[-1] in _FLOATING_ALIASES:
            message = "model_identifier must pin one exact model, not a floating alias"
            raise ValueError(message)
        return identifier

    @field_validator("credential_ref")
    @classmethod
    def _validate_credential_ref(cls, value: str) -> str:
        """Reject real secret material supplied where a reference belongs.

        Args:
            value: Candidate credential reference.

        Returns:
            Validated credential reference.

        Raises:
            ValueError: If the value looks like secret material.
        """
        reference = _text(value, "credential_ref")
        lowered = reference.lower()
        if any(lowered.startswith(prefix) for prefix in _SECRET_PREFIXES):
            message = "credential_ref must be a reference, not secret material"
            raise ValueError(message)
        if _LONG_OPAQUE.fullmatch(reference) is not None:
            message = "credential_ref must be a reference, not secret material"
            raise ValueError(message)
        return reference

    @field_validator(
        "max_context_tokens",
        "max_output_tokens",
        "max_latency_ms",
    )
    @classmethod
    def _validate_bound(cls, value: int) -> int:
        """Validate one positive profile bound.

        Args:
            value: Candidate bound.

        Returns:
            Validated bound.
        """
        return _positive(value, "model profile bound")

    @field_validator("max_cost_per_call")
    @classmethod
    def _validate_cost(cls, value: Decimal) -> Decimal:
        """Validate the per-call cost ceiling.

        Args:
            value: Candidate cost ceiling.

        Returns:
            Validated cost ceiling.

        Raises:
            ValueError: If the ceiling is non-finite or negative.
        """
        if not value.is_finite() or value < 0:
            message = "max_cost_per_call must be finite and non-negative"
            raise ValueError(message)
        return value

    @field_validator("cost_per_1k_input", "cost_per_1k_output")
    @classmethod
    def _validate_price(cls, value: Decimal | None) -> Decimal | None:
        """Validate one optional token price.

        Pricing is optional on the contract but required wherever an observed
        cost must be derived, so an unpriced profile fails loudly at derivation
        rather than silently reporting a zero cost.

        Args:
            value: Candidate price per 1000 tokens.

        Returns:
            Validated price, or None.

        Raises:
            ValueError: If the price is non-finite or negative.
        """
        if value is None:
            return None
        if not value.is_finite() or value < 0:
            message = "token prices must be finite and non-negative"
            raise ValueError(message)
        return value

    @field_serializer("cost_per_1k_input", "cost_per_1k_output", mode="plain")
    def _serialize_price(self, value: Decimal | None) -> str | None:
        """Serialize one optional token price without precision loss.

        Args:
            value: Exact price, or None.

        Returns:
            Canonical decimal string, or None.
        """
        return None if value is None else str(value)

    @field_validator("fallback_profile_id")
    @classmethod
    def _validate_fallback(cls, value: str | None) -> str | None:
        """Validate the optional evaluated fallback reference.

        Args:
            value: Candidate profile identity.

        Returns:
            Validated profile identity, or None.
        """
        if value is None:
            return None
        return _text(value, "fallback_profile_id")

    @model_validator(mode="after")
    def _validate_profile_consistency(self) -> Self:
        """Validate that an enabled profile is actually evaluated.

        Returns:
            The validated profile.

        Raises:
            ValueError: If a disabled evaluation state is enabled for use, or a
                profile declares itself as its own fallback.
        """
        if self.enabled and self.evaluation_state == "disabled":
            message = "a disabled model profile must not be enabled for invocation"
            raise ValueError(message)
        if self.fallback_profile_id == self.profile_id:
            message = "fallback_profile_id must differ from profile_id"
            raise ValueError(message)
        if self.max_output_tokens > self.max_context_tokens:
            message = "max_output_tokens must not exceed max_context_tokens"
            raise ValueError(message)
        return self

    @field_serializer("max_cost_per_call", mode="plain")
    def _serialize_cost(self, value: Decimal) -> str:
        """Serialize the cost ceiling without precision loss.

        Args:
            value: Exact cost ceiling.

        Returns:
            Canonical decimal string.
        """
        return str(value)


class ModelInvocation(_RuntimeModel):
    """One bounded governed request for a single model call.

    Attributes:
        invocation_id: Stable invocation identity.
        task_id: Owning task identity.
        role_id: Requesting registered role identity.
        composite_instruction_hash: Verified composed instruction digest.
        trusted_context: Bounded trusted structured context.
        untrusted_evidence: Bounded untrusted evidence, never instructions.
        max_output_tokens: Requested output ceiling.
        seed: Optional deterministic seed.
    """

    invocation_id: str
    task_id: str
    role_id: str
    composite_instruction_hash: str
    trusted_context: Mapping[str, str]
    untrusted_evidence: Mapping[str, str]
    max_output_tokens: int
    seed: int | None = None

    @field_validator("invocation_id", "task_id", "role_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded invocation reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "invocation reference")

    @field_validator("composite_instruction_hash")
    @classmethod
    def _validate_instruction_hash(cls, value: str) -> str:
        """Validate the verified composite instruction digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.

        Raises:
            ValueError: If the digest shape is invalid.
        """
        if re.fullmatch(r"[0-9a-f]{64}", value) is None:
            message = "composite_instruction_hash must be lowercase SHA-256 hexadecimal"
            raise ValueError(message)
        return value

    @field_validator("max_output_tokens")
    @classmethod
    def _validate_output_tokens(cls, value: int) -> int:
        """Validate the requested output ceiling.

        Args:
            value: Candidate ceiling.

        Returns:
            Validated ceiling.
        """
        return _positive(value, "max_output_tokens")

    @field_serializer("trusted_context", "untrusted_evidence", mode="plain")
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one bounded invocation mapping.

        Args:
            value: Bounded mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class ModelOutcome(_RuntimeModel):
    """The normalized provider-neutral result of one model call.

    Attributes:
        invocation_id: Invocation this outcome answers.
        status: Completion status.
        output: Structured output when the status is `ok`.
        reasons: Enumerated refusal or failure codes.
        provider: Provider that served the call.
        model_identifier: Exact model that served the call.
        tokens_used: Consumed tokens.
        latency_ms: Observed latency.
        cost: Observed cost.
    """

    invocation_id: str
    status: Literal["ok", "refused", "failed"]
    output: Mapping[str, str] | None = None
    reasons: tuple[str, ...] = ()
    provider: str
    model_identifier: str
    tokens_used: int
    latency_ms: int
    cost: Decimal

    @model_validator(mode="after")
    def _validate_outcome(self) -> Self:
        """Validate the status-to-output agreement.

        Returns:
            The validated outcome.

        Raises:
            ValueError: If the status and output or reasons disagree.
        """
        if self.status == "ok":
            if self.output is None:
                message = "an ok model outcome must carry structured output"
                raise ValueError(message)
            return self
        if self.output is not None:
            message = "a refused or failed model outcome must carry no output"
            raise ValueError(message)
        if not self.reasons:
            message = "a refused or failed model outcome must carry a reason"
            raise ValueError(message)
        return self

    @field_serializer("cost", mode="plain")
    def _serialize_cost(self, value: Decimal) -> str:
        """Serialize the observed cost without precision loss.

        Args:
            value: Exact observed cost.

        Returns:
            Canonical decimal string.
        """
        return str(value)

    @field_serializer("output", mode="plain")
    def _serialize_output(
        self, value: Mapping[str, str] | None
    ) -> dict[str, str] | None:
        """Serialize structured output deterministically.

        Args:
            value: Structured output, or None.

        Returns:
            Plain ordered mapping, or None.
        """
        return None if value is None else dict(value)


def build_model_profile(fields: Mapping[str, object]) -> ModelProfile:
    """Build one evaluated model profile.

    Args:
        fields: Complete profile fields.

    Returns:
        A validated immutable model profile.
    """
    logger.debug("Building model profile %s", fields.get("profile_id"))
    return ModelProfile.model_validate(fields)


def build_model_invocation(fields: Mapping[str, object]) -> ModelInvocation:
    """Build one bounded governed model invocation.

    Args:
        fields: Complete invocation fields.

    Returns:
        A validated immutable model invocation.
    """
    return ModelInvocation.model_validate(fields)


def derive_profile_digest(profile: ModelProfile) -> str:
    """Derive the canonical digest of one model profile.

    Args:
        profile: Validated model profile.

    Returns:
        The canonical profile digest recorded in provenance.
    """
    return canonical_digest(profile.model_dump(mode="json"))
