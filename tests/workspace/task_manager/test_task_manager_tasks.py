"""Tests for TaskManagerTasks engine and task models."""

from __future__ import annotations

import pytest
from app.workspace.task_manager.task_manager_projects import (
    TaskManagerProjects,
)
from app.workspace.task_manager.task_manager_tasks import TaskManagerTasks
from app.workspace.task_manager.task_manager_tasks_models import (
    AvailableTask,
    TaskActivateRequest,
    TaskCloneRequest,
    TaskConfig,
    TaskMoveRequest,
    TaskRenameRequest,
)


class TestTaskModels:
    """Test suite for Task models."""

    def test_task_models_serialization(self) -> None:
        """Verify AvailableTask and TaskConfig serialization."""
        avail = AvailableTask(type="Build", name="Build strategies")
        assert avail.to_dict() == {"type": "Build", "name": "Build strategies"}

        task = TaskConfig(
            task_name="Build 1",
            task_type="Build",
            task_title="Build Title",
            active=True,
            config={"param": 10},
            iterations=2,
        )
        task_dict = task.to_dict()
        assert task_dict["name"] == "Build 1"
        assert task_dict["taskName"] == "Build 1"
        assert task_dict["type"] == "Build"
        assert task_dict["title"] == "Build Title"
        assert task_dict["active"] is True
        assert task_dict["config"]["param"] == 10
        assert task_dict["iterations"] == 2

    def test_request_models(self) -> None:
        """Verify request dataclasses instantiation."""
        move = TaskMoveRequest(project_name="P", task_name="T1", to_index=2)
        assert move.to_index == 2
        rename = TaskRenameRequest(
            project_name="P", task_name="T1", task_title="New Title"
        )
        assert rename.task_title == "New Title"
        activate = TaskActivateRequest(project_name="P", task_name="T1", active=False)
        assert not activate.active
        clone = TaskCloneRequest(project_name="P", task_name="T1", position="after")
        assert clone.position == "after"


