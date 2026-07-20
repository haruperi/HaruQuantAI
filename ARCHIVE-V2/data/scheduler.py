"""Data update scheduler, job lifecycle, and feeds tracking manager.

Provides persisted job tracking, lease concurrency controls, background job loops,
and active feeds monitoring/heartbeat status checks.
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.data.errors import DataIntegrityError as DataError
from app.services.data.errors import DataValidationError as ValidationError
from app.services.data.feeds import (
    ACTIVE_FEEDS,
    get_feed_status,
    handle_feed_overflow,
    register_mock_feed,
)
from app.services.data.gateway import get_data
from app.services.data.storage import db_helper, save_market_data
from app.services.data.validation import (
    DEFAULT_BACKFILL_OHLCV_CHUNK_DAYS,
    DEFAULT_BACKFILL_OHLCV_CHUNK_RECORDS,
    DEFAULT_BACKFILL_TICK_CHUNK_DAYS,
    DEFAULT_BACKFILL_TICK_CHUNK_RECORDS,
    MAX_OHLCV_LIMIT,
    MAX_SYMBOLS_PER_JOB,
    MAX_TICK_LIMIT,
    MAX_TIMEFRAMES_PER_JOB,
    validate_license,
    validate_source_readiness,
)
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp

__all__ = [
    "ACTIVE_FEEDS",
    "create_data_update_job",
    "get_data_update_job_status",
    "get_feed_status",
    "handle_feed_overflow",
    "initialize_data_scheduler",
    "recover_crashed_jobs",
    "recover_data_jobs_on_startup",
    "register_mock_feed",
    "run_data_update_job_once",
    "start_data_update_job",
    "stop_data_update_job",
]

# In-memory maps
ACTIVE_JOB_TASKS: dict[str, asyncio.Task[None]] = {}
BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Helper to get running event loop or create a new one safely."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        try:
            return asyncio.get_event_loop_policy().get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


def recover_crashed_jobs() -> int:
    """Recover jobs that were left in the 'running' state after a system crash."""
    logger.info("Executing scheduler crash recovery sequence...")
    now_str = datetime.now(UTC).isoformat()
    count = 0
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, state FROM data_jobs WHERE state = 'running';"
            )
            rows = cursor.fetchall()
            for r in rows:
                job_id = r["id"]
                logger.warning(
                    f"Crashed job detected: name={r['name']}. "
                    "Transitioning to recovering state."
                )
                conn.execute(
                    """
                    UPDATE data_jobs
                    SET state = 'recovering',
                        last_error = 'SYSTEM_CRASH_DETECTION',
                        lease_owner = NULL,
                        lease_expires = NULL,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (now_str, job_id),
                )
                count += 1
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to perform database crash recovery: {e}")
    return count


def recover_data_jobs_on_startup() -> int:
    """Explicitly recover crashed jobs during intentional application startup.

    This replaces the previous import-time crash recovery. Importing
    `app.services.data` no longer touches the database; callers (app
    lifespan/startup hooks, or scripts) must invoke this explicitly.

    Returns:
        int: Number of jobs transitioned from 'running' to 'recovering'.
    """
    logger.info("recover_data_jobs_on_startup: explicit startup recovery invoked.")
    return recover_crashed_jobs()


# Backward-compatible alias for explicit startup initialization callers.
initialize_data_scheduler = recover_data_jobs_on_startup


