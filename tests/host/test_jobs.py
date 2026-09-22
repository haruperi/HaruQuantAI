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


def _build_runtime(
    tmp_path: Path,
    *,
    poll_interval: float = 0.01,
    roots: object = None,
    lease_duration: float = 30.0,
    drain_seconds: float = 5.0,
) -> Runtime:
    """Compose the S5 runtime over isolated temporary stores."""
    from app.host.catalog import CatalogRoot

    catalog_roots = roots if roots is not None else approved_catalog_roots()
    assert isinstance(catalog_roots, tuple) or isinstance(catalog_roots, object)
    del CatalogRoot
    return Runtime(
        (
            lambda: _storage_feature(
                StorageConfig(database_path=tmp_path / "storage.db")
            ),
            lambda: _artifacts_feature(
                ArtifactsConfig(root_dir=tmp_path / "artifacts")
            ),
            lambda: _catalog_feature(roots=catalog_roots),  # type: ignore[arg-type]
            _execution_feature,
            lambda: _workers_feature(WorkersConfig(max_concurrent_workers=2)),
            lambda: _jobs_feature(
                JobsConfig(
                    poll_interval_seconds=poll_interval,
                    lease_duration_seconds=lease_duration,
                    shutdown_drain_seconds=drain_seconds,
                )
            ),
        ),
    )


def test_transition_matrix_legal_and_illegal(tmp_path: Path) -> None:
    from app.host.jobs import _VALID_TRANSITIONS, TERMINAL_JOB_STATES

    # spec diagram transitions are exactly the allowed set
    assert _VALID_TRANSITIONS[JobState.QUEUED] == frozenset(
        {JobState.RUNNING, JobState.CANCELLED}
    )
    assert _VALID_TRANSITIONS[JobState.RUNNING] == frozenset(
        {
            JobState.SUCCEEDED,
            JobState.FAILED,
            JobState.CANCELLING,
            JobState.RECOVERY_PENDING,
        }
    )
    assert _VALID_TRANSITIONS[JobState.CANCELLING] == frozenset({JobState.CANCELLED})
    assert _VALID_TRANSITIONS[JobState.RECOVERY_PENDING] == frozenset(
        {JobState.QUEUED, JobState.FAILED}
    )
    for terminal in TERMINAL_JOB_STATES:
        assert _VALID_TRANSITIONS[terminal] == frozenset()

    async def scenario() -> None:
        runtime = _build_runtime(tmp_path, poll_interval=1000.0)
        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            job = await jobs.submit_job(
                JobRequest(
                    graph_document=_build_test_rsi_graph(),
                    inputs={"rsi_node.values": [1.0, 2.0, 3.0]},
                )
            )
            # queued -> cancelled legal; cancelling a terminal job is a
            # no-op returning the unchanged terminal record
            cancelled = await jobs.cancel_job(job.job_id)
            assert cancelled.state == JobState.CANCELLED
            unchanged = await jobs.cancel_job(job.job_id)
            assert unchanged.state == JobState.CANCELLED
            assert unchanged.revision == cancelled.revision

    asyncio.run(scenario())


def test_persisted_transition_events(tmp_path: Path) -> None:
    async def scenario() -> None:
        runtime = _build_runtime(tmp_path)
        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            job = await jobs.submit_job(
                JobRequest(
                    graph_document=_build_test_rsi_graph(),
                    inputs={"rsi_node.values": [44.0, 45.0, 46.0, 47.0]},
                )
            )
            terminal = await jobs.await_job(job.job_id, timeout_seconds=30.0)
            assert terminal.state == JobState.SUCCEEDED

            events = await jobs.job_events(job.job_id)
            transitions = [(e.from_state, e.to_state) for e in events]
            assert transitions == [
                (JobState.QUEUED, JobState.RUNNING),
                (JobState.RUNNING, JobState.SUCCEEDED),
            ]
            for event in events:
                assert event.utc.endswith("Z")
                assert event.seq >= 1

    asyncio.run(scenario())