class TestTaskManagerTasksEngine:
    """Test suite for TaskManagerTasks operations."""

    @pytest.fixture
    def engines(self) -> tuple[TaskManagerProjects, TaskManagerTasks]:
        """Provide paired project and task engines."""
        proj_engine = TaskManagerProjects()
        proj_engine.create_project("Alpha")
        task_engine = TaskManagerTasks(proj_engine)
        return proj_engine, task_engine

    def test_get_available_tasks(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify available tasks catalogue contains expected items."""
        _, task_engine = engines
        tasks = task_engine.get_available_tasks()
        assert len(tasks) == 20
        task_types = [t.type for t in tasks]
        assert "Build" in task_types
        assert "WaitFor" in task_types
        assert "ClearDatabanks" in task_types
        assert "DeleteFile" in task_types
        assert "GoToTask" in task_types
        assert "NeuralNetworkTrainer" not in task_types

    def test_add_task_success_and_duplicates(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify adding tasks and detecting duplicate names."""
        _, task_engine = engines
        t1 = task_engine.add_task("Alpha", "Build 1", "Build")
        assert t1.task_name == "Build 1"
        assert t1.task_title == "Build 1"

        # Explicit custom title and initial config
        t2 = task_engine.add_task(
            "Alpha",
            "Wait 1",
            "WaitFor",
            task_title="Wait for report",
            config={"file": "out.txt"},
        )
        assert t2.task_title == "Wait for report"
        assert t2.config["file"] == "out.txt"

        # Duplicate name rejection
        with pytest.raises(
            ValueError, match=r"Task with name 'Build 1' already exists\."
        ):
            task_engine.add_task("Alpha", "Build 1", "Build")

        # Project not found
        with pytest.raises(KeyError, match=r"Project 'Ghost' does not exist\."):
            task_engine.add_task("Ghost", "Task", "Build")

    def test_add_task_at_index(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify inserting task at specific index position."""
        proj_engine, task_engine = engines
        task_engine.add_task("Alpha", "T1", "Build")
        task_engine.add_task("Alpha", "T2", "Build")
        task_engine.add_task("Alpha", "T0", "Build", index=0)

        proj = proj_engine.get_project("Alpha")
        names = [t["name"] for t in proj.tasks]
        assert names == ["T0", "T1", "T2"]

    def test_remove_task(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify removing task and checking error cases."""
        proj_engine, task_engine = engines
        task_engine.add_task("Alpha", "T1", "Build")
        task_engine.add_task("Alpha", "T2", "Build")

        removed = task_engine.remove_task("Alpha", "T1")
        assert removed.task_name == "T1"
        proj = proj_engine.get_project("Alpha")
        assert len(proj.tasks) == 1
        assert proj.tasks[0]["name"] == "T2"

        # Non-existent task
        with pytest.raises(KeyError, match=r"Task 'NonExistent' does not exist\."):
            task_engine.remove_task("Alpha", "NonExistent")

    def test_move_task(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify reordering tasks in project list."""
        proj_engine, task_engine = engines
        task_engine.add_task("Alpha", "T1", "Build")
        task_engine.add_task("Alpha", "T2", "Build")
        task_engine.add_task("Alpha", "T3", "Build")

        # Move T1 to index 2 (end)
        task_engine.move_task("Alpha", "T1", 2)
        proj = proj_engine.get_project("Alpha")
        assert [t["name"] for t in proj.tasks] == ["T2", "T3", "T1"]

        # Move with out of bounds index clamps cleanly
        task_engine.move_task("Alpha", "T1", 0)
        assert [t["name"] for t in proj.tasks] == ["T1", "T2", "T3"]

        with pytest.raises(KeyError, match=r"Task 'Ghost' does not exist\."):
            task_engine.move_task("Alpha", "Ghost", 0)

    def test_rename_task(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify updating task title."""
        proj_engine, task_engine = engines
        task_engine.add_task("Alpha", "T1", "Build", task_title="Original")
        task_engine.rename_task("Alpha", "T1", "Updated Title")

        proj = proj_engine.get_project("Alpha")
        assert proj.tasks[0]["title"] == "Updated Title"
        assert proj.tasks[0]["taskTitle"] == "Updated Title"
        # Identifier remains unchanged
        assert proj.tasks[0]["name"] == "T1"

        with pytest.raises(KeyError, match=r"Task 'Ghost' does not exist\."):
            task_engine.rename_task("Alpha", "Ghost", "Title")

    def test_activate_task(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify toggling active status on task."""
        proj_engine, task_engine = engines
        task_engine.add_task("Alpha", "T1", "Build")
        proj = proj_engine.get_project("Alpha")
        assert proj.tasks[0]["active"] is True

        task_engine.activate_task("Alpha", "T1", False)
        assert bool(proj.tasks[0]["active"]) is False

        task_engine.activate_task("Alpha", "T1", True)
        assert bool(proj.tasks[0]["active"]) is True

        with pytest.raises(KeyError, match=r"Task 'Ghost' does not exist\."):
            task_engine.activate_task("Alpha", "Ghost", False)

    def test_clone_task(
        self, engines: tuple[TaskManagerProjects, TaskManagerTasks]
    ) -> None:
        """Verify cloning task at end and after positions."""
        proj_engine, task_engine = engines
        task_engine.add_task(
            "Alpha",
            "Build 1",
            "Build",
            task_title="Original Build",
            config={"data": "test"},
        )
        task_engine.add_task("Alpha", "T_Last", "WaitFor")

        # Clone at end
        cloned_end = task_engine.clone_task("Alpha", "Build 1", position="end")
        assert cloned_end.task_name == "Build 2"
        assert cloned_end.task_title == "Original Build - Cloned"
        assert cloned_end.config == {"data": "test"}

        proj = proj_engine.get_project("Alpha")
        assert [t["name"] for t in proj.tasks] == [
            "Build 1",
            "T_Last",
            "Build 2",
        ]

        # Clone after
        cloned_after = task_engine.clone_task("Alpha", "Build 1", position="after")
        assert cloned_after.task_name == "Build 3"
        assert [t["name"] for t in proj.tasks] == [
            "Build 1",
            "Build 3",
            "T_Last",
            "Build 2",
        ]

        with pytest.raises(KeyError, match=r"Task 'Ghost' does not exist\."):
            task_engine.clone_task("Alpha", "Ghost")
