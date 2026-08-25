"""Public capability protocols (ports) for Simulator capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.simulator.errors import SimulatorFailure
    from app.contracts.simulator.models import (
        CacheEvaluationsRequest,
        CacheEvaluationsSuccess,
        CalculateCostsRequest,
        CalculateCostsSuccess,
        CalculateProfilesRequest,
        CalculateProfilesSuccess,
        CommitResultsRequest,
        CommitResultsSuccess,
        ConfigureEngineRequest,
        ConfigureEngineSuccess,
        DistributeEvaluationsRequest,
        DistributeEvaluationsSuccess,
        ManageExitsRequest,
        ManageExitsSuccess,
        ModelPrecisionRequest,
        ModelPrecisionSuccess,
        PerturbInputsRequest,
        PerturbInputsSuccess,
        RunIndicatorsRequest,
        RunIndicatorsSuccess,
        SimulateOrdersRequest,
        SimulateOrdersSuccess,
        SimulateStockpickersRequest,
        SimulateStockpickersSuccess,
    )


@runtime_checkable
class ConfigureEngineCapability(Protocol):
    """Capability protocol for run manifest and engine profile operations."""

    async def configure_engine(
        self,
        request: ConfigureEngineRequest,
    ) -> ConfigureEngineSuccess | SimulatorFailure:
        """Define and list versioned target-runtime engine profiles.

        Args:
            request: Operation-discriminated engine profile request.

        Returns:
            The stored profile or the listed profile versions on success,
            otherwise a structured simulator failure.
        """
        ...


@runtime_checkable
class ModelPrecisionCapability(Protocol):
    """Capability protocol for precision model operations."""

    async def model_precision(
        self,
        request: ModelPrecisionRequest,
    ) -> ModelPrecisionSuccess | SimulatorFailure:
        """Define precision models and validate their declared inputs.

        Args:
            request: Operation-discriminated precision model request.

        Returns:
            The stored or validated precision model on success, otherwise
            a structured simulator failure.
        """
        ...


@runtime_checkable
class SimulateOrdersCapability(Protocol):
    """Capability protocol for simulation run and job-control operations."""

    async def simulate_orders(
        self,
        request: SimulateOrdersRequest,
    ) -> SimulateOrdersSuccess | SimulatorFailure:
        """Run deterministic simulations and control their jobs.

        Args:
            request: Operation-discriminated simulation and job-control
                request.

        Returns:
            The run reference, pinned manifest, inspected order, or
            earliest-mismatch comparison on success, otherwise a
            structured simulator failure.
        """
        ...


@runtime_checkable
class CalculateCostsCapability(Protocol):
    """Capability protocol for position sizing and trading-cost operations."""

    async def calculate_costs(
        self,
        request: CalculateCostsRequest,
    ) -> CalculateCostsSuccess | SimulatorFailure:
        """Calculate position sizes and reconciled trading costs.

        Args:
            request: Operation-discriminated sizing and trading-cost
                request.

        Returns:
            The sizing decision or exact cost breakdown on success,
            otherwise a structured simulator failure.
        """
        ...


@runtime_checkable
class ManageExitsCapability(Protocol):
    """Capability protocol for exit, collision, and ATM operations."""

    async def manage_exits(
        self,
        request: ManageExitsRequest,
    ) -> ManageExitsSuccess | SimulatorFailure:
        """Schedule exits, resolve collisions, and execute ATM state.

        Args:
            request: Operation-discriminated exit, collision, and ATM
                request.

        Returns:
            The stored exit schedule or partial-exit allocations on
            success, otherwise a structured simulator failure.
        """
        ...


@runtime_checkable
class RunIndicatorsCapability(Protocol):
    """Capability protocol for isolated indicator runtime operations."""

    async def run_indicators(
        self,
        request: RunIndicatorsRequest,
    ) -> RunIndicatorsSuccess | SimulatorFailure:
        """Prepare and evaluate isolated indicator runtime specifications.

        Args:
            request: Operation-discriminated indicator runtime request.

        Returns:
            The runtime specification and its evaluation findings on
            success, otherwise a structured simulator failure.
        """
        ...


@runtime_checkable
class CommitResultsCapability(Protocol):
    """Capability protocol for simulation result commit operations."""

    async def commit_results(
        self,
        request: CommitResultsRequest,
    ) -> CommitResultsSuccess | SimulatorFailure:
        """Validate and commit reconciled simulation results.

        Args:
            request: Operation-discriminated result commit request.

        Returns:
            The validated result or its commit receipt on success,
            otherwise a structured simulator failure.
        """
        ...


@runtime_checkable
class CacheEvaluationsCapability(Protocol):
    """Capability protocol for evaluation cache operations."""

    async def cache_evaluations(
        self,
        request: CacheEvaluationsRequest,
    ) -> CacheEvaluationsSuccess | SimulatorFailure:
        """Look up and store exact-content evaluation cache keys.

        Args:
            request: Operation-discriminated evaluation cache request.

        Returns:
            The resolved cache key on success, otherwise a structured
            simulator failure.
        """
        ...


@runtime_checkable
class CalculateProfilesCapability(Protocol):
    """Capability protocol for volume-profile and TPO operations."""

    async def calculate_profiles(
        self,
        request: CalculateProfilesRequest,
    ) -> CalculateProfilesSuccess | SimulatorFailure:
        """Calculate experimental volume profiles and TPO structures.

        Args:
            request: Operation-discriminated volume-profile and TPO
                request.

        Returns:
            The volume profile or TPO profile on success, otherwise a
            structured simulator failure.
        """
        ...


@runtime_checkable
class PerturbInputsCapability(Protocol):
    """Capability protocol for perturbation hook operations."""

    async def perturb_inputs(
        self,
        request: PerturbInputsRequest,
    ) -> PerturbInputsSuccess | SimulatorFailure:
        """Define deterministic input perturbation specifications.

        Args:
            request: Perturbation definition request.

        Returns:
            The stored perturbation specification on success, otherwise
            a structured simulator failure.
        """
        ...


@runtime_checkable
class DistributeEvaluationsCapability(Protocol):
    """Capability protocol for distributed evaluation operations."""

    async def distribute_evaluations(
        self,
        request: DistributeEvaluationsRequest,
    ) -> DistributeEvaluationsSuccess | SimulatorFailure:
        """Plan distributed evaluations and stream bounded progress.

        Args:
            request: Operation-discriminated distributed evaluation
                request.

        Returns:
            The distribution plan or its bounded progress summaries on
            success, otherwise a structured simulator failure.
        """
        ...


@runtime_checkable
class SimulateStockpickersCapability(Protocol):
    """Capability protocol for stockpicker simulation operations."""

    async def simulate_stockpickers(
        self,
        request: SimulateStockpickersRequest,
    ) -> SimulateStockpickersSuccess | SimulatorFailure:
        """Define and simulate stockpicker specifications.

        Args:
            request: Operation-discriminated stockpicker simulation
                request.

        Returns:
            The stored specification or its produced result identifier on
            success, otherwise a structured simulator failure.
        """
        ...
