"""Public capability protocols (ports) for Research capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.research.errors import ResearchFailure
    from app.contracts.research.models import (
        AcceptResearchRequest,
        AcceptResearchSuccess,
        AssistResearchAiRequest,
        AssistResearchAiSuccess,
        EvolveStrategiesRequest,
        EvolveStrategiesSuccess,
        GenerateStrategiesRequest,
        GenerateStrategiesSuccess,
        GovernResearchBudgetsRequest,
        GovernResearchBudgetsSuccess,
        MonitorMarketDriftRequest,
        MonitorMarketDriftSuccess,
        OptimizeParametersRequest,
        OptimizeParametersSuccess,
        ResearchNeuralModelsRequest,
        ResearchNeuralModelsSuccess,
        ResearchStockpickersRequest,
        ResearchStockpickersSuccess,
        RunResearchRequest,
        RunResearchSuccess,
        ScorePortfolioFitnessRequest,
        ScorePortfolioFitnessSuccess,
        TestRobustnessRequest,
        TestRobustnessSuccess,
        ValidateWalkForwardRequest,
        ValidateWalkForwardSuccess,
    )


@runtime_checkable
class RunResearchCapability(Protocol):
    """Capability protocol for manual research run operations."""

    async def run_research(
        self,
        request: RunResearchRequest,
    ) -> RunResearchSuccess | ResearchFailure:
        """Preview, start, control, commit, duplicate, and batch manual runs.

        Args:
            request: Operation-discriminated manual research run request.

        Returns:
            The manifest, run reference, status, and committed result
            identifier on success, otherwise a structured research failure.
        """
        ...


@runtime_checkable
class TestRobustnessCapability(Protocol):
    """Capability protocol for retest and robustness operations."""

    async def test_robustness(
        self,
        request: TestRobustnessRequest,
    ) -> TestRobustnessSuccess | ResearchFailure:
        """Plan and execute retests, Monte Carlo, scenarios, and permutations.

        Args:
            request: Operation-discriminated retest and robustness request.

        Returns:
            The robustness plan and result on success, otherwise a structured
            research failure.
        """
        ...


@runtime_checkable
class OptimizeParametersCapability(Protocol):
    """Capability protocol for parameter optimization operations."""

    async def optimize_parameters(
        self,
        request: OptimizeParametersRequest,
    ) -> OptimizeParametersSuccess | ResearchFailure:
        """Plan and execute simple, grid, and sequential optimizations.

        Args:
            request: Operation-discriminated parameter optimization request.

        Returns:
            The optimization plan and result on success, otherwise a
            structured research failure.
        """
        ...


@runtime_checkable
class ValidateWalkForwardCapability(Protocol):
    """Capability protocol for walk-forward research operations."""

    async def validate_walk_forward(
        self,
        request: ValidateWalkForwardRequest,
    ) -> ValidateWalkForwardSuccess | ResearchFailure:
        """Plan, execute, and matrix-evaluate walk-forward research.

        Args:
            request: Operation-discriminated walk-forward research request.

        Returns:
            The walk-forward plan and result on success, otherwise a
            structured research failure.
        """
        ...


@runtime_checkable
class GenerateStrategiesCapability(Protocol):
    """Capability protocol for Builder generation operations."""

    async def generate_strategies(
        self,
        request: GenerateStrategiesRequest,
    ) -> GenerateStrategiesSuccess | ResearchFailure:
        """Plan, generate, calibrate, and deduplicate Builder strategies.

        Args:
            request: Operation-discriminated Builder generation request.

        Returns:
            The builder plan and emitted candidates on success, otherwise a
            structured research failure.
        """
        ...


@runtime_checkable
class EvolveStrategiesCapability(Protocol):
    """Capability protocol for Improver and genetic evolution operations."""

    async def evolve_strategies(
        self,
        request: EvolveStrategiesRequest,
    ) -> EvolveStrategiesSuccess | ResearchFailure:
        """Plan, evolve, checkpoint, resume, and improve strategy candidates.

        Args:
            request: Operation-discriminated Improver and genetic evolution
                request.

        Returns:
            The evolution plan and candidates on success, otherwise a
            structured research failure.
        """
        ...


@runtime_checkable
class AcceptResearchCapability(Protocol):
    """Capability protocol for acceptance pipeline operations."""

    async def accept_research(
        self,
        request: AcceptResearchRequest,
    ) -> AcceptResearchSuccess | ResearchFailure:
        """Define acceptance pipelines, evaluate, and promote candidates.

        Args:
            request: Operation-discriminated acceptance pipeline request.

        Returns:
            The pipeline, decision, and promotion on success, otherwise a
            structured research failure.
        """
        ...


@runtime_checkable
class GovernResearchBudgetsCapability(Protocol):
    """Capability protocol for research budget governance operations."""

    async def govern_research_budgets(
        self,
        request: GovernResearchBudgetsRequest,
    ) -> GovernResearchBudgetsSuccess | ResearchFailure:
        """Define, check, and enforce research resource budgets.

        Args:
            request: Operation-discriminated research budget governance
                request.

        Returns:
            The governed budget on success, otherwise a structured research
            failure.
        """
        ...


@runtime_checkable
class ResearchStockpickersCapability(Protocol):
    """Capability protocol for stockpicker research operations."""

    async def research_stockpickers(
        self,
        request: ResearchStockpickersRequest,
    ) -> ResearchStockpickersSuccess | ResearchFailure:
        """Plan and execute point-in-time stockpicker research.

        Args:
            request: Operation-discriminated stockpicker research request.

        Returns:
            The stockpicker plan and result identifier on success, otherwise
            a structured research failure.
        """
        ...


@runtime_checkable
class AssistResearchAiCapability(Protocol):
    """Capability protocol for AI-assisted research operations."""

    async def assist_research_ai(
        self,
        request: AssistResearchAiRequest,
    ) -> AssistResearchAiSuccess | ResearchFailure:
        """Draft, validate, and improve strategies with external AI assistance.

        External AI failures never impair non-AI workflows.

        Args:
            request: Operation-discriminated AI-assisted research request.

        Returns:
            The AI draft and improvement proposal on success, otherwise a
            structured research failure.
        """
        ...


@runtime_checkable
class ResearchNeuralModelsCapability(Protocol):
    """Capability protocol for neural research operations."""

    async def research_neural_models(
        self,
        request: ResearchNeuralModelsRequest,
    ) -> ResearchNeuralModelsSuccess | ResearchFailure:
        """Plan and train governed neural research artifacts.

        Args:
            request: Operation-discriminated neural research request.

        Returns:
            The neural research plan on success, otherwise a structured
            research failure.
        """
        ...


@runtime_checkable
class ScorePortfolioFitnessCapability(Protocol):
    """Capability protocol for portfolio-aware Builder fitness operations."""

    async def score_portfolio_fitness(
        self,
        request: ScorePortfolioFitnessRequest,
    ) -> ScorePortfolioFitnessSuccess | ResearchFailure:
        """Score one candidate against a pinned immutable portfolio version.

        Args:
            request: Operation-discriminated portfolio-aware fitness request.

        Returns:
            The portfolio fitness score on success, otherwise a structured
            research failure.
        """
        ...


@runtime_checkable
class MonitorMarketDriftCapability(Protocol):
    """Capability protocol for market intelligence and drift operations."""

    async def monitor_market_drift(
        self,
        request: MonitorMarketDriftRequest,
    ) -> MonitorMarketDriftSuccess | ResearchFailure:
        """Observe point-in-time market intelligence and evaluate drift.

        Args:
            request: Operation-discriminated market intelligence and drift
                request.

        Returns:
            The intelligence observation and drift report on success,
            otherwise a structured research failure.
        """
        ...
