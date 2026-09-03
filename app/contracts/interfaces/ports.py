"""Public capability protocols (ports) for Interfaces domain."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from app.contracts.common.events import DomainEvent
    from app.contracts.interfaces.errors import InterfaceFailure
    from app.contracts.interfaces.models import (
        AdministerCapabilitiesRequest,
        AdministerCapabilitiesSuccess,
        ApiCompatibilityReport,
        ApiDeprecationNotice,
        ApplicationCommandRequest,
        ApplicationCommandResult,
        ArtifactDownloadRequest,
        ArtifactDownloadResponse,
        AsyncJobRef,
        AsyncJobState,
        DurableCommandRef,
        DurableJobStatus,
        EditProjectsRequest,
        EditProjectsSuccess,
        EventReplayBatch,
        InterfaceEventEnvelope,
        ObserveMarketDataEventSubscription,
        ObserveMarketDataRequest,
        ObserveMarketDataSuccess,
        OpenApiManifest,
        OperatePortfoliosRequest,
        OperatePortfoliosSuccess,
        OperateResearchRequest,
        OperateResearchSuccess,
        OperateTradingEventSubscription,
        OperateTradingRequest,
        OperateTradingSuccess,
    )


@runtime_checkable
class ServeApiEventsCapability(Protocol):
    """Protocol for serving versioned HTTP/OpenAPI contracts and SSE events."""

    def get_openapi_manifest(self) -> OpenApiManifest:
        """Get the complete OpenAPI 3.1 contract specification for served endpoints.

        Returns:
            OpenApiManifest containing all exposed route and schema definitions.
        """
        ...

    def serve_versioned_api(self, api_version: str = "v1") -> OpenApiManifest:
        """Serve versioned API contracts and route schemas for a version label.

        Args:
            api_version: API version string (e.g. 'v1').

        Returns:
            OpenApiManifest filtered and validated for the specified version.

        Raises:
            ApiIncompatibleError: If requested API version is unsupported.
        """
        ...

    def validate_concurrency_token(
        self,
        resource_id: str,
        expected_version: str | int | None,
        current_version: str | int,
    ) -> bool:
        """Validate an optimistic concurrency token against current version.

        Args:
            resource_id: Protected resource identifier.
            expected_version: Expected token from If-Match header.
            current_version: Current server-side version of the resource.

        Returns:
            True if version matches and mutation is permitted.

        Raises:
            VersionConflictError: If expected version does not match current version.
        """
        ...

    def deduplicate_mutation(
        self,
        idempotency_key: str,
        session_id: str,
        command_type: str,
        execute_fn: Callable[[], dict[str, object]],
    ) -> dict[str, object]:
        """Execute a mutation idempotently, returning cached results on repeat.

        Args:
            idempotency_key: Client-supplied idempotency key.
            session_id: Session identifier scope.
            command_type: Command classification.
            execute_fn: Callable producing the mutation response dictionary.

        Returns:
            Dictionary response payload from initial execution or cached replay.

        Raises:
            IdempotencyConflictError: If a concurrent execution is already in flight.
        """
        ...

    def publish_interface_event(
        self,
        event_type: str,
        topic: str,
        payload: dict[str, object],
    ) -> InterfaceEventEnvelope:
        """Publish a typed event into the interface event buffer.

        Args:
            event_type: Domain event classification name.
            topic: Topic or channel name.
            payload: Event data dictionary.

        Returns:
            InterfaceEventEnvelope with assigned sequence and event ID.
        """
        ...

    def replay_interface_events(
        self,
        last_event_id: str | None,
        max_events: int = 100,
    ) -> EventReplayBatch:
        """Replay retained interface events following a cursor.

        Args:
            last_event_id: Last received event ID / cursor string, or None for latest.
            max_events: Maximum number of events to return in this batch.

        Returns:
            EventReplayBatch with envelopes, next cursor, and resync flags.

        Raises:
            EventCursorExpiredError: If requested cursor is beyond the retention window.
        """
        ...

    def submit_async_job(
        self,
        command_type: str,
        runner_fn: Callable[[AsyncJobRef], None] | None = None,
    ) -> AsyncJobRef:
        """Submit a long-running task and return an AsyncJobRef immediately.

        Args:
            command_type: Initiating action category.
            runner_fn: Optional synchronous runner callable.

        Returns:
            AsyncJobRef with unique job ID and initial QUEUED or RUNNING state.
        """
        ...

    def get_async_job(self, job_id: str) -> AsyncJobRef:
        """Query the current state and progress of an asynchronous job.

        Args:
            job_id: Unique job UUID string.

        Returns:
            AsyncJobRef describing current state, progress, and stage.

        Raises:
            JobNotFoundError: If job ID is not registered.
        """
        ...

    def update_async_job(
        self,
        job_id: str,
        *,
        state: AsyncJobState | None = None,
        progress: float | None = None,
        stage: str | None = None,
        error_message: str | None = None,
        result_ref: str | None = None,
    ) -> AsyncJobRef:
        """Update the state or progress of an active asynchronous job.

        Args:
            job_id: Target job UUID string.
            state: Optional updated lifecycle state.
            progress: Optional updated progress float between 0.0 and 1.0.
            stage: Optional updated stage description.
            error_message: Optional error message on failure.
            result_ref: Optional result reference pointer on completion.

        Returns:
            Updated AsyncJobRef.

        Raises:
            JobNotFoundError: If job ID is not registered.
        """
        ...

    def validate_artifact_download(
        self,
        request: ArtifactDownloadRequest,
        storage_root: Path,
        committed_artifacts: dict[str, Path] | None = None,
    ) -> ArtifactDownloadResponse:
        """Validate and resolve an artifact file download.

        Validates artifact committed state, requested filename, byte range,
        and strict path containment against directory traversal.

        Args:
            request: Download request specification.
            storage_root: Root filesystem directory containing committed artifacts.
            committed_artifacts: Optional mapping of committed artifact IDs to paths.

        Returns:
            ArtifactDownloadResponse containing validated data bytes and range info.

        Raises:
            ArtifactAccessDeniedError: If artifact is uncommitted, missing,
                or escapes storage root containment.
        """
        ...

    def check_api_compatibility(self, client_version: str) -> ApiCompatibilityReport:
        """Check whether a client API version is compatible with this server.

        Args:
            client_version: Semantic version string of the client.

        Returns:
            ApiCompatibilityReport with status, deprecations, and breaking changes.
        """
        ...

    def get_deprecations(self) -> tuple[ApiDeprecationNotice, ...]:
        """Get all active machine-readable deprecation notices for this API version.

        Returns:
            Tuple of ApiDeprecationNotice descriptors.
        """
        ...


@runtime_checkable
class AutomateCommandsCapability(Protocol):
    """Protocol for unified CLI, MCP, and application command automation."""

    def delegate_application_call(
        self,
        request: ApplicationCommandRequest,
    ) -> ApplicationCommandResult:
        """Execute a normalized application command across UI, CLI, or MCP callers.

        Args:
            request: Standardized command invocation request.

        Returns:
            ApplicationCommandResult describing status, data, and errors.
        """
        ...

    def register_command_handler(
        self,
        command_name: str,
        handler: Callable[[dict[str, object]], dict[str, object]],
    ) -> None:
        """Register a handler callback for an application command name.

        Args:
            command_name: Canonical registered command name string.
            handler: Callable taking payload dictionary and returning output dictionary.
        """
        ...

    def track_durable_command(
        self,
        command_name: str,
        payload: dict[str, object],
        runner_fn: Callable[[DurableCommandRef], None] | None = None,
    ) -> DurableCommandRef:
        """Admit a durable long-running CLI or MCP command and return reference.

        Args:
            command_name: Target action or command name.
            payload: Parameter dictionary.
            runner_fn: Optional synchronous runner callable.

        Returns:
            DurableCommandRef with unique job ID and initial QUEUED state.
        """
        ...

    def get_durable_command_status(
        self,
        durable_job_id: str,
    ) -> DurableCommandRef:
        """Query lifecycle state and progress of a durable command.

        Args:
            durable_job_id: Unique durable job UUID string.

        Returns:
            DurableCommandRef describing current status, progress, and stage.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        ...

    def cancel_durable_command(
        self,
        durable_job_id: str,
    ) -> DurableCommandRef:
        """Request cooperative cancellation of an active durable command.

        Args:
            durable_job_id: Target durable job UUID string.

        Returns:
            Updated DurableCommandRef marked with cancellation requested.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        ...

    def update_durable_command(
        self,
        durable_job_id: str,
        *,
        status: DurableJobStatus | None = None,
        progress: float | None = None,
        stage: str | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> DurableCommandRef:
        """Update lifecycle state or progress of a durable command.

        Args:
            durable_job_id: Target durable job UUID string.
            status: Optional updated lifecycle state.
            progress: Optional progress float between 0.0 and 1.0.
            stage: Optional stage description.
            result: Optional completed result payload dictionary.
            error: Optional error description string.

        Returns:
            Updated DurableCommandRef.

        Raises:
            DurableJobNotFoundError: If durable job is not registered.
        """
        ...


@runtime_checkable
class ObserveMarketDataCapability(Protocol):
    """Protocol for the market data observation gateway."""

    async def observe_market_data(
        self,
        request: ObserveMarketDataRequest,
    ) -> ObserveMarketDataSuccess | InterfaceFailure:
        """Resolve and expose market tick snapshot projections.

        Args:
            request: Operation-discriminated market observation request.

        Returns:
            The market tick snapshot projection on success, otherwise a
            structured interface failure.
        """
        ...

    def subscribe_observe_market_data_events(
        self,
        request: ObserveMarketDataEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver market observation events as domain events.

        Args:
            request: Owner-required subscription selector carrying the
                bounded symbol filter, resume position, and bounded replay
                limit.

        Returns:
            An asynchronous iterator of market observation events wrapped
            in the common domain event envelope with ordered replay and
            resync semantics.
        """
        ...