def test_recovery_lease_expiry_and_attempts(tmp_path: Path) -> None:
    """Expired running jobs requeue or fail; unexpired leases are left alone."""
    import json as json_mod

    from app.host.jobs import (
        JOBS_NAMESPACE,
        _deserialize_job_record,
        _serialize_job_record,
    )
    from app.host.storage import (
        StorageConfig as SCfg,
    )
    from app.host.storage import (
        StorageMutation,
        _SqliteStorage,
    )

    async def scenario() -> None:
        db = tmp_path / "storage.db"
        storage = _SqliteStorage(SCfg(database_path=db))

        def put(
            job_id: str,
            attempts: int,
            max_attempts: int,
            lease: str,
            *,
            pinned: bool,
        ) -> None:
            record = _deserialize_job_record(
                json_mod.dumps(
                    {
                        "job_id": job_id,
                        "state": "running",
                        "request_wire": {
                            "graph": {
                                "schema_version": 1,
                                "spec": {
                                    "nodes": [
                                        {
                                            "id": "rsi_node",
                                            "plugin_ref": "indicator.rsi@1.0.0",
                                            "operation_id": "compute",
                                            "parameters": {"period": 2},
                                        }
                                    ],
                                    "edges": [],
                                    "designated_roots": [],
                                },
                            },
                            "inputs": {},
                            "seed": None,
                            "budget": {},
                            "catalog_fingerprint": "",
                        },
                        "attempts": attempts,
                        "max_attempts": max_attempts,
                        "lease_owner": "dead_scheduler",
                        "lease_expires_utc": lease,
                    }
                ).encode("utf-8"),
                0,
            )
            if pinned:
                from dataclasses import replace as dc_replace

                from app.plugins.schema import freeze_value
                from app.plugins.wire import value_to_wire

                req = value_to_wire(record.request_wire)
                req["entry_fingerprints"] = {"indicator.rsi@1.0.0#compute": "0" * 64}
                frozen_req = freeze_value(req)
                assert isinstance(frozen_req, FrozenObject)
                record = dc_replace(record, request_wire=frozen_req)
            storage.commit_transaction(
                [
                    StorageMutation(
                        namespace=JOBS_NAMESPACE,
                        key=job_id,
                        schema_version=1,
                        payload_bytes=_serialize_job_record(record),
                        expected_revision=0,
                    )
                ]
            )

        expired = "2020-01-01T00:00:00Z"
        valid = "2999-01-01T00:00:00Z"
        put("job_expired_retry", 1, 3, expired, pinned=True)
        put("job_expired_exhausted", 3, 3, expired, pinned=False)
        put("job_lease_valid", 1, 3, valid, pinned=False)
        storage.close()

        runtime = _build_runtime(tmp_path)
        async with runtime:
            jobs = runtime.require(HOST_JOBS)

            exhausted = await jobs.get_job("job_expired_exhausted")
            assert exhausted is not None
            assert exhausted.state == JobState.FAILED
            assert exhausted.error_code == "MAX_ATTEMPTS_EXCEEDED"

            still_running = await jobs.get_job("job_lease_valid")
            assert still_running is not None
            assert still_running.state == JobState.RUNNING  # lease respected

            retry = await jobs.get_job("job_expired_retry")
            assert retry is not None
            # The crafted record pins a fake entry fingerprint: recovery
            # must fail on exact-identity mismatch, never rebind.
            assert retry.state == JobState.FAILED
            assert retry.error_code == "RECOVERY_DEPENDENCY_MISSING"
            assert "indicator.rsi@1.0.0#compute" in str(retry.error_message)

    asyncio.run(scenario())


def test_recovery_missing_dependency_never_rebinds(tmp_path: Path) -> None:
    """Removing the required plugin fails recovery with the exact dependency."""
    from dataclasses import replace as dc_replace

    comp_dir = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "plugins"
        / "comparisons"
    )

    from app.host.catalog import HOST_CATALOG
    from app.host.jobs import (
        JOBS_NAMESPACE,
        _deserialize_job_record,
        _serialize_job_record,
    )
    from app.host.storage import (
        StorageConfig as SCfg,
    )
    from app.host.storage import (
        StorageMutation,
        _SqliteStorage,
    )
    from app.plugins.spec import PluginRef

    async def scenario() -> None:
        db = tmp_path / "storage.db"
        runtime = _build_runtime(tmp_path, poll_interval=1000.0)
        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            catalog = runtime.require(HOST_CATALOG)
            catalog.admit(PluginRef(id="indicator.rsi", version=(1, 0, 0)), "compute")
            job = await jobs.submit_job(
                JobRequest(
                    graph_document=_build_test_rsi_graph(),
                    inputs={"rsi_node.values": [1.0, 2.0, 3.0]},
                )
            )
            record = await jobs.get_job(job.job_id)
            assert record is not None
            interrupted = dc_replace(
                _deserialize_job_record(_serialize_job_record(record), 0),
                state=JobState.RUNNING,
                lease_owner="dead",
                lease_expires_utc="2020-01-01T00:00:00Z",
            )
            storage = _SqliteStorage(SCfg(database_path=db))
            storage.commit_transaction(
                [
                    StorageMutation(
                        namespace=JOBS_NAMESPACE,
                        key=job.job_id,
                        schema_version=1,
                        payload_bytes=_serialize_job_record(interrupted),
                        expected_revision=record.revision,
                    )
                ]
            )
            storage.close()

        # Restart WITHOUT the indicators family: dependency is gone
        from app.host.catalog import CatalogRoot

        reduced_roots = (CatalogRoot("comparisons", comp_dir, ("comparison",)),)
        runtime2 = _build_runtime(tmp_path, poll_interval=0.01, roots=reduced_roots)
        async with runtime2:
            jobs2 = runtime2.require(HOST_JOBS)
            failed = await jobs2.get_job(job.job_id)
            assert failed is not None
            assert failed.state == JobState.FAILED
            assert failed.error_code == "RECOVERY_DEPENDENCY_MISSING"
            assert "indicator.rsi@1.0.0#compute" in str(failed.error_message)

    asyncio.run(scenario())


