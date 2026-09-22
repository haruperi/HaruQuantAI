"""Host jobs owner: durable job state machine, recovery, and worker scheduling."""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, override

from app.host.artifacts import HOST_ARTIFACTS, ArtifactStore
from app.host.catalog import HOST_CATALOG, Catalog, CatalogAdmissionError
from app.host.execution import (
    DEFAULT_BUDGET,
    EXECUTION_ENGINE_VERSION,
    HOST_EXECUTION,
    Execution,
    ExecutionBudget,
)
from app.host.storage import (
    HOST_STORAGE,
    Storage,
    StorageDelete,
    StorageError,
    StorageMutation,
)
from app.host.workers import (
    HOST_WORKERS,
    WorkerBudget,
    WorkerCancellationError,
    WorkerResult,
    Workers,
    WorkerTask,
    WorkerTimeoutError,
)
from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.plugins.algebra import (
    GraphDocument,
    OpaqueGraphDocument,
)
from app.plugins.schema import (
    EMPTY_FROZEN_OBJECT,
    FrozenObject,
    freeze_value,
)
from app.plugins.wire import (
    graph_document_to_wire,
    to_canonical_json_bytes,
    value_to_wire,
)


class JobError(RuntimeError):
    """Base error for jobs owner failures."""


class JobNotFoundError(JobError):
    """Raised when a job ID is not found."""


class JobConflictError(JobError):
    """Raised when an idempotency key conflicts with an existing payload."""


class JobCancelledError(JobError):
    """Raised when a job has been cancelled."""


class JobStateError(JobError):
    """Raised on an illegal job state machine transition."""


class JobState(StrEnum):
    """Durable job lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    RECOVERY_PENDING = "recovery_pending"


TERMINAL_JOB_STATES = frozenset(
    {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}
)

_VALID_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.QUEUED: frozenset({JobState.RUNNING, JobState.CANCELLED}),
    JobState.RUNNING: frozenset(
        {
            JobState.SUCCEEDED,
            JobState.FAILED,
            JobState.CANCELLING,
            JobState.RECOVERY_PENDING,
        }
    ),
    JobState.CANCELLING: frozenset({JobState.CANCELLED}),
    JobState.RECOVERY_PENDING: frozenset({JobState.QUEUED, JobState.FAILED}),
    JobState.SUCCEEDED: frozenset(),
    JobState.FAILED: frozenset(),
    JobState.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class JobRequest:
    """Request to submit a durable quantitative job."""

    graph_document: GraphDocument | OpaqueGraphDocument
    inputs: Mapping[str, Any] = EMPTY_FROZEN_OBJECT
    seed: int | None = None
    budget: ExecutionBudget = DEFAULT_BUDGET
    idempotency_key: str | None = None
    max_attempts: int = 3
    tags: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate job request."""
        if not isinstance(self.graph_document, (GraphDocument, OpaqueGraphDocument)):
            raise TypeError("graph_document must be a GraphDocument")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")


@dataclass(frozen=True, slots=True)
class JobRecord:
    """Durable state record of a job."""

    job_id: str
    state: JobState
    revision: int
    request_wire: FrozenObject
    idempotency_key: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    lease_owner: str | None = None
    lease_expires_utc: str | None = None
    result_wire: FrozenObject | None = None
    artifact_refs: tuple[str, ...] = ()
    error_code: str | None = None
    error_message: str | None = None
    created_at_utc: str = ""
    updated_at_utc: str = ""
    last_heartbeat_utc: str = ""


@dataclass(frozen=True, slots=True)
class JobEvent:
    """Persisted job state-transition event record."""

    job_id: str
    seq: int
    from_state: JobState
    to_state: JobState
    utc: str
    reason: str = ""
    detail: str = ""


@dataclass(frozen=True, slots=True)
class JobQuery:
    """Query filters for job pagination."""

    state: JobState | None = None
    limit: int = 50
    after_job_id: str | None = None


@dataclass(frozen=True, slots=True)
class JobPage:
    """Deterministic page of job records."""

    records: tuple[JobRecord, ...]
    next_token: str | None = None
    total_count: int = 0


