"""HTTP boundary behavior tests for serve-api-events."""

from pathlib import Path

import pytest
from app.contracts.interfaces.errors import (
    ApiIncompatibleError,
    ArtifactAccessDeniedError,
    IdempotencyConflictError,
    InterfaceError,
    JobNotFoundError,
    VersionConflictError,
)
from app.contracts.interfaces.models import (
    ArtifactDownloadRequest,
    ArtifactRangeSpec,
    AsyncJobRef,
    AsyncJobState,
)
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.http import HttpBoundary


def _boundary(config: ServeApiEventsConfig | None = None) -> HttpBoundary:
    """Build an HTTP boundary with optional overrides."""
    return HttpBoundary(config or ServeApiEventsConfig())


def test_openapi_manifest_reflects_configuration() -> None:
    """Verify the manifest carries configured server prefixes."""
    boundary = _boundary(ServeApiEventsConfig(server_prefixes=("/api/v1", "/api/v2")))
    manifest = boundary.get_openapi_manifest()
    assert manifest.openapi_version == "3.1.0"
    assert manifest.version == "1.0.0"
    assert manifest.servers == ("/api/v1", "/api/v2")
    assert manifest.routes == ()


def test_serve_versioned_api_accepts_supported_label() -> None:
    """Verify a supported version label serves its manifest."""
    boundary = _boundary(ServeApiEventsConfig(supported_api_versions=("v1", "v2")))
    manifest = boundary.serve_versioned_api("v2")
    assert manifest.servers == ("/api/v1",)


def test_serve_versioned_api_rejects_unsupported_label() -> None:
    """Verify an unsupported version label fails closed."""
    boundary = _boundary()
    with pytest.raises(ApiIncompatibleError) as excinfo:
        boundary.serve_versioned_api("v9")
    assert excinfo.value.supported_versions == ("v1",)


def test_compatibility_report_semantics() -> None:
    """Verify compatibility comparisons and breaking-change reporting."""
    boundary = _boundary()
    assert boundary.check_api_compatibility("1.0.0").is_compatible
    assert boundary.check_api_compatibility("0.9.0").is_compatible is False
    assert boundary.check_api_compatibility("1.1.0").is_compatible is False
    report = boundary.check_api_compatibility("2.0.0")
    assert "major" in report.breaking_changes[0]
    with pytest.raises(ValueError, match="semantic version"):
        boundary.check_api_compatibility("one")


def test_deprecations_are_empty_in_foundation() -> None:
    """Verify no deprecations are active."""
    assert _boundary().get_deprecations() == ()


def test_concurrency_token_validation() -> None:
    """Verify token matching, absence, and conflict behavior."""
    boundary = _boundary()
    assert boundary.validate_concurrency_token("res-1", "3", 3)
    assert boundary.validate_concurrency_token("res-1", 3, "3")
    assert boundary.validate_concurrency_token("res-1", None, 7)
    assert boundary.validate_concurrency_token("res-1", "etag-a", "etag-a")
    with pytest.raises(VersionConflictError) as excinfo:
        boundary.validate_concurrency_token("res-1", 2, 3)
    assert excinfo.value.expected_version == 2
    assert excinfo.value.current_version == 3


def test_deduplicate_mutation_executes_once_and_replays_cache() -> None:
    """Verify idempotent execution with cached replay."""
    boundary = _boundary()
    calls: list[int] = []

    def mutation() -> dict[str, object]:
        calls.append(1)
        return {"status": "COMPLETED", "order": "abc"}

    first = boundary.deduplicate_mutation("key-1", "session-1", "ORDER", mutation)
    first["status"] = "MUTATED_LOCALLY"
    replayed = boundary.deduplicate_mutation("key-1", "session-1", "ORDER", mutation)

    assert len(calls) == 1
    assert replayed == {"status": "COMPLETED", "order": "abc"}


def test_deduplicate_mutation_conflicts_with_in_flight_execution() -> None:
    """Verify a concurrent duplicate raises instead of double-executing."""
    boundary = _boundary()

    def reentrant_mutation() -> dict[str, object]:
        return boundary.deduplicate_mutation(
            "key-2", "session-1", "ORDER", lambda: {"status": "NESTED"}
        )

    with pytest.raises(IdempotencyConflictError):
        boundary.deduplicate_mutation("key-2", "session-1", "ORDER", reentrant_mutation)


def test_deduplicate_mutation_records_failure_without_reexecution() -> None:
    """Verify a failed mutation never re-executes on retry."""
    boundary = _boundary()
    calls: list[int] = []

    def failing() -> dict[str, object]:
        calls.append(1)
        raise RuntimeError("broker rejected")

    with pytest.raises(RuntimeError, match="broker rejected"):
        boundary.deduplicate_mutation("key-3", "session-1", "ORDER", failing)
    with pytest.raises(InterfaceError, match="MUTATION_FAILED"):
        boundary.deduplicate_mutation("key-3", "session-1", "ORDER", failing)
    assert len(calls) == 1


