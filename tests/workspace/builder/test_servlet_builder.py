"""Unit tests for ServletBuilderDispatcher."""

from __future__ import annotations

from typing import Any

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.app_builder import BuilderWorkspaceState
from app.workspace.builder.servlet_builder import ServletBuilderDispatcher
from tests.workspace.builder.test_app_builder import (
    native_environment as native_environment,  # noqa: PLC0414
)


def test_golden_fixture_dispatch() -> None:
    """Verify dispatching 'build/status' returns state and 'build/unknown' raises BUILDER_UNKNOWN_ACTION."""
    dispatcher = ServletBuilderDispatcher()

    # Golden status dispatch
    status_resp = dispatcher.dispatch("build/status", {"project_id": "proj_1"})
    assert isinstance(status_resp.data, BuilderWorkspaceState)
    assert status_resp.data.project_id == "proj_1"

    # Golden unknown action dispatch
    with pytest.raises(DomainError) as exc:
        dispatcher.dispatch("build/unknown", {"project_id": "proj_1"})
    assert exc.value.code == "BUILDER_UNKNOWN_ACTION"


def test_lifecycle_dispatch_actions(native_environment: Any) -> None:
    """Dispatcher preserves saved project/task/revision and selected job identity."""
    home, jobs = native_environment
    config = home.load_project("acceptance-builder")["tasks"]["task"]["settings"][
        "execution"
    ]
    home.save_project_settings(
        "acceptance-builder", "task", {"execution": {**config, "candidates": 1000}}, 1
    )
    dispatcher = ServletBuilderDispatcher(home_service=home)
    started = dispatcher.dispatch(
        "build/start",
        {"project_id": "acceptance-builder", "task_id": "task", "expected_revision": 2},
    ).data
    payload = {"project_id": "acceptance-builder", "job_id": started.job_id}
    assert dispatcher.dispatch("build/pause", payload).data.status == "PAUSED"
    assert dispatcher.dispatch("build/resume", payload).data.status == "RUNNING"
    dispatcher.dispatch("build/stop", payload)
    assert jobs.wait_for_job(started.job_id, timeout=10).status == "CANCELLED"


def test_calibrate_dispatch() -> None:
    """Verify indyTester/calibrate dispatch."""
    dispatcher = ServletBuilderDispatcher()
    resp = dispatcher.dispatch(
        "indyTester/calibrate", {"project_id": "proj_1", "bars": ()}
    )
    assert isinstance(resp.data, dict)
    assert resp.request_id == "calibrate-proj_1"
