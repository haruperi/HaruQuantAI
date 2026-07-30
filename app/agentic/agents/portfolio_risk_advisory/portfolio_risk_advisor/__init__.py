"""Public `FEAT-AGT-19` Portfolio and Risk Advisory API."""

from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.agent import (
    advise_portfolio,
    critique_risk,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.schemas import (
    AllocationProposal,
    RiskAdvisory,
    build_allocation_proposal,
    build_risk_advisory,
)

__all__: tuple[str, ...] = (
    "AllocationProposal",
    "RiskAdvisory",
    "advise_portfolio",
    "build_allocation_proposal",
    "build_risk_advisory",
    "critique_risk",
)
