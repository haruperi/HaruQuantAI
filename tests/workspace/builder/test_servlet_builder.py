"""Unit tests for ServletBuilderDispatcher."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.app_builder import BuilderWorkspaceState
from app.workspace.builder.servlet_builder import ServletBuilderDispatcher


def test_golden_fixture_dispatch() -> None:
    """Verify dispatching 'build/status' returns state and 'build/unknown' raises BUILDER_UNKNOWN_ACTION."""
    dispatcher = ServletBuilderDispatcher()

    # Golden status dispatch
    status_resp = dispatcher.dispatch("build/status", {"project_id": "proj_1"})
    assert isinstance(status_resp.data, BuilderWorkspaceState)
    assert status_resp.data.project_id == "proj_1"

    # Golden unknown action dispatch
    with pytest.raises(DomainError) as exc:
        dispatcher.dispatch("build/unknown", {})
    assert exc.value.code == "BUILDER_UNKNOWN_ACTION"


def test_lifecycle_dispatch_actions() -> None:
    """Verify start, pause, resume, and stop action dispatches."""
    dispatcher = ServletBuilderDispatcher()
    payload = {"project_id": "proj_lifecycle"}

    res_start = dispatcher.dispatch("build/start", payload)
    assert res_start.data.status == "RUNNING"

    res_pause = dispatcher.dispatch("build/pause", payload)
    assert res_pause.data.status == "PAUSED"

    res_resume = dispatcher.dispatch("build/resume", payload)
    assert res_resume.data.status == "RUNNING"

    res_stop = dispatcher.dispatch("build/stop", payload)
    assert res_stop.data.status == "STOPPED"


def test_calibrate_dispatch() -> None:
    """Verify indyTester/calibrate dispatch."""
    dispatcher = ServletBuilderDispatcher()
    resp = dispatcher.dispatch(
        "indyTester/calibrate", {"project_id": "proj_1", "bars": ()}
    )
    assert isinstance(resp.data, dict)
    assert resp.request_id == "calibrate-proj_1"
