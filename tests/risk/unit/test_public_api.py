"""Unit tests for the exact public Risk package port."""

from app.services import risk


def test_root_public_api_is_exact_and_resolvable() -> None:
    """Expose every approved typed contract/operation and no private state port."""
    expected = {
        "ActionPolicyVerdict",
        "AllocationBudgetActivationRequest",
        "AllocationReviewRequest",
        "AllocationRiskDecision",
        "ApprovalAttestation",
        "ApprovalTokenService",
        "ApprovalValidationResult",
        "DecisionReuseValidationResult",
        "DecisionState",
        "KillSwitchCommand",
        "KillSwitchState",
        "LimitStatus",
        "PortfolioRiskSnapshot",
        "PortfolioState",
        "PositionSizingRequest",
        "PositionSizingResult",
        "ProposedTrade",
        "RegimeAssessment",
        "RiskApprovalToken",
        "RiskAuditChain",
        "RiskAuditRecord",
        "RiskConfig",
        "RiskDecisionPackage",
        "RiskDomainError",
        "RiskErrorCode",
        "RiskGovernor",
        "RiskLimitResult",
        "RiskReport",
        "ScenarioDefinition",
        "ScenarioResult",
        "StrategyOperationalEligibilityDecision",
        "StrategyOperationalEligibilityRequest",
        "activate_allocation_budget",
        "apply_kill_switch_command",
        "assess_risk_regime",
        "build_portfolio_risk_snapshot",
        "calculate_position_size",
        "check_risk_kill_switch",
        "compute_config_hash",
        "evaluate_market_context",
        "evaluate_portfolio_limits",
        "generate_risk_report",
        "load_risk_config",
        "revalidate_risk_decision",
        "review_allocation_proposal",
        "review_strategy_admission",
        "run_risk_scenario_analysis",
        "validate_market_context_evidence",
    }
    assert set(risk.__all__) == expected
    assert all(hasattr(risk, name) for name in risk.__all__)
    assert not any(name.startswith("_") for name in risk.__all__)
