"""Unit and acceptance tests for HTTP and Event Contracts (FEAT-IFACE-SERVE_API_EVENTS)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.contracts.interfaces.errors import (
    ApiIncompatibleError,
    ArtifactAccessDeniedError,
    EventCursorExpiredError,
    IdempotencyConflictError,
    JobNotFoundError,
    VersionConflictError,
)
from app.contracts.interfaces.models import (
    ApiDeprecationNotice,
    ArtifactDownloadRequest,
    ArtifactRangeSpec,
    AsyncJobRef,
    AsyncJobState,
    MutationIdempotencyRecord,
    MutationStatus,
)
from app.services.interfaces.api_events.api_events import ApiEventsService
from app.services.interfaces.api_events.config import ApiEventsConfig

# ============================================================================
# FR-IFACE-SERVE_VERSIONED_API
# ============================================================================


def test_iface_serve_versioned_api() -> None:
    """Verify FR-IFACE-SERVE_VERSIONED_API exposes OpenAPI v1 route specifications."""
    service = ApiEventsService(ApiEventsConfig(title="HaruQuantAI Engine"))
    manifest = service.fr_iface_serve_versioned_api("v1")

    assert manifest.openapi_version == "3.1.0"
    assert manifest.title == "HaruQuantAI Engine"
    assert manifest.version == "1.0.0"
    assert "/api/v1" in manifest.servers

    routes = {r.path: r for r in manifest.routes}
    assert "/api/v1/workspaces" in routes
    assert "/api/v1/catalogue/instruments" in routes
    assert "/api/v1/data/series" in routes
    assert "/api/v1/strategies" in routes
    assert "/api/v1/simulations" in routes
    assert "/api/v1/jobs/{job_id}" in routes
    assert "/api/v1/databanks" in routes
    assert "/api/v1/results/{result_id}" in routes
    assert "/api/v1/artifacts/{artifact_id}" in routes
    assert "/api/v1/plugins" in routes
    assert "/api/v1/codegen/generate" in routes

    assert service.get_openapi_manifest().title == "HaruQuantAI Engine"
    assert service.serve_versioned_api("1.0.0").version == "1.0.0"


def test_iface_serve_versioned_api_unsupported_version() -> None:
    """Verify requesting an unsupported version raises ApiIncompatibleError."""
    service = ApiEventsService()
    with pytest.raises(ApiIncompatibleError) as exc:
        service.fr_iface_serve_versioned_api("v9.0.0")
    assert exc.value.error_code == "UPGRADE_REQUIRED"


# ============================================================================
# FR-IFACE-ENFORCE_CONCURRENCY_TOKENS
# ============================================================================


def test_iface_enforce_concurrency_tokens() -> None:
    """Verify FR-IFACE-ENFORCE_CONCURRENCY_TOKENS matches tokens and detects conflicts."""
    service = ApiEventsService()

    assert service.fr_iface_enforce_concurrency_tokens("res_1", 1, 1) is True
    assert service.fr_iface_enforce_concurrency_tokens("res_1", "1", 1) is True
    assert (
        service.fr_iface_enforce_concurrency_tokens("res_1", '"etag_42"', "etag_42")
        is True
    )

    with pytest.raises(VersionConflictError) as exc_info:
        service.fr_iface_enforce_concurrency_tokens(
            "res_1", expected_version=1, current_version=2
        )
    assert exc_info.value.error_code == "VERSION_CONFLICT"
    assert exc_info.value.expected_version == "1"
    assert exc_info.value.current_version == "2"

    with pytest.raises(VersionConflictError):
        service.fr_iface_enforce_concurrency_tokens(
            "res_1", expected_version=None, current_version=1
        )

    assert service.validate_concurrency_token("res_1", 5, 5) is True


# ============================================================================
# FR-IFACE-DEDUPLICATE_MUTATIONS
# ============================================================================


def test_iface_deduplicate_mutations() -> None:
    """Verify FR-IFACE-DEDUPLICATE_MUTATIONS caches and replays idempotent mutations."""
    service = ApiEventsService()
    invocations = 0

    def mutation_action() -> dict[str, object]:
        nonlocal invocations
        invocations += 1
        return {"created_id": "strat_99", "status": "COMMITTED"}

    res1 = service.fr_iface_deduplicate_mutations(
        idempotency_key="idempotency_abc",
        session_id="session_1",
        command_type="CREATE_STRATEGY",
        execute_fn=mutation_action,
    )
    assert invocations == 1
    assert res1 == {"created_id": "strat_99", "status": "COMMITTED"}

    res2 = service.fr_iface_deduplicate_mutations(
        idempotency_key="idempotency_abc",
        session_id="session_1",
        command_type="CREATE_STRATEGY",
        execute_fn=mutation_action,
    )
    assert invocations == 1
    assert res2 == res1

    res3 = service.fr_iface_deduplicate_mutations(
        idempotency_key="idempotency_abc",
        session_id="session_2",
        command_type="CREATE_STRATEGY",
        execute_fn=mutation_action,
    )
    assert invocations == 2
    assert res3 == res1


def test_iface_deduplicate_mutations_in_flight_conflict() -> None:
    """Verify concurrent in-flight mutation with same key raises IdempotencyConflictError."""
    service = ApiEventsService()
    key = "sess_1:DO_WORK:idem_inflight"
    service._idempotency_store[key] = MutationIdempotencyRecord(
        idempotency_key="idem_inflight",
        session_id="sess_1",
        command_type="DO_WORK",
        status=MutationStatus.IN_PROGRESS,
    )

    with pytest.raises(IdempotencyConflictError):
        service.fr_iface_deduplicate_mutations(
            idempotency_key="idem_inflight",
            session_id="sess_1",
            command_type="DO_WORK",
            execute_fn=lambda: {"result": "ok"},
        )


def test_iface_deduplicate_mutations_failed_execution() -> None:
    """Verify mutation failure marks record as FAILED and raises exception."""
    service = ApiEventsService()

    def failing_fn() -> dict[str, object]:
        raise ValueError("Invalid strategy AST")

    with pytest.raises(ValueError, match="Invalid strategy AST"):
        service.fr_iface_deduplicate_mutations(
            idempotency_key="key_fail",
            session_id="sess_1",
            command_type="CREATE_STRATEGY",
            execute_fn=failing_fn,
        )

    record = service._idempotency_store["sess_1:CREATE_STRATEGY:key_fail"]
    assert record.status == MutationStatus.FAILED
    assert record.error_code == "ValueError"


# ============================================================================
# FR-IFACE-REPLAY_INTERFACE_EVENTS
# ============================================================================


def test_iface_replay_interface_events() -> None:
    """Verify FR-IFACE-REPLAY_INTERFACE_EVENTS replays events after Last-Event-ID."""
    service = ApiEventsService(ApiEventsConfig(event_buffer_size=10))

    empty_batch = service.fr_iface_replay_interface_events(None)
    assert empty_batch.events == ()
    assert empty_batch.is_resync_required is False

    for i in range(1, 6):
        service.publish_interface_event(
            event_type="JOB_PROGRESS",
            topic="jobs",
            payload={"progress": i * 0.2},
        )

    batch_all = service.fr_iface_replay_interface_events(None, max_events=10)
    assert len(batch_all.events) == 5
    assert batch_all.events[0].event_id == "evt_00000001"
    assert batch_all.events[-1].event_id == "evt_00000005"
    assert batch_all.is_resync_required is False

    batch_sub = service.fr_iface_replay_interface_events("evt_00000003")
    assert len(batch_sub.events) == 2
    assert [e.event_id for e in batch_sub.events] == ["evt_00000004", "evt_00000005"]


def test_iface_replay_interface_events_resync_on_expired_cursor() -> None:
    """Verify retention gap triggers resync required flag."""
    service = ApiEventsService(ApiEventsConfig(event_buffer_size=3))

    for i in range(1, 6):
        service.publish_interface_event("TICK", "market", {"price": 100 + i})

    batch = service.fr_iface_replay_interface_events("evt_00000001")
    assert batch.is_resync_required is True
    assert batch.events == ()


def test_iface_replay_interface_events_invalid_cursor_format() -> None:
    """Verify malformed cursor raises EventCursorExpiredError."""
    service = ApiEventsService()
    service.publish_interface_event("TEST", "test", {})

    with pytest.raises(EventCursorExpiredError):
        service.fr_iface_replay_interface_events("invalid-cursor-format")


# ============================================================================
# FR-IFACE-TRACK_ASYNC_JOBS
# ============================================================================


def test_iface_track_async_jobs() -> None:
    """Verify FR-IFACE-TRACK_ASYNC_JOBS tracks long-running async tasks."""
    service = ApiEventsService()

    job = service.fr_iface_track_async_jobs("SIMULATION_BACKTEST")
    assert job.command_type == "SIMULATION_BACKTEST"
    assert job.state == AsyncJobState.QUEUED
    assert job.progress == 0.0

    fetched = service.get_async_job(job.job_id)
    assert fetched.job_id == job.job_id

    service.update_async_job(
        job.job_id,
        state=AsyncJobState.RUNNING,
        progress=0.75,
        stage="Processing orders",
    )
    running = service.get_async_job(job.job_id)
    assert running.state == AsyncJobState.RUNNING
    assert running.progress == 0.75
    assert running.stage == "Processing orders"

    service.update_async_job(
        job.job_id,
        state=AsyncJobState.COMPLETED,
        progress=1.0,
        result_ref="res_sim_88",
    )
    completed = service.get_async_job(job.job_id)
    assert completed.state == AsyncJobState.COMPLETED
    assert completed.result_ref == "res_sim_88"


def test_iface_track_async_jobs_not_found() -> None:
    """Verify querying or updating an unknown job ID raises JobNotFoundError."""
    service = ApiEventsService()
    with pytest.raises(JobNotFoundError):
        service.get_async_job("non-existent-job-id")

    with pytest.raises(JobNotFoundError):
        service.update_async_job(
            job_id="non-existent-job-id", state=AsyncJobState.FAILED
        )


def test_iface_track_async_jobs_with_runner() -> None:
    """Verify submitting a job with a runner callable executes it."""
    service = ApiEventsService()

    def run_work(job_ref: AsyncJobRef) -> None:
        service.update_async_job(
            job_ref.job_id, state=AsyncJobState.COMPLETED, progress=1.0
        )

    job = service.submit_async_job("IMPORT_TICKS", runner_fn=run_work)
    completed = service.get_async_job(job.job_id)
    assert completed.state == AsyncJobState.COMPLETED
    assert completed.progress == 1.0


# ============================================================================
# FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS
# ============================================================================


def test_iface_validate_artifact_downloads(tmp_path: Path) -> None:
    """Verify FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS validates files and byte ranges."""
    service = ApiEventsService()

    artifact_file = tmp_path / "sim_result.json"
    content = b'{"strategy": "EMA_CROSS", "profit": 4200.50}'
    artifact_file.write_bytes(content)

    req_full = ArtifactDownloadRequest(
        artifact_id="art_01",
        filename="sim_result.json",
    )
    resp_full = service.fr_iface_validate_artifact_downloads(
        request=req_full,
        storage_root=tmp_path,
        committed_artifacts={"art_01": artifact_file},
    )
    assert resp_full.is_partial is False
    assert resp_full.data_bytes == content
    assert resp_full.total_size == len(content)
    assert resp_full.content_type == "application/json"

    req_range = ArtifactDownloadRequest(
        artifact_id="art_01",
        filename="sim_result.json",
        range_spec=ArtifactRangeSpec(start_byte=0, end_byte=11),
    )
    resp_range = service.fr_iface_validate_artifact_downloads(
        request=req_range,
        storage_root=tmp_path,
        committed_artifacts={"art_01": artifact_file},
    )
    assert resp_range.is_partial is True
    assert resp_range.data_bytes == b'{"strategy":'
    assert resp_range.range_spec is not None
    assert resp_range.range_spec.start_byte == 0
    assert resp_range.range_spec.end_byte == 11


def test_iface_validate_artifact_downloads_traversal_denied(tmp_path: Path) -> None:
    """Verify directory traversal attempts are blocked."""
    service = ApiEventsService()
    outside_file = tmp_path.parent / "secret.env"
    outside_file.write_text("API_SECRET=12345", encoding="utf-8")

    req = ArtifactDownloadRequest(
        artifact_id="art_malicious",
        filename="../secret.env",
    )
    with pytest.raises(
        ArtifactAccessDeniedError, match="escapes designated artifact storage root"
    ):
        service.fr_iface_validate_artifact_downloads(
            request=req,
            storage_root=tmp_path,
        )


def test_iface_validate_artifact_downloads_uncommitted_denied(tmp_path: Path) -> None:
    """Verify non-committed artifact requests are denied."""
    service = ApiEventsService()
    req = ArtifactDownloadRequest(
        artifact_id="art_uncommitted",
        filename="draft.json",
    )
    with pytest.raises(ArtifactAccessDeniedError, match="not committed"):
        service.fr_iface_validate_artifact_downloads(
            request=req,
            storage_root=tmp_path,
            committed_artifacts={"art_other": tmp_path / "other.json"},
        )


def test_iface_validate_artifact_downloads_missing_file(tmp_path: Path) -> None:
    """Verify missing file on disk raises ArtifactAccessDeniedError."""
    service = ApiEventsService()
    req = ArtifactDownloadRequest(
        artifact_id="art_missing",
        filename="ghost.json",
    )
    with pytest.raises(ArtifactAccessDeniedError, match="does not exist on disk"):
        service.fr_iface_validate_artifact_downloads(
            request=req,
            storage_root=tmp_path,
            committed_artifacts={"art_missing": tmp_path / "ghost.json"},
        )


def test_iface_validate_artifact_downloads_size_exceeded(tmp_path: Path) -> None:
    """Verify exceeding max configured download size raises error."""
    service = ApiEventsService(ApiEventsConfig(max_artifact_download_bytes=10))
    huge_file = tmp_path / "huge.dat"
    huge_file.write_bytes(b"0123456789ABCDEF")

    req = ArtifactDownloadRequest(artifact_id="art_huge", filename="huge.dat")
    with pytest.raises(ArtifactAccessDeniedError, match="exceeds maximum"):
        service.fr_iface_validate_artifact_downloads(
            request=req,
            storage_root=tmp_path,
            committed_artifacts={"art_huge": huge_file},
        )


# ============================================================================
# FR-IFACE-EVOLVE_API_COMPATIBLY
# ============================================================================


def test_iface_evolve_api_compatibly() -> None:
    """Verify FR-IFACE-EVOLVE_API_COMPATIBLY checks compatibility and deprecations."""
    service = ApiEventsService()
    service.add_deprecation_notice(
        ApiDeprecationNotice(
            feature_or_endpoint="/api/v1/legacy-auth",
            deprecated_version="1.1.0",
            sunset_version="2.0.0",
            replacement="/api/v1/sessions",
        )
    )

    report = service.fr_iface_evolve_api_compatibly("v1.2.0")
    assert report.is_compatible is True
    assert report.current_version == "1.0.0"
    assert len(report.deprecations) == 1
    assert report.deprecations[0].feature_or_endpoint == "/api/v1/legacy-auth"
    assert len(report.breaking_changes) == 0

    incompat = service.fr_iface_evolve_api_compatibly("v2.0.0")
    assert incompat.is_compatible is False
    assert len(incompat.breaking_changes) > 0

    deprecations = service.get_deprecations()
    assert len(deprecations) == 1
