"""Focused tests for host jobs owner: state machine, recovery, and worker scheduling."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.host.artifacts import (
    ArtifactsConfig,
    _artifacts_feature,
)
from app.host.bootstrap import approved_catalog_roots
from app.host.catalog import _catalog_feature
from app.host.execution import _execution_feature
from app.host.jobs import (
    HOST_JOBS,
    JobConflictError,
    JobRequest,
    JobsConfig,
    JobState,
    _jobs_feature,
)
from app.host.storage import StorageConfig, _storage_feature
from app.host.workers import WorkersConfig, _workers_feature
from app.kernel.bootstrapper import Runtime
from app.plugins.algebra import GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import FrozenObject
from app.plugins.spec import PluginRef


def _build_test_rsi_graph() -> GraphDocument:
    """Build an RSI graph document for job testing."""
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


def test_job_submission_and_idempotency(tmp_path: Path) -> None:
    """Test job submission, initial state, and idempotency key handling."""

    async def scenario() -> None:
        db_path = tmp_path / "storage.db"
        artifacts_dir = tmp_path / "artifacts"
        roots = approved_catalog_roots()

        feat_storage = _storage_feature(StorageConfig(database_path=db_path))
        feat_artifacts = _artifacts_feature(ArtifactsConfig(root_dir=artifacts_dir))
        feat_catalog = _catalog_feature(roots=roots)
        feat_execution = _execution_feature()
        feat_workers = _workers_feature(WorkersConfig(max_concurrent_workers=2))
        feat_jobs = _jobs_feature(JobsConfig(poll_interval_seconds=0.01))

        runtime = Runtime(
            (
                lambda: feat_storage,
                lambda: feat_artifacts,
                lambda: feat_catalog,
                lambda: feat_execution,
                lambda: feat_workers,
                lambda: feat_jobs,
            ),
        )

        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            doc = _build_test_rsi_graph()

            req = JobRequest(
                graph_document=doc,
                inputs={"rsi_node.values": [44.0, 45.0, 46.0, 47.0]},
                idempotency_key="idem_001",
            )

            job1 = await jobs.submit_job(req)
            assert job1.state in (JobState.QUEUED, JobState.RUNNING)
            assert job1.idempotency_key == "idem_001"

            # Resubmitting exact same request returns same job
            job1_dup = await jobs.submit_job(req)
            assert job1_dup.job_id == job1.job_id

            # Submitting different request with same idempotency key fails
            req_conflict = JobRequest(
                graph_document=doc,
                inputs={"rsi_node.values": [99.0, 100.0]},
                idempotency_key="idem_001",
            )
            with pytest.raises(
                JobConflictError, match="already used for a different payload"
            ):
                await jobs.submit_job(req_conflict)

    asyncio.run(scenario())


def test_job_execution_success_and_artifact_publication(tmp_path: Path) -> None:
    """Test full job execution flow: submit -> scheduled -> worker -> artifact -> succeeded."""

    async def scenario() -> None:
        db_path = tmp_path / "storage.db"
        artifacts_dir = tmp_path / "artifacts"
        roots = approved_catalog_roots()

        feat_storage = _storage_feature(StorageConfig(database_path=db_path))
        feat_artifacts = _artifacts_feature(ArtifactsConfig(root_dir=artifacts_dir))
        feat_catalog = _catalog_feature(roots=roots)
        feat_execution = _execution_feature()
        feat_workers = _workers_feature(WorkersConfig(max_concurrent_workers=2))
        feat_jobs = _jobs_feature(JobsConfig(poll_interval_seconds=0.01))

        runtime = Runtime(
            (
                lambda: feat_storage,
                lambda: feat_artifacts,
                lambda: feat_catalog,
                lambda: feat_execution,
                lambda: feat_workers,
                lambda: feat_jobs,
            ),
        )

        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            doc = _build_test_rsi_graph()

            req = JobRequest(
                graph_document=doc,
                inputs={
                    "rsi_node.values": [
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
                },
                idempotency_key="job_exec_001",
            )

            job = await jobs.submit_job(req)
            terminal_job = await jobs.await_job(job.job_id, timeout_seconds=10.0)

            assert terminal_job.state == JobState.SUCCEEDED
            assert terminal_job.result_wire is not None
            assert len(terminal_job.artifact_refs) == 1

            # Check that artifact exists in ArtifactStore
            from app.host.artifacts import HOST_ARTIFACTS

            artifacts = runtime.require(HOST_ARTIFACTS)
            artifact_digest = terminal_job.artifact_refs[0]
            assert artifacts.has_artifact(artifact_digest) is True
            raw_bytes = artifacts.get_artifact_bytes(artifact_digest)
            assert b"rsi_node.rsi" in raw_bytes

    asyncio.run(scenario())


def test_job_cancellation(tmp_path: Path) -> None:
    """Test cancelling a queued job."""

    async def scenario() -> None:
        db_path = tmp_path / "storage.db"
        artifacts_dir = tmp_path / "artifacts"
        roots = approved_catalog_roots()

        feat_storage = _storage_feature(StorageConfig(database_path=db_path))
        feat_artifacts = _artifacts_feature(ArtifactsConfig(root_dir=artifacts_dir))
        feat_catalog = _catalog_feature(roots=roots)
        feat_execution = _execution_feature()
        feat_workers = _workers_feature(WorkersConfig(max_concurrent_workers=2))
        # Long poll interval so job stays queued
        feat_jobs = _jobs_feature(JobsConfig(poll_interval_seconds=10.0))

        runtime = Runtime(
            (
                lambda: feat_storage,
                lambda: feat_artifacts,
                lambda: feat_catalog,
                lambda: feat_execution,
                lambda: feat_workers,
                lambda: feat_jobs,
            ),
        )

        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            doc = _build_test_rsi_graph()

            req = JobRequest(
                graph_document=doc,
                inputs={"rsi_node.values": [1.0, 2.0, 3.0]},
            )

            job = await jobs.submit_job(req)
            cancelled_job = await jobs.cancel_job(job.job_id)
            assert cancelled_job.state == JobState.CANCELLED

    asyncio.run(scenario())


def test_job_restart_recovery(tmp_path: Path) -> None:
    """Test restart recovery for interrupted jobs."""

    async def scenario() -> None:
        db_path = tmp_path / "storage.db"
        artifacts_dir = tmp_path / "artifacts"
        roots = approved_catalog_roots()

        # Step 1: Submit job in runtime 1, but do NOT run scheduler (poll interval huge)
        feat_storage = _storage_feature(StorageConfig(database_path=db_path))
        feat_artifacts = _artifacts_feature(ArtifactsConfig(root_dir=artifacts_dir))
        feat_catalog = _catalog_feature(roots=roots)
        feat_execution = _execution_feature()
        feat_workers = _workers_feature(WorkersConfig(max_concurrent_workers=2))
        feat_jobs = _jobs_feature(JobsConfig(poll_interval_seconds=10.0))

        runtime1 = Runtime(
            (
                lambda: feat_storage,
                lambda: feat_artifacts,
                lambda: feat_catalog,
                lambda: feat_execution,
                lambda: feat_workers,
                lambda: feat_jobs,
            ),
        )

        job_id = ""
        async with runtime1:
            jobs1 = runtime1.require(HOST_JOBS)
            doc = _build_test_rsi_graph()
            req = JobRequest(
                graph_document=doc,
                inputs={"rsi_node.values": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]},
            )
            job = await jobs1.submit_job(req)
            job_id = job.job_id

        # Step 2: Restart runtime with active scheduler; job should be recovered and executed
        feat_storage2 = _storage_feature(StorageConfig(database_path=db_path))
        feat_artifacts2 = _artifacts_feature(ArtifactsConfig(root_dir=artifacts_dir))
        feat_catalog2 = _catalog_feature(roots=roots)
        feat_execution2 = _execution_feature()
        feat_workers2 = _workers_feature(WorkersConfig(max_concurrent_workers=2))
        feat_jobs2 = _jobs_feature(JobsConfig(poll_interval_seconds=0.01))

        runtime2 = Runtime(
            (
                lambda: feat_storage2,
                lambda: feat_artifacts2,
                lambda: feat_catalog2,
                lambda: feat_execution2,
                lambda: feat_workers2,
                lambda: feat_jobs2,
            ),
        )

        async with runtime2:
            jobs2 = runtime2.require(HOST_JOBS)
            terminal_job = await jobs2.await_job(job_id, timeout_seconds=10.0)
            assert terminal_job.state == JobState.SUCCEEDED

    asyncio.run(scenario())
