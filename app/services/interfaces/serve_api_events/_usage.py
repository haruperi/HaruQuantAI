"""Bounded offline usage demonstration for FEAT-IFACE-SERVE_API_EVENTS.

Exercises:
    1. Versioned API envelope, OpenAPI negotiation, idempotency deduplication,
       and long-running command async job reference tracking
       (FR-TRC-IFACE-SERVE_API_EVENTS-001, AT-IFACE-SERVE_API_EVENTS-001).
    2. Monotonic event sequencing, stream buffer, replay from cursor,
       and expired cursor handling (FR-TRC-IFACE-SERVE_API_EVENTS-002,
       AT-IFACE-SERVE_API_EVENTS-002).
    3. Concurrency token checks, artifact download directory traversal guards,
       and fail-closed capability translation (FR-TRC-IFACE-SERVE_API_EVENTS-003,
       AT-IFACE-SERVE_API_EVENTS-003, NFR-TRC-IFACE-SERVE_API_EVENTS-001/002).
    4. Idempotent cleanup and disposal.

CLI command:
    uv run --frozen python -m app.services.interfaces.serve_api_events._usage
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.contracts.interfaces.errors import (
    ApiIncompatibleError,
    ArtifactAccessDeniedError,
    EventCursorExpiredError,
    InterfaceError,
    VersionConflictError,
)
from app.contracts.interfaces.models import (
    ArtifactDownloadRequest,
    AsyncJobState,
)
from app.kernel.capability import CapabilityUnavailableError
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.transport import (
    ServeApiEventsTransport,
    translate_capability_unavailable,
)

EXPECTED_HTTP_SERVICE_UNAVAILABLE = 503
STREAM_RETENTION = 5
REPLAY_BATCH_LIMIT = 10
TARGET_JOB_PROGRESS = 0.45
EXPECTED_SECOND_SEQUENCE = 2
TEST_CONCURRENCY_TOKEN = 10
MISMATCHED_CONCURRENCY_TOKEN = 9


def _demo_envelope_and_jobs(transport: ServeApiEventsTransport) -> None:
    """Demonstrate OpenAPI negotiation, idempotency, and async jobs.

    Raises:
        RuntimeError: If envelope or async job invariants fail.
    """
    print("=== [1/4] FR-001: API Envelope, Versioning, Idempotency & Job Tracking ===")
    manifest = transport.serve_versioned_api("v1")
    if manifest.openapi_version != "3.1.0" or manifest.version != "1.0.0":
        msg = f"Unexpected manifest versions: {manifest}"
        raise RuntimeError(msg)

    try:
        transport.serve_versioned_api("v9")
    except ApiIncompatibleError as err:
        if err.error_code != "UPGRADE_REQUIRED":
            msg = f"Unexpected error code: {err.error_code}"
            raise RuntimeError(msg) from err
    else:
        raise RuntimeError("Expected ApiIncompatibleError for unsupported version")

    execution_count = 0

    def execute_mutation() -> dict[str, object]:
        nonlocal execution_count
        execution_count += 1
        return {"status": "SUCCESS", "order_id": "ord-42"}

    first_res = transport.deduplicate_mutation(
        idempotency_key="idem-uuid-001",
        session_id="sess-alpha",
        command_type="SUBMIT_ORDER",
        execute_fn=execute_mutation,
    )
    if first_res.get("order_id") != "ord-42" or execution_count != 1:
        msg = f"First mutation failed: {first_res}, count={execution_count}"
        raise RuntimeError(msg)

    second_res = transport.deduplicate_mutation(
        idempotency_key="idem-uuid-001",
        session_id="sess-alpha",
        command_type="SUBMIT_ORDER",
        execute_fn=execute_mutation,
    )
    if second_res.get("order_id") != "ord-42" or execution_count != 1:
        msg = f"Idempotency replay failed: {second_res}, count={execution_count}"
        raise RuntimeError(msg)

    job_ref = transport.submit_async_job(command_type="CALCULATE_OPTIMIZATION")
    if job_ref.state not in (AsyncJobState.QUEUED, AsyncJobState.RUNNING):
        msg = f"Unexpected job state: {job_ref.state}"
        raise RuntimeError(msg)

    transport.update_async_job(
        job_ref.job_id,
        progress=TARGET_JOB_PROGRESS,
        stage="PERMUTING_GENES",
    )
    queried = transport.get_async_job(job_ref.job_id)
    if queried.progress != TARGET_JOB_PROGRESS or queried.stage != "PERMUTING_GENES":
        msg = f"Async job query mismatch: {queried}"
        raise RuntimeError(msg)
    print("  [OK] Envelope, idempotency and job reference verified.")


def _demo_monotonic_stream(transport: ServeApiEventsTransport) -> None:
    """Demonstrate monotonic event sequences, replay, and cursor eviction.

    Raises:
        RuntimeError: If stream or cursor replay invariants fail.
    """
    print("=== [2/4] FR-002: Monotonic Event Streaming, Replay & Cursor Expiry ===")
    ev1 = transport.publish_interface_event(
        event_type="market_tick",
        topic="market.BTCUSDT",
        payload={"price": 60000.0, "volume": 1.5},
    )
    if ev1.sequence_number != 1:
        msg = f"Expected sequence 1, got {ev1.sequence_number}"
        raise RuntimeError(msg)

    ev2 = transport.publish_interface_event(
        event_type="market_tick",
        topic="market.BTCUSDT",
        payload={"price": 60050.0, "volume": 0.8},
    )
    if ev2.sequence_number != EXPECTED_SECOND_SEQUENCE:
        msg = f"Expected sequence 2, got {ev2.sequence_number}"
        raise RuntimeError(msg)

    batch = transport.replay_interface_events(
        last_event_id=ev1.event_id,
        max_events=10,
    )
    if (
        len(batch.events) != 1
        or batch.events[0].sequence_number != EXPECTED_SECOND_SEQUENCE
    ):
        msg = f"Event replay mismatch: {batch}"
        raise RuntimeError(msg)

    for i in range(3, 10):
        transport.publish_interface_event(
            event_type="market_tick",
            topic="market.BTCUSDT",
            payload={"price": 60000.0 + i},
        )

    try:
        transport.replay_interface_events(
            last_event_id=ev1.event_id,
            max_events=10,
        )
    except EventCursorExpiredError as err:
        if err.error_code != "EVENT_CURSOR_EXPIRED":
            msg = f"Unexpected error code: {err.error_code}"
            raise RuntimeError(msg) from err
    else:
        raise RuntimeError("Expected EventCursorExpiredError for evicted cursor")
    print("  [OK] Stream monotonic ordering, replay, and cursor eviction verified.")


def _demo_artifact_download_security(transport: ServeApiEventsTransport) -> None:
    """Demonstrate artifact download directory traversal guards.

    Raises:
        RuntimeError: If traversal validation or file download fails.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_root = Path(tmp_dir)
        art_dir = storage_root / "art-abc"
        art_dir.mkdir(parents=True)
        (art_dir / "report.pdf").write_bytes(b"%PDF-sample-content")

        dl_resp = transport.validate_artifact_download(
            ArtifactDownloadRequest(artifact_id="art-abc", filename="report.pdf"),
            storage_root=storage_root,
            committed_artifacts={"art-abc": art_dir},
        )
        if dl_resp.data_bytes != b"%PDF-sample-content":
            msg = f"Unexpected downloaded data: {dl_resp.data_bytes!r}"
            raise RuntimeError(msg)

        try:
            transport.validate_artifact_download(
                ArtifactDownloadRequest(
                    artifact_id="art-abc",
                    filename="../etc/passwd",
                ),
                storage_root=storage_root,
                committed_artifacts={"art-abc": art_dir},
            )
        except ArtifactAccessDeniedError as err:
            if "safe path segment" not in str(err):
                msg = f"Unexpected error message: {err}"
                raise RuntimeError(msg) from err
        else:
            raise RuntimeError("Expected ArtifactAccessDeniedError on path traversal")