def test_recovery_crash_injection_bounded(tmp_path: Path) -> None:
    """A crashed running job with remaining attempts is requeued and rerun."""
    from dataclasses import replace as dc_replace

    from app.host.jobs import (
        JOBS_NAMESPACE,
        _deserialize_job_record,
        _serialize_job_record,
    )
    from app.host.storage import (
        StorageConfig as SCfg,
    )
    from app.host.storage import (
        StorageMutation,
        _SqliteStorage,
    )

    async def scenario() -> None:
        db = tmp_path / "storage.db"
        runtime = _build_runtime(tmp_path, poll_interval=1000.0)
        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            job = await jobs.submit_job(
                JobRequest(
                    graph_document=_build_test_rsi_graph(),
                    inputs={"rsi_node.values": [1.0, 2.0, 3.0]},
                    max_attempts=3,
                )
            )
            record = await jobs.get_job(job.job_id)
            assert record is not None
            crashed = dc_replace(
                _deserialize_job_record(_serialize_job_record(record), 0),
                state=JobState.RUNNING,
                attempts=1,
                lease_owner="crashed_scheduler",
                lease_expires_utc="2020-01-01T00:00:00Z",
            )
            storage = _SqliteStorage(SCfg(database_path=db))
            storage.commit_transaction(
                [
                    StorageMutation(
                        namespace=JOBS_NAMESPACE,
                        key=job.job_id,
                        schema_version=1,
                        payload_bytes=_serialize_job_record(crashed),
                        expected_revision=record.revision,
                    )
                ]
            )
            storage.close()

        runtime2 = _build_runtime(tmp_path, poll_interval=0.01)
        async with runtime2:
            jobs2 = runtime2.require(HOST_JOBS)
            terminal = await jobs2.await_job(job.job_id, timeout_seconds=30.0)
            assert terminal.state == JobState.SUCCEEDED
            assert terminal.attempts == 2  # crashed attempt + successful rerun
            events = await jobs2.job_events(job.job_id)
            assert events[-1].to_state == JobState.SUCCEEDED
            assert JobState.RECOVERY_PENDING in [e.to_state for e in events]

    asyncio.run(scenario())


IMPURE_PROBE_SOURCE = '''"""Impure probe plugin: declares an io effect."""
from app.plugins.spec import (
    OperationContribution, OperationImplementation, PluginContribution,
    PluginRef, PluginSpec, OperationSpec,
)
from app.plugins.schema import ParameterBindingResult, PortSpec, ValueKind
from app.plugins.lowering import LoweringResult


class ImpureOp(OperationImplementation):
    def validate_parameters(self, v):
        return ParameterBindingResult(True)

    def warmup_samples(self, v):
        return 0

    def execute(self, i, p, b):
        return {"out": ()}

    def lower(self, c, p):
        return LoweringResult(success=True)


def plugin():
    op = OperationSpec(
        operation_id="compute",
        title="Impure",
        inputs=(PortSpec(key="x", kind=ValueKind.NUMBER),),
        outputs=(PortSpec(key="out", kind=ValueKind.NUMBER),),
        effects=("pure", "io"),
    )
    spec = PluginSpec(
        ref=PluginRef(id="indicator.impure_probe", version=(1, 0, 0)),
        kind="indicator", title="Impure Probe", operations=(op,),
    )
    return PluginContribution(
        spec=spec, operations=(OperationContribution("compute", ImpureOp()),)
    )
'''


