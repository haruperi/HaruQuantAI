"""Risk Governor package.

Exposes the RiskGovernor orchestrator and decision synthesis utilities,
retaining V1 namespace compatibility.
"""

from __future__ import annotations

from app.services.risk.correlation import CorrelationEngine
from app.services.risk.exposure import CurrencyExposureEngine
from app.services.risk.feasibility import (
    DrawdownGovernor,
    ExecutionRiskGate,
    MarginRiskEngine,
)
from app.services.risk.governance.allocation import RiskAllocator
from app.services.risk.governor.decision_synthesis import (
    GateResult,
    GovernorEvaluationContext,
    RiskReductionPlan,
    determine_decision_status,
    is_decision_token_eligible,
    select_primary_risk_reason,
    synthesize_decision,
)
from app.services.risk.governor.governor import (
    RiskGovernor,
    RiskGovernorDecision,
    review_allocation_proposal,
    review_live_readiness,
    review_mode_promotion,
    review_strategy_admission,
    review_trade_risk,
    run_portfolio_risk_governor,
    run_risk_governor_checks,
)
from app.services.risk.limits import LimitEngine

# Namespace exports for V1 compatibility
from app.services.risk.models.contracts import (
    ProposedTrade,
    RiskAssessmentRequest,
    RiskDecisionPackage,
)
from app.services.risk.policy import RiskPolicyEngine
from app.services.risk.regime import RegimeRiskEngine
from app.services.risk.sizing import VolatilitySizingEngine
from app.services.risk.stress import StressTestingEngine
from app.services.risk.tail_risk import (
    ExpectedShortfallEngine,
    PortfolioVaREngine,
)

__all__ = [
    "CorrelationEngine",
    "CurrencyExposureEngine",
    "DrawdownGovernor",
    "ExecutionRiskGate",
    "ExpectedShortfallEngine",
    # V2 Synthesis
    "GateResult",
    "GovernorEvaluationContext",
    "LimitEngine",
    "MarginRiskEngine",
    "PortfolioVaREngine",
    # Compatibility exports
    "ProposedTrade",
    "RegimeRiskEngine",
    "RiskAllocator",
    "RiskAssessmentRequest",
    "RiskDecisionPackage",
    # V1/V2 Governor
    "RiskGovernor",
    "RiskGovernorDecision",
    "RiskPolicyEngine",
    "RiskReductionPlan",
    "StressTestingEngine",
    "VolatilitySizingEngine",
    "determine_decision_status",
    "is_decision_token_eligible",
    "review_allocation_proposal",
    "review_live_readiness",
    "review_mode_promotion",
    "review_strategy_admission",
    "review_trade_risk",
    "run_portfolio_risk_governor",
    "run_risk_governor_checks",
    "select_primary_risk_reason",
    "synthesize_decision",
]