@dataclass(frozen=True, slots=True)
class JobsConfig:
    """Configuration for durable jobs scheduler."""

    poll_interval_seconds: float = 0.05
    lease_duration_seconds: float = 30.0
    shutdown_drain_seconds: float = 5.0
    scheduler_id: str = ""

    def __post_init__(self) -> None:
        """Validate jobs configuration."""
        if self.poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        if self.lease_duration_seconds <= 0:
            raise ValueError("lease_duration_seconds must be > 0")
        if self.shutdown_drain_seconds <= 0:
            raise ValueError("shutdown_drain_seconds must be > 0")


class Jobs(Protocol):
    """Public capability protocol for durable jobs orchestration."""

    async def submit_job(self, request: JobRequest) -> JobRecord:
        """Submit a job idempotently and persist its initial queued record."""
        ...

    async def get_job(self, job_id: str) -> JobRecord | None:
        """Retrieve a job by its unique ID."""
        ...

    async def list_jobs(self, query: JobQuery | None = None) -> JobPage:
        """List jobs matching query filters."""
        ...

    async def cancel_job(self, job_id: str) -> JobRecord:
        """Request cancellation for a queued or running job."""
        ...

    async def await_job(self, job_id: str, timeout_seconds: float = 60.0) -> JobRecord:
        """Wait until a job reaches a terminal state."""
        ...

    async def job_events(self, job_id: str) -> tuple[JobEvent, ...]:
        """Return persisted transition events for a job in order."""
        ...

    async def close(self) -> None:
        """Stop scheduler and drain active jobs."""
        ...


HOST_JOBS = Capability[Jobs]("host.jobs", 1)

