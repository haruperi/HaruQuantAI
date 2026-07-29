"""Private central resolution point for every bounded Agentic limit.

This module declares the versioned limits profiles and resolves one by
identifier. It declares values; it does not import them from a capability, so
the dependency direction stays acyclic.

Every limit is deterministic and model-non-overridable. An agent may request a
smaller bound; nothing in the package may raise one. An unregistered profile
identifier fails closed rather than falling back to a permissive default.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.utils import get_logger

logger = get_logger(__name__)


class AgenticLimitsProfile(BaseModel):
    """One immutable versioned bound set for an Agentic deployment.

    Attributes:
        profile_id: Stable versioned profile identity.
        max_participants: Maximum deliberation participants for one run.
        max_fan_out: Maximum parallel branches from one workflow node.
        max_rounds: Maximum bounded rebuttal rounds.
        max_retries: Maximum bounded transient retries for one node.
        max_active_runs: Maximum concurrently active workflow runs.
        deadline_seconds: Maximum wall-clock lifetime of one run.
        context_token_budget: Maximum assembled context tokens.
        output_token_budget: Maximum model output tokens for one call.
        max_schema_repairs: Maximum structured-output repair attempts.
        working_memory_ttl_seconds: Working-memory expiry.
        evidence_retention_days: Immutable evidence retention.
        audit_retention_days: Operational audit retention.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    profile_id: str
    max_participants: int
    max_fan_out: int
    max_rounds: int
    max_retries: int
    max_active_runs: int
    deadline_seconds: int
    context_token_budget: int
    output_token_budget: int
    max_schema_repairs: int
    working_memory_ttl_seconds: int
    evidence_retention_days: int
    audit_retention_days: int

    @model_validator(mode="after")
    def _validate_bounds(self) -> Self:
        """Reject a profile that would remove a bound.

        Returns:
            The validated profile.

        Raises:
            ValueError: If a bound is absent, non-positive, or negative.
        """
        logger.debug("Validating Agentic limits profile %s", self.profile_id)
        if not self.profile_id or self.profile_id != self.profile_id.strip():
            message = "profile_id must be non-empty trimmed text"
            raise ValueError(message)
        positive = (
            "max_participants",
            "max_fan_out",
            "max_rounds",
            "max_active_runs",
            "deadline_seconds",
            "context_token_budget",
            "output_token_budget",
            "working_memory_ttl_seconds",
            "evidence_retention_days",
            "audit_retention_days",
        )
        for field in positive:
            if getattr(self, field) <= 0:
                message = f"{field} must be positive"
                raise ValueError(message)
        # Retries and schema repairs may legitimately be zero: a feature may
        # specify that a class of failure is never retried at all.
        for field in ("max_retries", "max_schema_repairs"):
            if getattr(self, field) < 0:
                message = f"{field} must be non-negative"
                raise ValueError(message)
        return self


# The default rebuttal allowance is one round; a mandate may reduce it but no
# agent may raise it. Schema repair is limited to one attempt.
_SANDBOX_V1: Final = AgenticLimitsProfile(
    profile_id="agentic-limits-sandbox-v1",
    max_participants=8,
    max_fan_out=4,
    max_rounds=1,
    max_retries=2,
    max_active_runs=4,
    deadline_seconds=1_800,
    context_token_budget=120_000,
    output_token_budget=8_000,
    max_schema_repairs=1,
    working_memory_ttl_seconds=3_600,
    evidence_retention_days=365,
    audit_retention_days=730,
)

_RESEARCH_V1: Final = AgenticLimitsProfile(
    profile_id="agentic-limits-research-v1",
    max_participants=12,
    max_fan_out=6,
    max_rounds=2,
    max_retries=3,
    max_active_runs=8,
    deadline_seconds=3_600,
    context_token_budget=200_000,
    output_token_budget=16_000,
    max_schema_repairs=1,
    working_memory_ttl_seconds=7_200,
    evidence_retention_days=365,
    audit_retention_days=730,
)

_REGISTERED_PROFILES: Final[Mapping[str, AgenticLimitsProfile]] = MappingProxyType(
    {
        _SANDBOX_V1.profile_id: _SANDBOX_V1,
        _RESEARCH_V1.profile_id: _RESEARCH_V1,
    },
)


def get_registered_limits_profiles() -> tuple[str, ...]:
    """Return every registered limits-profile identifier.

    Returns:
        Ordered registered profile identifiers.
    """
    return tuple(sorted(_REGISTERED_PROFILES))


def resolve_limits_profile(profile_id: str) -> AgenticLimitsProfile:
    """Resolve one registered versioned limits profile.

    Args:
        profile_id: Versioned limits-profile identity.

    Returns:
        The registered immutable limits profile.

    Raises:
        ValueError: If the profile is not registered.
    """
    logger.debug("Resolving Agentic limits profile %s", profile_id)
    profile = _REGISTERED_PROFILES.get(profile_id)
    if profile is None:
        message = f"unregistered Agentic limits profile: {profile_id}"
        raise ValueError(message)
    return profile
