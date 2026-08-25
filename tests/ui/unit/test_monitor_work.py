"""Unit tests for FEAT-UI-MONITOR_WORK presentation logic.

Covers FR-UI-TRACK_PROGRESS, FR-UI-STREAM_ACTIVITY, and FR-UI-PRESENT_FAILURES
against the ratified ``ui.monitor-work@1`` presentation port in ``app/contracts/ui``.
"""

from collections.abc import AsyncIterator
from typing import override

import pytest
from pydantic import ValidationError

from app.contracts.common.events import DomainEvent
from app.contracts.common.models import ProblemDetails
from app.contracts.ui.errors import UiFailure
from app.contracts.ui.models import (
    ErrorPresentationWire,
    MonitorWorkPresentationEventSubscription,
    MonitorWorkPresentationRequest,
    MonitorWorkPresentationSuccess,
    ProgressPresentationWire,
)
from app.contracts.ui.ports import MonitorWorkPresentationCapability

_REQUEST_ID = "018f9a2b-7c1d-7abc-9def-0123456789a1"
_SNAPSHOT_ID = "018f9a2b-7c1d-7abc-9def-0123456789a2"
_TASK_ID = "018f9a2b-7c1d-7abc-9def-0123456789a3"
_JOB_ID = "018f9a2b-7c1d-7abc-9def-0123456789a4"