def test_non_pure_effects_rejected_at_submission(tmp_path: Path) -> None:
    from app.host.catalog import CatalogRoot
    from app.host.jobs import JobError

    ind_dir = tmp_path / "indicators"
    ind_dir.mkdir()
    rsi_path = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "plugins"
        / "indicators"
        / "rsi.py"
    )
    (ind_dir / "rsi.py").write_text(rsi_path.read_text(encoding="utf-8"), "utf-8")
    (ind_dir / "impure_probe.py").write_text(IMPURE_PROBE_SOURCE, encoding="utf-8")
    roots = (CatalogRoot("indicators", ind_dir, ("indicator",)),)

    async def scenario() -> None:
        runtime = _build_runtime(tmp_path, poll_interval=1000.0, roots=roots)
        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            node = NodeSpec(
                id="imp",
                plugin_ref=PluginRef(id="indicator.impure_probe", version=(1, 0, 0)),
                operation_id="compute",
            )
            doc = GraphDocument(spec=GraphSpec(nodes=(node,)))
            with pytest.raises(JobError, match="non-pure effects"):
                await jobs.submit_job(
                    JobRequest(graph_document=doc, inputs={"imp.x": [1.0]})
                )

    asyncio.run(scenario())


def test_shutdown_keeps_providers_alive_through_cleanup(tmp_path: Path) -> None:
    from app.host.storage import HOST_STORAGE

    async def scenario() -> None:
        runtime = _build_runtime(tmp_path, poll_interval=0.01, drain_seconds=1.0)
        async with runtime:
            jobs_svc = runtime.require(HOST_JOBS)
            storage = runtime.require(HOST_STORAGE)
            job = await jobs_svc.submit_job(
                JobRequest(
                    graph_document=_build_test_rsi_graph(),
                    inputs={"rsi_node.values": [1.0, 2.0, 3.0]},
                )
            )
            terminal = await jobs_svc.await_job(job.job_id, timeout_seconds=30.0)
            assert terminal.state == JobState.SUCCEEDED
            # storage serves queries while jobs is still open
            assert storage.status().ready is True

    asyncio.run(scenario())


def test_recovery_pending_record_restarts_without_illegal_transition(
    tmp_path: Path,
) -> None:
    """An interrupted RECOVERY_PENDING job resumes instead of re-transitioning."""
    from dataclasses import replace as dc_replace

    from app.host.jobs import (
        JOBS_NAMESPACE,
        _deserialize_job_record,
        _serialize_job_record,
    )
    from app.host.storage import (
        StorageConfig as SCfg,
    )
    from app.host.storage import (
        StorageMutation,
        _SqliteStorage,
    )

    async def scenario() -> None:
        db = tmp_path / "storage.db"
        runtime = _build_runtime(tmp_path, poll_interval=1000.0)
        async with runtime:
            jobs = runtime.require(HOST_JOBS)
            job = await jobs.submit_job(
                JobRequest(
                    graph_document=_build_test_rsi_graph(),
                    inputs={"rsi_node.values": [1.0, 2.0, 3.0]},
                    max_attempts=3,
                )
            )
            record = await jobs.get_job(job.job_id)
            assert record is not None
            pending = dc_replace(
                _deserialize_job_record(_serialize_job_record(record), 0),
                state=JobState.RECOVERY_PENDING,
                attempts=1,
                lease_owner="dead",
                lease_expires_utc="2020-01-01T00:00:00Z",
            )
            storage = _SqliteStorage(SCfg(database_path=db))
            storage.commit_transaction(
                [
                    StorageMutation(
                        namespace=JOBS_NAMESPACE,
                        key=job.job_id,
                        schema_version=1,
                        payload_bytes=_serialize_job_record(pending),
                        expected_revision=record.revision,
                    )
                ]
            )
            storage.close()

        # Restart must not attempt RECOVERY_PENDING -> RECOVERY_PENDING
        runtime2 = _build_runtime(tmp_path, poll_interval=0.01)
        async with runtime2:
            jobs2 = runtime2.require(HOST_JOBS)
            terminal = await jobs2.await_job(job.job_id, timeout_seconds=30.0)
            assert terminal.state == JobState.SUCCEEDED
            events = await jobs2.job_events(job.job_id)
            # the pre-existing pending record resumed directly:
            # RECOVERY_PENDING -> QUEUED, never pending -> pending
            assert events[0].from_state == JobState.RECOVERY_PENDING
            assert events[0].to_state == JobState.QUEUED
            assert [e.to_state for e in events][1:] == [
                JobState.RUNNING,
                JobState.SUCCEEDED,
            ]

    asyncio.run(scenario())
