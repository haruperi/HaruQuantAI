"""Provider-neutral governed model invocation.

`invoke_model` is the single governed entry point for one model call. It
enforces the pinned profile's bounds before the call and verifies the served
model identity after it, so a provider cannot silently substitute a different
model behind an unchanged profile identifier.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.composition.logging import get_logger

if TYPE_CHECKING:
    from app.agentic.runtime.models import (
        ModelInvocation,
        ModelOutcome,
        ModelProfile,
    )

logger = get_logger(__name__)


@runtime_checkable
class ModelGateway(Protocol):
    """One provider adapter capable of serving a governed invocation."""

    def invoke(
        self,
        profile: ModelProfile,
        invocation: ModelInvocation,
    ) -> ModelOutcome:
        """Serve one governed invocation.

        Args:
            profile: Pinned evaluated model profile.
            invocation: Bounded governed invocation.

        Returns:
            The normalized provider-neutral outcome.
        """
        ...


def _validate_profile_ready(profile: ModelProfile) -> None:
    """Validate that the profile may be invoked at all.

    Args:
        profile: Candidate model profile.

    Raises:
        ValueError: If the profile is disabled or not evaluated.
    """
    if not profile.enabled:
        message = f"model profile {profile.profile_id} is disabled"
        raise ValueError(message)
    if profile.evaluation_state != "evaluated":
        message = (
            f"model profile {profile.profile_id} is {profile.evaluation_state}; "
            "only an evaluated profile may serve a governed invocation"
        )
        raise ValueError(message)


def _validate_invocation_bounds(
    profile: ModelProfile,
    invocation: ModelInvocation,
) -> None:
    """Validate the invocation against the pinned profile bounds.

    Args:
        profile: Pinned evaluated model profile.
        invocation: Candidate invocation.

    Raises:
        ValueError: If the invocation exceeds a declared profile bound.
    """
    if invocation.max_output_tokens > profile.max_output_tokens:
        message = (
            f"invocation requests {invocation.max_output_tokens} output tokens, "
            f"exceeding the profile ceiling of {profile.max_output_tokens}"
        )
        raise ValueError(message)


def _validate_served_identity(
    profile: ModelProfile,
    outcome: ModelOutcome,
) -> None:
    """Validate that the served model matches the pinned model.

    Args:
        profile: Pinned evaluated model profile.
        outcome: Provider outcome.

    Raises:
        ValueError: If the provider served a different model or provider.
    """
    if outcome.provider != profile.provider:
        message = (
            f"provider substitution detected: pinned {profile.provider}, "
            f"served {outcome.provider}"
        )
        raise ValueError(message)
    if outcome.model_identifier != profile.model_identifier:
        message = (
            f"model substitution detected: pinned {profile.model_identifier}, "
            f"served {outcome.model_identifier}"
        )
        raise ValueError(message)


def _validate_observed_limits(
    profile: ModelProfile,
    outcome: ModelOutcome,
) -> None:
    """Validate the observed call against the profile's declared ceilings.

    Args:
        profile: Pinned evaluated model profile.
        outcome: Provider outcome.

    Raises:
        ValueError: If the observed cost or latency exceeded its ceiling.
    """
    if outcome.cost > profile.max_cost_per_call:
        message = (
            f"observed cost {outcome.cost} exceeded the profile ceiling "
            f"{profile.max_cost_per_call}"
        )
        raise ValueError(message)
    if outcome.latency_ms > profile.max_latency_ms:
        message = (
            f"observed latency {outcome.latency_ms}ms exceeded the profile ceiling "
            f"{profile.max_latency_ms}ms"
        )
        raise ValueError(message)


def invoke_model(
    gateway: ModelGateway,
    profile: ModelProfile,
    invocation: ModelInvocation,
) -> ModelOutcome:
    """Perform one governed structured model invocation.

    Args:
        gateway: Injected provider adapter.
        profile: Pinned evaluated model profile.
        invocation: Bounded governed invocation.

    Returns:
        The normalized provider-neutral outcome.

    Raises:
        ValueError: If the profile is ineligible, the invocation exceeds a
            declared bound, or the provider substituted a model.
    """
    logger.info(
        "Invoking model profile %s for role %s",
        profile.profile_id,
        invocation.role_id,
    )
    _validate_profile_ready(profile)
    _validate_invocation_bounds(profile, invocation)
    outcome = gateway.invoke(profile, invocation)
    if outcome.invocation_id != invocation.invocation_id:
        message = "provider outcome does not answer the submitted invocation"
        raise ValueError(message)
    _validate_served_identity(profile, outcome)
    _validate_observed_limits(profile, outcome)
    logger.info(
        "Model profile %s returned %s in %dms",
        profile.profile_id,
        outcome.status,
        outcome.latency_ms,
    )
    return outcome
