"""Unit tests for app/services/data/data_jobs/job.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from app.services.data.contracts import DataError
from app.services.data.data_jobs.contracts import (
    JobDefinition,
    JobStatusRequest,
    ScheduleJobRequest,
)
from app.services.data.data_jobs.job import (
    _acquire_job_run_lease,
    _get_active_lease_state,
    _handle_create,
    _handle_start,
    _handle_stop,
    _stop_background_loop,
    create_data_update_job,
    get_data_update_job_status,
    read_update_job_status,
    run_data_update_job_once,
    schedule_update_job,
    start_data_update_job,
    stop_data_update_job,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def _make_definition(job_id: str = "job1", **kwargs) -> JobDefinition:
    defaults = {
        "job_id": job_id,
        "source_id": "mt5",
        "symbols": ("EURUSD",),
        "timeframes": ("M1",),
        "data_kinds": ("ohlcv",),
        "start": _NOW,
        "end": _NOW + timedelta(days=1),
        "enabled": True,
        "created_at": _NOW,
        "request_id": _REQ_ID,
    }
    defaults.update(kwargs)
    return JobDefinition(**defaults)


def test_get_active_lease_state() -> None:
    """Test _get_active_lease_state calculation."""
    assert _get_active_lease_state(None, _NOW) == "none"
    future_iso = datetime(2030, 1, 1, tzinfo=UTC).isoformat()
    past_iso = datetime(2020, 1, 1, tzinfo=UTC).isoformat()
    assert _get_active_lease_state(future_iso, _NOW) == "held"
    assert _get_active_lease_state(past_iso, _NOW) == "expired"


def test_handle_create_limits_exceeded() -> None:
    """Test _handle_create raises LIMIT_EXCEEDED for excess symbols or timeframes."""
    # Excess symbols > 500
    defl_symbols = _make_definition(
        "job1", symbols=tuple(f"SYM_{i}" for i in range(501))
    )
    req1 = ScheduleJobRequest(
        action="create",
        job_id="job1",
        definition=defl_symbols,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        _handle_create(req1)
    assert exc_info.value.code == "LIMIT_EXCEEDED"

    # Excess timeframes > 20
    defl_tf = _make_definition("job2", timeframes=tuple(f"TF_{i}" for i in range(21)))
    req2 = ScheduleJobRequest(
        action="create",
        job_id="job2",
        definition=defl_tf,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        _handle_create(req2)
    assert exc_info.value.code == "LIMIT_EXCEEDED"

    # Low interval < 60
    defl_interval = _make_definition("job3", interval_seconds=10)
    req3 = ScheduleJobRequest(
        action="create",
        job_id="job3",
        definition=defl_interval,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        _handle_create(req3)
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_handle_start_job_not_found() -> None:
    """Test _handle_start raises JOB_NOT_FOUND for non-existent job."""
    req = ScheduleJobRequest(
        action="start",
        job_id="nonexistent_job_123",
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        _handle_start(req)
    assert exc_info.value.code == "JOB_NOT_FOUND"


def test_handle_stop_job_not_found() -> None:
    """Test _handle_stop raises JOB_NOT_FOUND for non-existent job."""
    req = ScheduleJobRequest(
        action="stop",
        job_id="nonexistent_job_123",
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        _handle_stop(req)
    assert exc_info.value.code == "JOB_NOT_FOUND"


def test_acquire_job_run_lease_checks() -> None:
    """Test _acquire_job_run_lease checks for disabled job and concurrent lock."""
    # Disabled job -> POLICY_BLOCKED
    res_disabled = MagicMock()
    res_disabled.rows = [{"enabled": 0}]

    with patch(
        "app.services.data.data_jobs.job._execute_transaction_raw",
        return_value=res_disabled,
    ):
        with pytest.raises(DataError) as exc_info:
            _acquire_job_run_lease("job1", _NOW, _REQ_ID)
        assert exc_info.value.code == "POLICY_BLOCKED"

    # Running and lease held -> CONCURRENT_WRITE_LOCKED
    res_running = MagicMock()
    future_iso = datetime(2030, 1, 1, tzinfo=UTC).isoformat()
    res_running.rows = [
        {
            "enabled": 1,
            "state": "running",
            "lease_expires_at": future_iso,
        }
    ]

    with patch(
        "app.services.data.data_jobs.job._execute_transaction_raw",
        return_value=res_running,
    ):
        with pytest.raises(DataError) as exc_info:
            _acquire_job_run_lease("job1", _NOW, _REQ_ID)
        assert exc_info.value.code == "CONCURRENT_WRITE_LOCKED"


def test_read_update_job_status_nonexistent() -> None:
    """Test read_update_job_status raises JOB_NOT_FOUND for non-existent job."""
    req = JobStatusRequest(job_id="nonexistent_job_123", request_id=_REQ_ID)
    with pytest.raises(DataError) as exc_info:
        read_update_job_status(req)
    assert exc_info.value.code == "JOB_NOT_FOUND"


def test_schedule_update_job_actions() -> None:
    """Test schedule_update_job router dispatch."""
    mock_status = MagicMock()

    with (
        patch("app.services.data.data_jobs.job._handle_create") as mock_c,
        patch("app.services.data.data_jobs.job._handle_start") as mock_s,
        patch("app.services.data.data_jobs.job._handle_stop") as mock_st,
        patch("app.services.data.data_jobs.job.run_data_update_job_once") as mock_r,
        patch(
            "app.services.data.data_jobs.job.read_update_job_status",
            return_value=mock_status,
        ),
    ):
        defl = _make_definition("job1")

        req_create = ScheduleJobRequest(
            action="create", job_id="job1", definition=defl, request_id=_REQ_ID
        )
        assert schedule_update_job(req_create) == mock_status
        mock_c.assert_called_once()

        req_start = ScheduleJobRequest(
            action="start", job_id="job1", request_id=_REQ_ID
        )
        assert schedule_update_job(req_start) == mock_status
        mock_s.assert_called_once()

        req_stop = ScheduleJobRequest(action="stop", job_id="job1", request_id=_REQ_ID)
        assert schedule_update_job(req_stop) == mock_status
        mock_st.assert_called_once()

        req_run = ScheduleJobRequest(
            action="run_once", job_id="job1", request_id=_REQ_ID
        )
        assert schedule_update_job(req_run) == mock_status
        mock_r.assert_called_once()


def test_run_data_update_job_once_nonexistent() -> None:
    """Test run_data_update_job_once returns state='failed' for non-existent job."""
    res = run_data_update_job_once("nonexistent_job_123", _REQ_ID)
    assert res.state == "failed"
    assert res.error_code == "JOB_NOT_FOUND"


def test_stop_background_loop_task() -> None:
    """Test _stop_background_loop cancels running task if present."""
    mock_task = MagicMock()
    with patch(
        "app.services.data.data_jobs.job._BACKGROUND_TASKS", {"job1": mock_task}
    ):
        _stop_background_loop("job1")
        mock_task.cancel.assert_called_once()


def test_public_convenience_functions() -> None:
    """Test public convenience functions delegate properly."""
    mock_status = MagicMock()
    defl = _make_definition("job1")
    req_status = JobStatusRequest(job_id="job1", request_id=_REQ_ID)

    with (
        patch(
            "app.services.data.data_jobs.job.schedule_update_job",
            return_value=mock_status,
        ),
        patch(
            "app.services.data.data_jobs.job.read_update_job_status",
            return_value=mock_status,
        ),
    ):
        assert create_data_update_job(defl, _REQ_ID) == mock_status
        assert start_data_update_job("job1", _REQ_ID) == mock_status
        assert stop_data_update_job("job1", _REQ_ID) == mock_status
        assert get_data_update_job_status(req_status) == mock_status
