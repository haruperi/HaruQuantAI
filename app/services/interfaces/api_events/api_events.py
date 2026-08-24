"""HTTP and Event Contracts service implementation.

Purpose:
    Expose versioned, idempotent, paged, and bounded HTTP/OpenAPI contracts
    and SSE event streams for the HaruQuantAI platform.

Key capabilities:
    * Generate and serve OpenAPI 3.1 contracts for /api/v1 platform endpoints.
    * Enforce optimistic concurrency tokens to prevent lost updates.
    * Deduplicate retryable create/action mutations with scoped keys.
    * Stream and replay retained interface events over SSE with cursors.
    * Track long-running asynchronous jobs with immediate handle return.
    * Validate committed artifact downloads, ranges, and path containment.
    * Enforce API evolution compatibility and machine-readable deprecations.

Python API usage:
    from app.services.interfaces.api_events.api_events import ApiEventsService
    from app.services.interfaces.api_events.config import ApiEventsConfig

    service = ApiEventsService(ApiEventsConfig())
    manifest = service.serve_versioned_api("v1")
    concurrency_ok = service.validate_concurrency_token("res_1", 1, 1)

CLI usage:
    uv run python -m app.services.interfaces.api_events.api_events
"""

from __future__ import annotations

import datetime
import logging
import mimetypes
import tempfile
import uuid
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import override

from app.contracts.interfaces.errors import (
    ApiIncompatibleError,
    ArtifactAccessDeniedError,
    EventCursorExpiredError,
    IdempotencyConflictError,
    JobNotFoundError,
    VersionConflictError,
)
from app.contracts.interfaces.models import (
    ApiCompatibilityReport,
    ApiDeprecationNotice,
    ApiRouteSpec,
    ArtifactDownloadRequest,
    ArtifactDownloadResponse,
    ArtifactRangeSpec,
    AsyncJobRef,
    AsyncJobState,
    EventReplayBatch,
    InterfaceEventEnvelope,
    MutationIdempotencyRecord,
    MutationStatus,
    OpenApiManifest,
)
from app.contracts.interfaces.ports import ServeApiEventsCapability
from app.services.interfaces.api_events.config import ApiEventsConfig

logger = logging.getLogger(__name__)

_SUPPORTED_VERSIONS: tuple[str, ...] = ("v1", "1.0.0")

_STANDARD_V1_ROUTES: tuple[ApiRouteSpec, ...] = (
    ApiRouteSpec(
        path="/api/v1/workspaces",
        method="GET",
        summary="List discovered workspaces",
        description="Retrieve all available workspaces in the environment.",
        tags=("Workspace",),
    ),
    ApiRouteSpec(
        path="/api/v1/workspaces",
        method="POST",
        summary="Initialize workspace",
        description="Create and initialize a new local workspace.",
        tags=("Workspace",),
    ),
    ApiRouteSpec(
        path="/api/v1/catalogue/instruments",
        method="GET",
        summary="Query instruments",
        description="Query the canonical instrument catalogue with filtering.",
        tags=("Catalogue",),
    ),
    ApiRouteSpec(
        path="/api/v1/data/series",
        method="GET",
        summary="Query data series",
        description="Retrieve normalized historical market data series.",
        tags=("Data",),
    ),
    ApiRouteSpec(
        path="/api/v1/strategies",
        method="GET",
        summary="List strategies",
        description="List authored typed strategies in the workspace.",
        tags=("Strategy",),
    ),
    ApiRouteSpec(
        path="/api/v1/strategies",
        method="POST",
        summary="Save strategy version",
        description="Commit a new typed StrategyVersion AST.",
        tags=("Strategy",),
    ),
    ApiRouteSpec(
        path="/api/v1/simulations",
        method="POST",
        summary="Start simulation run",
        description="Admit and launch a deterministic simulation backtest job.",
        tags=("Simulator",),
    ),
    ApiRouteSpec(
        path="/api/v1/jobs/{job_id}",
        method="GET",
        summary="Get async job status",
        description="Query lifecycle status and progress of an async job.",
        tags=("Jobs",),
    ),
    ApiRouteSpec(
        path="/api/v1/databanks",
        method="GET",
        summary="Query databanks",
        description="Query databank collections and filtered candidate results.",
        tags=("Analytics",),
    ),
    ApiRouteSpec(
        path="/api/v1/results/{result_id}",
        method="GET",
        summary="Get simulation result",
        description="Retrieve committed result metrics and equity segments.",
        tags=("Simulator", "Analytics"),
    ),
    ApiRouteSpec(
        path="/api/v1/artifacts/{artifact_id}",
        method="GET",
        summary="Download artifact",
        description="Download a committed artifact file with range support.",
        tags=("Artifacts",),
    ),
    ApiRouteSpec(
        path="/api/v1/plugins",
        method="GET",
        summary="List plugins",
        description="List installed and active plugins in the workspace.",
        tags=("Plugins",),
    ),
    ApiRouteSpec(
        path="/api/v1/codegen/generate",
        method="POST",
        summary="Generate target code",
        description="Generate MQL5 or deployment packages from a strategy.",
        tags=("Strategy", "Codegen"),
    ),
)


