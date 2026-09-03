"""HTTP boundary semantics for the serve-api-events transport.

Purpose:
    Own the transport-level HTTP semantics of the serve-api-events
    capability: API version negotiation, OpenAPI manifest projection,
    compatibility and deprecation reporting, optimistic concurrency
    validation, idempotent mutation deduplication, asynchronous job
    references, and artifact download validation.

Key capabilities:
    * Serve version-filtered OpenAPI manifests for configured API labels.
    * Execute mutations exactly once per idempotency key and session.
    * Track bounded asynchronous job lifecycle transitions.
    * Deny uncommitted or path-traversing artifact downloads.

Python API usage:
    boundary = HttpBoundary(ServeApiEventsConfig())
    manifest = boundary.serve_versioned_api("v1")
    result = boundary.deduplicate_mutation("key", "session", "TEST", fn)

CLI usage:
    uv run python -m app.services.interfaces.serve_api_events.transport
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from app.contracts.interfaces.errors import (
    ApiIncompatibleError,
    ArtifactAccessDeniedError,
    IdempotencyConflictError,
    InterfaceError,
    JobNotFoundError,
    VersionConflictError,
)
from app.contracts.interfaces.models import (
    ApiCompatibilityReport,
    ApiDeprecationNotice,
    ArtifactDownloadRequest,
    ArtifactDownloadResponse,
    AsyncJobRef,
    AsyncJobState,
    MutationIdempotencyRecord,
    MutationStatus,
    OpenApiManifest,
)

if TYPE_CHECKING:
    from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig

_API_VERSION = "1.0.0"
_OPENAPI_VERSION = "3.1.0"
_SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _utc_now() -> str:
    """Return the current instant as an ISO 8601 UTC timestamp.

    Returns:
        Timezone-aware UTC timestamp string.
    """
    return datetime.now(UTC).isoformat()


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semantic version string into numeric components.

    Args:
        version: Dotted semantic version string such as '1.0.0'.

    Returns:
        (major, minor, patch) numeric triple.

    Raises:
        ValueError: If the string is not a valid semantic version.
    """
    if not isinstance(version, str) or not _SEMVER_PATTERN.match(version):
        message = f"version must be a semantic version string: {version!r}"
        raise ValueError(message)
    major, minor, patch = (int(part) for part in version.split("."))
    return (major, minor, patch)


def _versions_equal(expected: str | int, current: str | int) -> bool:
    """Compare two version tokens numerically when both are integral.

    Args:
        expected: Token supplied by the caller.
        current: Authoritative server-side token.

    Returns:
        True when both tokens denote the same version.
    """
    try:
        return int(expected) == int(current)
    except TypeError, ValueError:
        return str(expected) == str(current)


