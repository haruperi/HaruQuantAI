"""Unit tests for job scheduling, status monitoring, and run-once execution."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.services.data.contracts import (
    JobDefinition,
    JobStatusRequest,
    ScheduleJobRequest,
)
from app.services.data.contracts.errors import DataError
from app.services.data.jobs.scheduler import (
    read_update_job_status,
    run_data_update_job_once,
    schedule_update_job,
)
from app.services.data.storage.migrations import run_data_migrations


@pytest.fixture
def test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Setup test environment variables and database tables."""
    db_path = tmp_path / "data_jobs.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.name}")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )
    return tmp_path


def test_scheduler_enforces_symbol_and_timeframe_limits(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test scheduler creation action rejects configuration exceeding safety limits."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    # 1. Exceed symbols limit
    def_too_many_symbols = JobDefinition(
        job_id="job-1",
        source_id="test",
        symbols=tuple(f"S{i}" for i in range(505)),  # Max is 500
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=300,
        enabled=True,
        created_at=t,
        request_id="req-8fa9722abd39e4a315591d98a4124e3cf2feab1dc0720b274edfc9fdbd1a89ca",
    )
    req1 = ScheduleJobRequest(
        action="create",
        job_id="job-1",
        definition=def_too_many_symbols,
        request_id="req-8fa9722abd39e4a315591d98a4124e3cf2feab1dc0720b274edfc9fdbd1a89ca",
    )

    with pytest.raises(DataError) as exc_info:
        schedule_update_job(req1)
    assert exc_info.value.args[0] == "LIMIT_EXCEEDED"

    # 2. Exceed timeframes limit
    def_too_many_tfs = JobDefinition(
        job_id="job-2",
        source_id="test",
        symbols=("BTC/USD",),
        timeframes=tuple(f"M{i}" for i in range(25)),  # Max is 20
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=300,
        enabled=True,
        created_at=t,
        request_id="req-db56c680103b26550ae84b160ebc634d5a8909e74a7cdec0bc7e40f6736de842",
    )
    req2 = ScheduleJobRequest(
        action="create",
        job_id="job-2",
        definition=def_too_many_tfs,
        request_id="req-db56c680103b26550ae84b160ebc634d5a8909e74a7cdec0bc7e40f6736de842",
    )

    with pytest.raises(DataError) as exc_info:
        schedule_update_job(req2)
    assert exc_info.value.args[0] == "LIMIT_EXCEEDED"


def test_scheduler_cannot_report_false_success(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify state transitions and run_once execution returns valid run results."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    from decimal import Decimal

    from app.services.data.contracts import DataQualityReport, MarketDataset
    from app.services.data.contracts.records import OHLCVRecord

    mock_records = (
        OHLCVRecord(
            timestamp=t,
            source="test-src",
            source_symbol="BTC/USD",
            source_revision="v1",
            available_at=t,
            open=Decimal("100.0"),
            high=Decimal("101.0"),
            low=Decimal("99.0"),
            close=Decimal("100.5"),
            volume=Decimal("10.0"),
            price_unit="USD",
            volume_unit="Units",
        ),
    )
    mock_dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="BTC/USD",
        timeframe="M5",
        records=mock_records,
        start=t,
        end=t,
        available_at=t,
        record_count=1,
        quality_report=DataQualityReport(
            quality_status="passed",
            quality_score=Decimal("1.0"),
            issues=(),
            warnings=(),
            record_count=1,
            checked_count=1,
            truncated=False,
            sample_limit=1000,
            schema_version="v1",
            generated_at=t,
        ),
        source_metadata={},
        license_metadata={},
        cache_status="miss",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-72ce963e0c5f7c540ff7d0ed2fc7739dc72e59fa5d58fcaa880d430989932a21",
    )

    monkeypatch.setattr(
        "app.services.data.jobs.scheduler.evaluate_source_policy",
        lambda _: None,
    )
    monkeypatch.setattr(
        "app.services.data.jobs.backfill.fetch_market_dataset",
        lambda _: mock_dataset,
    )
    # Create valid job definition
    job_def = JobDefinition(
        job_id="job-ok",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        end=t + timedelta(days=1),
        interval_seconds=300,
        enabled=True,
        created_at=t,
        request_id="req-87aadafd7cdbc6230b952fd2aa55d4e3cdf875d7063c59efda305f83034a85aa",
    )

    schedule_update_job(
        ScheduleJobRequest(
            action="create",
            job_id="job-ok",
            definition=job_def,
            request_id="req-87aadafd7cdbc6230b952fd2aa55d4e3cdf875d7063c59efda305f83034a85aa",
        )
    )

    # Run job once
    run_result = run_data_update_job_once(
        "job-ok", "req-72ce963e0c5f7c540ff7d0ed2fc7739dc72e59fa5d58fcaa880d430989932a21"
    )
    assert run_result.state == "succeeded"
    assert run_result.committed_chunks == 1
    assert run_result.record_count == 1
    assert run_result.last_checkpoint is not None

    # Verify status reflects successful run
    status = read_update_job_status(
        JobStatusRequest(
            job_id="job-ok",
            request_id="req-245109e726fe1df9efbeb3d8421b995ae50c728ad1a2956533b0722748f63e4e",
        )
    )
    assert status.last_run_status == "succeeded"
    assert status.last_checkpoint == run_result.last_checkpoint
    assert status.state == "stopped"  # Lease released, loops complete


def test_scheduler_stop_cancels_asyncio_task(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test starting and stopping a job spawns and cancels asyncio tasks correctly."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    class MockLoop:
        def create_task(self, coroutine: object) -> object:
            coroutine.close()  # type: ignore[attr-defined]

            class MockTask:
                def __init__(self) -> None:
                    self._cancelled = False

                def cancel(self) -> None:
                    self._cancelled = True

                def done(self) -> bool:
                    return self._cancelled

                def cancelled(self) -> bool:
                    return self._cancelled

            return MockTask()

    loop_inst = MockLoop()
    monkeypatch.setattr("asyncio.get_running_loop", lambda: loop_inst)

    monkeypatch.setattr(
        "app.services.data.jobs.scheduler.evaluate_source_policy",
        lambda _: None,
    )

    job_def = JobDefinition(
        job_id="job-loop",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=300,
        enabled=True,
        created_at=t,
        request_id="req-230623360ecc365490ebe78b3af42ce1cebee593d19bc17d851703432cf32a87",
    )

    schedule_update_job(
        ScheduleJobRequest(
            action="create",
            job_id="job-loop",
            definition=job_def,
            request_id="req-230623360ecc365490ebe78b3af42ce1cebee593d19bc17d851703432cf32a87",
        )
    )

    # Starting job should start background task
    from app.services.data.jobs.scheduler import _BACKGROUND_TASKS

    assert "job-loop" in _BACKGROUND_TASKS
    task = _BACKGROUND_TASKS["job-loop"]
    assert not task.done()

    # Stopping job should cancel the task
    schedule_update_job(
        ScheduleJobRequest(
            action="stop",
            job_id="job-loop",
            request_id="req-0b1a44b1fb99c51634214e5c6dc0516d9c8902a6350f30f1909203754f1d2adf",
        )
    )
    assert "job-loop" not in _BACKGROUND_TASKS
    assert task.cancelled() or task.done()


def test_scheduler_start_action(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test starting a job updates database state and spawns loops."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.data.jobs.scheduler.evaluate_source_policy",
        lambda _: None,
    )

    job_def = JobDefinition(
        job_id="job-start",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=300,
        enabled=False,  # Create as disabled
        created_at=t,
        request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
    )

    schedule_update_job(
        ScheduleJobRequest(
            action="create",
            job_id="job-start",
            definition=job_def,
            request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
        )
    )

    # Verify initially disabled
    status = read_update_job_status(
        JobStatusRequest(
            job_id="job-start",
            request_id="req-39898485fdc3ff92c82d38bba7db1347db4de1368eacc4bbde61a6212e9b5c15",
        )
    )
    assert status.enabled is False

    # Start loop mock
    class MockLoop:
        def create_task(self, coroutine: object) -> object:
            coroutine.close()  # type: ignore[attr-defined]

            class DummyTask:
                def done(self) -> bool:
                    return False

            return DummyTask()

    monkeypatch.setattr("asyncio.get_running_loop", MockLoop)

    # Start the job
    schedule_update_job(
        ScheduleJobRequest(
            action="start",
            job_id="job-start",
            request_id="req-47206a85555eb95c4f849dd5f3f619f02f8b3c2809770d749c0e562cd21eefc1",
        )
    )

    status_started = read_update_job_status(
        JobStatusRequest(
            job_id="job-start",
            request_id="req-c110a6b5b5d0f20fc87cf8cdbcb53d48bfe206e4883b4a1be227851e41d3d024",
        )
    )
    assert status_started.enabled is True


def test_scheduler_errors_job_not_found(test_env: Path) -> None:
    """Test scheduler actions raise JOB_NOT_FOUND when job does not exist."""
    req = ScheduleJobRequest(
        action="start",
        job_id="non-existent",
        request_id="req-e0a1e59a78e583e7ca175cd08aaa8aef9033a0958471840a58f8e5f0f3321471",
    )
    with pytest.raises(DataError) as exc:
        schedule_update_job(req)
    assert exc.value.args[0] == "JOB_NOT_FOUND"

    with pytest.raises(DataError) as exc:
        schedule_update_job(
            ScheduleJobRequest(
                action="stop",
                job_id="non-existent",
                request_id="req-e0a1e59a78e583e7ca175cd08aaa8aef9033a0958471840a58f8e5f0f3321471",
            )
        )
    assert exc.value.args[0] == "JOB_NOT_FOUND"

    with pytest.raises(DataError) as exc:
        read_update_job_status(
            JobStatusRequest(
                job_id="non-existent",
                request_id="req-e0a1e59a78e583e7ca175cd08aaa8aef9033a0958471840a58f8e5f0f3321471",
            )
        )
    assert exc.value.args[0] == "JOB_NOT_FOUND"

    res = run_data_update_job_once(
        "non-existent",
        "req-e0a1e59a78e583e7ca175cd08aaa8aef9033a0958471840a58f8e5f0f3321471",
    )
    assert res.state == "failed"
    assert res.error_code == "JOB_NOT_FOUND"


def test_scheduler_run_once_fails(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test job run once transitions to failed state on execution errors."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.data.jobs.scheduler.evaluate_source_policy",
        lambda _: None,
    )

    # Mock fetch_market_dataset to raise error
    def _mock_fail(_: object) -> None:
        raise DataError("DATA_QUALITY_FAILED")

    monkeypatch.setattr(
        "app.services.data.jobs.backfill.fetch_market_dataset",
        _mock_fail,
    )

    job_def = JobDefinition(
        job_id="job-fail",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        end=t + timedelta(days=1),
        interval_seconds=300,
        enabled=True,
        created_at=t,
        request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
    )

    schedule_update_job(
        ScheduleJobRequest(
            action="create",
            job_id="job-fail",
            definition=job_def,
            request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
        )
    )

    res = run_data_update_job_once(
        "job-fail",
        "req-158bd48fae5d15f2cd880b351e4bb27c7e65d5167ef52a2e88788c316711f8cc",
    )
    assert res.state == "failed"

    status = read_update_job_status(
        JobStatusRequest(
            job_id="job-fail",
            request_id="req-f09e27992d5a69d28ab251d5d941310d46e61e94d556bbb7cd32198ec03aa605",
        )
    )
    assert status.last_run_status == "failed"


def test_scheduler_create_action_fails_if_already_exists(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test job creation fails if the job ID is already registered."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.data.jobs.scheduler.evaluate_source_policy",
        lambda _: None,
    )

    job_def = JobDefinition(
        job_id="job-dup",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=300,
        enabled=True,
        created_at=t,
        request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
    )

    schedule_update_job(
        ScheduleJobRequest(
            action="create",
            job_id="job-dup",
            definition=job_def,
            request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
        )
    )

    with pytest.raises(DataError) as exc:
        schedule_update_job(
            ScheduleJobRequest(
                action="create",
                job_id="job-dup",
                definition=job_def,
                request_id="req-327703761b49b6bd7b02ef9e24160fb5db57be87c6c0b6e1e967f1cf7f5ea3c7",
            )
        )
    assert exc.value.args[0] == "VALIDATION_FAILED"


def test_scheduler_create_action_invalid_interval(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test job creation fails if interval is below the minimum allowed."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    job_def = JobDefinition(
        job_id="job-invalid-int",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=30,  # Below min (60)
        enabled=True,
        created_at=t,
        request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
    )

    with pytest.raises(DataError) as exc:
        schedule_update_job(
            ScheduleJobRequest(
                action="create",
                job_id="job-invalid-int",
                definition=job_def,
                request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
            )
        )
    assert exc.value.args[0] == "VALIDATION_FAILED"


def test_scheduler_run_disabled_job_fails(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test run once fails if the job is disabled."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.data.jobs.scheduler.evaluate_source_policy",
        lambda _: None,
    )

    job_def = JobDefinition(
        job_id="job-disabled",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=300,
        enabled=False,
        created_at=t,
        request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
    )

    schedule_update_job(
        ScheduleJobRequest(
            action="create",
            job_id="job-disabled",
            definition=job_def,
            request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
        )
    )

    res = run_data_update_job_once(
        "job-disabled",
        "req-158bd48fae5d15f2cd880b351e4bb27c7e65d5167ef52a2e88788c316711f8cc",
    )
    assert res.state == "failed"
    assert res.error_code == "POLICY_BLOCKED"


def test_scheduler_lease_locked_start(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test starting a job fails if another request holds an active lease."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.data.jobs.scheduler.evaluate_source_policy",
        lambda _: None,
    )

    job_def = JobDefinition(
        job_id="job-locked",
        source_id="test-src",
        symbols=("BTC/USD",),
        timeframes=("M5",),
        data_kinds=("ohlcv",),
        start=t,
        interval_seconds=300,
        enabled=True,
        created_at=t,
        request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
    )

    schedule_update_job(
        ScheduleJobRequest(
            action="create",
            job_id="job-locked",
            definition=job_def,
            request_id="req-f15bd4bb7192a990d1b91a9c7ba695dfe23ed30c828832897b2f3267938e1947",
        )
    )

    # Lock lease
    expires = (
        (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    )
    update_sql = (
        "UPDATE data_update_jobs "
        "SET state = 'running', lease_owner = 'other-owner', lease_expires_at = ? "
        "WHERE job_id = 'job-locked'"
    )
    from app.services.data.contracts import StatementPlan, TransactionRequest
    from app.services.data.storage.database import execute_transaction

    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(update_sql,),
                parameter_sets=((expires,),),
                max_rows=1,
            ),
            request_id="req-260d767de86bce74ab18edef881e84c4a1ddbfba4294f098b4f8f726682cb637",
        )
    )

    with pytest.raises(DataError) as exc:
        schedule_update_job(
            ScheduleJobRequest(
                action="start",
                job_id="job-locked",
                request_id="req-47206a85555eb95c4f849dd5f3f619f02f8b3c2809770d749c0e562cd21eefc1",
            )
        )
    assert exc.value.args[0] == "CONCURRENT_WRITE_LOCKED"
