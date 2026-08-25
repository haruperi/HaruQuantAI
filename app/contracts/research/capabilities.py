"""Research domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.research.ports import (
        AcceptResearchCapability,
        AssistResearchAiCapability,
        EvolveStrategiesCapability,
        GenerateStrategiesCapability,
        GovernResearchBudgetsCapability,
        MonitorMarketDriftCapability,
        OptimizeParametersCapability,
        ResearchNeuralModelsCapability,
        ResearchStockpickersCapability,
        RunResearchCapability,
        ScorePortfolioFitnessCapability,
        TestRobustnessCapability,
        ValidateWalkForwardCapability,
    )

RUN_RESEARCH_CAPABILITY: CapabilityKey[RunResearchCapability] = CapabilityKey(
    name="research.run-research",
    major=1,
)

TEST_ROBUSTNESS_CAPABILITY: CapabilityKey[TestRobustnessCapability] = CapabilityKey(
    name="research.test-robustness",
    major=1,
)

OPTIMIZE_PARAMETERS_CAPABILITY: CapabilityKey[OptimizeParametersCapability] = (
    CapabilityKey(
        name="research.optimize-parameters",
        major=1,
    )
)

VALIDATE_WALK_FORWARD_CAPABILITY: CapabilityKey[ValidateWalkForwardCapability] = (
    CapabilityKey(
        name="research.validate-walk-forward",
        major=1,
    )
)

GENERATE_STRATEGIES_CAPABILITY: CapabilityKey[GenerateStrategiesCapability] = (
    CapabilityKey(
        name="research.generate-strategies",
        major=1,
    )
)

EVOLVE_STRATEGIES_CAPABILITY: CapabilityKey[EvolveStrategiesCapability] = CapabilityKey(
    name="research.evolve-strategies",
    major=1,
)

ACCEPT_RESEARCH_CAPABILITY: CapabilityKey[AcceptResearchCapability] = CapabilityKey(
    name="research.accept-research",
    major=1,
)

GOVERN_RESEARCH_BUDGETS_CAPABILITY: CapabilityKey[GovernResearchBudgetsCapability] = (
    CapabilityKey(
        name="research.govern-research-budgets",
        major=1,
    )
)

RESEARCH_STOCKPICKERS_CAPABILITY: CapabilityKey[ResearchStockpickersCapability] = (
    CapabilityKey(
        name="research.research-stockpickers",
        major=1,
    )
)

ASSIST_RESEARCH_AI_CAPABILITY: CapabilityKey[AssistResearchAiCapability] = (
    CapabilityKey(
        name="research.assist-research-ai",
        major=1,
    )
)

RESEARCH_NEURAL_MODELS_CAPABILITY: CapabilityKey[ResearchNeuralModelsCapability] = (
    CapabilityKey(
        name="research.research-neural-models",
        major=1,
    )
)

SCORE_PORTFOLIO_FITNESS_CAPABILITY: CapabilityKey[ScorePortfolioFitnessCapability] = (
    CapabilityKey(
        name="research.score-portfolio-fitness",
        major=1,
    )
)

MONITOR_MARKET_DRIFT_CAPABILITY: CapabilityKey[MonitorMarketDriftCapability] = (
    CapabilityKey(
        name="research.monitor-market-drift",
        major=1,
    )
)