# --- Scheduler Jobs Business Logic ---
def _validate_job_creation_args(
    name: str,
    source: str,
    symbols: list[str],
    timeframes: list[str],
    request_id: str | None = None,
) -> None:
    """Validate job creation parameters (licensing, lengths, non-emptiness)."""
    if not name or not name.strip():
        raise ValidationError("Job name cannot be empty.", code="INVALID_INPUT")
    if not source:
        raise ValidationError(
            "Source identifier cannot be empty.", code="INVALID_INPUT"
        )
    if not symbols:
        raise ValidationError("Symbols list cannot be empty.", code="INVALID_INPUT")
    if not timeframes:
        raise ValidationError("Timeframes list cannot be empty.", code="INVALID_INPUT")

    if len(symbols) > MAX_SYMBOLS_PER_JOB:
        raise ValidationError("Max symbols limit exceeded.", code="INVALID_INPUT")
    if len(timeframes) > MAX_TIMEFRAMES_PER_JOB:
        raise ValidationError("Max timeframes limit exceeded.", code="INVALID_INPUT")

    validate_source_readiness(source, "research", request_id=request_id)

    for sym in symbols:
        try:
            validate_license(
                source,
                sym,
                workflow_context="research",
                request_id=request_id,
            )
        except ValidationError as e:
            logger.error(f"License check failed for {source}:{sym}: {e}")
            err_msg = f"License check failed: {e}"
            raise ValidationError(err_msg, code="LICENSE_RESTRICTION") from e


def create_data_update_job(
    name: str,
    source: str,
    symbols: list[str],
    timeframes: list[str],
    data_kind: str,
    storage_format: str,
    storage_path: str,
    start_time: str | None = None,
    end_time: str | None = None,
    schedule: str | None = None,
    enabled: bool = True,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a persisted job definition in the database."""
    logger.info(
        f"Creating data update job: name={name}, source={source}",
        extra={"request_id": request_id},
    )

    _validate_job_creation_args(
        name=name,
        source=source,
        symbols=symbols,
        timeframes=timeframes,
        request_id=request_id,
    )

    exists = False
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT id FROM data_jobs WHERE name = ?;", (name,))
            if cursor.fetchone():
                exists = True
    except Exception as e:
        err_msg = f"Database error checking duplicate jobs: {e}"
        raise DataError(err_msg) from e

    if exists:
        err_msg = f"Job with name '{name}' already exists."
        raise ValidationError(err_msg, code="INVALID_INPUT")

    job_id = f"job_{name.lower().replace(' ', '_')}"
    now_str = datetime.now(UTC).isoformat()
    symbols_str = ",".join(symbols)
    timeframes_str = ",".join(timeframes)

    job_data = {
        "id": job_id,
        "name": name,
        "source": source,
        "symbols": symbols_str,
        "timeframes": timeframes_str,
        "data_kind": data_kind,
        "storage_format": storage_format,
        "storage_path": storage_path,
        "start_time": start_time,
        "end_time": end_time,
        "schedule": schedule,
        "enabled": 1 if enabled else 0,
        "state": "created",
        "last_run_status": None,
        "last_checkpoint": None,
        "last_error": None,
        "next_run": None,
        "lease_owner": None,
        "lease_expires": None,
        "created_at": now_str,
        "updated_at": now_str,
    }

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO data_jobs (
                    id, name, source, symbols, timeframes, data_kind, storage_format,
                    storage_path, start_time, end_time, schedule, enabled, state,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    job_id,
                    name,
                    source,
                    symbols_str,
                    timeframes_str,
                    data_kind,
                    storage_format,
                    storage_path,
                    start_time,
                    end_time,
                    schedule,
                    1 if enabled else 0,
                    "created",
                    now_str,
                    now_str,
                ),
            )
    except Exception as e:
        logger.error(f"Failed to create job {name} in DB: {e}")
        err_msg = f"Database error writing job definition: {e}"
        raise DataError(err_msg) from e

    return job_data


async def _run_job_loop(job_name: str) -> None:
    """Internal task loop representing a running scheduled job."""
    logger.info(f"Background worker loop started for job '{job_name}'.")
    while True:
        try:
            # Check enabled status and lease
            job = None
            with db_helper.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM data_jobs WHERE name = ?;", (job_name,)
                )
                row = cursor.fetchone()
                if row:
                    job = dict(row)

            if not job or not job["enabled"]:
                logger.info(f"Job '{job_name}' disabled. Stopping worker loop.")
                break

            # Execute one real chunked, checkpointed update cycle.
            now_str = datetime.now(UTC).isoformat()
            with db_helper.get_connection() as conn:
                conn.execute(
                    "UPDATE data_jobs SET state = 'running', updated_at = ? "
                    "WHERE name = ?;",
                    (now_str, job_name),
                )
            await _execute_single_run(job_name)

            # Rest briefly
            await asyncio.sleep(60.0)

        except asyncio.CancelledError:
            logger.info(f"Worker task for '{job_name}' was cancelled.")
            break
        except Exception as e:  # noqa: BLE001
            logger.error(f"Scheduler worker loop error on job '{job_name}': {e}")
            await asyncio.sleep(10.0)


def start_data_update_job(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Start recurring background execution for a job."""
    logger.info(
        f"Starting scheduled job: name={name}",
        extra={"request_id": request_id},
    )

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database lookup failure: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job with name '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    if not job["schedule"]:
        err_msg = f"Job '{name}' cannot start recurringly because schedule is omitted."
        raise ValidationError(
            err_msg,
            code="INVALID_INPUT",
        )

    if name in ACTIVE_JOB_TASKS and not ACTIVE_JOB_TASKS[name].done():
        return {"job_id": job["id"], "state": "running"}

    now_str = datetime.now(UTC).isoformat()
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                "UPDATE data_jobs SET enabled = 1, state = 'running', "
                "updated_at = ? WHERE name = ?;",
                (now_str, name),
            )
    except Exception as e:
        err_msg = f"Failed to enable job '{name}': {e}"
        raise DataError(err_msg) from e

    loop = _get_or_create_event_loop()
    task = loop.create_task(_run_job_loop(name))
    ACTIVE_JOB_TASKS[name] = task

    return {"job_id": job["id"], "state": "running"}


