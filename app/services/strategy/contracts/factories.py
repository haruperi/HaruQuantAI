"""Function-only constructors for Strategy contract values."""

from __future__ import annotations

from app.services.strategy.contracts.enums import (
    StrategyEnvironment,
    StrategyLifecycleStatus,
    StrategyTimingPolicy,
)
from app.services.strategy.contracts.execution import (
    StrategyDecision,
    StrategyEvent,
    StrategyExecutionContext,
    StrategyExecutionResult,
)
from app.services.strategy.contracts.manifest import StrategyManifest
from app.services.strategy.contracts.outcomes import StrategyMutationResult
from app.services.strategy.contracts.policy import StrategyValidationPolicy
from app.services.strategy.contracts.references import (
    StrategyConfig,
    StrategyRef,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.requests import (
    StrategyParameterUpdateRequest,
    StrategyRegistrationRequest,
)
from app.services.strategy.contracts.signals import (
    StrategySignal,
    StrategySignalEvidence,
)


def create_strategy_config(**kwargs: object) -> StrategyConfig:
    """Create one declarative Strategy configuration.

    Args:
        **kwargs: Validated Strategy configuration field values.

    Returns:
        Declarative Strategy configuration.
    """
    return StrategyConfig.model_validate(kwargs)


def create_strategy_ref(**kwargs: object) -> StrategyRef:
    """Create one unresolved immutable Strategy reference.

    Args:
        **kwargs: Validated Strategy reference field values.

    Returns:
        Unresolved immutable Strategy reference.
    """
    return StrategyRef.model_validate(kwargs)


def create_validated_strategy_ref(**kwargs: object) -> ValidatedStrategyRef:
    """Create one validated immutable Strategy reference.

    Args:
        **kwargs: Validated resolved-reference field values.

    Returns:
        Validated immutable Strategy reference.
    """
    return ValidatedStrategyRef.model_validate(kwargs)


def create_validated_strategy_config(**kwargs: object) -> ValidatedStrategyConfig:
    """Create one validated immutable Strategy configuration.

    Args:
        **kwargs: Validated normalized-configuration field values.

    Returns:
        Validated immutable Strategy configuration.
    """
    return ValidatedStrategyConfig.model_validate(kwargs)


def create_strategy_manifest(**kwargs: object) -> StrategyManifest:
    """Create one immutable Strategy manifest.

    Args:
        **kwargs: Validated Strategy manifest field values.

    Returns:
        Immutable Strategy manifest.
    """
    return StrategyManifest.model_validate(kwargs)


def create_strategy_validation_policy(**kwargs: object) -> StrategyValidationPolicy:
    """Create one explicit Strategy validation policy.

    Args:
        **kwargs: Validated Strategy policy field values.

    Returns:
        Explicit Strategy validation policy.
    """
    return StrategyValidationPolicy.model_validate(kwargs)


def create_strategy_registration_request(
    **kwargs: object,
) -> StrategyRegistrationRequest:
    """Create one governed Strategy registration request.

    Args:
        **kwargs: Validated registration-request field values.

    Returns:
        Governed Strategy registration request.
    """
    return StrategyRegistrationRequest.model_validate(kwargs)


def create_strategy_parameter_update_request(
    **kwargs: object,
) -> StrategyParameterUpdateRequest:
    """Create one governed Strategy parameter-update request.

    Args:
        **kwargs: Validated parameter-update field values.

    Returns:
        Governed Strategy parameter-update request.
    """
    return StrategyParameterUpdateRequest.model_validate(kwargs)


def create_strategy_execution_context(**kwargs: object) -> StrategyExecutionContext:
    """Create one fixed Strategy execution context.

    Args:
        **kwargs: Validated execution-context field values.

    Returns:
        Fixed Strategy execution context.
    """
    return StrategyExecutionContext.model_validate(kwargs)


def create_strategy_event(**kwargs: object) -> StrategyEvent:
    """Create one immutable typed Strategy event.

    Args:
        **kwargs: Validated Strategy event field values.

    Returns:
        Immutable typed Strategy event.
    """
    return StrategyEvent.model_validate(kwargs)


def create_strategy_decision(**kwargs: object) -> StrategyDecision:
    """Create one immutable Strategy decision.

    Args:
        **kwargs: Validated Strategy decision field values.

    Returns:
        Immutable Strategy decision.
    """
    return StrategyDecision.model_validate(kwargs)


def create_strategy_signal_evidence(**kwargs: object) -> StrategySignalEvidence:
    """Create one point-in-time Strategy signal-evidence value.

    Args:
        **kwargs: Validated signal-evidence field values.

    Returns:
        Point-in-time Strategy signal evidence.
    """
    return StrategySignalEvidence.model_validate(kwargs)


def create_strategy_signal(**kwargs: object) -> StrategySignal:
    """Create one immutable deterministic Strategy signal value.

    Args:
        **kwargs: Validated Strategy signal field values.

    Returns:
        Immutable deterministic Strategy signal.
    """
    return StrategySignal.model_validate(kwargs)


def create_strategy_execution_result(**kwargs: object) -> StrategyExecutionResult:
    """Create one atomic Strategy execution result value.

    Args:
        **kwargs: Validated execution-result field values.

    Returns:
        Atomic Strategy execution result.
    """
    return StrategyExecutionResult.model_validate(kwargs)


def create_strategy_mutation_result(**kwargs: object) -> StrategyMutationResult:
    """Create one immutable Strategy mutation result value.

    Args:
        **kwargs: Validated mutation-result field values.

    Returns:
        Immutable Strategy mutation result.
    """
    return StrategyMutationResult.model_validate(kwargs)


def get_strategy_environment(value: str) -> StrategyEnvironment:
    """Return the approved Strategy environment represented by ``value``.

    Args:
        value: Environment string representation.

    Returns:
        Approved Strategy environment enum instance.
    """
    if value == "SIM":
        value = "SIMULATION"
    return StrategyEnvironment(value)


def get_strategy_timing_policy(value: str) -> StrategyTimingPolicy:
    """Return the approved Strategy timing policy represented by ``value``.

    Args:
        value: Timing policy string representation.

    Returns:
        Approved Strategy timing policy enum instance.
    """
    return StrategyTimingPolicy(value)


def get_strategy_lifecycle_status(value: str) -> StrategyLifecycleStatus:
    """Return the Strategy lifecycle status represented by ``value``.

    Args:
        value: Lifecycle status string representation.

    Returns:
        Approved Strategy lifecycle status enum instance.
    """
    return StrategyLifecycleStatus(value)


__all__ = [
    "create_strategy_config",
    "create_strategy_decision",
    "create_strategy_event",
    "create_strategy_execution_context",
    "create_strategy_execution_result",
    "create_strategy_manifest",
    "create_strategy_mutation_result",
    "create_strategy_parameter_update_request",
    "create_strategy_ref",
    "create_strategy_registration_request",
    "create_strategy_signal",
    "create_strategy_signal_evidence",
    "create_strategy_validation_policy",
    "create_validated_strategy_config",
    "create_validated_strategy_ref",
    "get_strategy_environment",
    "get_strategy_lifecycle_status",
    "get_strategy_timing_policy",
]