def _demo_concurrency_and_security(transport: ServeApiEventsTransport) -> None:
    """Demonstrate concurrency checks and error translation.

    Raises:
        RuntimeError: If concurrency checks or error translation fails.
    """
    print("=== [3/4] FR-003: Concurrency, Artifact Bounds & Capability Translation ===")
    if not transport.validate_concurrency_token(
        "res-1",
        TEST_CONCURRENCY_TOKEN,
        TEST_CONCURRENCY_TOKEN,
    ):
        raise RuntimeError("Expected valid concurrency token check to succeed")

    try:
        transport.validate_concurrency_token(
            "res-1",
            MISMATCHED_CONCURRENCY_TOKEN,
            TEST_CONCURRENCY_TOKEN,
        )
    except VersionConflictError as err:
        if err.error_code != "VERSION_CONFLICT":
            msg = f"Unexpected error code: {err.error_code}"
            raise RuntimeError(msg) from err
    else:
        raise RuntimeError("Expected VersionConflictError on mismatched token")

    _demo_artifact_download_security(transport)

    missing_err = CapabilityUnavailableError("interfaces.operate-trading@1")
    failure = translate_capability_unavailable(missing_err)
    if failure.code != "CAPABILITY_UNAVAILABLE":
        msg = f"Unexpected failure code: {failure.code}"
        raise RuntimeError(msg)
    if failure.problem.status != EXPECTED_HTTP_SERVICE_UNAVAILABLE:
        msg = f"Unexpected HTTP status: {failure.problem.status}"
        raise RuntimeError(msg)
    print("  [OK] Concurrency, artifact security, and translation verified.")


def _demo_lifecycle(transport: ServeApiEventsTransport) -> None:
    """Demonstrate transport disposal idempotency and closed state.

    Raises:
        RuntimeError: If lifecycle checks fail.
    """
    print("=== [4/4] Lifecycle Disposal ===")
    transport.close()
    transport.close()
    try:
        transport.serve_versioned_api("v1")
    except InterfaceError as err:
        if err.error_code != "TRANSPORT_CLOSED":
            msg = f"Unexpected error code: {err.error_code}"
            raise RuntimeError(msg) from err
    else:
        raise RuntimeError("Expected InterfaceError after transport close")
    print("  [OK] Idempotent disposal and fail-closed state verified.")


def _run_usage_example() -> None:
    """Execute the bounded offline usage demonstration.

    Raises:
        RuntimeError: If any scenario check fails.
    """
    config = ServeApiEventsConfig(
        supported_api_versions=("v1",),
        stream_retention_events=STREAM_RETENTION,
        stream_replay_batch_limit=REPLAY_BATCH_LIMIT,
    )
    transport = ServeApiEventsTransport(config)
    _demo_envelope_and_jobs(transport)
    _demo_monotonic_stream(transport)
    _demo_concurrency_and_security(transport)
    _demo_lifecycle(transport)

    print(
        "FEAT-IFACE-SERVE_API_EVENTS usage passed: envelope versioning, "
        "monotonic events, async jobs, and path validation confirmed."
    )


if __name__ == "__main__":
    _run_usage_example()
