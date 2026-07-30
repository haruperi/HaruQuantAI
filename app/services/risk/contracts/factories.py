"""Function-only construction and inspection for Risk-owned contracts."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.risk.contracts.catalog import RISK_ERROR_CATALOG, ErrorDefinition
from app.services.risk.contracts.enums import DecisionState, LimitStatus, RiskErrorCode
from app.services.risk.contracts.errors import RiskDomainError
from app.services.risk.contracts.evidence import PortfolioRiskSnapshot, PortfolioState
from app.services.risk.contracts.requests import (
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    ApprovalAttestation,
    KillSwitchCommand,
    PositionSizingRequest,
    ProposedTrade,
    ScenarioDefinition,
    StrategyOperationalEligibilityRequest,
)
from app.services.risk.contracts.results import (
    ActionPolicyVerdict,
    AllocationRiskDecision,
    ApprovalValidationResult,
    DecisionReuseValidationResult,
    KillSwitchState,
    PortfolioBudgetExecutionVerdict,
    PositionSizingResult,
    RegimeAssessment,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskLimitResult,
    RiskReport,
    ScenarioResult,
    StrategyOperationalEligibilityDecision,
)


def create_action_policy_verdict(**values: object) -> ActionPolicyVerdict:
    """Construct one validated action-policy verdict.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal action-policy verdict.
    """
    return ActionPolicyVerdict.model_validate(values)


def create_allocation_budget_activation_request(
    **values: object,
) -> AllocationBudgetActivationRequest:
    """Construct one validated allocation-budget activation request.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal activation request.
    """
    return AllocationBudgetActivationRequest.model_validate(values)


def create_allocation_review_request(**values: object) -> AllocationReviewRequest:
    """Construct one validated allocation-review request.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal allocation-review request.
    """
    return AllocationReviewRequest.model_validate(values)


def create_allocation_risk_decision(**values: object) -> AllocationRiskDecision:
    """Construct one validated allocation-risk decision.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal allocation-risk decision.
    """
    return AllocationRiskDecision.model_validate(values)


def create_approval_attestation(**values: object) -> ApprovalAttestation:
    """Construct one validated approval attestation.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal approval attestation.
    """
    return ApprovalAttestation.model_validate(values)


def create_approval_validation_result(**values: object) -> ApprovalValidationResult:
    """Construct one validated approval result.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal approval result.
    """
    return ApprovalValidationResult.model_validate(values)


def create_decision_reuse_validation_result(
    **values: object,
) -> DecisionReuseValidationResult:
    """Construct one validated decision-reuse result.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal reuse result.
    """
    return DecisionReuseValidationResult.model_validate(values)


def create_kill_switch_command(**values: object) -> KillSwitchCommand:
    """Construct one validated kill-switch command.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal kill-switch command.
    """
    return KillSwitchCommand.model_validate(values)


def create_kill_switch_state(**values: object) -> KillSwitchState:
    """Construct one validated kill-switch state.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal kill-switch state.
    """
    return KillSwitchState.model_validate(values)


def create_portfolio_budget_execution_verdict(
    **values: object,
) -> PortfolioBudgetExecutionVerdict:
    """Construct one validated portfolio-budget execution verdict.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal execution verdict.
    """
    return PortfolioBudgetExecutionVerdict.model_validate(values)


def create_portfolio_risk_snapshot(**values: object) -> PortfolioRiskSnapshot:
    """Construct one validated portfolio-risk snapshot.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal portfolio-risk snapshot.
    """
    return PortfolioRiskSnapshot.model_validate(values)


def create_portfolio_state(**values: object) -> PortfolioState:
    """Construct one validated portfolio state.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal portfolio state.
    """
    return PortfolioState.model_validate(values)


def create_position_sizing_request(**values: object) -> PositionSizingRequest:
    """Construct one validated position-sizing request.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal sizing request.
    """
    return PositionSizingRequest.model_validate(values)


def create_position_sizing_result(**values: object) -> PositionSizingResult:
    """Construct one validated position-sizing result.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal sizing result.
    """
    return PositionSizingResult.model_validate(values)


def create_proposed_trade(**values: object) -> ProposedTrade:
    """Construct one validated proposed trade.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal proposed trade.
    """
    return ProposedTrade.model_validate(values)


def create_regime_assessment(**values: object) -> RegimeAssessment:
    """Construct one validated regime assessment.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal regime assessment.
    """
    return RegimeAssessment.model_validate(values)


def create_risk_approval_token(**values: object) -> RiskApprovalToken:
    """Construct one validated Risk approval token.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal approval token.
    """
    return RiskApprovalToken.model_validate(values)


def create_risk_audit_record(**values: object) -> RiskAuditRecord:
    """Construct one validated Risk audit record.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal audit record.
    """
    return RiskAuditRecord.model_validate(values)


def create_risk_decision_package(**values: object) -> RiskDecisionPackage:
    """Construct one validated Risk decision package.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal decision package.
    """
    return RiskDecisionPackage.model_validate(values)


def create_risk_domain_error(code: RiskErrorCode, details: str) -> RiskDomainError:
    """Construct one redacted Risk domain error.

    Args:
        code: Risk error code value returned by :func:`get_risk_error_code`.
        details: Secret-safe diagnostic detail.

    Returns:
        Internal Risk domain exception.
    """
    return RiskDomainError(code, details)


def create_risk_limit_result(**values: object) -> RiskLimitResult:
    """Construct one validated Risk limit result.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal limit result.
    """
    return RiskLimitResult.model_validate(values)


def create_risk_report(**values: object) -> RiskReport:
    """Construct one validated Risk report.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal Risk report.
    """
    return RiskReport.model_validate(values)


def create_scenario_definition(**values: object) -> ScenarioDefinition:
    """Construct one validated scenario definition.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal scenario definition.
    """
    return ScenarioDefinition.model_validate(values)


def create_scenario_result(**values: object) -> ScenarioResult:
    """Construct one validated scenario result.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal scenario result.
    """
    return ScenarioResult.model_validate(values)


def create_strategy_operational_eligibility_decision(
    **values: object,
) -> StrategyOperationalEligibilityDecision:
    """Construct one validated strategy-eligibility decision.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal eligibility decision.
    """
    return StrategyOperationalEligibilityDecision.model_validate(values)


def create_strategy_operational_eligibility_request(
    **values: object,
) -> StrategyOperationalEligibilityRequest:
    """Construct one validated strategy-eligibility request.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal eligibility request.
    """
    return StrategyOperationalEligibilityRequest.model_validate(values)


def get_decision_state(value: str) -> DecisionState:
    """Resolve one canonical decision-state value.

    Args:
        value: Registered decision-state value or member name.

    Returns:
        Internal canonical decision-state value.
    """
    member = DecisionState.__members__.get(value.upper())
    return member if member is not None else DecisionState(value.lower())


def get_limit_status(value: str) -> LimitStatus:
    """Resolve one canonical limit-status value.

    Args:
        value: Registered limit-status value or member name.

    Returns:
        Internal canonical limit-status value.
    """
    member = LimitStatus.__members__.get(value.upper())
    return member if member is not None else LimitStatus(value.lower())


def get_risk_error_catalog() -> Mapping[str, ErrorDefinition]:
    """Return the immutable Risk error catalogue.

    Returns:
        Risk error definitions keyed by stable code.
    """
    return RISK_ERROR_CATALOG


def get_risk_error_code(value: str) -> RiskErrorCode:
    """Resolve one canonical Risk error code.

    Args:
        value: Registered Risk error-code value or member name.

    Returns:
        Internal canonical Risk error code.
    """
    member = RiskErrorCode.__members__.get(value.upper())
    return member if member is not None else RiskErrorCode(value.upper())


def is_risk_domain_error(value: object) -> bool:
    """Return whether a value is the internal Risk domain exception.

    Args:
        value: Value to inspect.

    Returns:
        True only for Risk domain exceptions.
    """
    return isinstance(value, RiskDomainError)


__all__ = [
    "create_action_policy_verdict",
    "create_allocation_budget_activation_request",
    "create_allocation_review_request",
    "create_allocation_risk_decision",
    "create_approval_attestation",
    "create_approval_validation_result",
    "create_decision_reuse_validation_result",
    "create_kill_switch_command",
    "create_kill_switch_state",
    "create_portfolio_budget_execution_verdict",
    "create_portfolio_risk_snapshot",
    "create_portfolio_state",
    "create_position_sizing_request",
    "create_position_sizing_result",
    "create_proposed_trade",
    "create_regime_assessment",
    "create_risk_approval_token",
    "create_risk_audit_record",
    "create_risk_decision_package",
    "create_risk_domain_error",
    "create_risk_limit_result",
    "create_risk_report",
    "create_scenario_definition",
    "create_scenario_result",
    "create_strategy_operational_eligibility_decision",
    "create_strategy_operational_eligibility_request",
    "get_decision_state",
    "get_limit_status",
    "get_risk_error_catalog",
    "get_risk_error_code",
    "is_risk_domain_error",
]