JOBS_NAMESPACE = "jobs"
JOBS_EVENTS_NAMESPACE = "jobs.events"
IDEMPOTENCY_NAMESPACE = "job_idempotency"


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _utc_now_iso() -> str:
    return _utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _serialize_job_record(record: JobRecord) -> bytes:
    data = {
        "job_id": record.job_id,
        "state": record.state.value,
        "revision": record.revision,
        "request_wire": value_to_wire(record.request_wire),
        "idempotency_key": record.idempotency_key,
        "attempts": record.attempts,
        "max_attempts": record.max_attempts,
        "lease_owner": record.lease_owner,
        "lease_expires_utc": record.lease_expires_utc,
        "result_wire": (
            value_to_wire(record.result_wire) if record.result_wire else None
        ),
        "artifact_refs": list(record.artifact_refs),
        "error_code": record.error_code,
        "error_message": record.error_message,
        "created_at_utc": record.created_at_utc,
        "updated_at_utc": record.updated_at_utc,
        "last_heartbeat_utc": record.last_heartbeat_utc,
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _deserialize_job_record(payload_bytes: bytes, revision: int) -> JobRecord:
    data = json.loads(payload_bytes.decode("utf-8"))
    res_raw = data.get("result_wire")
    frozen_res = freeze_value(res_raw) if res_raw is not None else None
    req_raw = data.get("request_wire", {})
    frozen_req = freeze_value(req_raw)
    if not isinstance(frozen_req, FrozenObject):
        frozen_req = EMPTY_FROZEN_OBJECT

    return JobRecord(
        job_id=data["job_id"],
        state=JobState(data["state"]),
        revision=revision,
        request_wire=frozen_req,
        idempotency_key=data.get("idempotency_key"),
        attempts=data.get("attempts", 0),
        max_attempts=data.get("max_attempts", 3),
        lease_owner=data.get("lease_owner"),
        lease_expires_utc=data.get("lease_expires_utc"),
        result_wire=frozen_res if isinstance(frozen_res, FrozenObject) else None,
        artifact_refs=tuple(data.get("artifact_refs", [])),
        error_code=data.get("error_code"),
        error_message=data.get("error_message"),
        created_at_utc=data.get("created_at_utc", ""),
        updated_at_utc=data.get("updated_at_utc", ""),
        last_heartbeat_utc=data.get("last_heartbeat_utc", ""),
    )


class _DurableJobs(Jobs):
    """Private implementation of the durable jobs scheduler and state machine."""

    def __init__(
        self,
        config: JobsConfig,
        storage: Storage,
        *,
        artifacts: ArtifactStore,
        workers: Workers,
        catalog: Catalog,
        execution: Execution,
    ) -> None:
        self._config = config
        self._storage = storage
        self._artifacts = artifacts
        self._workers = workers
        self._catalog = catalog
        self._execution = execution
        self._scheduler_id = config.scheduler_id or f"scheduler_{uuid.uuid4().hex[:8]}"
        self._running = False
        self._loop_task: asyncio.Task[None] | None = None
        self._active_tasks: dict[str, asyncio.Task[None]] = {}
        self._completion_events: dict[str, asyncio.Event] = {}

    async def start(self) -> None:
        """Start recovery and scheduler background loop."""
        self._running = True
        await self._recover_interrupted_jobs()
        self._loop_task = asyncio.create_task(self._scheduler_loop())

    async def _recover_interrupted_jobs(self) -> None:
        """Scan all nonterminal jobs at startup and recover or fail them.

        Expired running pure jobs are requeued only when their exact
        entry-fingerprint dependencies are still admitted and attempts
        remain; otherwise they fail with a stable recovery code. Cancelling
        jobs resolve to cancelled. Successful jobs are never rerun.
        """
        after_key: str | None = None
        while True:
            page = await self._storage.async_scan_records(
                JOBS_NAMESPACE, limit=100, after_key=after_key
            )
            if not page.records:
                break
            for rec in page.records:
                job = _deserialize_job_record(rec.payload_bytes, rec.revision)
                await self._recover_one(job)
            if page.next_token is None:
                break
            after_key = page.next_token

    async def _recover_one(self, job: JobRecord) -> None:
        """Apply the recovery policy to a single nonterminal job."""
        if job.state in TERMINAL_JOB_STATES:
            return

        if job.state == JobState.CANCELLING:
            await self._transition_job(job, JobState.CANCELLED)
            return

        if job.state == JobState.QUEUED:
            return  # the scheduler will claim it

        if job.state not in (JobState.RUNNING, JobState.RECOVERY_PENDING):
            return

        # A still-valid lease means a live scheduler elsewhere owns the job.
        lease_valid = (
            job.lease_expires_utc is not None and job.lease_expires_utc > _utc_now_iso()
        )
        if lease_valid:
            return

        if job.state == JobState.RUNNING:
            pending = await self._transition_job(job, JobState.RECOVERY_PENDING)
        else:
            # Already RECOVERY_PENDING (interrupted twice); do not
            # re-transition into the same state.
            pending = job

        missing = self._missing_dependencies(pending)
        if missing:
            await self._transition_job(
                pending,
                JobState.FAILED,
                error_code="RECOVERY_DEPENDENCY_MISSING",
                error_message=(
                    f"Required dependency missing or changed across restart: {missing}"
                ),
            )
        elif pending.attempts >= pending.max_attempts:
            await self._transition_job(
                pending,
                JobState.FAILED,
                error_code="MAX_ATTEMPTS_EXCEEDED",
                error_message=f"Job exceeded max attempts ({pending.max_attempts})",
            )
        else:
            await self._transition_job(
                pending,
                JobState.QUEUED,
                lease_owner=None,
                lease_expires_utc=None,
            )

    def _missing_dependencies(self, job: JobRecord) -> str | None:
        """Return the first missing/changed pinned dependency, if any."""
        req_data = value_to_wire(job.request_wire)
        entry_fps = req_data.get("entry_fingerprints") or {}
        if entry_fps:
            for key, expected in entry_fps.items():
                ref_str, _, op_id = str(key).rpartition("#")
                try:
                    from app.plugins.spec import PluginRef

                    admitted = self._catalog.admit(PluginRef.parse(ref_str), op_id)
                except KeyError, ValueError, TypeError, CatalogAdmissionError:
                    return str(key)
                if admitted.entry_fingerprint != expected:
                    return str(key)
            return None

        # Legacy records without pinned fingerprints: id+version fallback.
        graph_data = req_data.get("graph", {})
        snapshot = self._catalog.snapshot()
        installed = {e.ref.id: e.ref.version for e in snapshot.view.entries}
        for node in graph_data.get("nodes", []):
            p_id = node.get("plugin_id") or node.get("plugin_ref", {}).get("id")
            p_ver_raw = node.get("plugin_version")
            if p_ver_raw is None:
                p_ver = node.get("plugin_ref", {}).get("version")
            else:
                p_ver = p_ver_raw
            if p_id is None or installed.get(p_id) != p_ver:
                return f"{p_id}@{p_ver}"
        return None

    async def _transition_job(
        self,
        job: JobRecord,
        new_state: JobState,
        *,
        lease_owner: str | None = None,
        lease_expires_utc: str | None = None,
        result_wire: FrozenObject | None = None,
        artifact_refs: tuple[str, ...] = (),
        error_code: str | None = None,
        error_message: str | None = None,
        increment_attempts: bool = False,
    ) -> JobRecord:
        """Atomically transition job to a new state with CAS revision check."""
        allowed = _VALID_TRANSITIONS.get(job.state, frozenset())
        if new_state not in allowed:
            raise JobStateError(
                f"Cannot transition job {job.job_id} from {job.state} to {new_state}"
            )

        updated_attempts = job.attempts + (1 if increment_attempts else 0)
        now_iso = _utc_now_iso()

        new_record = JobRecord(
            job_id=job.job_id,
            state=new_state,
            revision=job.revision + 1,
            request_wire=job.request_wire,
            idempotency_key=job.idempotency_key,
            attempts=updated_attempts,
            max_attempts=job.max_attempts,
            lease_owner=lease_owner if lease_owner is not None else job.lease_owner,
            lease_expires_utc=(
                lease_expires_utc
                if lease_expires_utc is not None
                else job.lease_expires_utc
            ),
            result_wire=result_wire if result_wire is not None else job.result_wire,
            artifact_refs=artifact_refs or job.artifact_refs,
            error_code=error_code if error_code is not None else job.error_code,
            error_message=(
                error_message if error_message is not None else job.error_message
            ),
            created_at_utc=job.created_at_utc,
            updated_at_utc=now_iso,
        )

        payload_bytes = _serialize_job_record(new_record)
        mutation = StorageMutation(
            namespace=JOBS_NAMESPACE,
            key=job.job_id,
            schema_version=1,
            payload_bytes=payload_bytes,
            expected_revision=job.revision,
        )
        event_bytes = json.dumps(
            {
                "job_id": job.job_id,
                "seq": new_record.revision,
                "from_state": job.state.value,
                "to_state": new_state.value,
                "utc": now_iso,
                "reason": error_code or "",
                "detail": error_message or "",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        event_mutation = StorageMutation(
            namespace=JOBS_EVENTS_NAMESPACE,
            key=f"{job.job_id}:{new_record.revision:08d}",
            schema_version=1,
            payload_bytes=event_bytes,
        )

        tx_res = await self._storage.async_commit_transaction(
            [mutation, event_mutation]
        )
        if not tx_res.committed:
            raise JobStateError(
                f"CAS revision conflict while transitioning job {job.job_id}"
            )

        if new_state in TERMINAL_JOB_STATES:
            evt = self._completion_events.get(job.job_id)
            if evt:
                evt.set()

        return new_record

    def _pin_request_identity(
        self, request: JobRequest
    ) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
        """Admit every referenced operation, pinning exact entry identity.

        Enforces the pure-only effect policy: an operation whose effects
        exceed {"pure"} is rejected for durable jobs.
        """
        if isinstance(request.graph_document, OpaqueGraphDocument):
            raise JobError("Opaque graph documents cannot be pinned")
        entry_fingerprints: dict[str, str] = {}
        policies: dict[str, dict[str, Any]] = {}
        for node in request.graph_document.spec.nodes:
            try:
                admitted = self._catalog.admit(node.plugin_ref, node.operation_id)
            except (KeyError, ValueError, TypeError, CatalogAdmissionError) as err:
                raise JobError(
                    f"Dependency admission failed for node {node.id!r}: {err}"
                ) from err
            unsafe_effects = set(admitted.spec.effects) - {"pure"}
            if unsafe_effects:
                raise JobError(
                    f"Node {node.id!r} declares non-pure effects "
                    f"{sorted(unsafe_effects)}; only pure execution is "
                    "permitted for durable jobs"
                )
            entry_fingerprints[f"{node.plugin_ref.to_string()}#{node.operation_id}"] = (
                admitted.entry_fingerprint
            )
            policy = admitted.spec.numerical_policy
            policies[node.id] = {
                "tolerance": policy.tolerance,
                "nan_policy": policy.nan_policy,
                "missing_policy": policy.missing_policy,
            }
        return entry_fingerprints, policies

    @override
    async def submit_job(self, request: JobRequest) -> JobRecord:
        """Submit a job with optional idempotency key validation.

        The submission freezes the full execution identity: wire version,
        graph, inputs hash, seed, budgets, catalog/entry/dependency
        fingerprints, numerical policies, engine version, and a pure-only
        effect policy. Refresh never silently rebinds any of them.
        """
        if isinstance(request.graph_document, OpaqueGraphDocument):
            raise JobError("Opaque graph documents cannot be submitted as durable jobs")

        graph_wire = graph_document_to_wire(request.graph_document)
        inputs_frozen = freeze_value(request.inputs)
        if not isinstance(inputs_frozen, FrozenObject):
            inputs_frozen = EMPTY_FROZEN_OBJECT

        snapshot = self._catalog.snapshot()

        entry_fingerprints, policies = self._pin_request_identity(request)
        dependency_fingerprint = hashlib.sha256(
            ":".join(sorted(entry_fingerprints.values())).encode("utf-8")
        ).hexdigest()
        input_hash = hashlib.sha256(
            to_canonical_json_bytes(value_to_wire(inputs_frozen))
        ).hexdigest()

        req_dict = {
            "wire_version": 1,
            "graph": graph_wire,
            "inputs": value_to_wire(inputs_frozen),
            "seed": request.seed,
            "budget": {
                "max_nodes": request.budget.max_nodes,
                "max_samples": request.budget.max_samples,
                "max_output_values": request.budget.max_output_values,
                "max_trials": request.budget.max_trials,
                "max_elapsed_seconds": request.budget.max_elapsed_seconds,
            },
            "catalog_fingerprint": snapshot.whole_fingerprint,
            "entry_fingerprints": entry_fingerprints,
            "dependency_fingerprint": dependency_fingerprint,
            "input_hash": input_hash,
            "numerical_policies": policies,
            "engine_version": EXECUTION_ENGINE_VERSION,
            "effect_policy": "pure",
        }
        req_bytes = to_canonical_json_bytes(req_dict)
        req_hash = hashlib.sha256(req_bytes).hexdigest()

        now_iso = _utc_now_iso()

        # Check idempotency
        if request.idempotency_key:
            idem_rec = await self._storage.async_get_record(
                IDEMPOTENCY_NAMESPACE, request.idempotency_key
            )
            if idem_rec is not None:
                parsed = json.loads(idem_rec.payload_bytes.decode("utf-8"))
                if parsed.get("request_hash") != req_hash:
                    raise JobConflictError(
                        f"Idempotency key {request.idempotency_key} already used "
                        "for a different payload"
                    )
                existing_job_id = parsed["job_id"]
                existing_job = await self.get_job(existing_job_id)
                if existing_job is not None:
                    return existing_job

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        frozen_req = freeze_value(req_dict)
        if not isinstance(frozen_req, FrozenObject):
            frozen_req = EMPTY_FROZEN_OBJECT

        record = JobRecord(
            job_id=job_id,
            state=JobState.QUEUED,
            revision=1,
            request_wire=frozen_req,
            idempotency_key=request.idempotency_key,
            attempts=0,
            max_attempts=request.max_attempts,
            created_at_utc=now_iso,
            updated_at_utc=now_iso,
        )

        job_mutation = StorageMutation(
            namespace=JOBS_NAMESPACE,
            key=job_id,
            schema_version=1,
            payload_bytes=_serialize_job_record(record),
            expected_revision=0,
        )

        mutations: list[StorageMutation | StorageDelete] = [job_mutation]

        if request.idempotency_key:
            idem_payload = json.dumps(
                {"job_id": job_id, "request_hash": req_hash},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            idem_mutation = StorageMutation(
                namespace=IDEMPOTENCY_NAMESPACE,
                key=request.idempotency_key,
                schema_version=1,
                payload_bytes=idem_payload,
                expected_revision=0,
            )
            mutations.append(idem_mutation)

        tx_res = await self._storage.async_commit_transaction(mutations)
        if not tx_res.committed:
            raise JobConflictError(f"Failed to commit new job {job_id}")

        self._completion_events[job_id] = asyncio.Event()
        return record

    @override
    async def get_job(self, job_id: str) -> JobRecord | None:
        """Fetch job record by ID."""
        rec = await self._storage.async_get_record(JOBS_NAMESPACE, job_id)
        if rec is None:
            return None
        return _deserialize_job_record(rec.payload_bytes, rec.revision)

    @override
    async def list_jobs(self, query: JobQuery | None = None) -> JobPage:
        """List job records, filtering before pagination."""
        q = query if query is not None else JobQuery()
        scan_limit = max(q.limit, 50)
        matched: list[JobRecord] = []
        after_key = q.after_job_id
        last_scanned: str | None = q.after_job_id
        total = 0
        while len(matched) <= q.limit:
            page = await self._storage.async_scan_records(
                JOBS_NAMESPACE, limit=scan_limit, after_key=after_key
            )
            total = page.total_count
            if not page.records:
                last_scanned = None
                break
            for rec in page.records:
                job = _deserialize_job_record(rec.payload_bytes, rec.revision)
                last_scanned = rec.key
                if q.state is None or job.state == q.state:
                    matched.append(job)
                    if len(matched) > q.limit:
                        break
            if page.next_token is None:
                last_scanned = None
                break
            after_key = page.next_token

        has_more = len(matched) > q.limit
        return JobPage(
            records=tuple(matched[: q.limit]),
            next_token=last_scanned if has_more else None,
            total_count=total,
        )

    @override
    async def cancel_job(self, job_id: str) -> JobRecord:
        """Request cancellation for a queued or running job."""
        for _ in range(3):
            job = await self.get_job(job_id)
            if job is None:
                raise JobNotFoundError(f"Job {job_id} not found")

            if job.state in TERMINAL_JOB_STATES:
                return job

            if job.state == JobState.QUEUED:
                try:
                    return await self._transition_job(job, JobState.CANCELLED)
                except JobStateError:
                    continue  # raced with a claim; re-read

            if job.state in (JobState.RUNNING, JobState.CANCELLING):
                try:
                    job = await self._transition_job(job, JobState.CANCELLING)
                except JobStateError:
                    continue  # raced with completion; re-read
                active = self._active_tasks.get(job_id)
                if active is not None and not active.done():
                    active.cancel()
                return job

            return job

        final = await self.get_job(job_id)
        if final is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return final

    @override
    async def await_job(self, job_id: str, timeout_seconds: float = 60.0) -> JobRecord:
        """Await terminal status for a job."""
        job = await self.get_job(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")

        if job.state in TERMINAL_JOB_STATES:
            return job

        evt = self._completion_events.setdefault(job_id, asyncio.Event())
        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout_seconds)
        except TimeoutError:
            raise TimeoutError(
                f"Job {job_id} did not reach terminal state within {timeout_seconds}s"
            ) from None

        final_job = await self.get_job(job_id)
        if final_job is None:
            raise JobNotFoundError(f"Job {job_id} not found after completion")
        return final_job

    async def _scheduler_loop(self) -> None:
        """Asynchronous scheduler background poll loop.

        Sleeps before the first poll so startup and submission ordering is
        deterministic with respect to the configured interval.
        """
        while self._running:
            await asyncio.sleep(self._config.poll_interval_seconds)
            with contextlib.suppress(asyncio.CancelledError, JobError, StorageError):
                await self._poll_and_schedule_next()

    async def _poll_and_schedule_next(self) -> None:
        """Claim the next available queued job and dispatch to workers."""
        if not self._running:
            return

        page = await self._storage.async_scan_records(JOBS_NAMESPACE, limit=20)
        for rec in page.records:
            job = _deserialize_job_record(rec.payload_bytes, rec.revision)
            if job.state == JobState.QUEUED:
                # Try to claim via CAS
                lease_expiry = (
                    (
                        _utc_now()
                        + datetime.timedelta(
                            seconds=self._config.lease_duration_seconds
                        )
                    )
                    .isoformat()
                    .replace("+00:00", "Z")
                )

                try:
                    running_job = await self._transition_job(
                        job,
                        JobState.RUNNING,
                        lease_owner=self._scheduler_id,
                        lease_expires_utc=lease_expiry,
                        increment_attempts=True,
                    )
                except JobStateError:
                    # Concurrently claimed by another worker/thread
                    continue

                # Spawn worker execution task
                task = asyncio.create_task(self._execute_job(running_job))
                self._active_tasks[job.job_id] = task

    async def _handle_worker_result(
        self, job: JobRecord, worker_result: WorkerResult
    ) -> None:
        """Persist worker result artifacts and transition job to terminal state."""
        current_job = await self.get_job(job.job_id)
        if current_job is None:
            return
        if current_job.state == JobState.CANCELLING:
            await self._transition_job(current_job, JobState.CANCELLED)
            return

        if worker_result.success:
            result_bytes = to_canonical_json_bytes(
                value_to_wire(worker_result.result_payload)
            )
            dep_fp = str(
                value_to_wire(job.request_wire).get("dependency_fingerprint", "")
            )
            artifact_res = await asyncio.to_thread(
                self._artifacts.put_artifact,
                result_bytes,
                media_type="application/json",
                provenance_hash=job.job_id,
                dependency_fingerprint=dep_fp,
                tags=[("job_id", job.job_id)],
            )
            await self._transition_job(
                current_job,
                JobState.SUCCEEDED,
                result_wire=worker_result.result_payload,
                artifact_refs=(artifact_res.ref.digest,),
            )
        else:
            await self._transition_job(
                current_job,
                JobState.FAILED,
                error_code=worker_result.error_code or "WORKER_ERROR",
                error_message=worker_result.error_message or "Worker execution failed",
            )

    def _lease_expiry_iso(self) -> str:
        """Compute the lease expiry timestamp for renewal."""
        return (
            (
                _utc_now()
                + datetime.timedelta(seconds=self._config.lease_duration_seconds)
            )
            .isoformat()
            .replace("+00:00", "Z")
        )

    async def _heartbeat_loop(self, job_id: str) -> None:
        """Persist bounded lease-renewal heartbeats while the worker runs."""
        interval = max(self._config.lease_duration_seconds / 3.0, 0.05)
        while True:
            await asyncio.sleep(interval)
            current = await self.get_job(job_id)
            if current is None or current.state != JobState.RUNNING:
                return
            renewed = JobRecord(
                job_id=current.job_id,
                state=current.state,
                revision=current.revision,
                request_wire=current.request_wire,
                idempotency_key=current.idempotency_key,
                attempts=current.attempts,
                max_attempts=current.max_attempts,
                lease_owner=current.lease_owner,
                lease_expires_utc=self._lease_expiry_iso(),
                result_wire=current.result_wire,
                artifact_refs=current.artifact_refs,
                error_code=current.error_code,
                error_message=current.error_message,
                created_at_utc=current.created_at_utc,
                updated_at_utc=_utc_now_iso(),
                last_heartbeat_utc=_utc_now_iso(),
            )
            await self._storage.async_commit_transaction(
                [
                    StorageMutation(
                        namespace=JOBS_NAMESPACE,
                        key=job_id,
                        schema_version=1,
                        payload_bytes=_serialize_job_record(renewed),
                        expected_revision=current.revision,
                    )
                ]
            )

    async def _execute_job(self, job: JobRecord) -> None:
        """Execute a claimed running job via Workers and ArtifactStore."""
        heartbeat = asyncio.create_task(self._heartbeat_loop(job.job_id))
        try:
            req_data = value_to_wire(job.request_wire)
            timeout = float(req_data.get("budget", {}).get("max_elapsed_seconds", 60.0))
            worker_task = WorkerTask(
                task_id=job.job_id,
                task_kind="execution.evaluate",
                payload=job.request_wire,
                budget=WorkerBudget(timeout_seconds=timeout),
            )

            worker_result = await self._workers.run_task(worker_task)
            await self._handle_worker_result(job, worker_result)

        except asyncio.CancelledError:
            # The scheduler task was cancelled (running-job cancellation).
            with contextlib.suppress(JobError, StorageError):
                current_job = await self.get_job(job.job_id)
                if current_job is not None and (
                    current_job.state == JobState.CANCELLING
                ):
                    await self._transition_job(current_job, JobState.CANCELLED)
            raise
        except WorkerCancellationError:
            current_job = await self.get_job(job.job_id)
            if current_job is not None:
                await self._transition_job(current_job, JobState.CANCELLED)
        except WorkerTimeoutError as err:
            current_job = await self.get_job(job.job_id)
            if current_job is not None:
                await self._transition_job(
                    current_job,
                    JobState.FAILED,
                    error_code="TIMEOUT",
                    error_message=str(err),
                )
        except Exception as err:  # noqa: BLE001 - job boundary failure containment
            current_job = await self.get_job(job.job_id)
            if current_job is not None:
                await self._transition_job(
                    current_job,
                    JobState.FAILED,
                    error_code=type(err).__name__,
                    error_message=str(err),
                )
        finally:
            heartbeat.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat
            self._active_tasks.pop(job.job_id, None)

    @override
    async def job_events(self, job_id: str) -> tuple[JobEvent, ...]:
        """Return the persisted transition events for a job, in order."""
        events: list[JobEvent] = []
        after_key: str | None = None
        prefix = f"{job_id}:"
        while True:
            page = await self._storage.async_scan_records(
                JOBS_EVENTS_NAMESPACE,
                prefix=prefix,
                limit=100,
                after_key=after_key,
            )
            for rec in page.records:
                data = json.loads(rec.payload_bytes.decode("utf-8"))
                events.append(
                    JobEvent(
                        job_id=data["job_id"],
                        seq=data["seq"],
                        from_state=JobState(data["from_state"]),
                        to_state=JobState(data["to_state"]),
                        utc=data["utc"],
                        reason=data.get("reason", ""),
                        detail=data.get("detail", ""),
                    )
                )
            if page.next_token is None:
                break
            after_key = page.next_token
        return tuple(events)

    @override
    async def close(self) -> None:
        """Stop admission, request cancellation, drain to the deadline.

        Storage, artifacts, and workers providers stay alive throughout:
        the composition root closes them only after jobs cleanup ends.
        """
        self._running = False
        if self._loop_task is not None:
            self._loop_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._loop_task

        # Request cancellation of running jobs, then drain to the deadline.
        for task in list(self._active_tasks.values()):
            if not task.done():
                task.cancel()
        # Deadline reached: nonterminal jobs remain durable and are
        # recovered at the next startup scan.
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(
                asyncio.gather(*self._active_tasks.values(), return_exceptions=True),
                timeout=self._config.shutdown_drain_seconds,
            )
        self._active_tasks.clear()


class _JobsFeature:
    """Feature providing HOST_JOBS requiring storage, artifacts, workers."""

    spec = FeatureSpec(
        "host.jobs",
        provides=frozenset({HOST_JOBS}),
        requires=frozenset(
            {
                HOST_STORAGE,
                HOST_ARTIFACTS,
                HOST_WORKERS,
                HOST_CATALOG,
                HOST_EXECUTION,
            }
        ),
        description="Durable quantitative job scheduler and recovery owner",
    )

    def __init__(self, config: JobsConfig) -> None:
        self._config = config
        self._service: _DurableJobs | None = None

    async def start(self, context: FeatureContext) -> None:
        storage = context.require(HOST_STORAGE)
        artifacts = context.require(HOST_ARTIFACTS)
        workers = context.require(HOST_WORKERS)
        catalog = context.require(HOST_CATALOG)
        execution = context.require(HOST_EXECUTION)

        self._service = _DurableJobs(
            self._config,
            storage,
            artifacts=artifacts,
            workers=workers,
            catalog=catalog,
            execution=execution,
        )
        await self._service.start()
        context.on_close(self._service.close)
        context.provide(HOST_JOBS, self._service)


def _jobs_feature(config: JobsConfig) -> _JobsFeature:
    """Construct the jobs owner for the host composition root only."""
    return _JobsFeature(config)


__all__ = (
    "HOST_JOBS",
    "JOBS_EVENTS_NAMESPACE",
    "TERMINAL_JOB_STATES",
    "JobCancelledError",
    "JobConflictError",
    "JobError",
    "JobEvent",
    "JobNotFoundError",
    "JobPage",
    "JobQuery",
    "JobRecord",
    "JobRequest",
    "JobState",
    "JobStateError",
    "Jobs",
    "JobsConfig",
    "_jobs_feature",
)