@runtime_checkable
class OperateResearchCapability(Protocol):
    """Protocol for the research preview gateway."""

    async def operate_research(
        self,
        request: OperateResearchRequest,
    ) -> OperateResearchSuccess | InterfaceFailure:
        """Resolve and expose research preview and admission projections.

        Args:
            request: Operation-discriminated research preview request.

        Returns:
            The research preview on success, otherwise a structured
            interface failure.
        """
        ...


@runtime_checkable
class EditProjectsCapability(Protocol):
    """Protocol for the project graph gateway."""

    async def edit_projects(
        self,
        request: EditProjectsRequest,
    ) -> EditProjectsSuccess | InterfaceFailure:
        """Resolve and expose project graph validation and command contracts.

        Edge and condition commands delegate to Orchestration public
        contracts; this gateway adds none.

        Args:
            request: Operation-discriminated project graph request.

        Returns:
            The project graph projection on success, otherwise a
            structured interface failure.
        """
        ...


@runtime_checkable
class OperatePortfoliosCapability(Protocol):
    """Protocol for the portfolio operations gateway."""

    async def operate_portfolios(
        self,
        request: OperatePortfoliosRequest,
    ) -> OperatePortfoliosSuccess | InterfaceFailure:
        """Resolve and expose portfolio projections and commands.

        Simulation, search, and attribution commands delegate to Portfolio
        public contracts.

        Args:
            request: Operation-discriminated portfolio operations request.

        Returns:
            The portfolio builder projection and issues on success,
            otherwise a structured interface failure.
        """
        ...