def test_deduplicate_mutation_rejects_non_dict_response() -> None:
    """Verify non-dictionary mutation results fail closed."""
    boundary = _boundary()

    def bad_result() -> dict[str, object]:
        return "not-a-dictionary"  # type: ignore[return-value]

    with pytest.raises(TypeError):
        boundary.deduplicate_mutation("key-4", "session-1", "ORDER", bad_result)


def test_async_job_lifecycle() -> None:
    """Verify job submission, inline runner, updates, and lookup."""
    boundary = _boundary()

    def runner(ref: AsyncJobRef) -> None:
        boundary.update_async_job(ref.job_id, state=AsyncJobState.RUNNING, progress=0.5)

    ref = boundary.submit_async_job("BACKTEST", runner)
    assert ref.state is AsyncJobState.RUNNING
    assert boundary.get_async_job(ref.job_id).progress == 0.5

    updated = boundary.update_async_job(
        ref.job_id,
        state=AsyncJobState.COMPLETED,
        progress=1.0,
        stage="finished",
        result_ref="artifact-1",
    )
    assert updated.state is AsyncJobState.COMPLETED
    assert updated.result_ref == "artifact-1"


def test_async_job_failure_marks_job_failed() -> None:
    """Verify a raising runner marks the job failed and re-raises."""

    def failing_runner(_ref: AsyncJobRef) -> None:
        raise RuntimeError("worker crashed")

    boundary = _boundary()
    with pytest.raises(RuntimeError, match="worker crashed"):
        boundary.submit_async_job("BACKTEST", failing_runner)


def test_async_job_unknown_and_invalid_updates() -> None:
    """Verify unknown jobs and out-of-range progress fail closed."""
    boundary = _boundary()
    with pytest.raises(JobNotFoundError):
        boundary.get_async_job("job-missing")
    with pytest.raises(JobNotFoundError):
        boundary.update_async_job("job-missing", state=AsyncJobState.RUNNING)

    ref = boundary.submit_async_job("BACKTEST")
    with pytest.raises(ValueError, match="progress"):
        boundary.update_async_job(ref.job_id, progress=1.5)


def test_artifact_download_full_and_partial(tmp_path: Path) -> None:
    """Verify committed artifact downloads with byte ranges."""
    root = tmp_path
    artifact_dir = root / "art-1"
    artifact_dir.mkdir()
    (artifact_dir / "report.csv").write_bytes(b"0123456789")
    boundary = _boundary()

    full = boundary.validate_artifact_download(
        ArtifactDownloadRequest(artifact_id="art-1", filename="report.csv"),
        root,
        committed_artifacts={"art-1": artifact_dir},
    )
    assert full.data_bytes == b"0123456789"
    assert full.is_partial is False
    assert full.total_size == 10

    partial = boundary.validate_artifact_download(
        ArtifactDownloadRequest(
            artifact_id="art-1",
            filename="report.csv",
            range_spec=ArtifactRangeSpec(start_byte=2, end_byte=5, total_bytes=10),
        ),
        root,
        committed_artifacts={"art-1": artifact_dir},
    )
    assert partial.data_bytes == b"2345"
    assert partial.is_partial is True


def test_artifact_download_denials(tmp_path: Path) -> None:
    """Verify uncommitted, traversal, escape, and missing denials."""
    root = tmp_path
    artifact_dir = root / "art-1"
    artifact_dir.mkdir()
    (artifact_dir / "report.csv").write_bytes(b"0123456789")
    boundary = _boundary()

    with pytest.raises(ArtifactAccessDeniedError, match="not committed"):
        boundary.validate_artifact_download(
            ArtifactDownloadRequest(artifact_id="art-2", filename="report.csv"),
            root,
            committed_artifacts={"art-1": artifact_dir},
        )
    with pytest.raises(ArtifactAccessDeniedError, match="safe path segment"):
        boundary.validate_artifact_download(
            ArtifactDownloadRequest(artifact_id="art-1", filename="../secret"),
            root,
            committed_artifacts={"art-1": artifact_dir},
        )
    with pytest.raises(ArtifactAccessDeniedError, match="missing"):
        boundary.validate_artifact_download(
            ArtifactDownloadRequest(artifact_id="art-1", filename="absent.csv"),
            root,
            committed_artifacts={"art-1": artifact_dir},
        )
    with pytest.raises(ValueError, match="out of artifact bounds"):
        boundary.validate_artifact_download(
            ArtifactDownloadRequest(
                artifact_id="art-1",
                filename="report.csv",
                range_spec=ArtifactRangeSpec(start_byte=8, end_byte=99, total_bytes=10),
            ),
            root,
            committed_artifacts={"art-1": artifact_dir},
        )


def test_closed_boundary_rejects_use() -> None:
    """Verify disposal fails all subsequent operations closed."""
    boundary = _boundary()
    boundary.close()
    boundary.close()
    with pytest.raises(InterfaceError, match="TRANSPORT_CLOSED"):
        boundary.get_openapi_manifest()
