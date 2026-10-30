"""Unit tests for ServletGridControl API routes and wire models."""

from __future__ import annotations

import logging

import pytest
from app.workspace.grid_control.models import (
    FinishedJobSnapshot,
    GridDataPayload,
    GridDataResponse,
    RunningJobSnapshot,
    WaitingJobSnapshot,
)
from app.workspace.grid_control.service import GridControlService
from app.workspace.grid_control.views import create_grid_control_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_models_wire_serialization() -> None:
    """Verify camelCase wire serialization matches donor DescriptionsSerializer."""
    running = RunningJobSnapshot(
        job_id="job-run-1",
        job_group_id="group-a",
        create_time_ms=1000,
        progress=45,
        duration_ms=500,
        duration_with_wait_ms=1500,
        start_time_ms=1500,
        waiting=False,
    )
    r_dict = running.to_wire_dict()
    assert r_dict == {
        "jobId": "job-run-1",
        "jobGroupId": "group-a",
        "createTime": 1000,
        "progress": 45,
        "duration": 500,
        "durationWithWait": 1500,
        "startTime": 1500,
        "waiting": False,
    }

    waiting = WaitingJobSnapshot(
        job_id="job-wait-1",
        job_group_id="group-b",
        create_time_ms=2000,
    )
    assert waiting.to_wire_dict() == {
        "jobId": "job-wait-1",
        "jobGroupId": "group-b",
        "createTime": 2000,
    }

    finished_ok = FinishedJobSnapshot(
        job_id="job-fin-1",
        job_group_id="group-c",
        create_time_ms=100,
        duration_ms=200,
        duration_with_wait_ms=300,
        start_time_ms=200,
        finish_time_ms=400,
        success=True,
    )
    assert finished_ok.to_wire_dict() == {
        "jobId": "job-fin-1",
        "jobGroupId": "group-c",
        "createTime": 100,
        "duration": 200,
        "durationWithWait": 300,
        "startTime": 200,
        "finishTime": 400,
        "success": True,
    }

    finished_err = FinishedJobSnapshot(
        job_id="job-fin-2",
        job_group_id="group-c",
        create_time_ms=100,
        duration_ms=50,
        duration_with_wait_ms=100,
        start_time_ms=150,
        finish_time_ms=200,
        success=False,
        message="Node failure",
    )
    assert finished_err.to_wire_dict() == {
        "jobId": "job-fin-2",
        "jobGroupId": "group-c",
        "createTime": 100,
        "duration": 50,
        "durationWithWait": 100,
        "startTime": 150,
        "finishTime": 200,
        "success": False,
        "message": "Node failure",
    }

    payload = GridDataPayload(
        running=(running,),
        waiting=(waiting,),
        finished=(finished_ok, finished_err),
    )
    response = GridDataResponse(grid_data=payload)
    resp_dict = response.to_wire_dict()

    assert resp_dict["success"] == "Databanks listed."
    assert "gridData" in resp_dict
    assert len(resp_dict["gridData"]["running"]) == 1
    assert len(resp_dict["gridData"]["waiting"]) == 1
    assert len(resp_dict["gridData"]["finished"]) == 2


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client with grid control routes."""
    app = FastAPI()
    service = GridControlService()
    router = create_grid_control_router(service)
    app.include_router(router)
    return TestClient(app)


def test_get_data_default_command(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify GET /gridControl/ defaults to getData and returns wire JSON."""
    with caplog.at_level(logging.INFO):
        res = client.get("/gridControl/")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] == "Databanks listed."
    assert "gridData" in data
    assert "running" in data["gridData"]
    assert "waiting" in data["gridData"]
    assert "finished" in data["gridData"]
    assert "FR-GRID-API-GETDATA" in caplog.text


def test_get_data_direct_endpoint(client: TestClient) -> None:
    """Verify GET /gridControl/getData returns 200."""
    res = client.get("/gridControl/getData")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] == "Databanks listed."
    assert "gridData" in data


def test_post_data_command(client: TestClient) -> None:
    """Verify POST /gridControl/ handles command in body or query."""
    res_query = client.post("/gridControl/?command=getData")
    assert res_query.status_code == 200

    res_body = client.post("/gridControl/", json={"command": "getData"})
    assert res_body.status_code == 200

    # Invalid JSON body fallback to default query parameter
    res_bad_json = client.post(
        "/gridControl/",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert res_bad_json.status_code == 200


def test_unknown_command_returns_400(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify unknown command returns 400 and logs warning."""
    with caplog.at_level(logging.WARNING):
        res = client.get("/gridControl/?command=unknownCmd")
    assert res.status_code == 400
    assert "Unknown command 'unknownCmd'." in res.json()["detail"]
    assert "FR-GRID-API-VALIDATION" in caplog.text

    res_post = client.post("/gridControl/", json={"command": "badCmd"})
    assert res_post.status_code == 400
    assert "Unknown command 'badCmd'." in res_post.json()["detail"]