class MonitorWorkPresentationService(MonitorWorkPresentationCapability):
    """Implementation of the monitor-work presentation port (test evidence)."""

    def __init__(self, *, is_available: bool = True) -> None:
        """Initialize with predefined progress, errors, and event log."""
        self._is_available = is_available
        self._events: list[DomainEvent] = [
            DomainEvent(
                event_id="018f9a2b-7c1d-7abc-9def-0123456789e1",
                sequence=1,
                event_type="JOB_QUEUED",
                occurred_at="2026-08-26T00:00:01.000000Z",
                request_id=_REQUEST_ID,
                capability_snapshot_id=_SNAPSHOT_ID,
                job_id=_JOB_ID,
                payload={"stage": "queue"},
            ),
            DomainEvent(
                event_id="018f9a2b-7c1d-7abc-9def-0123456789e2",
                sequence=2,
                event_type="JOB_STARTED",
                occurred_at="2026-08-26T00:00:02.000000Z",
                request_id=_REQUEST_ID,
                capability_snapshot_id=_SNAPSHOT_ID,
                job_id=_JOB_ID,
                payload={"stage": "init"},
            ),
            DomainEvent(
                event_id="018f9a2b-7c1d-7abc-9def-0123456789e3",
                sequence=3,
                event_type="STAGE_PROGRESS",
                occurred_at="2026-08-26T00:00:03.000000Z",
                request_id=_REQUEST_ID,
                capability_snapshot_id=_SNAPSHOT_ID,
                job_id=_JOB_ID,
                payload={"stage": "simulation", "percent": "50"},
            ),
            DomainEvent(
                event_id="018f9a2b-7c1d-7abc-9def-0123456789e4",
                sequence=4,
                event_type="STAGE_COMPLETED",
                occurred_at="2026-08-26T00:00:04.000000Z",
                request_id=_REQUEST_ID,
                capability_snapshot_id=_SNAPSHOT_ID,
                job_id=_JOB_ID,
                payload={"stage": "simulation"},
            ),
        ]

    @override
    async def monitor_work(
        self,
        request: MonitorWorkPresentationRequest,
    ) -> MonitorWorkPresentationSuccess | UiFailure:
        """Track progress, control jobs, present failures, and notify."""
        if not self._is_available:
            return UiFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:haruquantai:ui:monitor-unavailable",
                    title="Monitor Unavailable",
                    status=503,
                    code="UI_MONITOR_UNAVAILABLE",
                    detail="Work monitoring service is temporarily unavailable.",
                    request_id=request.request_id,
                ),
            )
        if request.operation == "TRACK":
            return MonitorWorkPresentationSuccess(
                request_id=request.request_id,
                progress=ProgressPresentationWire(
                    task_id=_TASK_ID,
                    stage_name="Running Simulation",
                    progress_percent="75.5",
                    is_indeterminate=False,
                    message="Processing bars 755/1000",
                ),
            )
        if request.operation == "PRESENT_FAILURES":
            return MonitorWorkPresentationSuccess(
                request_id=request.request_id,
                error=ErrorPresentationWire(
                    error_code="ERR_JOB_EXECUTION_TIMEOUT",
                    title="Simulation Timeout",
                    detail="Simulation exceeded allocated run budget of 120s.",
                    causal_reference="job-exec-timeout-902",
                    is_retryable=True,
                    suggested_action="Increase execution budget and retry the job.",
                ),
            )
        # CONTROL and NOTIFY are Stage 14.10 mock-build lines
        return MonitorWorkPresentationSuccess(request_id=request.request_id)

    @override
    async def subscribe_monitor_work_events(
        self,
        request: MonitorWorkPresentationEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver work monitoring events as domain events with replay/resync."""
        start_index = 0
        if request.resume_event_id is not None:
            # Find the resume event and start after it
            for idx, event in enumerate(self._events):
                if event.event_id == request.resume_event_id:
                    start_index = idx + 1
                    break

        slice_events = self._events[start_index:]
        if request.replay_limit > 0:
            slice_events = slice_events[: request.replay_limit]

        for event in slice_events:
            yield event


@pytest.mark.asyncio
async def test_track_progress_returns_bounded_progress() -> None:
    """FR-UI-TRACK_PROGRESS: Show bounded progress without fabricating precision."""
    service = MonitorWorkPresentationService()
    req = MonitorWorkPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="TRACK",
    )
    result = await service.monitor_work(req)
    assert isinstance(result, MonitorWorkPresentationSuccess)
    assert result.progress is not None
    assert result.progress.task_id == _TASK_ID
    assert result.progress.stage_name == "Running Simulation"
    assert result.progress.progress_percent == "75.5"
    assert result.progress.is_indeterminate is False
    assert result.progress.message == "Processing bars 755/1000"


@pytest.mark.asyncio
async def test_track_progress_indeterminate_discrimination() -> None:
    """FR-UI-TRACK_PROGRESS: Indeterminate work is labeled indeterminate (R15)."""
    indeterminate_progress = ProgressPresentationWire(
        task_id=_TASK_ID,
        stage_name="Discovering Feeds",
        progress_percent=None,
        is_indeterminate=True,
        message="Connecting to market data feed...",
    )
    assert indeterminate_progress.is_indeterminate is True
    assert indeterminate_progress.progress_percent is None

    # Percent must be within [0, 100] when provided
    with pytest.raises(ValidationError):
        ProgressPresentationWire(
            task_id=_TASK_ID,
            stage_name="Invalid Range",
            progress_percent="105",
        )

    with pytest.raises(ValidationError):
        ProgressPresentationWire(
            task_id=_TASK_ID,
            stage_name="Negative Range",
            progress_percent="-5",
        )


@pytest.mark.asyncio
async def test_present_failures_structured_error() -> None:
    """FR-UI-PRESENT_FAILURES: Present structured failures with retryability (R16)."""
    service = MonitorWorkPresentationService()
    req = MonitorWorkPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="PRESENT_FAILURES",
    )
    result = await service.monitor_work(req)
    assert isinstance(result, MonitorWorkPresentationSuccess)
    assert result.error is not None
    assert result.error.error_code == "ERR_JOB_EXECUTION_TIMEOUT"
    assert result.error.title == "Simulation Timeout"
    assert result.error.detail == "Simulation exceeded allocated run budget of 120s."
    assert result.error.causal_reference == "job-exec-timeout-902"
    assert result.error.is_retryable is True
    assert (
        result.error.suggested_action == "Increase execution budget and retry the job."
    )


@pytest.mark.asyncio
async def test_monitor_work_failure_response() -> None:
    """Service returns structured UiFailure when unavailable."""
    service = MonitorWorkPresentationService(is_available=False)
    req = MonitorWorkPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="TRACK",
    )
    result = await service.monitor_work(req)
    assert isinstance(result, UiFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"
    assert result.problem.status == 503


@pytest.mark.asyncio
async def test_stream_activity_subscription_ordered_and_bounded() -> None:
    """FR-UI-STREAM_ACTIVITY: Deliver ordered events with replay limit and resume cursor."""
    service = MonitorWorkPresentationService()

    # Full subscription with bounded replay limit
    sub = MonitorWorkPresentationEventSubscription(
        job_id=_JOB_ID,
        replay_limit=2,
    )
    events: list[DomainEvent] = []
    async for event in service.subscribe_monitor_work_events(sub):
        events.append(event)

    assert len(events) == 2
    assert events[0].sequence == 1
    assert events[0].event_type == "JOB_QUEUED"
    assert events[1].sequence == 2
    assert events[1].event_type == "JOB_STARTED"

    # Resume subscription starting after sequence 2 (event 2)
    resume_sub = MonitorWorkPresentationEventSubscription(
        job_id=_JOB_ID,
        resume_event_id="018f9a2b-7c1d-7abc-9def-0123456789e2",
        replay_limit=10,
    )
    resumed_events: list[DomainEvent] = []
    async for event in service.subscribe_monitor_work_events(resume_sub):
        resumed_events.append(event)

    assert len(resumed_events) == 2
    assert resumed_events[0].sequence == 3
    assert resumed_events[0].event_type == "STAGE_PROGRESS"
    assert resumed_events[1].sequence == 4
    assert resumed_events[1].event_type == "STAGE_COMPLETED"
