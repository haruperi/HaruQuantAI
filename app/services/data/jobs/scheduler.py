"""Scheduler orchestration for recurring data update jobs."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Final, Literal

from app.services.data.contracts import (
    BackfillChunkRequest,
    JobRunResult,
    JobStatus,
    JobStatusRequest,
    ScheduleJobRequest,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.contracts.errors import DataError
from app.services.data.jobs.backfill import (
    BACKFILL_MAX_RECORDS_PER_CHUNK,
    JOB_LEASE_TIMEOUT_SECONDS,
    execute_backfill_chunk,
)
from app.services.data.sources.policy import evaluate_source_policy
from app.services.data.storage.database import execute_transaction
from app.utils import Clock, derive_stable_id, logger, utc_now

# Configuration Limits
JOB_MAX_SYMBOLS: Final[int] = 500
JOB_MAX_TIMEFRAMES: Final[int] = 20
JOB_MIN_INTERVAL_SECONDS: Final[int] = 60

# Background task manager for single-node in-process asyncio scheduler
_BACKGROUND_TASKS: dict[str, asyncio.Task[None]] = {}


def _get_active_lease_state(
    lease_expires_at: str | None, now: datetime
) -> Literal["none", "held", "expired"]:
    """Compute lease state based on lease_expires_at timestamp."""
    logger.debug("Running DATA function: _get_active_lease_state")
    if not lease_expires_at:
        return "none"
    expires = datetime.fromisoformat(lease_expires_at)
    return "held" if expires > now else "expired"


def _handle_create(request: ScheduleJobRequest) -> None:
    """Handle creation of a job definition in SQLite."""
    logger.debug("Running DATA function: _handle_create")
    definition = request.definition
    if definition is None:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "create action requires a definition"},
            request_id=request.request_id,
        )

    # 1. Enforce validation bounds
    if len(definition.symbols) > JOB_MAX_SYMBOLS:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={
                "symbols_count": len(definition.symbols),
                "allowed": JOB_MAX_SYMBOLS,
            },
            request_id=request.request_id,
        )
    if len(definition.timeframes) > JOB_MAX_TIMEFRAMES:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={
                "timeframes_count": len(definition.timeframes),
                "allowed": JOB_MAX_TIMEFRAMES,
            },
            request_id=request.request_id,
        )
    if (
        definition.interval_seconds is not None
        and definition.interval_seconds < JOB_MIN_INTERVAL_SECONDS
    ):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "interval": definition.interval_seconds,
                "min_allowed": JOB_MIN_INTERVAL_SECONDS,
            },
            request_id=request.request_id,
        )

    # 2. Evaluate source policies
    from app.services.data.contracts import MarketDataRequest

    dkind: Literal["bars", "ticks", "spreads"] = (
        "bars" if "ohlcv" in definition.data_kinds else "ticks"
    )
    dummy_req = MarketDataRequest(
        source_id=definition.source_id,
        symbol=definition.symbols[0],
        data_kind=dkind,
        timeframe=definition.timeframes[0] if definition.timeframes else None,
        start=definition.start,
        end=definition.end or (definition.start + timedelta(hours=1)),
        limit=10,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id=request.request_id,
    )
    evaluate_source_policy(dummy_req)

    # 3. Check if job already exists
    check_sql = "SELECT job_id FROM data_update_jobs WHERE job_id = ?"
    exists_res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(check_sql,),
                parameter_sets=((request.job_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    if exists_res.rows:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": f"Job {request.job_id} already exists"},
            request_id=request.request_id,
        )

    # 4. Insert definition into SQLite
    insert_sql = (
        "INSERT INTO data_update_jobs ("
        "    job_id, source_id, symbols_json, timeframes_json, data_kinds_json, "
        "    start, end, interval_seconds, enabled, created_at, request_id, "
        "    state, recovery_state"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'created', 'clean')"
    )
    start_str = definition.start.astimezone(UTC).isoformat().replace("+00:00", "Z")
    end_str = (
        definition.end.astimezone(UTC).isoformat().replace("+00:00", "Z")
        if definition.end
        else None
    )
    created_str = (
        definition.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    )

    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(insert_sql,),
                parameter_sets=(
                    (
                        request.job_id,
                        definition.source_id,
                        json.dumps(definition.symbols),
                        json.dumps(definition.timeframes),
                        json.dumps(definition.data_kinds),
                        start_str,
                        end_str,
                        definition.interval_seconds,
                        1 if definition.enabled else 0,
                        created_str,
                        request.request_id,
                    ),
                ),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )

    # Start background loop if enabled
    if definition.enabled and definition.interval_seconds is not None:
        _start_background_loop(request.job_id, definition.interval_seconds)


def _handle_start(request: ScheduleJobRequest, clock: Clock | None = None) -> None:
    """Handle starting an update job."""
    logger.debug("Running DATA function: _handle_start")
    query_sql = (
        "SELECT job_id, interval_seconds, state, lease_owner, lease_expires_at "
        "FROM data_update_jobs WHERE job_id = ?"
    )
    job_res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(query_sql,),
                parameter_sets=((request.job_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    if not job_res.rows:
        raise DataError(
            "JOB_NOT_FOUND",
            safe_details={"job_id": request.job_id},
            request_id=request.request_id,
        )
    row = job_res.rows[0]

    # Check lease
    now = utc_now(clock)
    lease_expires_val = row["lease_expires_at"]
    lease_expires_str = (
        str(lease_expires_val) if lease_expires_val is not None else None
    )
    lease_state = _get_active_lease_state(lease_expires_str, now)
    if str(row["state"]) == "running" and lease_state == "held":
        raise DataError(
            "CONCURRENT_WRITE_LOCKED",
            safe_details={"message": "Cannot start a job while lease is held"},
            request_id=request.request_id,
        )

    # Update enabled state
    update_sql = (
        "UPDATE data_update_jobs SET enabled = 1, state = 'created' WHERE job_id = ?"
    )
    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(update_sql,),
                parameter_sets=((request.job_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )

    # Start loop
    interval = row["interval_seconds"]
    if interval is not None:
        _start_background_loop(request.job_id, int(interval))


def _handle_stop(request: ScheduleJobRequest) -> None:
    """Handle stopping an update job."""
    logger.debug("Running DATA function: _handle_stop")
    query_sql = "SELECT job_id FROM data_update_jobs WHERE job_id = ?"
    job_res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(query_sql,),
                parameter_sets=((request.job_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    if not job_res.rows:
        raise DataError(
            "JOB_NOT_FOUND",
            safe_details={"job_id": request.job_id},
            request_id=request.request_id,
        )

    # Cancel background loop
    _stop_background_loop(request.job_id)

    # Update to stopped
    update_sql = (
        "UPDATE data_update_jobs "
        "SET enabled = 0, "
        "    state = 'stopped', "
        "    lease_owner = NULL, "
        "    lease_expires_at = NULL "
        "WHERE job_id = ?"
    )
    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(update_sql,),
                parameter_sets=((request.job_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )


def schedule_update_job(
    request: ScheduleJobRequest,
    *,
    clock: Clock | None = None,
) -> JobStatus:
    """Coordinate create/start/stop/run-once lifecycle for update jobs.

    Args:
        request: The schedule job request.
        clock: Optional injected UTC clock.

    Returns:
        The updated JobStatus.

    Raises:
        DataError: If transition, lease, source-policy, or schedule validation fails.
    """
    logger.info(
        "Scheduling update job %s with action %s (request: %s)",
        request.job_id,
        request.action,
        request.request_id,
    )

    if request.action == "create":
        _handle_create(request)
    elif request.action == "start":
        _handle_start(request, clock)
    elif request.action == "stop":
        _handle_stop(request)
    elif request.action == "run_once":
        run_data_update_job_once(request.job_id, request.request_id, clock=clock)

    return read_update_job_status(
        JobStatusRequest(job_id=request.job_id, request_id=request.request_id),
        clock=clock,
    )


def read_update_job_status(
    request: JobStatusRequest,
    *,
    clock: Clock | None = None,
) -> JobStatus:
    """Query current status of a job definition from SQLite database.

    Args:
        request: The job status request.
        clock: Optional injected UTC clock.

    Returns:
        The fetched JobStatus.
    """
    logger.info("Reading status for update job %s", request.job_id)

    query_sql = (
        "SELECT job_id, state, enabled, last_run_status, last_checkpoint, "
        "last_error, next_run_at, lease_owner, lease_expires_at, recovery_state "
        "FROM data_update_jobs WHERE job_id = ?"
    )
    res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(query_sql,),
                parameter_sets=((request.job_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )

    if not res.rows:
        raise DataError(
            "JOB_NOT_FOUND",
            safe_details={"job_id": request.job_id},
            request_id=request.request_id,
        )

    row = res.rows[0]
    now = utc_now(clock)

    lease_expires_val = row["lease_expires_at"]
    lease_expires_str = (
        str(lease_expires_val) if lease_expires_val is not None else None
    )
    lease_state = _get_active_lease_state(lease_expires_str, now)
    next_run = (
        datetime.fromisoformat(str(row["next_run_at"])) if row["next_run_at"] else None
    )

    return JobStatus(
        job_id=str(row["job_id"]),
        state=str(row["state"]),  # type: ignore[arg-type]
        enabled=bool(row["enabled"]),
        last_run_status=str(row["last_run_status"]) if row["last_run_status"] else None,  # type: ignore[arg-type]
        last_checkpoint=str(row["last_checkpoint"]) if row["last_checkpoint"] else None,
        last_error=str(row["last_error"]) if row["last_error"] else None,
        next_run_at=next_run,
        lease_state=lease_state,
        recovery_state=str(row["recovery_state"]),  # type: ignore[arg-type]
        request_id=request.request_id,
    )


def _acquire_job_run_lease(
    job_id: str, started_at: datetime, request_id: str
) -> dict[str, object]:
    """Verify job execution permissions and acquire the lease in SQLite."""
    logger.debug("Running DATA function: _acquire_job_run_lease")
    query_sql = (
        "SELECT job_id, source_id, symbols_json, timeframes_json, data_kinds_json, "
        "start, end, interval_seconds, enabled, state, lease_owner, lease_expires_at "
        "FROM data_update_jobs WHERE job_id = ?"
    )
    res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(query_sql,),
                parameter_sets=((job_id,),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if not res.rows:
        raise DataError(
            "JOB_NOT_FOUND",
            safe_details={"job_id": job_id},
            request_id=request_id,
        )
    row = res.rows[0]

    # Verify enabled
    if not bool(row["enabled"]):
        raise DataError(
            "POLICY_BLOCKED",
            safe_details={"message": f"Job {job_id} is currently disabled"},
            request_id=request_id,
        )

    # Acquire lease or check concurrency
    lease_expires_val = row["lease_expires_at"]
    lease_expires_str = (
        str(lease_expires_val) if lease_expires_val is not None else None
    )
    lease_state = _get_active_lease_state(lease_expires_str, started_at)
    if str(row["state"]) == "running" and lease_state == "held":
        raise DataError(
            "CONCURRENT_WRITE_LOCKED",
            safe_details={"message": "Job lease already held", "job_id": job_id},
            request_id=request_id,
        )

    # Acquire/update lease
    lease_expires = started_at + timedelta(seconds=JOB_LEASE_TIMEOUT_SECONDS)
    lease_expires_str = lease_expires.isoformat().replace("+00:00", "Z")
    update_lease_sql = (
        "UPDATE data_update_jobs "
        "SET state = 'running', lease_owner = ?, lease_expires_at = ? "
        "WHERE job_id = ?"
    )
    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(update_lease_sql,),
                parameter_sets=((request_id, lease_expires_str, job_id),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    return dict(row)


def _determine_run_range(
    row: dict[str, object],
    job_id: str,
    request_id: str,
    observed_at: datetime,
) -> tuple[datetime, datetime]:
    """Calculate the precise start and end times for the backfill run."""
    logger.debug("Running DATA function: _determine_run_range")
    job_start = datetime.fromisoformat(str(row["start"]))
    job_end = datetime.fromisoformat(str(row["end"])) if row["end"] else None

    # Determine start timestamp from last committed checkpoint
    query_max_committed = (
        "SELECT MAX(committed_end) as max_end "
        "FROM data_backfill_checkpoints WHERE job_id = ?"
    )
    chk_res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(query_max_committed,),
                parameter_sets=((job_id,),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    start_time = job_start
    if chk_res.rows and chk_res.rows[0]["max_end"]:
        max_end_str = str(chk_res.rows[0]["max_end"])
        max_end_dt = datetime.fromisoformat(max_end_str)
        start_time = max(job_start, max_end_dt)

    end_time = job_end or observed_at

    # If start_time >= end_time, construct at least one small chunk
    # of 1 minute to satisfy the committed chunk requirement
    if start_time >= end_time:
        end_time = start_time + timedelta(minutes=1)

    return start_time, end_time


def _execute_run_chunks(
    row: dict[str, object],
    start_time: datetime,
    end_time: datetime,
    request_id: str,
    clock: Clock | None,
) -> tuple[int, int, str | None]:
    """Loop and execute all required backfill chunk requests."""
    logger.debug("Running DATA function: _execute_run_chunks")
    job_id = str(row["job_id"])
    symbols = json.loads(str(row["symbols_json"]))
    timeframes = json.loads(str(row["timeframes_json"]))
    data_kinds = json.loads(str(row["data_kinds_json"]))

    committed_chunks = 0
    record_count = 0
    last_chk = None

    current_time = start_time
    while current_time < end_time:
        next_time = min(current_time + timedelta(days=1), end_time)

        for kind in data_kinds:
            for symbol in symbols:
                tfs = timeframes if kind == "ohlcv" else [None]
                for tf in tfs:
                    chunk_req = BackfillChunkRequest(
                        job_id=job_id,
                        source_id=str(row["source_id"]),
                        symbol=symbol,
                        data_kind=kind,
                        timeframe=tf,
                        start=current_time,
                        end=next_time,
                        schema_version="v1",
                        normalization_version="v1",
                        max_records=BACKFILL_MAX_RECORDS_PER_CHUNK,
                        request_id=request_id,
                    )
                    chunk_res = execute_backfill_chunk(chunk_req, clock=clock)
                    committed_chunks += 1
                    record_count += chunk_res.record_count
                    last_chk = chunk_res.checkpoint

        current_time = next_time

    return committed_chunks, record_count, last_chk


def run_data_update_job_once(
    job_id: str,
    request_id: str,
    *,
    clock: Clock | None = None,
) -> JobRunResult:
    """Execute a data update job synchronously once.

    Args:
        job_id: The job identifier.
        request_id: The request identifier.
        clock: Optional injected UTC clock.

    Returns:
        The JobRunResult details.
    """
    logger.info("Executing job run once for %s", job_id)
    started_at = utc_now(clock)
    run_material = f"{job_id}:{request_id}:{started_at.isoformat()}"
    run_id = f"run-{hashlib.sha256(run_material.encode()).hexdigest()}"

    try:
        row = _acquire_job_run_lease(job_id, started_at, request_id)
        start_time, end_time = _determine_run_range(row, job_id, request_id, started_at)
        committed_chunks, record_count, last_chk = _execute_run_chunks(
            row, start_time, end_time, request_id, clock
        )

        # Update database with success
        finished_at = utc_now(clock)
        next_run_str = None
        interval_val = row["interval_seconds"]
        if interval_val is not None:
            next_run = finished_at + timedelta(seconds=int(str(interval_val)))
            next_run_str = next_run.isoformat().replace("+00:00", "Z")

        update_success_sql = (
            "UPDATE data_update_jobs "
            "SET state = 'stopped', "
            "    last_run_status = 'succeeded', "
            "    last_checkpoint = ?, "
            "    last_error = NULL, "
            "    next_run_at = ?, "
            "    lease_owner = NULL, "
            "    lease_expires_at = NULL "
            "WHERE job_id = ?"
        )
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(update_success_sql,),
                    parameter_sets=((last_chk, next_run_str, job_id),),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        )

        return JobRunResult(
            job_id=job_id,
            run_id=run_id,
            state="succeeded",
            started_at=started_at,
            finished_at=finished_at,
            committed_chunks=committed_chunks,
            record_count=record_count,
            last_checkpoint=last_chk,
            request_id=request_id,
        )

    except Exception as error:  # noqa: BLE001
        logger.error("Job run once failed for job %s", job_id)
        finished_at = utc_now(clock)
        err_code = error.code if isinstance(error, DataError) else "SCHEDULER_ERROR"

        update_fail_sql = (
            "UPDATE data_update_jobs "
            "SET state = 'failed', "
            "    last_run_status = 'failed', "
            "    last_error = ?, "
            "    lease_owner = NULL, "
            "    lease_expires_at = NULL "
            "WHERE job_id = ?"
        )
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(update_fail_sql,),
                    parameter_sets=((err_code, job_id),),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        )

        return JobRunResult(
            job_id=job_id,
            run_id=run_id,
            state="failed",
            started_at=started_at,
            finished_at=finished_at,
            committed_chunks=0,
            record_count=0,
            last_checkpoint=None,
            error_code=err_code,
            request_id=request_id,
        )


def _start_background_loop(job_id: str, interval_seconds: int) -> None:
    """Helper to start the background asyncio scheduler loop for one job."""
    if job_id in _BACKGROUND_TASKS:
        logger.info("Scheduler task for job %s is already running", job_id)
        return

    async def _loop() -> None:
        """Execute one private DATA operation."""
        logger.info("Entering background scheduler loop for job %s", job_id)
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                # Check if job is still enabled
                query_sql = "SELECT enabled FROM data_update_jobs WHERE job_id = ?"
                chk = execute_transaction(
                    TransactionRequest(
                        plan=StatementPlan(
                            statements=(query_sql,),
                            parameter_sets=((job_id,),),
                            max_rows=1,
                        ),
                        request_id=derive_stable_id("req", f"scheduler-loop:{job_id}"),
                    )
                )
                if not chk.rows or not bool(chk.rows[0]["enabled"]):
                    logger.info("Job %s disabled, exiting background loop", job_id)
                    break

                try:
                    run_data_update_job_once(
                        job_id,
                        derive_stable_id("req", f"scheduler-run:{job_id}"),
                    )
                except Exception:  # noqa: BLE001
                    logger.error("Background job execution failed for %s", job_id)

        except asyncio.CancelledError:
            logger.info("Background loop for job %s was cancelled", job_id)
            raise

    try:
        loop = asyncio.get_running_loop()
        coroutine = _loop()
        try:
            task = loop.create_task(coroutine)
        except BaseException:
            coroutine.close()
            raise
        _BACKGROUND_TASKS[job_id] = task
    except RuntimeError:
        logger.warning(
            "No running event loop found. Background loop for job %s will not start.",
            job_id,
        )


def _stop_background_loop(job_id: str) -> None:
    """Helper to stop/cancel the background asyncio loop for one job."""
    task = _BACKGROUND_TASKS.pop(job_id, None)
    if task:
        logger.info("Cancelling background loop task for job %s", job_id)
        task.cancel()