class ApiEventsService(ServeApiEventsCapability):
    """Production implementation of HTTP, OpenAPI, and Event stream capabilities."""

    def __init__(self, config: ApiEventsConfig | None = None) -> None:
        """Initialize the API and Events service.

        Args:
            config: Optional configuration instance.
        """
        self._config = config or ApiEventsConfig()
        self._event_buffer: deque[InterfaceEventEnvelope] = deque(
            maxlen=self._config.event_buffer_size
        )
        self._event_sequence: int = 0
        self._idempotency_store: dict[str, MutationIdempotencyRecord] = {}
        self._jobs_store: dict[str, AsyncJobRef] = {}
        self._deprecations: list[ApiDeprecationNotice] = []
        logger.info(
            "ApiEventsService initialized with api_version=%s, buffer_size=%d",
            self._config.api_version,
            self._config.event_buffer_size,
        )

    def fr_iface_serve_versioned_api(
        self,
        api_version: str = "v1",
    ) -> OpenApiManifest:
        """FR-IFACE-SERVE_VERSIONED_API: Expose versioned OpenAPI contracts.

        Args:
            api_version: Requested API version string.

        Returns:
            OpenApiManifest containing all exposed route definitions.

        Raises:
            ApiIncompatibleError: If requested API version is unsupported.
        """
        normalized = api_version.strip().lower()
        if normalized not in _SUPPORTED_VERSIONS:
            raise ApiIncompatibleError(
                client_version=api_version,
                supported_versions=_SUPPORTED_VERSIONS,
            )

        return OpenApiManifest(
            openapi_version="3.1.0",
            title=self._config.title,
            version="1.0.0",
            description=(
                "OpenAPI 3.1 contracts for HaruQuantAI workspace, catalogue, "
                "data, strategies, simulations, jobs, databanks, results, "
                "artifacts, plugins, and code generation."
            ),
            routes=_STANDARD_V1_ROUTES,
            servers=("/api/v1",),
        )

    @override
    def get_openapi_manifest(self) -> OpenApiManifest:
        """Get OpenAPI 3.1 contract specification for served endpoints.

        Returns:
            OpenApiManifest containing all exposed route definitions.
        """
        return self.fr_iface_serve_versioned_api(self._config.api_version)

    @override
    def serve_versioned_api(self, api_version: str = "v1") -> OpenApiManifest:
        """Serve versioned API contracts and route schemas for a version label.

        Args:
            api_version: API version string (e.g. 'v1').

        Returns:
            OpenApiManifest filtered and validated for the specified version.
        """
        return self.fr_iface_serve_versioned_api(api_version)

    def fr_iface_enforce_concurrency_tokens(
        self,
        resource_id: str,
        expected_version: str | int | None,
        current_version: str | int,
    ) -> bool:
        """FR-IFACE-ENFORCE_CONCURRENCY_TOKENS: Validate concurrency tokens.

        Args:
            resource_id: Protected resource identifier.
            expected_version: Expected version or concurrency token.
            current_version: Current server-side version of the resource.

        Returns:
            True if version matches and mutation is permitted.

        Raises:
            VersionConflictError: If expected version does not match current.
        """
        if expected_version is None:
            msg = "Precondition required: expected version token is missing"
            raise VersionConflictError(
                message=msg,
                expected_version=None,
                current_version=current_version,
            )

        exp_str = str(expected_version).strip().strip('"')
        cur_str = str(current_version).strip().strip('"')

        if exp_str != cur_str:
            logger.warning(
                "Concurrency conflict on resource %s: expected=%s, current=%s",
                resource_id,
                exp_str,
                cur_str,
            )
            msg = f"Version conflict on resource '{resource_id}'"
            raise VersionConflictError(
                message=msg,
                expected_version=exp_str,
                current_version=cur_str,
            )

        return True

    @override
    def validate_concurrency_token(
        self,
        resource_id: str,
        expected_version: str | int | None,
        current_version: str | int,
    ) -> bool:
        """Validate an optimistic concurrency token against current version.

        Args:
            resource_id: Protected resource identifier.
            expected_version: Expected version or concurrency token.
            current_version: Current server-side version of the resource.

        Returns:
            True if version matches and mutation is permitted.
        """
        return self.fr_iface_enforce_concurrency_tokens(
            resource_id=resource_id,
            expected_version=expected_version,
            current_version=current_version,
        )

    def fr_iface_deduplicate_mutations(
        self,
        idempotency_key: str,
        session_id: str,
        command_type: str,
        execute_fn: Callable[[], dict[str, object]],
    ) -> dict[str, object]:
        """FR-IFACE-DEDUPLICATE_MUTATIONS: Execute mutation idempotently.

        Args:
            idempotency_key: Client-supplied idempotency key.
            session_id: Session identifier scope.
            command_type: Command classification.
            execute_fn: Callable producing the mutation response dictionary.

        Returns:
            Dictionary response payload from initial execution or cached replay.

        Raises:
            IdempotencyConflictError: If a concurrent execution is in flight.
        """
        key = f"{session_id}:{command_type}:{idempotency_key}"
        existing = self._idempotency_store.get(key)

        if existing is not None:
            if existing.status == MutationStatus.IN_PROGRESS:
                logger.warning(
                    "Idempotency conflict: key %s in flight for session %s",
                    idempotency_key,
                    session_id,
                )
                raise IdempotencyConflictError(idempotency_key=idempotency_key)
            if (
                existing.status == MutationStatus.COMPLETED
                and existing.response_payload is not None
            ):
                logger.info(
                    "Idempotent replay served for key %s (session %s)",
                    idempotency_key,
                    session_id,
                )
                return existing.response_payload

        now_str = datetime.datetime.now(datetime.UTC).isoformat()
        in_progress_record = MutationIdempotencyRecord(
            idempotency_key=idempotency_key,
            session_id=session_id,
            command_type=command_type,
            status=MutationStatus.IN_PROGRESS,
            created_at=now_str,
        )
        self._idempotency_store[key] = in_progress_record

        try:
            result = execute_fn()
            completed_str = datetime.datetime.now(datetime.UTC).isoformat()
            self._idempotency_store[key] = MutationIdempotencyRecord(
                idempotency_key=idempotency_key,
                session_id=session_id,
                command_type=command_type,
                status=MutationStatus.COMPLETED,
                response_payload=result,
                created_at=now_str,
                completed_at=completed_str,
            )
            return result
        except Exception as exc:
            self._idempotency_store[key] = MutationIdempotencyRecord(
                idempotency_key=idempotency_key,
                session_id=session_id,
                command_type=command_type,
                status=MutationStatus.FAILED,
                error_code=type(exc).__name__,
                created_at=now_str,
                completed_at=datetime.datetime.now(datetime.UTC).isoformat(),
            )
            raise

    @override
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
        """
        return self.fr_iface_deduplicate_mutations(
            idempotency_key=idempotency_key,
            session_id=session_id,
            command_type=command_type,
            execute_fn=execute_fn,
        )

    @override
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
        self._event_sequence += 1
        now_str = datetime.datetime.now(datetime.UTC).isoformat()
        event_id = f"evt_{self._event_sequence:08d}"

        envelope = InterfaceEventEnvelope(
            event_id=event_id,
            sequence_number=self._event_sequence,
            event_type=event_type,
            topic=topic,
            payload=payload,
            timestamp=now_str,
        )
        self._event_buffer.append(envelope)
        return envelope

    def fr_iface_replay_interface_events(
        self,
        last_event_id: str | None,
        max_events: int = 100,
    ) -> EventReplayBatch:
        """FR-IFACE-REPLAY_INTERFACE_EVENTS: Replay retained SSE events.

        Args:
            last_event_id: Last received event ID / cursor string.
            max_events: Maximum number of events to return in this batch.

        Returns:
            EventReplayBatch with envelopes, next cursor, and resync flags.

        Raises:
            EventCursorExpiredError: If requested cursor is invalid.
        """
        if not self._event_buffer:
            return EventReplayBatch(
                events=(),
                next_cursor=None,
                has_more=False,
                is_resync_required=False,
            )

        oldest_seq = self._event_buffer[0].sequence_number

        if last_event_id is None:
            events_slice = list(self._event_buffer)[-max_events:]
            next_cursor = events_slice[-1].event_id if events_slice else None
            return EventReplayBatch(
                events=tuple(events_slice),
                next_cursor=next_cursor,
                has_more=False,
                is_resync_required=False,
            )

        try:
            target_seq = int(last_event_id.replace("evt_", ""))
        except ValueError:
            raise EventCursorExpiredError(cursor=last_event_id) from None

        if target_seq < oldest_seq - 1:
            logger.warning(
                "Event cursor expired: requested %d, oldest is %d",
                target_seq,
                oldest_seq,
            )
            return EventReplayBatch(
                events=(),
                next_cursor=self._event_buffer[-1].event_id,
                has_more=False,
                is_resync_required=True,
            )

        matching = [
            evt for evt in self._event_buffer if evt.sequence_number > target_seq
        ]
        batch = matching[:max_events]
        has_more = len(matching) > max_events
        next_cursor = batch[-1].event_id if batch else last_event_id

        return EventReplayBatch(
            events=tuple(batch),
            next_cursor=next_cursor,
            has_more=has_more,
            is_resync_required=False,
        )

    @override
    def replay_interface_events(
        self,
        last_event_id: str | None,
        max_events: int = 100,
    ) -> EventReplayBatch:
        """Replay retained interface events following a cursor.

        Args:
            last_event_id: Last received event ID / cursor string, or None.
            max_events: Maximum number of events to return in this batch.

        Returns:
            EventReplayBatch with envelopes, next cursor, and resync flags.
        """
        return self.fr_iface_replay_interface_events(
            last_event_id=last_event_id,
            max_events=max_events,
        )

    def fr_iface_track_async_jobs(
        self,
        command_type: str,
        runner_fn: Callable[[AsyncJobRef], None] | None = None,
    ) -> AsyncJobRef:
        """FR-IFACE-TRACK_ASYNC_JOBS: Submit long-running task and return job ref.

        Args:
            command_type: Initiating action category.
            runner_fn: Optional synchronous runner callable.

        Returns:
            AsyncJobRef with unique job ID and initial QUEUED state.
        """
        job_id = str(uuid.uuid4())
        now_str = datetime.datetime.now(datetime.UTC).isoformat()

        job_ref = AsyncJobRef(
            job_id=job_id,
            command_type=command_type,
            state=AsyncJobState.QUEUED,
            progress=0.0,
            stage="Job admitted into execution queue",
            created_at=now_str,
            updated_at=now_str,
        )
        self._jobs_store[job_id] = job_ref
        logger.info("Admitted async job %s for command %s", job_id, command_type)

        if runner_fn is not None:
            job_ref = self.update_async_job(
                job_id,
                state=AsyncJobState.RUNNING,
                stage="Executing runner",
            )
            try:
                runner_fn(job_ref)
            except Exception as exc:
                self.update_async_job(
                    job_id,
                    state=AsyncJobState.FAILED,
                    error_message=str(exc),
                )
                raise

        return self._jobs_store[job_id]

    @override
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
        return self.fr_iface_track_async_jobs(command_type, runner_fn)

    @override
    def get_async_job(self, job_id: str) -> AsyncJobRef:
        """Query the current state and progress of an asynchronous job.

        Args:
            job_id: Unique job UUID string.

        Returns:
            AsyncJobRef describing current state, progress, and stage.

        Raises:
            JobNotFoundError: If job ID is not registered.
        """
        job = self._jobs_store.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id=job_id)
        return job

    @override
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
        existing = self.get_async_job(job_id)
        now_str = datetime.datetime.now(datetime.UTC).isoformat()

        new_state = state if state is not None else existing.state
        new_progress = progress if progress is not None else existing.progress
        new_stage = stage if stage is not None else existing.stage
        new_err = error_message if error_message is not None else existing.error_message
        new_res = result_ref if result_ref is not None else existing.result_ref

        updated = AsyncJobRef(
            job_id=job_id,
            command_type=existing.command_type,
            state=new_state,
            progress=max(0.0, min(1.0, new_progress)),
            stage=new_stage,
            error_message=new_err,
            result_ref=new_res,
            created_at=existing.created_at,
            updated_at=now_str,
        )
        self._jobs_store[job_id] = updated
        return updated

    def fr_iface_validate_artifact_downloads(
        self,
        request: ArtifactDownloadRequest,
        storage_root: Path,
        committed_artifacts: dict[str, Path] | None = None,
    ) -> ArtifactDownloadResponse:
        """FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS: Validate artifact download.

        Args:
            request: Download request specification.
            storage_root: Storage directory root containing committed artifacts.
            committed_artifacts: Optional mapping of committed artifact paths.

        Returns:
            ArtifactDownloadResponse containing validated data and range info.

        Raises:
            ArtifactAccessDeniedError: If artifact is uncommitted or escapes root.
        """
        resolved_root = storage_root.resolve()

        if committed_artifacts is not None:
            if request.artifact_id not in committed_artifacts:
                msg = f"Artifact '{request.artifact_id}' is not committed"
                raise ArtifactAccessDeniedError(
                    path=request.filename,
                    reason=msg,
                )
            target_path = committed_artifacts[request.artifact_id].resolve()
        else:
            target_path = (resolved_root / request.filename).resolve()

        try:
            target_path.relative_to(resolved_root)
        except ValueError:
            logger.exception(
                "Directory traversal detected: target=%s, root=%s",
                target_path,
                resolved_root,
            )
            msg = "Path escapes designated artifact storage root"
            raise ArtifactAccessDeniedError(
                path=request.filename,
                reason=msg,
            ) from None

        if not target_path.is_file():
            msg = f"Artifact file '{target_path.name}' does not exist on disk"
            raise ArtifactAccessDeniedError(
                path=request.filename,
                reason=msg,
            )

        total_size = target_path.stat().st_size
        if total_size > self._config.max_artifact_download_bytes:
            msg = (
                f"Artifact size ({total_size} bytes) exceeds maximum "
                f"({self._config.max_artifact_download_bytes} bytes)"
            )
            raise ArtifactAccessDeniedError(
                path=request.filename,
                reason=msg,
            )

        content_type, _ = mimetypes.guess_type(target_path.name)
        if not content_type:
            content_type = "application/octet-stream"

        if request.range_spec is not None:
            start = max(0, request.range_spec.start_byte)
            end = (
                min(total_size - 1, request.range_spec.end_byte)
                if request.range_spec.end_byte is not None
                else total_size - 1
            )
            if start > end or start >= total_size:
                msg = f"Requested range bytes={start}-{end} is unsatisfiable"
                raise ArtifactAccessDeniedError(
                    path=request.filename,
                    reason=msg,
                )

            with target_path.open("rb") as f:
                f.seek(start)
                data_bytes = f.read(end - start + 1)

            applied_range = ArtifactRangeSpec(
                start_byte=start,
                end_byte=end,
                total_bytes=total_size,
            )
            return ArtifactDownloadResponse(
                artifact_id=request.artifact_id,
                filename=target_path.name,
                content_type=content_type,
                total_size=total_size,
                data_bytes=data_bytes,
                is_partial=True,
                range_spec=applied_range,
            )

        data_bytes = target_path.read_bytes()
        return ArtifactDownloadResponse(
            artifact_id=request.artifact_id,
            filename=target_path.name,
            content_type=content_type,
            total_size=total_size,
            data_bytes=data_bytes,
            is_partial=False,
            range_spec=None,
        )

    @override
    def validate_artifact_download(
        self,
        request: ArtifactDownloadRequest,
        storage_root: Path,
        committed_artifacts: dict[str, Path] | None = None,
    ) -> ArtifactDownloadResponse:
        """Validate and resolve an artifact file download.

        Args:
            request: Download request specification.
            storage_root: Storage directory root containing committed artifacts.
            committed_artifacts: Optional mapping of committed artifact paths.

        Returns:
            ArtifactDownloadResponse containing validated data and range info.
        """
        return self.fr_iface_validate_artifact_downloads(
            request=request,
            storage_root=storage_root,
            committed_artifacts=committed_artifacts,
        )

    def fr_iface_evolve_api_compatibly(
        self,
        client_version: str,
    ) -> ApiCompatibilityReport:
        """FR-IFACE-EVOLVE_API_COMPATIBLY: Enforce API evolution compatibility.

        Args:
            client_version: Client semantic version string.

        Returns:
            ApiCompatibilityReport with compatibility status and deprecations.
        """
        normalized = client_version.strip().lower()

        if normalized.startswith(("v1", "1.", "1")):
            return ApiCompatibilityReport(
                is_compatible=True,
                current_version="1.0.0",
                client_version=client_version,
                deprecations=tuple(self._deprecations),
                breaking_changes=(),
            )

        breaking = (
            (
                f"Client major version '{client_version}' is incompatible with "
                "server API v1.0.0. Upgrade to client >=1.0.0 is required."
            ),
        )
        return ApiCompatibilityReport(
            is_compatible=False,
            current_version="1.0.0",
            client_version=client_version,
            deprecations=tuple(self._deprecations),
            breaking_changes=breaking,
        )

    @override
    def check_api_compatibility(self, client_version: str) -> ApiCompatibilityReport:
        """Check whether a client API version is compatible with this server.

        Args:
            client_version: Semantic version string of the client.

        Returns:
            ApiCompatibilityReport with compatibility status and deprecations.
        """
        return self.fr_iface_evolve_api_compatibly(client_version)

    def add_deprecation_notice(self, notice: ApiDeprecationNotice) -> None:
        """Register a machine-readable deprecation notice.

        Args:
            notice: Notice describing deprecated endpoint or feature.
        """
        self._deprecations.append(notice)

    @override
    def get_deprecations(self) -> tuple[ApiDeprecationNotice, ...]:
        """Get all active machine-readable deprecation notices for this version.

        Returns:
            Tuple of ApiDeprecationNotice descriptors.
        """
        return tuple(self._deprecations)


def _scenario_1_versioned_api(service: ApiEventsService) -> None:
    """Verify FR-IFACE-SERVE_VERSIONED_API scenario.

    Args:
        service: Active ApiEventsService instance.

    Raises:
        RuntimeError: If OpenAPI manifest validation fails.
    """
    min_expected_routes = 10
    manifest = service.fr_iface_serve_versioned_api("v1")
    if not manifest.routes or len(manifest.routes) < min_expected_routes:
        msg = "FR-IFACE-SERVE_VERSIONED_API failed: missing routes"
        raise RuntimeError(msg)
    print(f"[OK] FR-IFACE-SERVE_VERSIONED_API: Served {len(manifest.routes)} routes")


def _scenario_2_concurrency(service: ApiEventsService) -> None:
    """Verify FR-IFACE-ENFORCE_CONCURRENCY_TOKENS scenario.

    Args:
        service: Active ApiEventsService instance.

    Raises:
        RuntimeError: If concurrency checks fail.
    """
    token_ok = service.fr_iface_enforce_concurrency_tokens("strategy_1", 3, 3)
    if not token_ok:
        msg = "FR-IFACE-ENFORCE_CONCURRENCY_TOKENS failed on match"
        raise RuntimeError(msg)
    try:
        service.fr_iface_enforce_concurrency_tokens("strategy_1", 2, 3)
        msg = "FR-IFACE-ENFORCE_CONCURRENCY_TOKENS failed to reject mismatch"
        raise RuntimeError(msg)
    except VersionConflictError:
        print("[OK] FR-IFACE-ENFORCE_CONCURRENCY_TOKENS: Conflict on stale token")


def _scenario_3_idempotency(service: ApiEventsService) -> None:
    """Verify FR-IFACE-DEDUPLICATE_MUTATIONS scenario.

    Args:
        service: Active ApiEventsService instance.

    Raises:
        RuntimeError: If mutation deduplication fails.
    """
    call_count = 0

    def mutation_fn() -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        return {"order_id": "ord_1001", "status": "SUBMITTED"}

    res1 = service.fr_iface_deduplicate_mutations(
        "idem_key_42", "sess_1", "SUBMIT_ORDER", mutation_fn
    )
    res2 = service.fr_iface_deduplicate_mutations(
        "idem_key_42", "sess_1", "SUBMIT_ORDER", mutation_fn
    )
    if call_count != 1 or res1 != res2:
        msg = "FR-IFACE-DEDUPLICATE_MUTATIONS failed: mutation called more than once"
        raise RuntimeError(msg)
    print("[OK] FR-IFACE-DEDUPLICATE_MUTATIONS: Mutation deduplicated on replay")


def _scenario_4_events(service: ApiEventsService) -> None:
    """Verify FR-IFACE-REPLAY_INTERFACE_EVENTS scenario.

    Args:
        service: Active ApiEventsService instance.

    Raises:
        RuntimeError: If event replay verification fails.
    """
    expected_event_count = 2
    service.publish_interface_event("JOB_QUEUED", "jobs", {"job_id": "job_1"})
    service.publish_interface_event("JOB_STARTED", "jobs", {"job_id": "job_1"})
    service.publish_interface_event("JOB_COMPLETED", "jobs", {"job_id": "job_1"})

    batch = service.fr_iface_replay_interface_events("evt_00000001", max_events=10)
    if len(batch.events) != expected_event_count:
        msg = f"FR-IFACE-REPLAY_INTERFACE_EVENTS failed: got {len(batch.events)} events"
        raise RuntimeError(msg)
    print(f"[OK] FR-IFACE-REPLAY_INTERFACE_EVENTS: Replayed {len(batch.events)} events")


def _scenario_5_jobs(service: ApiEventsService) -> None:
    """Verify FR-IFACE-TRACK_ASYNC_JOBS scenario.

    Args:
        service: Active ApiEventsService instance.

    Raises:
        RuntimeError: If job tracking verification fails.
    """
    expected_progress = 0.5
    job_ref = service.fr_iface_track_async_jobs("SIMULATION_RUN")
    if job_ref.state != AsyncJobState.QUEUED:
        msg = "FR-IFACE-TRACK_ASYNC_JOBS failed initial QUEUED state"
        raise RuntimeError(msg)
    service.update_async_job(
        job_ref.job_id,
        state=AsyncJobState.RUNNING,
        progress=expected_progress,
        stage="Simulating bars",
    )
    updated = service.get_async_job(job_ref.job_id)
    if updated.progress != expected_progress or updated.state != AsyncJobState.RUNNING:
        msg = "FR-IFACE-TRACK_ASYNC_JOBS failed progress update"
        raise RuntimeError(msg)
    print(f"[OK] FR-IFACE-TRACK_ASYNC_JOBS: Async job {job_ref.job_id} tracked")


def _scenario_6_artifacts(service: ApiEventsService) -> None:
    """Verify FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS scenario.

    Args:
        service: Active ApiEventsService instance.

    Raises:
        RuntimeError: If artifact download verification fails.
    """
    expected_slice_len = 16
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir).resolve()
        artifact_file = root_path / "result_123.json"
        artifact_file.write_bytes(b'{"equity": [10000, 10500, 11200], "sharpe": 1.85}')

        req = ArtifactDownloadRequest(
            artifact_id="art_123",
            filename="result_123.json",
            range_spec=ArtifactRangeSpec(start_byte=0, end_byte=15),
        )
        dl_resp = service.fr_iface_validate_artifact_downloads(
            request=req,
            storage_root=root_path,
            committed_artifacts={"art_123": artifact_file},
        )
        if not dl_resp.is_partial or len(dl_resp.data_bytes) != expected_slice_len:
            msg = "FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS range slice failed"
            raise RuntimeError(msg)

        traversal_req = ArtifactDownloadRequest(
            artifact_id="art_bad",
            filename="../secret.env",
        )
        try:
            service.fr_iface_validate_artifact_downloads(
                traversal_req, storage_root=root_path
            )
            msg = "FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS failed to block traversal"
            raise RuntimeError(msg)
        except ArtifactAccessDeniedError:
            print("[OK] FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS: Verified download")


def _scenario_7_compatibility(service: ApiEventsService) -> None:
    """Verify FR-IFACE-EVOLVE_API_COMPATIBLY scenario.

    Args:
        service: Active ApiEventsService instance.

    Raises:
        RuntimeError: If API compatibility verification fails.
    """
    compat = service.fr_iface_evolve_api_compatibly("v1.2.0")
    if not compat.is_compatible:
        msg = "FR-IFACE-EVOLVE_API_COMPATIBLY failed for v1.2.0"
        raise RuntimeError(msg)
    incompat = service.fr_iface_evolve_api_compatibly("v2.0.0")
    if incompat.is_compatible:
        msg = "FR-IFACE-EVOLVE_API_COMPATIBLY failed to reject v2.0.0"
        raise RuntimeError(msg)
    print("[OK] FR-IFACE-EVOLVE_API_COMPATIBLY: Version compatibility verified")


def _run_usage_example() -> None:
    """Run standalone teaching and verification harness for FEAT-IFACE-SERVE_API_EVENTS.

    Raises:
        RuntimeError: If any scenario assertion fails.
    """
    print("=================================================================")
    print("Executing FEAT-IFACE-SERVE_API_EVENTS Standalone Usage Harness")
    print("=================================================================")

    config = ApiEventsConfig(title="HaruQuantAI Gateway", api_version="v1")
    service = ApiEventsService(config)

    _scenario_1_versioned_api(service)
    _scenario_2_concurrency(service)
    _scenario_3_idempotency(service)
    _scenario_4_events(service)
    _scenario_5_jobs(service)
    _scenario_6_artifacts(service)
    _scenario_7_compatibility(service)

    print("\n[SUCCESS] All 7 FR scenarios verified successfully!")


if __name__ == "__main__":
    _run_usage_example()
