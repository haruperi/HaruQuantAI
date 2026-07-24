"""Authenticated Strategy catalogue and mutation HTTP boundary."""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.api.identity import require_auth_context, require_human_permission
from app.services.strategy import (
    StrategyMutationResult,
    StrategyParameterUpdateRequest,
    StrategyRegistrationRequest,
    StrategyValidationPolicy,
    register_strategy_version,
    update_strategy_parameters,
)
from app.utils import AuthContext, logger

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


def _strategy_validation_policy() -> StrategyValidationPolicy:
    """Fail closed until composition injects the host Strategy policy.

    Raises:
        HTTPException: Always when the host policy is unavailable.
    """
    logger.warning("Rejecting Strategy registration without host policy")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="STRATEGY_POLICY_UNAVAILABLE",
    )


def _raise_outcome_error() -> NoReturn:
    """Raise a bounded HTTP failure for an owner-domain infrastructure error.

    Raises:
        HTTPException: Always.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="STRATEGY_MUTATION_UNAVAILABLE",
    )


@router.post("/parameter-updates", response_model=StrategyMutationResult)
def _adopt_optimization_result(
    request: StrategyParameterUpdateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> StrategyMutationResult:
    """Submit one explicitly approved Optimization-derived update.

    Args:
        request: Strategy-owned parameter-update command.
        auth: Authenticated human approver.

    Returns:
        Strategy-owned immutable mutation truth.

    Raises:
        HTTPException: If approval evidence or delegation fails.
    """
    logger.info("Delegating approved Strategy parameter update")
    require_human_permission(auth, "strategy:update")
    if request.principal_id != auth.principal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PRINCIPAL_MISMATCH",
        )
    if request.optimization_result_ref is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="OPTIMIZATION_RESULT_APPROVAL_REQUIRED",
        )
    outcome = update_strategy_parameters(request, auth)
    if outcome.status == "error" or outcome.data is None:
        _raise_outcome_error()
    return outcome.data


@router.post("/registrations", response_model=StrategyMutationResult)
def _register_research_candidate(
    request: StrategyRegistrationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    policy: Annotated[
        StrategyValidationPolicy,
        Depends(_strategy_validation_policy),
    ],
) -> StrategyMutationResult:
    """Submit one explicitly reviewed Research-derived registration.

    Args:
        request: Strategy-owned registration command.
        auth: Authenticated human approver.
        policy: Injected host validation policy.

    Returns:
        Strategy-owned immutable mutation truth.

    Raises:
        HTTPException: If principal evidence or delegation fails.
    """
    logger.info("Delegating approved Strategy registration")
    require_human_permission(auth, "strategy:register")
    if request.principal_id != auth.principal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PRINCIPAL_MISMATCH",
        )
    outcome = register_strategy_version(request, auth, policy)
    if outcome.status == "error" or outcome.data is None:
        _raise_outcome_error()
    return outcome.data


__all__ = ("router",)
