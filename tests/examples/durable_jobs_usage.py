"""Deterministic offline end-to-end durable jobs example for Stage S5.

Demonstrates SQLite storage, content-addressed artifact store, subprocess worker execution,
durable job state machine, artifact publication, restart recovery, persisted transition
events, frozen submission identity, and bounded crash recovery.

Run with: `uv run python -m tests.examples.durable_jobs_usage`
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from dataclasses import replace as dc_replace
from pathlib import Path
from typing import Any

from app.host.artifacts import HOST_ARTIFACTS, ArtifactsConfig
from app.host.bootstrap import approved_catalog_roots, create_runtime
from app.host.jobs import (
    HOST_JOBS,
    JOBS_NAMESPACE,
    JobRequest,
    JobsConfig,
    JobState,
    _deserialize_job_record,
    _serialize_job_record,
)
from app.host.storage import (
    StorageConfig,
    StorageMutation,
    _SqliteStorage,
)
from app.host.workers import WorkersConfig
from app.plugins.algebra import GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import FrozenObject
from app.plugins.spec import PluginRef
from app.plugins.wire import value_to_wire

PRICES = [
    44.34,
    44.09,
    44.15,
    43.61,
    44.33,
    44.83,
    45.10,
    45.42,
    45.84,
    46.08,
    45.89,
    46.03,
    45.61,
    46.28,
    46.28,
    46.00,
]


def _build_rsi_job_graph() -> GraphDocument:
    """Build a valid quantitative RSI graph document."""
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    rsi_node = NodeSpec(
        id="rsi_node",
        plugin_ref=rsi_ref,
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"period": 14}),
    )
    graph_spec = GraphSpec(
        nodes=(rsi_node,),
        designated_roots=(PortRef("rsi_node", "rsi"),),
    )
    return GraphDocument(spec=graph_spec)


def _compose(db_path: Path, artifacts_dir: Path) -> Any:
    """Compose the durable-jobs runtime over isolated temporary stores."""
    return create_runtime(
        catalog_roots=approved_catalog_roots(),
        storage_config=StorageConfig(database_path=db_path),
        artifacts_config=ArtifactsConfig(root_dir=artifacts_dir),
        workers_config=WorkersConfig(max_concurrent_workers=2),
        jobs_config=JobsConfig(poll_interval_seconds=0.01),
    )


async def _phase_one(temp_dir: Path) -> tuple[str, str]:
    """Submit and execute a durable job in a worker subprocess."""
    runtime = _compose(temp_dir / "storage.db", temp_dir / "artifacts")
    async with runtime:
        jobs = runtime.require(HOST_JOBS)
        artifacts = runtime.require(HOST_ARTIFACTS)

        req = JobRequest(
            graph_document=_build_rsi_job_graph(),
            inputs={"rsi_node.values": PRICES},
            idempotency_key="example_job_001",
        )
        submitted = await jobs.submit_job(req)
        print(f"[Stage S5] Job submitted: id={submitted.job_id}, state=queued")

        terminal = await jobs.await_job(submitted.job_id, timeout_seconds=30.0)
        print(
            f"[Stage S5] Job completed: state={terminal.state.value}, "
            f"attempts={terminal.attempts}"
        )
        assert terminal.state == JobState.SUCCEEDED
        assert len(terminal.artifact_refs) == 1

        digest = terminal.artifact_refs[0]
        assert artifacts.has_artifact(digest)
        raw = artifacts.get_artifact_bytes(digest)
        print(
            f"[Stage S5] Result artifact published: digest={digest[:16]}..., "
            f"size={len(raw)} bytes"
        )
        assert b"rsi_node.rsi" in raw
        return submitted.job_id, digest


async def _phase_two(temp_dir: Path, job_id: str, digest: str) -> None:
    """Restart the host and retrieve the same terminal job and artifact."""
    runtime = _compose(temp_dir / "storage.db", temp_dir / "artifacts")
    async with runtime:
        jobs = runtime.require(HOST_JOBS)
        artifacts = runtime.require(HOST_ARTIFACTS)

        persisted = await jobs.get_job(job_id)
        assert persisted is not None
        assert persisted.state == JobState.SUCCEEDED
        assert persisted.artifact_refs == (digest,)

        events = await jobs.job_events(job_id)
        assert [e.to_state for e in events] == [
            JobState.RUNNING,
            JobState.SUCCEEDED,
        ]

        meta = artifacts.get_metadata(digest)
        assert meta is not None
        assert meta.ref.digest == digest
        print(
            f"[Stage S5] Restart verified: job {job_id} and artifact "
            f"{digest[:16]}... recovered with {len(events)} persisted events"
        )


async def _phase_three(temp_dir: Path) -> str:
    """Injected worker crash -> expired lease -> bounded recovery rerun."""
    crash_dir = temp_dir / "crash"
    db_path = crash_dir / "storage.db"
    runtime = _compose(db_path, crash_dir / "artifacts")
    job_id = ""
    async with runtime:
        jobs = runtime.require(HOST_JOBS)
        submitted = await jobs.submit_job(
            JobRequest(
                graph_document=_build_rsi_job_graph(),
                inputs={"rsi_node.values": [10.0, 11.0, 12.0, 13.0, 14.0]},
                idempotency_key="example_crash_001",
                max_attempts=3,
            )
        )
        job_id = submitted.job_id
        baseline = await jobs.await_job(job_id, timeout_seconds=30.0)
        assert baseline.state == JobState.SUCCEEDED

    # Simulate the crash: rewrite the terminal record as an interrupted
    # running job with an expired lease, then restart and prove recovery
    # re-runs it exactly once more.
    storage = _SqliteStorage(StorageConfig(database_path=db_path))
    current = storage.get_record(JOBS_NAMESPACE, job_id)
    assert current is not None
    interrupted = dc_replace(
        _deserialize_job_record(current.payload_bytes, current.revision),
        state=JobState.RUNNING,
        attempts=1,
        lease_owner="crashed_scheduler",
        lease_expires_utc="2020-01-01T00:00:00Z",
    )
    storage.commit_transaction(
        [
            StorageMutation(
                namespace=JOBS_NAMESPACE,
                key=job_id,
                schema_version=1,
                payload_bytes=_serialize_job_record(interrupted),
                expected_revision=current.revision,
            )
        ]
    )
    storage.close()

    runtime2 = _compose(db_path, crash_dir / "artifacts")
    async with runtime2:
        jobs2 = runtime2.require(HOST_JOBS)
        recovered = await jobs2.await_job(job_id, timeout_seconds=30.0)
        assert recovered.state == JobState.SUCCEEDED
        assert recovered.attempts == 2
        events = await jobs2.job_events(job_id)
        assert JobState.RECOVERY_PENDING in [e.to_state for e in events]
        print(
            "[Stage S5] Crash injection recovered: expired lease requeued, "
            f"job rerun to success with attempts={recovered.attempts}"
        )
    return str(job_id)


async def _phase_four(db_path: Path, artifacts_dir: Path, job_id: str) -> None:
    """The frozen submission identity is complete and pinned."""
    runtime = _compose(db_path, artifacts_dir)
    async with runtime:
        jobs = runtime.require(HOST_JOBS)
        frozen_job = await jobs.get_job(job_id)
        assert frozen_job is not None
        frozen = value_to_wire(frozen_job.request_wire)
        assert frozen["wire_version"] == 1
        assert frozen["effect_policy"] == "pure"
        assert "indicator.rsi@1.0.0#compute" in frozen["entry_fingerprints"]
        assert frozen["dependency_fingerprint"]
        assert frozen["input_hash"]
        assert frozen["engine_version"]
        assert frozen["numerical_policies"]
        print(
            "[Stage S5] Submission identity frozen: wire_version, entry "
            "fingerprints, dependency fingerprint, input hash, numerical "
            "policies, engine version, pure effect policy."
        )


async def run_durable_jobs_example() -> None:
    """Execute end-to-end durable job lifecycle."""
    temp_dir = Path(tempfile.mkdtemp(prefix="haru_s5_example_"))
    try:
        job_id, digest = await _phase_one(temp_dir)
        await _phase_two(temp_dir, job_id, digest)
        crash_job_id = await _phase_three(temp_dir)
        await _phase_four(
            temp_dir / "crash" / "storage.db",
            temp_dir / "crash" / "artifacts",
            crash_job_id,
        )
        print(
            "[Stage S5] Durable jobs, SQLite persistence, and artifact "
            "storage verified successfully."
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(run_durable_jobs_example())