@runtime_checkable
class AdministerCapabilitiesCapability(Protocol):
    """Protocol for the capability administration gateway."""

    async def administer_capabilities(
        self,
        request: AdministerCapabilitiesRequest,
    ) -> AdministerCapabilitiesSuccess | InterfaceFailure:
        """Resolve and expose capability-administration projections.

        Args:
            request: Operation-discriminated capability administration
                request.

        Returns:
            The capability administration projection on success, otherwise
            a structured interface failure.
        """
        ...


@runtime_checkable
class OperateTradingCapability(Protocol):
    """Protocol for the governed trading operations gateway."""

    async def operate_trading(
        self,
        request: OperateTradingRequest,
    ) -> OperateTradingSuccess | InterfaceFailure:
        """Resolve and expose governed operational projections and commands.

        Args:
            request: Operation-discriminated trading operations request.

        Returns:
            The session, readiness, preview, kill switch, market state, or
            operator analytics projection on success, otherwise a
            structured interface failure.
        """
        ...

    def subscribe_operate_trading_events(
        self,
        request: OperateTradingEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver governed trading operations events as domain events.

        Args:
            request: Owner-required subscription selector carrying the
                scope filter, session binding, resume position, and
                bounded replay limit.

        Returns:
            An asynchronous iterator of trading operations events wrapped
            in the common domain event envelope with ordered replay and
            resync semantics.
        """
        ...
