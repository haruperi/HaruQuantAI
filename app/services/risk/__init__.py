"""Public typed Risk domain contracts and operations."""

from app.services.risk.admission import review_strategy_admission
from app.services.risk.allocation import (
    activate_allocation_budget,
    review_allocation_proposal,
)
from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig, compute_config_hash, load_risk_config
from app.services.risk.contracts import (
    ActionPolicyVerdict,
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    AllocationRiskDecision,
    ApprovalAttestation,
    ApprovalValidationResult,
    DecisionReuseValidationResult,
    DecisionState,
    KillSwitchCommand,
    KillSwitchState,
    LimitStatus,
    PortfolioBudgetExecutionVerdict,
    PortfolioRiskSnapshot,
    PortfolioState,
    PositionSizingRequest,
    PositionSizingResult,
    ProposedTrade,
    RegimeAssessment,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
    RiskLimitResult,
    RiskReport,
    ScenarioDefinition,
    ScenarioResult,
    StrategyOperationalEligibilityDecision,
    StrategyOperationalEligibilityRequest,
    validate_market_context_evidence,
)
from app.services.risk.governor import RiskGovernor
from app.services.risk.kill_switch import (
    apply_kill_switch_command,
    check_risk_kill_switch,
)
from app.services.risk.limits import (
    evaluate_market_context,
    evaluate_portfolio_limits,
)
from app.services.risk.portfolio import build_portfolio_risk_snapshot
from app.services.risk.regimes import assess_risk_regime
from app.services.risk.reporting import generate_risk_report
from app.services.risk.scenarios import run_risk_scenario_analysis
from app.services.risk.sizing import calculate_position_size
from app.services.risk.validity import revalidate_risk_decision

__all__ = (
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
    "PortfolioBudgetExecutionVerdict",
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
)