class HttpBoundary:
    """In-memory HTTP boundary state for one mounted transport generation.

    The boundary owns registries for idempotent mutations and asynchronous
    jobs plus the versioning, compatibility, concurrency, and artifact
    validation semantics those registries serve. It performs no network
    I/O and starts no server.
    """

    def __init__(self, config: ServeApiEventsConfig) -> None:
        """Initialize boundary state from validated configuration.

        Args:
            config: Feature configuration with version labels and bounds.
        """
        self._config = config
        self._mutations: dict[tuple[str, str, str], MutationIdempotencyRecord] = {}
        self._jobs: dict[str, AsyncJobRef] = {}
        self._closed = False

    def get_openapi_manifest(self) -> OpenApiManifest:
        """Return the complete OpenAPI manifest for served endpoints.

        Returns:
            OpenAPI 3.1 manifest carrying the configured server prefixes.
            Route specifications are contributed by vertical-slice gateway
            features; the transport foundation serves none itself.

        Raises:
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        return OpenApiManifest(
            openapi_version=_OPENAPI_VERSION,
            title="HaruQuantAI API",
            version=_API_VERSION,
            description=(
                "Versioned HTTP/SSE interface contracts for HaruQuantAI platform."
            ),
            routes=(),
            servers=self._config.server_prefixes,
        )

    def serve_versioned_api(self, api_version: str = "v1") -> OpenApiManifest:
        """Serve the OpenAPI manifest filtered to one API version label.

        Args:
            api_version: API version label such as 'v1'.

        Returns:
            Manifest whose routes all belong to the requested version.

        Raises:
            ApiIncompatibleError: If the version label is not served.
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        if api_version not in self._config.supported_api_versions:
            raise ApiIncompatibleError(
                client_version=api_version,
                supported_versions=self._config.supported_api_versions,
            )
        manifest = self.get_openapi_manifest()
        return replace(
            manifest,
            routes=tuple(
                route_spec
                for route_spec in manifest.routes
                if route_spec.version == api_version
            ),
        )

    def check_api_compatibility(self, client_version: str) -> ApiCompatibilityReport:
        """Check whether a client API version is compatible with the server.

        A client is compatible when its major version matches the server
        major and it does not exceed the server's minor and patch level.

        Args:
            client_version: Semantic version string of the client.

        Returns:
            Compatibility report with deprecations and breaking changes.

        Raises:
            ValueError: If the version string is not a semantic version.
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        client = _parse_semver(client_version)
        current = _parse_semver(_API_VERSION)
        is_compatible = client[0] == current[0] and client[1:] <= current[1:]
        breaking: tuple[str, ...] = ()
        if not is_compatible:
            if client[0] != current[0]:
                breaking = (
                    f"client major version {client[0]} does not match server "
                    f"major version {current[0]}",
                )
            else:
                breaking = (f"client {client_version} exceeds server {_API_VERSION}",)
        return ApiCompatibilityReport(
            is_compatible=is_compatible,
            current_version=_API_VERSION,
            client_version=client_version,
            deprecations=self.get_deprecations(),
            breaking_changes=breaking,
        )

    def get_deprecations(self) -> tuple[ApiDeprecationNotice, ...]:
        """Return active deprecation notices for the current API version.

        Returns:
            Empty tuple; no served surface is deprecated in this
            foundation.

        Raises:
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        return ()

    def validate_concurrency_token(
        self,
        resource_id: str,
        expected_version: str | int | None,
        current_version: str | int,
    ) -> bool:
        """Validate an optimistic concurrency token against current truth.

        Args:
            resource_id: Protected resource identifier for diagnostics.
            expected_version: Caller-supplied expected version or None.
            current_version: Current server-side version of the resource.

        Returns:
            True when the mutation is permitted.

        Raises:
            VersionConflictError: If the expected version is stale.
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        if expected_version is None or _versions_equal(
            expected_version, current_version
        ):
            return True
        raise VersionConflictError(
            message=f"Stale version for resource '{resource_id}'",
            expected_version=expected_version,
            current_version=current_version,
        )

    def deduplicate_mutation(
        self,
        idempotency_key: str,
        session_id: str,
        command_type: str,
        execute_fn: Callable[[], dict[str, object]],
    ) -> dict[str, object]:
        """Execute a mutation exactly once per idempotency scope.

        Repeats of a completed mutation return a copy of the cached
        response without re-execution; repeats of a failed mutation raise
        the recorded failure instead of re-executing.

        Args:
            idempotency_key: Client-supplied idempotency key.
            session_id: Session or caller scope identifier.
            command_type: Command or mutation action category.
            execute_fn: Callable producing the mutation response.

        Returns:
            Response payload from the initial execution or cached replay.

        Raises:
            ValueError: If any scope label is not a non-empty string.
            TypeError: If execute_fn returns a non-dictionary.
            IdempotencyConflictError: If the same key is already executing.
            InterfaceError: When replaying a previously failed mutation or
                if the boundary is disposed.
        """
        self._ensure_open()
        for label, value in (
            ("idempotency_key", idempotency_key),
            ("session_id", session_id),
            ("command_type", command_type),
        ):
            if not isinstance(value, str) or not value:
                message = f"{label} must be a non-empty string"
                raise ValueError(message)
        dedup_key = (session_id, command_type, idempotency_key)
        existing = self._mutations.get(dedup_key)
        if existing is not None:
            if existing.status is MutationStatus.IN_PROGRESS:
                raise IdempotencyConflictError(idempotency_key)
            if existing.status is MutationStatus.COMPLETED:
                return dict(existing.response_payload or {})
            failed_code = existing.error_code or "MUTATION_FAILED"
            raise InterfaceError(
                "Mutation previously failed with " + failed_code,
                error_code=failed_code,
            )
        record = MutationIdempotencyRecord(
            idempotency_key=idempotency_key,
            session_id=session_id,
            command_type=command_type,
            status=MutationStatus.IN_PROGRESS,
            created_at=_utc_now(),
        )
        self._mutations[dedup_key] = record
        try:
            response: object = execute_fn()
        except Exception:
            self._mutations[dedup_key] = replace(
                record,
                status=MutationStatus.FAILED,
                error_code="MUTATION_FAILED",
                completed_at=_utc_now(),
            )
            raise
        if not isinstance(response, dict):
            self._mutations[dedup_key] = replace(
                record,
                status=MutationStatus.FAILED,
                error_code="MUTATION_RESULT_INVALID",
                completed_at=_utc_now(),
            )
            raise TypeError("mutation execute_fn must return a dictionary")
        self._mutations[dedup_key] = replace(
            record,
            status=MutationStatus.COMPLETED,
            response_payload=dict(response),
            completed_at=_utc_now(),
        )
        return dict(response)

    def submit_async_job(
        self,
        command_type: str,
        runner_fn: Callable[[AsyncJobRef], None] | None = None,
    ) -> AsyncJobRef:
        """Register an asynchronous job and optionally run it inline.

        When a runner is supplied it executes synchronously exactly once;
        lifecycle transitions belong to the runner (via
        ``update_async_job``) or to the submitting surface. A runner
        failure marks the job FAILED and re-raises.

        Args:
            command_type: Initiating action category.
            runner_fn: Optional synchronous runner receiving the job ref.

        Returns:
            Job reference with its current state.

        Raises:
            ValueError: If command_type is not a non-empty string.
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        if not isinstance(command_type, str) or not command_type:
            raise ValueError("command_type must be a non-empty string")
        now = _utc_now()
        ref = AsyncJobRef(
            job_id=f"job-{uuid4()}",
            command_type=command_type,
            state=AsyncJobState.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self._jobs[ref.job_id] = ref
        if runner_fn is None:
            return ref
        try:
            runner_fn(ref)
        except Exception as error:
            self._jobs[ref.job_id] = replace(
                ref,
                state=AsyncJobState.FAILED,
                error_message=str(error),
                updated_at=_utc_now(),
            )
            raise
        return self._jobs[ref.job_id]

    def get_async_job(self, job_id: str) -> AsyncJobRef:
        """Query the current state of an asynchronous job.

        Args:
            job_id: Unique job identifier.

        Returns:
            Job reference describing the current lifecycle state.

        Raises:
            JobNotFoundError: If the job is not registered.
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        ref = self._jobs.get(job_id)
        if ref is None:
            raise JobNotFoundError(job_id)
        return ref

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
        """Update the lifecycle state or progress of a job.

        Args:
            job_id: Target job identifier.
            state: Optional updated lifecycle state.
            progress: Optional progress ratio within [0.0, 1.0].
            stage: Optional human-readable stage description.
            error_message: Optional failure description.
            result_ref: Optional completed-result reference pointer.

        Returns:
            Updated job reference.

        Raises:
            JobNotFoundError: If the job is not registered.
            ValueError: If the progress ratio is outside [0.0, 1.0].
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        ref = self._jobs.get(job_id)
        if ref is None:
            raise JobNotFoundError(job_id)
        if progress is not None and not 0.0 <= progress <= 1.0:
            raise ValueError("progress must be within [0.0, 1.0]")
        updated = replace(
            ref,
            state=state if state is not None else ref.state,
            progress=progress if progress is not None else ref.progress,
            stage=stage if stage is not None else ref.stage,
            error_message=(
                error_message if error_message is not None else ref.error_message
            ),
            result_ref=result_ref if result_ref is not None else ref.result_ref,
            updated_at=_utc_now(),
        )
        self._jobs[job_id] = updated
        return updated

    def validate_artifact_download(
        self,
        request: ArtifactDownloadRequest,
        storage_root: Path,
        committed_artifacts: dict[str, Path] | None = None,
    ) -> ArtifactDownloadResponse:
        """Validate and resolve one artifact file download.

        Args:
            request: Download request with artifact id and filename.
            storage_root: Root directory containing committed artifacts.
            committed_artifacts: Optional committed artifact-id mapping;
                when provided, uncommitted ids are denied.

        Returns:
            Validated response with payload bytes and range information.

        Raises:
            ArtifactAccessDeniedError: If the artifact is uncommitted,
                missing, unsafe, or escapes the storage root.
            ValueError: If the requested byte range is out of bounds.
            InterfaceError: If the boundary is disposed.
        """
        self._ensure_open()
        filename = request.filename
        unsafe_filename = (
            not filename
            or "/" in filename
            or "\\" in filename
            or filename in {".", ".."}
        )
        if unsafe_filename:
            raise ArtifactAccessDeniedError(
                filename or "<empty>",
                "filename must be a single safe path segment",
            )
        root = storage_root.resolve()
        if committed_artifacts is not None:
            base = committed_artifacts.get(request.artifact_id)
            if base is None:
                raise ArtifactAccessDeniedError(
                    request.artifact_id,
                    "artifact is not committed",
                )
        else:
            base = root / request.artifact_id
        candidate = (base / filename).resolve()
        if not candidate.is_relative_to(root):
            raise ArtifactAccessDeniedError(
                filename,
                "resolved path escapes the storage root",
            )
        if not candidate.is_file():
            raise ArtifactAccessDeniedError(filename, "artifact file is missing")
        data = candidate.read_bytes()
        total = len(data)
        range_spec = request.range_spec
        if range_spec is None:
            payload = data
            is_partial = False
        else:
            start = range_spec.start_byte
            end = range_spec.end_byte if range_spec.end_byte is not None else total - 1
            if start < 0 or end < start or end >= total:
                raise ValueError("byte range is out of artifact bounds")
            payload = data[start : end + 1]
            is_partial = True
        return ArtifactDownloadResponse(
            artifact_id=request.artifact_id,
            filename=filename,
            content_type="application/octet-stream",
            total_size=total,
            data_bytes=payload,
            is_partial=is_partial,
            range_spec=range_spec,
        )

    def close(self) -> None:
        """Dispose boundary registries; safe to call repeatedly."""
        self._mutations.clear()
        self._jobs.clear()
        self._closed = True

    def _ensure_open(self) -> None:
        """Reject use after disposal.

        Raises:
            InterfaceError: If the boundary is disposed.
        """
        if self._closed:
            raise InterfaceError(
                "HTTP boundary is disposed",
                error_code="TRANSPORT_CLOSED",
            )
