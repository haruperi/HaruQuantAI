"""Deterministic offline end-to-end durable jobs example for Stage S5.

Demonstrates SQLite storage, content-addressed artifact store, subprocess worker execution,
durable job state machine, artifact publication, and restart recovery.

Run with: `uv run python -m tests.examples.durable_jobs_usage`
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from app.host.artifacts import HOST_ARTIFACTS, ArtifactsConfig
from app.host.bootstrap import approved_catalog_roots, create_runtime
from app.host.jobs import (
    HOST_JOBS,
    JobRequest,
    JobsConfig,
    JobState,
)
from app.host.storage import StorageConfig
from app.host.workers import WorkersConfig
from app.plugins.algebra import GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import FrozenObject
from app.plugins.spec import PluginRef


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


async def run_durable_jobs_example() -> None:
    """Execute end-to-end durable job lifecycle."""
    temp_dir = Path(tempfile.mkdtemp(prefix="haru_s5_example_"))
    try:
        db_path = temp_dir / "storage.db"
        artifacts_dir = temp_dir / "artifacts"
        catalog_roots = approved_catalog_roots()

        # Phase 1: Submit and execute durable job in worker subprocess
        runtime1 = create_runtime(
            catalog_roots=catalog_roots,
            storage_config=StorageConfig(database_path=db_path),
            artifacts_config=ArtifactsConfig(root_dir=artifacts_dir),
            workers_config=WorkersConfig(max_concurrent_workers=2),
            jobs_config=JobsConfig(poll_interval_seconds=0.01),
        )

        job_id = ""
        artifact_digest = ""

        async with runtime1:
            jobs = runtime1.require(HOST_JOBS)
            artifacts = runtime1.require(HOST_ARTIFACTS)

            doc = _build_rsi_job_graph()
            prices = [
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
            req = JobRequest(
                graph_document=doc,
                inputs={"rsi_node.values": prices},
                idempotency_key="example_job_001",
            )

            # Submit job
            submitted_job = await jobs.submit_job(req)
            job_id = submitted_job.job_id
            print(
                f"[Stage S5] Job submitted: id={job_id}, state={submitted_job.state.value}"
            )

            # Await worker execution
            terminal_job = await jobs.await_job(job_id, timeout_seconds=15.0)
            print(
                f"[Stage S5] Job completed: state={terminal_job.state.value}, attempts={terminal_job.attempts}"
            )
            assert terminal_job.state == JobState.SUCCEEDED
            assert len(terminal_job.artifact_refs) == 1

            artifact_digest = terminal_job.artifact_refs[0]
            assert artifacts.has_artifact(artifact_digest)
            raw_output = artifacts.get_artifact_bytes(artifact_digest)
            print(
                f"[Stage S5] Result artifact published: digest={artifact_digest[:16]}..., size={len(raw_output)} bytes"
            )
            assert b"rsi_node.rsi" in raw_output

        # Phase 2: Verify state persistence and restart recovery across host restart
        runtime2 = create_runtime(
            catalog_roots=catalog_roots,
            storage_config=StorageConfig(database_path=db_path),
            artifacts_config=ArtifactsConfig(root_dir=artifacts_dir),
            workers_config=WorkersConfig(max_concurrent_workers=2),
            jobs_config=JobsConfig(poll_interval_seconds=0.01),
        )

        async with runtime2:
            jobs2 = runtime2.require(HOST_JOBS)
            artifacts2 = runtime2.require(HOST_ARTIFACTS)

            # Retrieve previous terminal job across restart
            persisted_job = await jobs2.get_job(job_id)
            assert persisted_job is not None
            assert persisted_job.state == JobState.SUCCEEDED
            assert persisted_job.artifact_refs == (artifact_digest,)

            # Verify artifact is still accessible
            meta = artifacts2.get_metadata(artifact_digest)
            assert meta is not None
            assert meta.ref.digest == artifact_digest
            print(
                f"[Stage S5] Restart verified: persisted job {job_id} recovered with artifact {artifact_digest[:16]}..."
            )

        print(
            "[Stage S5] Durable jobs, SQLite persistence, and artifact storage verified successfully."
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(run_durable_jobs_example())
