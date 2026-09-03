"""Serve-api-events transport: the capability provider assembly.

Purpose:
    Compose the HTTP boundary and the event stream buffer into the
    ServeApiEventsCapability provider, translate kernel capability absence
    into the stable CAPABILITY_UNAVAILABLE failure, and own bounded
    idempotent disposal.

Key capabilities:
    * Implement every ServeApiEventsCapability protocol method.
    * Serve versioned OpenAPI manifests and compatibility reports.
    * Publish ordered events and replay them from bounded cursors.
    * Translate CapabilityUnavailableError into InterfaceFailure.

Python API usage:
    transport = ServeApiEventsTransport(ServeApiEventsConfig())
    envelope = transport.publish_interface_event("tick", "market", {})
    failure = translate_capability_unavailable(
        CapabilityUnavailableError("data.market-snapshots@1")
    )

CLI usage:
    uv run python -m app.services.interfaces.serve_api_events.transport
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid7

from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import EventCursorExpiredError, InterfaceFailure
from app.kernel.capability import CapabilityUnavailableError
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.http import HttpBoundary
from app.services.interfaces.serve_api_events.sse import EventStreamBuffer

if TYPE_CHECKING:
    from app.contracts.interfaces.models import (
        ApiCompatibilityReport,
        ApiDeprecationNotice,
        ArtifactDownloadRequest,
        ArtifactDownloadResponse,
        AsyncJobRef,
        AsyncJobState,
        EventReplayBatch,
        InterfaceEventEnvelope,
        OpenApiManifest,
    )


def translate_capability_unavailable(
    error: CapabilityUnavailableError,
) -> InterfaceFailure:
    """Translate a kernel capability absence into the stable failure result.

    The translation performs no mutation and carries the missing
    capability identifier so external consumers can block unsafe commands
    instead of receiving an invented fallback.

    Args:
        error: Kernel resolution failure carrying the missing identifier.

    Returns:
        Structured CAPABILITY_UNAVAILABLE failure envelope.
    """
    return InterfaceFailure(
        request_id=str(uuid7()),
        code="CAPABILITY_UNAVAILABLE",
        problem=ProblemDetails(
            type="urn:haruquantai:error:capability-unavailable",
            title="Capability unavailable",
            status=503,
            code="CAPABILITY_UNAVAILABLE",
            detail=(
                f"Capability '{error.capability}' has no active provider; "
                "the request was not executed."
            ),
            capability_key=error.capability,
        ),
    )


class ServeApiEventsTransport:
    """ServeApiEventsCapability provider for one mounted feature generation.

    The transport owns no business logic and no business-domain
    dependency; it composes the HTTP boundary and the event stream buffer
    and exposes exactly the protocol declared in
    ``app/contracts/interfaces/ports.py``.
    """

    def __init__(self, config: ServeApiEventsConfig) -> None:
        """Assemble the transport from validated configuration.

        Args:
            config: Feature configuration with version labels and bounds.
        """
        self._config = config
        self._http = HttpBoundary(config)
        self._events = EventStreamBuffer(config)

    @property
    def config(self) -> ServeApiEventsConfig:
        """Return the validated transport configuration."""
        return self._config

    def get_openapi_manifest(self) -> OpenApiManifest:
        """Get the complete OpenAPI contract specification.

        Returns:
            OpenAPI manifest for all served endpoints.
        """
        return self._http.get_openapi_manifest()

    def serve_versioned_api(self, api_version: str = "v1") -> OpenApiManifest:
        """Serve versioned API contracts for one version label.

        Args:
            api_version: API version string such as 'v1'.

        Returns:
            OpenAPI manifest filtered to the requested version.

        Raises:
            ApiIncompatibleError: If the requested version is unsupported.
        """
        return self._http.serve_versioned_api(api_version)

    def validate_concurrency_token(
        self,
        resource_id: str,
        expected_version: str | int | None,
        current_version: str | int,
    ) -> bool:
        """Validate an optimistic concurrency token.

        Args:
            resource_id: Protected resource identifier.
            expected_version: Expected token supplied by the caller.
            current_version: Current server-side resource version.

        Returns:
            True if the version matches and the mutation is permitted.

        Raises:
            VersionConflictError: If the expected version is stale.
        """
        return self._http.validate_concurrency_token(
            resource_id,
            expected_version,
            current_version,
        )

    def deduplicate_mutation(
        self,
        idempotency_key: str,
        session_id: str,
        command_type: str,
        execute_fn: Callable[[], dict[str, object]],
    ) -> dict[str, object]:
        """Execute a mutation idempotently for one idempotency scope.

        Args:
            idempotency_key: Client-supplied idempotency key.
            session_id: Session or caller scope identifier.
            command_type: Command classification.
            execute_fn: Callable producing the mutation response.

        Returns:
            Response payload from the initial execution or cached replay.

        Raises:
            IdempotencyConflictError: If the same key is already executing.
        """
        return self._http.deduplicate_mutation(
            idempotency_key,
            session_id,
            command_type,
            execute_fn,
        )

    def publish_interface_event(
        self,
        event_type: str,
        topic: str,
        payload: dict[str, object],
    ) -> InterfaceEventEnvelope:
        """Publish one typed event into the bounded interface buffer.

        Args:
            event_type: Domain event classification name.
            topic: Topic or channel name.
            payload: Event data mapping.

        Returns:
            Envelope with assigned sequence and event ID.
        """
        return self._events.publish(event_type, topic, payload)

    def replay_interface_events(
        self,
        last_event_id: str | None,
        max_events: int = 100,
    ) -> EventReplayBatch:
        """Replay retained interface events following a cursor.

        Args:
            last_event_id: Last received event ID, or None for the tail.
            max_events: Maximum number of events in this batch.

        Returns:
            Batch with envelopes, the next cursor, and resync flags.

        Raises:
            EventCursorExpiredError: If the cursor is beyond retention.
        """
        return self._events.replay(last_event_id, max_events)

    def submit_async_job(
        self,
        command_type: str,
        runner_fn: Callable[[AsyncJobRef], None] | None = None,
    ) -> AsyncJobRef:
        """Submit a long-running task and return its job reference.

        Args:
            command_type: Initiating action category.
            runner_fn: Optional synchronous runner callable.

        Returns:
            Job reference with unique ID and initial state.
        """
        return self._http.submit_async_job(command_type, runner_fn)

    def get_async_job(self, job_id: str) -> AsyncJobRef:
        """Query the current state of an asynchronous job.

        Args:
            job_id: Unique job identifier.

        Returns:
            Job reference with current state and progress.

        Raises:
            JobNotFoundError: If the job is not registered.
        """
        return self._http.get_async_job(job_id)

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
        """Update the state or progress of an active job.

        Args:
            job_id: Target job identifier.
            state: Optional updated lifecycle state.
            progress: Optional progress ratio within [0.0, 1.0].
            stage: Optional stage description.
            error_message: Optional failure description.
            result_ref: Optional result reference pointer.

        Returns:
            Updated job reference.

        Raises:
            JobNotFoundError: If the job is not registered.
        """
        return self._http.update_async_job(
            job_id,
            state=state,
            progress=progress,
            stage=stage,
            error_message=error_message,
            result_ref=result_ref,
        )

    def validate_artifact_download(
        self,
        request: ArtifactDownloadRequest,
        storage_root: Path,
        committed_artifacts: dict[str, Path] | None = None,
    ) -> ArtifactDownloadResponse:
        """Validate and resolve one artifact file download.

        Args:
            request: Download request specification.
            storage_root: Root directory containing committed artifacts.
            committed_artifacts: Optional committed artifact mapping.

        Returns:
            Validated response with payload bytes and range info.

        Raises:
            ArtifactAccessDeniedError: If the artifact is uncommitted,
                missing, or escapes storage-root containment.
        """
        return self._http.validate_artifact_download(
            request,
            storage_root,
            committed_artifacts,
        )

    def check_api_compatibility(self, client_version: str) -> ApiCompatibilityReport:
        """Check whether a client API version is compatible.

        Args:
            client_version: Semantic version string of the client.

        Returns:
            Compatibility report with deprecations and breaking changes.
        """
        return self._http.check_api_compatibility(client_version)

    def get_deprecations(self) -> tuple[ApiDeprecationNotice, ...]:
        """Get active machine-readable deprecation notices.

        Returns:
            Tuple of deprecation descriptors; empty in this foundation.
        """
        return self._http.get_deprecations()

    def close(self) -> None:
        """Dispose both boundary halves; safe to call repeatedly."""
        self._http.close()
        self._events.close()


def _verify_versioning(transport: ServeApiEventsTransport) -> None:
    """Demonstrate manifest serving and compatibility reporting.

    Args:
        transport: Transport under demonstration.

    Raises:
        RuntimeError: If any observed value differs from the contract.
    """
    manifest = transport.serve_versioned_api("v1")
    if manifest.version != "1.0.0" or manifest.servers != ("/api/v1",):
        raise RuntimeError("usage verification: manifest mismatch")
    report = transport.check_api_compatibility("1.0.0")
    if not report.is_compatible:
        raise RuntimeError("usage verification: expected compatible client")


def _verify_streaming(transport: ServeApiEventsTransport) -> int:
    """Demonstrate bounded publish, replay, and retention semantics.

    Args:
        transport: Transport under demonstration.

    Returns:
        Number of events replayed in the bounded demonstration batch.

    Raises:
        RuntimeError: If any observed value differs from the contract.
    """
    published = [
        transport.publish_interface_event("tick", "market", {"index": index})
        for index in range(6)
    ]
    if [event.sequence_number for event in published] != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("usage verification: sequence assignment failed")
    try:
        transport.replay_interface_events(published[0].event_id)
    except EventCursorExpiredError:
        pass
    else:
        raise RuntimeError("usage verification: retention bound not enforced")
    batch = transport.replay_interface_events(published[2].event_id, max_events=10)
    if [event.sequence_number for event in batch.events] != [4, 5]:
        raise RuntimeError("usage verification: replay batch mismatch")
    if not batch.has_more:
        raise RuntimeError("usage verification: has_more flag missing")
    return len(batch.events)


def _verify_idempotency(transport: ServeApiEventsTransport) -> int:
    """Demonstrate exactly-once mutation execution per idempotency scope.

    Args:
        transport: Transport under demonstration.

    Returns:
        Number of times the demonstrated mutation executed.

    Raises:
        RuntimeError: If any observed value differs from the contract.
    """
    calls: list[int] = []

    def mutation() -> dict[str, object]:
        calls.append(1)
        return {"status": "COMPLETED"}

    first = transport.deduplicate_mutation(
        "usage-key", "usage-session", "USAGE", mutation
    )
    replayed = transport.deduplicate_mutation(
        "usage-key", "usage-session", "USAGE", mutation
    )
    if first != replayed or len(calls) != 1:
        raise RuntimeError("usage verification: idempotency dedup failed")
    return len(calls)


def _run_usage_example() -> None:
    """Run the bounded public usage demonstration.

    Raises:
        RuntimeError: If any verified behavior differs from the contract.
    """
    config = ServeApiEventsConfig.from_dict(
        {"stream_retention_events": 4, "stream_replay_batch_limit": 2}
    )
    transport = ServeApiEventsTransport(config)

    _verify_versioning(transport)
    replayed_events = _verify_streaming(transport)
    mutations_executed = _verify_idempotency(transport)

    failure = translate_capability_unavailable(
        CapabilityUnavailableError("interfaces.observe-market-data@1")
    )
    if failure.code != "CAPABILITY_UNAVAILABLE":
        raise RuntimeError("usage verification: unavailable translation failed")

    transport.close()
    transport.close()
    print(
        "Usage verification passed: "
        f"versions={','.join(config.supported_api_versions)} "
        f"replayed_events={replayed_events} "
        f"mutations_executed={mutations_executed} "
        f"unavailable_code={failure.code}"
    )


if __name__ == "__main__":
    _run_usage_example()