def stop_data_update_job(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Stop or disable scheduled background execution for a job."""
    logger.info(f"Stopping job: name={name}", extra={"request_id": request_id})

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database lookup error: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    task = ACTIVE_JOB_TASKS.get(name)
    if task and not task.done():
        task.cancel()

    now_str = datetime.now(UTC).isoformat()
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                UPDATE data_jobs
                SET enabled = 0,
                    state = 'stopped',
                    lease_owner = NULL,
                    lease_expires = NULL,
                    updated_at = ?
                WHERE name = ?;
                """,
                (now_str, name),
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to update database on stop for {name}: {e}")

    return {"job_id": job["id"], "state": "stopped"}


def _normalize_job_data_kind(data_kind: str | None) -> str:
    """Map a persisted job `data_kind` onto a gateway retrieval kind."""
    kind = (data_kind or "ohlcv").lower()
    if kind in ("ticks", "tick"):
        return "ticks"
    if kind in ("spreads", "spread"):
        return "spreads"
    # 'bars', 'ohlcv', and 'volume' all retrieve OHLCV bars.
    return "ohlcv"


def _chunk_windows(
    start: datetime,
    end: datetime,
    chunk_days: int,
) -> list[tuple[datetime, datetime]]:
    """Split `[start, end)` into consecutive windows of at most `chunk_days`."""
    windows: list[tuple[datetime, datetime]] = []
    cursor = start
    step = timedelta(days=chunk_days)
    while cursor < end:
        upper = min(cursor + step, end)
        windows.append((cursor, upper))
        cursor = upper
    return windows


def _build_chunk_plan(job: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """Build the ordered symbol x timeframe x window chunk plan for a job.

    Chunk windows are sized by `DEFAULT_BACKFILL_OHLCV_CHUNK_DAYS` for bar
    kinds and `DEFAULT_BACKFILL_TICK_CHUNK_DAYS` for tick/spread kinds
    (FR-DATA-044). Jobs without an explicit window default to one trailing
    chunk ending now (incremental update).

    Returns:
        tuple[list[dict[str, Any]], str]: The chunk plan and normalized kind.
    """
    kind = _normalize_job_data_kind(job.get("data_kind"))
    chunk_days = (
        DEFAULT_BACKFILL_OHLCV_CHUNK_DAYS
        if kind == "ohlcv"
        else DEFAULT_BACKFILL_TICK_CHUNK_DAYS
    )
    end = (
        normalize_timestamp(job["end_time"])
        if job.get("end_time")
        else datetime.now(UTC)
    )
    start = (
        normalize_timestamp(job["start_time"])
        if job.get("start_time")
        else end - timedelta(days=chunk_days)
    )
    symbols = [s for s in (job.get("symbols") or "").split(",") if s]
    timeframes: list[str | None]
    if kind == "ohlcv":
        timeframes = [t for t in (job.get("timeframes") or "").split(",") if t]
    else:
        timeframes = [None]

    plan: list[dict[str, Any]] = []
    for symbol in symbols:
        for tf in timeframes:
            for window_start, window_end in _chunk_windows(start, end, chunk_days):
                plan.append(
                    {
                        "symbol": symbol,
                        "timeframe": tf,
                        "start": window_start,
                        "end": window_end,
                    }
                )
    return plan, kind


def _resume_index(plan: list[dict[str, Any]], checkpoint_str: str | None) -> int:
    """Return the plan index to resume from after the last committed checkpoint.

    Unparseable or legacy checkpoints restart from the beginning; completed
    chunks are cache-backed, so a restart is cheap and idempotent.
    """
    if not checkpoint_str:
        return 0
    try:
        checkpoint = json.loads(checkpoint_str)
    except (TypeError, ValueError):
        return 0
    if not isinstance(checkpoint, dict):
        return 0
    for index, chunk in enumerate(plan):
        if (
            chunk["symbol"] == checkpoint.get("symbol")
            and (chunk["timeframe"] or "") == (checkpoint.get("timeframe") or "")
            and chunk["end"].isoformat() == checkpoint.get("chunk_end")
        ):
            return index + 1
    return 0


def _commit_chunk_checkpoint(
    name: str,
    chunk: dict[str, Any],
    index: int,
    total: int,
) -> None:
    """Transactionally commit a completed chunk as the job's checkpoint."""
    checkpoint = json.dumps(
        {
            "symbol": chunk["symbol"],
            "timeframe": chunk["timeframe"],
            "chunk_end": chunk["end"].isoformat(),
            "chunk_index": index + 1,
            "total_chunks": total,
        }
    )
    now_str = datetime.now(UTC).isoformat()
    with db_helper.get_connection() as conn:
        conn.execute(
            "UPDATE data_jobs SET last_checkpoint = ?, updated_at = ? WHERE name = ?;",
            (checkpoint, now_str, name),
        )


def _chunk_dataset_path(
    storage_path: str,
    chunk: dict[str, Any],
    kind: str,
    extension: str,
) -> str:
    """Build the deterministic, idempotent dataset path for one chunk."""
    label = chunk["timeframe"] or kind
    file_name = (
        f"{chunk['symbol']}_{label}_"
        f"{chunk['start']:%Y%m%dT%H%M%S}_{chunk['end']:%Y%m%dT%H%M%S}.{extension}"
    )
    return f"{storage_path.rstrip('/')}/{file_name}"


async def _execute_single_run(name: str) -> None:
    """Execute one real, chunked, checkpoint-committed update run for a job.

    Implements FR-DATA-043/FR-DATA-044: each symbol x timeframe window is
    split into `DEFAULT_BACKFILL_*_CHUNK_DAYS` chunks; every chunk is
    retrieved through the governed gateway (`WF-DATA-001`), bounded by
    `DEFAULT_BACKFILL_*_CHUNK_RECORDS`, persisted atomically as its own
    dataset file (`WF-DATA-021`), and committed as a checkpoint so a crashed
    or failed run resumes from the last committed chunk.
    """
    logger.info(f"Starting one-time execution run for job '{name}'...")
    now_str = datetime.now(UTC).isoformat()
    try:
        job: dict[str, Any] | None = None
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
        if not job:
            err_msg = f"Job '{name}' not found for execution."
            raise DataError(err_msg)

        plan, kind = _build_chunk_plan(job)
        record_cap = (
            DEFAULT_BACKFILL_OHLCV_CHUNK_RECORDS
            if kind == "ohlcv"
            else DEFAULT_BACKFILL_TICK_CHUNK_RECORDS
        )
        request_limit = min(
            record_cap, MAX_OHLCV_LIMIT if kind == "ohlcv" else MAX_TICK_LIMIT
        )
        extension = (
            "parquet"
            if str(job.get("storage_format", "csv")).lower() == "parquet"
            else "csv"
        )
        start_index = _resume_index(plan, job.get("last_checkpoint"))
        total = len(plan)
        logger.info(
            f"Job '{name}': executing {total - start_index}/{total} chunk(s) "
            f"(resume_index={start_index}, kind={kind})."
        )

        for index in range(start_index, total):
            chunk = plan[index]
            records = get_data(
                symbol=chunk["symbol"],
                start_time=chunk["start"].isoformat(),
                end_time=chunk["end"].isoformat(),
                data_kind=kind,
                timeframe=chunk["timeframe"],
                source=job["source"],
                limit=request_limit,
                stale_data_behavior="refresh_and_return",
                workflow_context="research",
            )
            if len(records) > record_cap:
                records = records[:record_cap]
            if records:
                dataset_path = _chunk_dataset_path(
                    str(job["storage_path"]), chunk, kind, extension
                )
                save_market_data(records, dataset_path, extension, overwrite=True)
            _commit_chunk_checkpoint(name, chunk, index, total)
            await asyncio.sleep(0)

        with db_helper.get_connection() as conn:
            conn.execute(
                """
                UPDATE data_jobs
                SET state = 'completed',
                    last_run_status = 'success',
                    last_error = NULL,
                    updated_at = ?
                WHERE name = ?;
                """,
                (datetime.now(UTC).isoformat(), name),
            )
    except Exception as ex:  # noqa: BLE001
        logger.error(f"One-off execution failed for '{name}': {ex}")
        try:
            with db_helper.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE data_jobs
                    SET state = 'failed',
                        last_run_status = 'failed',
                        last_error = ?,
                        updated_at = ?
                    WHERE name = ?;
                    """,
                    (str(ex), now_str, name),
                )
        except Exception as db_ex:  # noqa: BLE001
            logger.error(f"Failed to record job failure for '{name}': {db_ex}")


def run_data_update_job_once(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Execute one immediate update run of a job definition."""
    logger.info(
        f"Triggering immediate run: name={name}",
        extra={"request_id": request_id},
    )

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database lookup error: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    now_str = datetime.now(UTC).isoformat()
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                "UPDATE data_jobs SET state = 'running', "
                "updated_at = ? WHERE name = ?;",
                (now_str, name),
            )
    except Exception as e:
        err_msg = f"Database update failure: {e}"
        raise DataError(err_msg) from e

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_execute_single_run(name))
        BACKGROUND_TASKS.add(task)
        task.add_done_callback(BACKGROUND_TASKS.discard)
    except RuntimeError:
        asyncio.run(_execute_single_run(name))

    return {"job_id": job["id"], "state": "running"}


def get_data_update_job_status(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Inspect the status details of a job definition."""
    logger.info(
        f"Retrieving status for job: name={name}",
        extra={"request_id": request_id},
    )

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database query error: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    return {
        "job_id": job["id"],
        "name": job["name"],
        "source": job["source"],
        "symbols": job["symbols"].split(",") if job["symbols"] else [],
        "timeframes": job["timeframes"].split(",") if job["timeframes"] else [],
        "data_kind": job["data_kind"],
        "state": job["state"],
        "enabled": bool(job["enabled"]),
        "last_run_status": job["last_run_status"],
        "last_checkpoint": job["last_checkpoint"],
        "last_error": job["last_error"],
        "next_run": job["next_run"],
        "lease_owner": job["lease_owner"],
        "lease_expires": job["lease_expires"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }
