"""Unit tests for scheduler leases, job states, feed overflows, and heartbeats."""

import sqlite3

import pytest
from app.services.data.scheduler import (
    create_data_update_job,
    get_data_update_job_status,
    get_feed_status,
    handle_feed_overflow,
    recover_crashed_jobs,
    register_mock_feed,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.storage import db_helper
from app.utils.errors import ValidationError
from app.utils.logger import logger


@pytest.fixture(autouse=True)
def cleanup_database() -> None:
    """Clean data_jobs and feed_state tables before/after each test."""
    try:
        with db_helper.get_connection() as conn:
            conn.execute("DELETE FROM data_jobs;")
            conn.execute("DELETE FROM feed_state;")
    except sqlite3.Error as e:
        logger.warning("Database cleanup failed: {}", e)


def test_real_time_feed_overflow_policies() -> None:
    """Verify overflow handler actions under different policies."""
    feed_id = "test_feed_id"
    register_mock_feed(feed_id, "mt5", "EURUSD", "ticks")

    # Halt policy should fail/halt feed
    res = handle_feed_overflow(feed_id, "halt")
    assert res["state"] == "failed"

    # drop_and_reconcile should increment dropped/gap counts
    # and move state to reconciling
    res = handle_feed_overflow(feed_id, "drop_and_reconcile")
    assert res["state"] == "reconciling"
    assert res["dropped_count"] == 1
    assert res["gap_count"] == 1

    # backpressure policy keeps connected
    res = handle_feed_overflow(feed_id, "backpressure")
    assert res["state"] == "connected"


def test_get_feed_status_observability() -> None:
    """Test get_feed_status tool lookup."""
    feed_id = "feed_obs_id"
    register_mock_feed(feed_id, "ctrader", "GBPUSD", "bars")

    res = get_feed_status(feed_id=feed_id)
    assert isinstance(res, dict)
    assert res["feed_id"] == feed_id
    assert res["source"] == "ctrader"


def test_scheduler_jobs_lifecycle() -> None:
    """Test scheduler job creation, deduplication, start, stop, status."""
    job_name = "EURUSD_M5_Ingestion"

    # Create job
    res = create_data_update_job(
        name=job_name,
        source="csv",
        symbols=["EURUSD"],
        timeframes=["M5"],
        data_kind="bars",
        storage_format="csv",
        storage_path="data/raw",
        schedule="* * * * *",
    )
    assert res["name"] == job_name
    assert res["state"] == "created"

    # Attempt duplicate creation should fail
    with pytest.raises(ValidationError):
        create_data_update_job(
            name=job_name,
            source="csv",
            symbols=["EURUSD"],
            timeframes=["M5"],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )

    # Start job
    start_res = start_data_update_job(job_name)
    assert start_res["state"] == "running"

    # Check status
    status_res = get_data_update_job_status(job_name)
    assert status_res["state"] == "running"

    # Stop job
    stop_res = stop_data_update_job(job_name)
    assert stop_res["state"] == "stopped"


def test_run_job_once_behavior() -> None:
    """Verify run-once does not schedule background loop but executes immediately."""
    job_name = "Run_Once_Job"
    create_data_update_job(
        name=job_name,
        source="synthetic",
        symbols=["GBPUSD"],
        timeframes=["M15"],
        data_kind="bars",
        storage_format="parquet",
        storage_path="data/processed",
        schedule=None,  # No schedule
    )

    # Start recurring should fail due to no schedule
    with pytest.raises(ValidationError):
        start_data_update_job(job_name)

    # Run once
    run_res = run_data_update_job_once(job_name)
    assert run_res["state"] == "running"


def test_crash_recovery_sequence() -> None:
    """Verify crashed job (running in DB) recovers to 'recovering' state."""
    job_name = "Crashed_Job"
    create_data_update_job(
        name=job_name,
        source="csv",
        symbols=["EURUSD"],
        timeframes=["M1"],
        data_kind="bars",
        storage_format="csv",
        storage_path="data/raw",
        schedule="* * * * *",
    )

    # Force database state to running
    with db_helper.get_connection() as conn:
        conn.execute(
            "UPDATE data_jobs SET state = 'running' WHERE name = ?;", (job_name,)
        )

    # Trigger recovery
    recovered = recover_crashed_jobs()
    assert recovered >= 1

    # Check state
    status = get_data_update_job_status(job_name)
    assert status["state"] == "recovering"
    assert status["last_error"] == "SYSTEM_CRASH_DETECTION"


def test_validate_job_creation_args_errors() -> None:
    # Empty name
    with pytest.raises(ValidationError, match="name cannot be empty"):
        create_data_update_job(
            name="",
            source="csv",
            symbols=["EURUSD"],
            timeframes=["M5"],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )

    # Empty source
    with pytest.raises(ValidationError, match="Source identifier"):
        create_data_update_job(
            name="Job1",
            source="",
            symbols=["EURUSD"],
            timeframes=["M5"],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )

    # Empty symbols
    with pytest.raises(ValidationError, match="Symbols list"):
        create_data_update_job(
            name="Job1",
            source="csv",
            symbols=[],
            timeframes=["M5"],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )

    # Empty timeframes
    with pytest.raises(ValidationError, match="Timeframes list"):
        create_data_update_job(
            name="Job1",
            source="csv",
            symbols=["EURUSD"],
            timeframes=[],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )

    # Limit symbols exceeded
    with pytest.raises(ValidationError, match="Max symbols"):
        create_data_update_job(
            name="Job1",
            source="csv",
            symbols=["S" + str(i) for i in range(505)],
            timeframes=["M5"],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )


def test_start_stop_job_errors() -> None:
    # Start non-existent job
    with pytest.raises(ValidationError, match=r"Job.*not found"):
        start_data_update_job("NonExistentJob")

    # Stop non-existent job
    with pytest.raises(ValidationError, match=r"Job.*not found"):
        stop_data_update_job("NonExistentJob")

    # Get status of non-existent job
    with pytest.raises(ValidationError, match=r"Job.*not found"):
        get_data_update_job_status("NonExistentJob")

    # Create and start a job, then start it again (already running)
    job_name = "DoubleStartJob"
    create_data_update_job(
        name=job_name,
        source="csv",
        symbols=["EURUSD"],
        timeframes=["M5"],
        data_kind="bars",
        storage_format="csv",
        storage_path="data/raw",
        schedule="* * * * *",
    )
    res_start1 = start_data_update_job(job_name)
    assert res_start1["state"] == "running"
    res_start2 = start_data_update_job(job_name)
    assert res_start2["state"] == "running"

    # Stop stopped job
    res_stop1 = stop_data_update_job(job_name)
    assert res_stop1["state"] == "stopped"
    res_stop2 = stop_data_update_job(job_name)
    assert res_stop2["state"] == "stopped"


def test_feed_status_errors() -> None:
    # Feed not found
    with pytest.raises(ValidationError, match="No matching real-time feeds found"):
        get_feed_status("NonExistentFeed")

    # Handle overflow for non-existent feed
    with pytest.raises(ValidationError, match=r"Feed.*not found"):
        handle_feed_overflow("NonExistentFeed", "halt")


def test_async_job_execution_loops() -> None:
    import asyncio
    from unittest.mock import MagicMock, patch

    from app.services.data.scheduler import (
        _execute_single_run,
        _run_job_loop,
        create_data_update_job,
        start_data_update_job,
        stop_data_update_job,
    )

    async def run_test() -> None:
        job_name = "Async_Loop_Job"
        create_data_update_job(
            name=job_name,
            source="csv",
            symbols=["EURUSD"],
            timeframes=["M5"],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )

        # 1. Test execute single run success
        await _execute_single_run(job_name)

        # 2. Test execute single run database error path
        with patch("app.services.data.storage.db_helper.get_connection") as mock_conn:
            mock_conn.side_effect = [RuntimeError("DB Fail"), MagicMock()]
            await _execute_single_run(job_name)  # Should catch exception and log it

        # 3. Test run_job_loop disabled break path
        # Set job state to disabled (not enabled)
        stop_data_update_job(job_name)
        await _run_job_loop(job_name)  # Should read db, see disabled, and break immediately

        # 4. Test run_job_loop CancelledError path
        # We will patch sleep to raise CancelledError
        start_data_update_job(job_name)
        with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
            await _run_job_loop(job_name)  # Should log cancellation and break

        # 5. Test run_job_loop database exception path
        # Patch db_helper to raise exception on first call, then patch sleep to raise CancelledError
        # so it breaks out of the infinite loop
        with patch("app.services.data.storage.db_helper.get_connection", side_effect=RuntimeError("DB Fail")):
            with patch("asyncio.sleep", side_effect=[None, asyncio.CancelledError]):
                try:
                    await _run_job_loop(job_name)
                except asyncio.CancelledError:
                    pass

    asyncio.run(run_test())
