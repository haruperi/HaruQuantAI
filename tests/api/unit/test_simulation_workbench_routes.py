"""Route tests for the Simulation Workbench HTTP boundaries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.api.identity import build_auth_context
from app.services.api.widgets.simulator.workbench_routes import (
    _cancel_batch,
    _close_live_session,
    _create_live_session,
    _finalize_live_session,
    _get_batch,
    _get_live_session,
    _get_viewport,
    _list_live_sessions,
    _retry_failed,
    _simulation_workbench_source,
    _step_live_session,
    _submit_command,
)
from app.services.api.widgets.simulator.workbench_schemas import (
    LiveSessionCommandRequest,
    LiveSessionCreateRequest,
    StepRequest,
    ViewportQuery,
)
from app.utils import generate_id
from fastapi import HTTPException


def _context(*permissions: str) -> Any:
    """Return an authenticated principal carrying the given permissions."""
    return build_auth_context(
        principal={
            "principal_id": "user-workbench",
            "principal_type": "USER",
            "roles": ("researcher",),
            "permissions": permissions,
            "scopes": (),
            "tenant_or_environment": "development",
            "runtime_profile": "simulation",
        },
        trace={
            "issued_at": datetime.now(UTC),
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
        },
    )


class _RecordingSource:
    """Dispatch source recording operations and replaying results."""

    def __init__(self, results: dict[str, object] | None = None) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.results = results or {}

    def __call__(self, operation: str, *args: object, **kwargs: object) -> object:
        self.calls.append((operation, args, kwargs))
        if operation in self.results:
            result = self.results[operation]
            if isinstance(result, Exception):
                raise result
            return result
        return {"operation": operation}


def test_uncomposed_source_fails_closed() -> None:
    """The workbench dependency refuses service until composed."""
    with pytest.raises(HTTPException) as raised:
        _simulation_workbench_source()
    assert raised.value.status_code == 503
    assert raised.value.detail == "SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE"


def test_reads_require_the_simulation_read_permission() -> None:
    """Authorization happens before any resource access."""
    source = _RecordingSource()
    with pytest.raises(HTTPException) as raised:
        _get_live_session("session-1", _context(), source)
    assert raised.value.status_code == 403


def test_foreign_or_unknown_sessions_return_404() -> None:
    """Unknown and foreign-owned resources are indistinguishable 404s."""
    source = _RecordingSource(results={"get_session": None})
    with pytest.raises(HTTPException) as raised:
        _get_live_session("session-1", _context("simulation:read"), source)
    assert raised.value.status_code == 404
    assert raised.value.detail == "SIMULATION_SESSION_NOT_FOUND"


def test_session_listing_is_principal_scoped() -> None:
    """Listing delegates once with the authenticated principal."""
    source = _RecordingSource(results={"list_sessions": ()})
    payload = _list_live_sessions(_context("simulation:read"), source)
    assert payload == {"sessions": ()}
    assert source.calls[0][0] == "list_sessions"
    assert source.calls[0][2]["principal_id"] == "user-workbench"


def test_viewport_rejects_future_rows() -> None:
    """A viewport requesting rows after the cursor is refused with 422."""
    context = _context("simulation:read")
    source = _RecordingSource(
        results={"viewport": ValueError("SIMULATION_VIEWPORT_INVALID")}
    )
    with pytest.raises(HTTPException) as raised:
        _get_viewport(
            "session-1",
            ViewportQuery(),
            context,
            source,
        )
    assert raised.value.status_code == 422
    assert raised.value.detail == "SIMULATION_VIEWPORT_INVALID"


@pytest.mark.anyio
async def test_command_requires_idempotency_and_returns_owner_truth() -> None:
    """Commands need an idempotency key and never invent fills."""
    context = _context("simulation:run")
    source = _RecordingSource(
        results={
            "command": {
                "receipt": {"receipt_id": "r-1", "status": "filled"},
                "session": {"session_id": "session-1"},
            }
        }
    )
    with pytest.raises(HTTPException) as raised:
        await _submit_command(
            "session-1",
            LiveSessionCommandRequest(command="close_position"),
            context,
            source,
        )
    assert raised.value.status_code == 422
    assert raised.value.detail == "IDEMPOTENCY_KEY_REQUIRED"
    result = await _submit_command(
        "session-1",
        LiveSessionCommandRequest(command="close_position"),
        context,
        source,
        idempotency_key=generate_id("req"),
    )
    assert result["receipt"]["receipt_id"] == "r-1"
    assert result["session"]["session_id"] == "session-1"
    assert source.calls[0][0] == "command"


@pytest.mark.anyio
async def test_command_awaits_an_asynchronous_live_authority() -> None:
    """A live authority that returns an awaitable is resolved, not returned."""

    async def _pending() -> dict[str, object]:
        return {
            "receipts": ({"receipt_id": "r-2", "filled_quantity": "0"},),
            "session": {"session_id": "session-1"},
        }

    context = _context("simulation:run")
    source = _RecordingSource(results={"command": _pending()})
    result = await _submit_command(
        "session-1",
        LiveSessionCommandRequest(command="cancel_pending_order", order_id="order-7"),
        context,
        source,
        idempotency_key=generate_id("req"),
    )
    assert result["receipts"][0]["receipt_id"] == "r-2"
    assert result["session"]["session_id"] == "session-1"


def test_step_requires_permission_and_delegates() -> None:
    """Stepping is a governed write delegating to the live authority."""
    with pytest.raises(HTTPException) as raised:
        _step_live_session(
            "session-1",
            StepRequest(ticks=10),
            _context("simulation:read"),
            _RecordingSource(),
        )
    assert raised.value.status_code == 403
    source = _RecordingSource()
    _step_live_session(
        "session-1",
        StepRequest(ticks=10),
        _context("simulation:run"),
        source,
    )
    assert source.calls[0][0] == "step"
    assert source.calls[0][2]["ticks"] == 10


def test_finalize_stays_advisory_and_requires_idempotency() -> None:
    """Finalization is one idempotent advisory seal operation."""
    context = _context("simulation:run")
    source = _RecordingSource()
    with pytest.raises(HTTPException) as raised:
        _finalize_live_session("session-1", context, source)
    assert raised.value.status_code == 422
    _finalize_live_session(
        "session-1", context, source, idempotency_key=generate_id("req")
    )
    assert source.calls[0][0] == "finalize"


def test_create_session_requires_idempotency_and_404s_foreign_runs() -> None:
    """Session creation is idempotent and 404s unknown runs."""
    context = _context("simulation:run")
    source = _RecordingSource(results={"create_session": None})
    request = LiveSessionCreateRequest(run_id="run-1")
    with pytest.raises(HTTPException) as raised:
        _create_live_session(request, context, source)
    assert raised.value.status_code == 422
    with pytest.raises(HTTPException) as raised:
        _create_live_session(
            request, context, source, idempotency_key=generate_id("req")
        )
    assert raised.value.status_code == 404
    assert raised.value.detail == "SIMULATION_RUN_NOT_FOUND"


def test_batch_routes_require_ownership() -> None:
    """Unknown or foreign batches are uniform 404s."""
    context = _context("simulation:read", "simulation:run")
    source = _RecordingSource(results={"get_batch": None, "cancel_batch": None})
    with pytest.raises(HTTPException) as raised:
        _get_batch("batch-1", context, source)
    assert raised.value.status_code == 404
    assert raised.value.detail == "SIMULATION_BATCH_NOT_FOUND"
    with pytest.raises(HTTPException) as raised:
        _cancel_batch("batch-1", context, source, idempotency_key=generate_id("req"))
    assert raised.value.status_code == 404


def test_retry_failed_requires_idempotency_and_delegates() -> None:
    """Retry-failed is one idempotent governed write."""
    context = _context("simulation:run")
    source = _RecordingSource(results={"retry_failed": {"retried_items": 0}})
    with pytest.raises(HTTPException) as raised:
        _retry_failed("batch-1", context, source)
    assert raised.value.status_code == 422
    result = _retry_failed(
        "batch-1", context, source, idempotency_key=generate_id("req")
    )
    assert result == {"retried_items": 0}
    assert source.calls[0][0] == "retry_failed"


def test_close_session_requires_governed_permission() -> None:
    """Closing is a governed write over an owned session."""
    with pytest.raises(HTTPException) as raised:
        _close_live_session(
            "session-1", _context("simulation:read"), _RecordingSource()
        )
    assert raised.value.status_code == 403
    source = _RecordingSource(results={"close_session": {"status": "closed"}})
    result = _close_live_session("session-1", _context("simulation:run"), source)
    assert result == {"status": "closed"}
