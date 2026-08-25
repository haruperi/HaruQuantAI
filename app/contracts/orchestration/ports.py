"""Public capability protocols (ports) for Orchestration capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.orchestration.errors import OrchestrationFailure
    from app.contracts.orchestration.models import (
        DefineProjectsRequest,
        DefineProjectsSuccess,
        EvaluateConditionsRequest,
        EvaluateConditionsSuccess,
        RunDomainTasksRequest,
        RunDomainTasksSuccess,
        RunTasksRequest,
        RunTasksSuccess,
        RunUtilityTasksRequest,
        RunUtilityTasksSuccess,
        TrackRunHistoryRequest,
        TrackRunHistorySuccess,
        TrainNetworksRequest,
        TrainNetworksSuccess,
    )


@runtime_checkable
class DefineProjectsCapability(Protocol):
    """Capability protocol for project definition operations."""

    async def define_projects(
        self,
        request: DefineProjectsRequest,
    ) -> DefineProjectsSuccess | OrchestrationFailure:
        """Version, validate, publish, and compare project graphs.

        Args:
            request: Operation-discriminated project definition request.

        Returns:
            The created or edited project version, graph payload, and
            validation findings on success, otherwise a structured
            orchestration failure.
        """
        ...


@runtime_checkable
class RunTasksCapability(Protocol):
    """Capability protocol for task runtime operations."""

    async def run_tasks(
        self,
        request: RunTasksRequest,
    ) -> RunTasksSuccess | OrchestrationFailure:
        """Run project runs and task state machines.

        Args:
            request: Operation-discriminated project run and task command
                request.

        Returns:
            The project run reference, task state, and logical progress on
            success, otherwise a structured orchestration failure.
        """
        ...


@runtime_checkable
class EvaluateConditionsCapability(Protocol):
    """Capability protocol for variable and condition operations."""

    async def evaluate_conditions(
        self,
        request: EvaluateConditionsRequest,
    ) -> EvaluateConditionsSuccess | OrchestrationFailure:
        """Resolve typed project variables and evaluate expressions.

        Args:
            request: Operation-discriminated variable and condition request.

        Returns:
            The resolved variables and expression result on success,
            otherwise a structured orchestration failure.
        """
        ...


@runtime_checkable
class RunDomainTasksCapability(Protocol):
    """Capability protocol for built-in domain task operations."""

    async def run_domain_tasks(
        self,
        request: RunDomainTasksRequest,
    ) -> RunDomainTasksSuccess | OrchestrationFailure:
        """Delegate, pin, and dry-run built-in domain tasks.

        Args:
            request: Operation-discriminated built-in domain task request.

        Returns:
            The domain task request and dry-run impact record on success,
            otherwise a structured orchestration failure.
        """
        ...


@runtime_checkable
class RunUtilityTasksCapability(Protocol):
    """Capability protocol for external and utility task operations."""

    async def run_utility_tasks(
        self,
        request: RunUtilityTasksRequest,
    ) -> RunUtilityTasksSuccess | OrchestrationFailure:
        """Run executables, workspace utilities, and notifications.

        Args:
            request: Operation-discriminated external and utility task
                request.

        Returns:
            The utility task request, allowlist entry, channel, session, or
            receipt on success, otherwise a structured orchestration failure.
        """
        ...


@runtime_checkable
class TrackRunHistoryCapability(Protocol):
    """Capability protocol for run history operations."""

    async def track_run_history(
        self,
        request: TrackRunHistoryRequest,
    ) -> TrackRunHistorySuccess | OrchestrationFailure:
        """Record and query retained project run history.

        Args:
            request: Operation-discriminated run history request.

        Returns:
            The matching history entries on success, otherwise a structured
            orchestration failure.
        """
        ...


@runtime_checkable
class TrainNetworksCapability(Protocol):
    """Capability protocol for neural network trainer operations."""

    async def train_networks(
        self,
        request: TrainNetworksRequest,
    ) -> TrainNetworksSuccess | OrchestrationFailure:
        """Plan and train neural networks (Experimental section 21.3).

        Args:
            request: Operation-discriminated neural network trainer request.

        Returns:
            The training plan and training result on success, otherwise a
            structured orchestration failure.
        """
        ...
