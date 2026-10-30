"""Tests for Task Manager FastAPI routes and REST endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.workspace.task_manager.routes import (
    task_manager_router,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient with the task manager router mounted."""
    app = FastAPI()
    app.include_router(task_manager_router)
    return TestClient(app)


class TestTaskManagerRoutes:
    """Test suite for Task Manager REST endpoints."""

    def test_project_lifecycle_routes(self, client: TestClient) -> None:
        """Test create, list, clone, rename, and remove project endpoints."""
        # List initially
        res = client.get("/taskmanager/listProjects")
        assert res.status_code == 200
        assert res.json()["success"] == "Projects listed."

        # Create
        res = client.post(
            "/taskmanager/createProject", json={"projectName": "RouteProj"}
        )
        assert res.status_code == 200
        assert res.json()["projectName"] == "RouteProj"

        # Create duplicate fails
        res = client.post(
            "/taskmanager/createProject", json={"projectName": "RouteProj"}
        )
        assert res.status_code == 400

        # Clone
        res = client.post(
            "/taskmanager/cloneProject", json={"projectName": "RouteProj"}
        )
        assert res.status_code == 200
        cloned_name = res.json()["projectName"]
        assert cloned_name == "RouteProj(2)"

        # Rename
        res = client.post(
            "/taskmanager/renameProject",
            json={"oldName": "RouteProj(2)", "newName": "RouteProjRenamed"},
        )
        assert res.status_code == 200

        # Remove
        res = client.post(
            "/taskmanager/removeProject", json={"projectName": "RouteProjRenamed"}
        )
        assert res.status_code == 200

    def test_file_operations_routes(self, client: TestClient, tmp_path: Path) -> None:
        """Test save, validate, and open project endpoints."""
        # Create project first
        client.post("/taskmanager/createProject", json={"projectName": "FileProj"})

        target_file = tmp_path / "route_proj.json"

        # Save
        res = client.post(
            "/taskmanager/saveProject",
            json={"projectName": "FileProj", "file": str(target_file)},
        )
        assert res.status_code == 200

        # Validate
        res = client.post(
            "/taskmanager/validateProject",
            json={"filePath": str(target_file)},
        )
        assert res.status_code == 200
        assert res.json()["valid"] is True

        # Open
        res = client.post(
            "/taskmanager/openProject",
            json={"file": str(target_file), "loadAsIs": True},
        )
        assert res.status_code == 200
        assert res.json()["projectName"] == "FileProj"

    def test_task_graph_routes(self, client: TestClient) -> None:
        """Test task graph manipulation endpoints."""
        client.post("/taskmanager/createProject", json={"projectName": "TaskProj"})

        # Get available tasks
        res = client.get("/taskmanager/getAvailableTasks")
        assert res.status_code == 200
        assert len(res.json()["tasks"]) == 20

        # Add task
        res = client.post(
            "/taskmanager/addTask",
            json={
                "projectName": "TaskProj",
                "taskName": "Build 1",
                "taskType": "Build",
                "taskTitle": "My Build",
            },
        )
        assert res.status_code == 200
        assert res.json()["task"]["taskName"] == "Build 1"

        # Add second task
        client.post(
            "/taskmanager/addTask",
            json={
                "projectName": "TaskProj",
                "taskName": "Wait 1",
                "taskType": "WaitFor",
            },
        )

        # Move task
        res = client.post(
            "/taskmanager/moveTask",
            json={"projectName": "TaskProj", "taskName": "Build 1", "toIndex": 1},
        )
        assert res.status_code == 200

        # Rename task
        res = client.post(
            "/taskmanager/renameTask",
            json={
                "projectName": "TaskProj",
                "taskName": "Build 1",
                "taskTitle": "New Title",
            },
        )
        assert res.status_code == 200

        # Clone task
        res = client.post(
            "/taskmanager/cloneTask",
            json={
                "projectName": "TaskProj",
                "taskName": "Build 1",
                "position": "after",
            },
        )
        assert res.status_code == 200
        assert "Build 2" in res.json()["task"]["taskName"]

        # Activate task
        res = client.post(
            "/taskmanager/activateTask",
            json={"projectName": "TaskProj", "taskName": "Build 1", "active": False},
        )
        assert res.status_code == 200

        # Remove task
        res = client.post(
            "/taskmanager/removeTask",
            json={"projectName": "TaskProj", "taskName": "Wait 1"},
        )
        assert res.status_code == 200

    def test_symbols_routes(self, client: TestClient) -> None:
        """Test symbol modification endpoints."""
        client.post("/taskmanager/createProject", json={"projectName": "SymProj"})
        client.post(
            "/taskmanager/addTask",
            json={
                "projectName": "SymProj",
                "taskName": "Build 1",
                "taskType": "Build",
                "config": {"Data": {"symbol": "EURUSD", "timeframe": "M1"}},
            },
        )

        # Modify symbols list
        res = client.post(
            "/taskmanager/modifySymbolsList", json={"projectName": "SymProj"}
        )
        assert res.status_code == 200
        assert res.json()["symbols"] == ["EURUSD/M1"]

        # Modify symbols
        res = client.post(
            "/taskmanager/modifySymbols",
            json={
                "projectName": "SymProj",
                "symbols": [{"symbolFrom": "EURUSD/M1", "symbolTo": "GBPUSD/M5"}],
            },
        )
        assert res.status_code == 200

        # Verify updated
        res = client.post(
            "/taskmanager/modifySymbolsList", json={"projectName": "SymProj"}
        )
        assert res.json()["symbols"] == ["GBPUSD/M5"]

    def test_pipeline_control_routes(self, client: TestClient) -> None:
        """Test pipeline start, pause, stop, and status endpoints."""
        client.post("/taskmanager/createProject", json={"projectName": "PipeProj"})
        client.post(
            "/taskmanager/addTask",
            json={
                "projectName": "PipeProj",
                "taskName": "T1",
                "taskType": "Build",
            },
        )

        # Start
        res = client.post("/taskmanager/startProject", json={"projectName": "PipeProj"})
        assert res.status_code == 200

        # Status
        res = client.get(
            "/taskmanager/projectStatus", params={"projectName": "PipeProj"}
        )
        assert res.status_code == 200
        assert res.json()["runningStatus"] == "running"

        # Pause
        res = client.post("/taskmanager/pauseProject", json={"projectName": "PipeProj"})
        assert res.status_code == 200

        # Stop
        res = client.post("/taskmanager/stopProject", json={"projectName": "PipeProj"})
        assert res.status_code == 200

        # Custom project stats
        res = client.get("/taskmanager/customProjectStats")
        assert res.status_code == 200
        assert "stats" in res.json()
