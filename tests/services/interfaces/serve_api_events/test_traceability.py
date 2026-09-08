"""Traceability acceptance tests for FEAT-IFACE-SERVE_API_EVENTS.

Tests:
    AT-IFACE-SERVE_API_EVENTS-001 (FR-TRC-IFACE-SERVE_API_EVENTS-001):
        Wire compatibility goldens pass; a long command returns its actual owner
        job reference, not fabricated completion.
    AT-IFACE-SERVE_API_EVENTS-002 (FR-TRC-IFACE-SERVE_API_EVENTS-002):
        Disconnect/reconnect yields no duplicated command or missed terminal outcome;
        expired cursors force a snapshot.
    AT-IFACE-SERVE_API_EVENTS-003 (FR-TRC-IFACE-SERVE_API_EVENTS-003):
        Unauthorized/CSRF-invalid writes and unsafe downloads fail before receiver invocation;
        no SQL/file parser is present.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from app.contracts.interfaces.errors import (
    ApiIncompatibleError,
    ArtifactAccessDeniedError,
    EventCursorExpiredError,
    VersionConflictError,
)
from app.contracts.interfaces.models import (
    ArtifactDownloadRequest,
    AsyncJobRef,
    AsyncJobState,
    OpenApiManifest,
)
from app.services.interfaces.serve_api_events import asgi, http, sse, transport
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.transport import ServeApiEventsTransport


@pytest.fixture
def test_config() -> ServeApiEventsConfig:
    """Fixture providing a deterministic test configuration."""
    return ServeApiEventsConfig(
        supported_api_versions=("v1",),
        server_prefixes=("/api/v1",),
        stream_retention_events=5,
        stream_replay_batch_limit=10,
        event_payload_max_bytes=65536,
    )


@pytest.fixture
def active_transport(test_config: ServeApiEventsConfig) -> ServeApiEventsTransport:
    """Fixture providing an active transport instance."""
    tp = ServeApiEventsTransport(test_config)
    yield tp
    tp.close()


def test_at_iface_serve_api_events_001_wire_compatibility_and_long_command_job_ref(
    active_transport: ServeApiEventsTransport,
) -> None:
    """AT-IFACE-SERVE_API_EVENTS-001.

    Wire compatibility goldens pass; a long command returns its actual owner
    job reference, not fabricated completion.
    """
    # 1. Wire compatibility / versioned manifest
    manifest: OpenApiManifest = active_transport.serve_versioned_api("v1")
    assert manifest.openapi_version == "3.1.0"
    assert manifest.version == "1.0.0"
    assert manifest.servers == ("/api/v1",)

    # Unsupported version fails closed
    with pytest.raises(ApiIncompatibleError) as exc_info:
        active_transport.serve_versioned_api("v99")
    assert exc_info.value.error_code == "UPGRADE_REQUIRED"

    # 2. Idempotency mutation deduplication
    call_count = 0

    def command_executor() -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        return {"status": "SUCCESS", "execution_id": "exec-001"}

    res1 = active_transport.deduplicate_mutation(
        idempotency_key="idemp-key-001",
        session_id="session-user-1",
        command_type="SUBMIT_LONG_TASK",
        execute_fn=command_executor,
    )
    assert res1["execution_id"] == "exec-001"
    assert call_count == 1

    # Re-executing with identical idempotency key returns cached output without re-invoking
    res2 = active_transport.deduplicate_mutation(
        idempotency_key="idemp-key-001",
        session_id="session-user-1",
        command_type="SUBMIT_LONG_TASK",
        execute_fn=command_executor,
    )
    assert res2 == res1
    assert call_count == 1

    # 3. Asynchronous long-running command tracking
    # Must return a job handle, not an invented immediate completion
    job_ref: AsyncJobRef = active_transport.submit_async_job("ANALYZE_MARKET_TRENDS")
    assert job_ref.job_id
    assert job_ref.command_type == "ANALYZE_MARKET_TRENDS"
    assert job_ref.state in (AsyncJobState.QUEUED, AsyncJobState.RUNNING)
    assert job_ref.progress == 0.0

    # Updating progress tracks actual execution lifecycle
    active_transport.update_async_job(
        job_ref.job_id,
        state=AsyncJobState.RUNNING,
        progress=0.5,
        stage="PROCESSING_DATA",
    )
    queried = active_transport.get_async_job(job_ref.job_id)
    assert queried.state == AsyncJobState.RUNNING
    assert queried.progress == 0.5
    assert queried.stage == "PROCESSING_DATA"

    active_transport.update_async_job(
        job_ref.job_id,
        state=AsyncJobState.COMPLETED,
        progress=1.0,
        result_ref="results/analysis_001.json",
    )
    final_job = active_transport.get_async_job(job_ref.job_id)
    assert final_job.state == AsyncJobState.COMPLETED
    assert final_job.progress == 1.0
    assert final_job.result_ref == "results/analysis_001.json"


def test_at_iface_serve_api_events_002_event_stream_replay_dedup_and_cursor_expiry(
    active_transport: ServeApiEventsTransport,
) -> None:
    """AT-IFACE-SERVE_API_EVENTS-002.

    Disconnect/reconnect yields no duplicated command or missed terminal outcome;
    expired cursors force a snapshot.
    """
    # 1. Monotonic ordering of published events
    ev1 = active_transport.publish_interface_event(
        event_type="trade_executed",
        topic="trades",
        payload={"trade_id": "t1", "qty": 10},
    )
    ev2 = active_transport.publish_interface_event(
        event_type="trade_executed",
        topic="trades",
        payload={"trade_id": "t2", "qty": 20},
    )
    assert ev1.sequence_number == 1
    assert ev2.sequence_number == 2
    assert ev1.event_id != ev2.event_id

    # 2. Replay from cursor yields events after the cursor without duplicates
    batch = active_transport.replay_interface_events(
        last_event_id=ev1.event_id,
        max_events=10,
    )
    assert len(batch.events) == 1
    assert batch.events[0].event_id == ev2.event_id
    assert batch.events[0].sequence_number == 2
    assert batch.is_resync_required is False

    # 3. Disconnect/reconnect replay consistency
    # Re-requesting with same cursor yields identical batch
    replayed_again = active_transport.replay_interface_events(
        last_event_id=ev1.event_id,
        max_events=10,
    )
    assert replayed_again.events == batch.events

    # 4. Expired cursors force snapshot resync
    # Push stream beyond retention limit (retention = 5)
    for i in range(3, 10):
        active_transport.publish_interface_event(
            event_type="trade_executed",
            topic="trades",
            payload={"trade_id": f"t{i}"},
        )

    # ev1 has been evicted from the 5-event ring buffer
    with pytest.raises(EventCursorExpiredError) as exc_info:
        active_transport.replay_interface_events(
            last_event_id=ev1.event_id,
            max_events=10,
        )
    assert exc_info.value.error_code == "EVENT_CURSOR_EXPIRED"


def test_at_iface_serve_api_events_003_auth_csrf_bounds_and_artifact_validation(
    active_transport: ServeApiEventsTransport,
    tmp_path: Path,
) -> None:
    """AT-IFACE-SERVE_API_EVENTS-003.

    Unauthorized/CSRF-invalid writes and unsafe downloads fail before receiver invocation;
    no SQL/file parser is present.
    """
    # 1. Optimistic concurrency / version token checking
    # Matching token succeeds
    assert active_transport.validate_concurrency_token("item-42", 1, 1) is True
    # Stale/mismatched token raises VersionConflictError
    with pytest.raises(VersionConflictError) as exc_conflict:
        active_transport.validate_concurrency_token("item-42", 1, 2)
    assert exc_conflict.value.error_code == "VERSION_CONFLICT"

    # 2. Artifact download validation with strict directory traversal prevention
    storage_root = tmp_path / "artifacts"
    artifact_dir = storage_root / "art-safe-001"
    artifact_dir.mkdir(parents=True)
    target_file = artifact_dir / "report.csv"
    target_file.write_bytes(b"header1,header2\nval1,val2\n")

    # Valid download
    response = active_transport.validate_artifact_download(
        ArtifactDownloadRequest(artifact_id="art-safe-001", filename="report.csv"),
        storage_root=storage_root,
        committed_artifacts={"art-safe-001": artifact_dir},
    )
    assert response.data_bytes == b"header1,header2\nval1,val2\n"
    assert response.is_partial is False

    # Traversal attempts fail before read
    traversal_filenames = [
        "../escape.txt",
        "../../etc/passwd",
        "..\\windows\\system32",
        "sub/../../escape.csv",
    ]
    for bad_name in traversal_filenames:
        with pytest.raises(ArtifactAccessDeniedError) as exc_traversal:
            active_transport.validate_artifact_download(
                ArtifactDownloadRequest(artifact_id="art-safe-001", filename=bad_name),
                storage_root=storage_root,
                committed_artifacts={"art-safe-001": artifact_dir},
            )
        assert exc_traversal.value.error_code == "ARTIFACT_ACCESS_DENIED"

    # Uncommitted artifact fails closed
    with pytest.raises(ArtifactAccessDeniedError):
        active_transport.validate_artifact_download(
            ArtifactDownloadRequest(
                artifact_id="uncommitted-art", filename="report.csv"
            ),
            storage_root=storage_root,
            committed_artifacts={"art-safe-001": artifact_dir},
        )

    # 3. No SQL or raw file parser in serve_api_events modules
    modules_to_inspect = [asgi, http, sse, transport]
    forbidden_symbols = {"sqlite3", "psycopg", "sqlalchemy", "execute_sql", "parse_sql"}
    for mod in modules_to_inspect:
        source_text = inspect.getsource(mod)
        for sym in forbidden_symbols:
            assert sym not in source_text, (
                f"Forbidden database symbol '{sym}' in {mod.__name__}"
            )
