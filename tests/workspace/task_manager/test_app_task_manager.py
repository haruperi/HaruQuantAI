"""Tests for AppTaskManager pipeline execution engine."""

from __future__ import annotations

import pytest
from app.workspace.task_manager.app_task_manager import AppTaskManager
from app.workspace.task_manager.app_task_manager_models import (
    ExecutionStatus,
    ProjectExecutionState,
    TaskIterationRecord,
)
from app.workspace.task_manager.task_manager_projects import (
    TaskManagerProjects,
)
from app.workspace.task_manager.task_manager_tasks import TaskManagerTasks


class TestAppTaskManagerModels:
    """Test suite for AppTaskManager domain models."""

    def test_iteration_record(self) -> None:
        """Verify TaskIterationRecord dictionary conversion."""
        rec = TaskIterationRecord(task_name="Build 1", iterations=5)
        assert rec.to_dict() == {"taskName": "Build 1", "iterations": 5}

    def test_project_execution_state(self) -> None:
        """Verify ProjectExecutionState dictionary conversion."""
        state = ProjectExecutionState(
            project_name="Alpha",
            running_status=ExecutionStatus.RUNNING,
            active_task="Build 1",
            tasks_iterations=[TaskIterationRecord("Build 1", 2)],
        )
        data = state.to_dict()
        assert data["projectName"] == "Alpha"
        assert data["runningStatus"] == "running"
        assert data["activeTask"] == "Build 1"
        assert len(data["tasksIterations"]) == 1


class TestAppTaskManagerPipeline:
    """Test suite for AppTaskManager execution and condition handling."""

    @pytest.fixture
    def setup_pipeline(
        self,
    ) -> tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager]:
        """Provide configured pipeline engines."""
        proj_engine = TaskManagerProjects()
        task_engine = TaskManagerTasks(proj_engine)
        app_tm = AppTaskManager(proj_engine)
        return proj_engine, task_engine, app_tm

    def test_lifecycle_transitions(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """Verify start, pause, stop transitions."""
        proj_engine, task_engine, app_tm = setup_pipeline
        proj_engine.create_project("Alpha")
        task_engine.add_task("Alpha", "T1", "Build")
        task_engine.add_task("Alpha", "T2", "Build")

        # Initial state
        assert app_tm.get_project_status("Alpha").running_status.value == "stopped"
        assert app_tm.get_project_status("Alpha").active_task is None

        # Start
        app_tm.start_project("Alpha")
        assert app_tm.get_project_status("Alpha").running_status.value == "running"
        assert app_tm.get_project_status("Alpha").active_task == "T1"

        # Pause
        app_tm.pause_project("Alpha")
        assert app_tm.get_project_status("Alpha").running_status.value == "paused"

        # Stop
        app_tm.stop_project("Alpha")
        assert app_tm.get_project_status("Alpha").running_status.value == "stopped"
        assert app_tm.get_project_status("Alpha").active_task is None

    def test_empty_project_start(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """Start on project with no active tasks finishes immediately."""
        proj_engine, _, app_tm = setup_pipeline
        proj_engine.create_project("Empty")
        app_tm.start_project("Empty")
        state = app_tm.get_project_status("Empty")
        assert state.running_status.value == "finished"
        assert state.active_task is None

    def test_sequential_stepping(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """Step through normal sequential tasks."""
        proj_engine, task_engine, app_tm = setup_pipeline
        proj_engine.create_project("Alpha")
        task_engine.add_task("Alpha", "T1", "Build")
        task_engine.add_task("Alpha", "T2", "Build")

        # Stepping when not running returns False
        assert not app_tm.step_project("Alpha")

        app_tm.start_project("Alpha")
        # Step T1
        has_more = app_tm.step_project("Alpha")
        assert has_more is True
        assert app_tm.get_project_status("Alpha").active_task == "T2"

        # Step T2
        has_more = app_tm.step_project("Alpha")
        assert has_more is False
        assert app_tm.get_project_status("Alpha").running_status.value == "finished"
        assert app_tm.get_project_status("Alpha").active_task is None

        # Check iterations
        final_state = app_tm.get_project_status("Alpha")
        iter_map = {r.task_name: r.iterations for r in final_state.tasks_iterations}
        assert iter_map["T1"] == 1
        assert iter_map["T2"] == 1

    def test_inactive_task_skipped(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """Verify inactive task is skipped in pipeline."""
        proj_engine, task_engine, app_tm = setup_pipeline
        proj_engine.create_project("Alpha")
        task_engine.add_task("Alpha", "T1", "Build")
        task_engine.add_task("Alpha", "T2", "Build")
        task_engine.activate_task("Alpha", "T2", False)
        task_engine.add_task("Alpha", "T3", "Build")

        app_tm.start_project("Alpha")
        app_tm.step_project("Alpha")  # executes T1
        state = app_tm.get_project_status("Alpha")
        # Next should be T3, skipping inactive T2
        assert state.active_task == "T3"

    def test_wait_for_user_pauses(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """WaitFor user action pauses the project."""
        proj_engine, task_engine, app_tm = setup_pipeline
        proj_engine.create_project("WaitProj")
        task_engine.add_task("WaitProj", "Wait1", "WaitFor", config={"action": "user"})

        app_tm.start_project("WaitProj")
        cont = app_tm.step_project("WaitProj")
        assert cont is False
        state = app_tm.get_project_status("WaitProj")
        assert state.running_status.value == "paused"

    def test_goto_task_with_conditions(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """Verify GoToTask loop execution based on evaluated/activated counters."""
        proj_engine, task_engine, app_tm = setup_pipeline
        proj_engine.create_project("LoopProj")
        task_engine.add_task("LoopProj", "T1", "Build")
        task_engine.add_task(
            "LoopProj",
            "GoTo1",
            "GoToTask",
            config={
                "task": "T1",
                "conditions": [
                    {
                        "type": "GoToEvaluated",
                        "comparator": "<",
                        "number": 3,
                    }
                ],
            },
        )
        task_engine.add_task("LoopProj", "T_Final", "DeleteFile")

        app_tm.start_project("LoopProj")
        steps = app_tm.run_pipeline("LoopProj", max_steps=20)
        # Should loop T1 -> GoTo1 until GoToEvaluated condition reaches 3, then proceed to T_Final
        assert steps > 4
        state = app_tm.get_project_status("LoopProj")
        assert state.running_status.value == "finished"

        iter_map = {r.task_name: r.iterations for r in state.tasks_iterations}
        assert iter_map["T1"] >= 3
        assert iter_map["GoTo1"] >= 3
        assert iter_map["T_Final"] == 1

    def test_stop_and_start_task(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """StopAndStart halts project execution when conditions are met."""
        proj_engine, task_engine, app_tm = setup_pipeline
        proj_engine.create_project("StopProj")
        task_engine.add_task(
            "StopProj",
            "Stop1",
            "StopAndStart",
            config={
                "conditions": [
                    {
                        "type": "ResultsCount",
                        "comparator": ">=",
                        "number": 10,
                        "databank": "Results",
                    }
                ]
            },
        )
        task_engine.add_task("StopProj", "NeverReached", "Build")

        # Databank count < 10 -> continues
        app_tm.set_databank_counts("StopProj", {"Results": 5})
        app_tm.start_project("StopProj")
        app_tm.step_project("StopProj")
        state = app_tm.get_project_status("StopProj")
        assert state.active_task == "NeverReached"

        # Databank count >= 10 -> stops
        app_tm.stop_project("StopProj")
        app_tm.set_databank_counts("StopProj", {"Results": 15})
        app_tm.start_project("StopProj")
        cont = app_tm.step_project("StopProj")
        assert cont is False
        state = app_tm.get_project_status("StopProj")
        assert state.running_status.value == "stopped"

    def test_custom_project_stats(
        self,
        setup_pipeline: tuple[TaskManagerProjects, TaskManagerTasks, AppTaskManager],
    ) -> None:
        """Verify stats extraction across multiple projects."""
        proj_engine, task_engine, app_tm = setup_pipeline
        proj_engine.create_project("P1")
        p2 = proj_engine.create_project("AppPredefined")
        p2.is_app_project = True

        task_engine.add_task("P1", "Build1", "Build")

        stats = app_tm.get_custom_project_stats()
        # Predefined is filtered out
        assert len(stats) == 1
        assert stats[0]["projectName"] == "P1"
        assert "runningStatus" in stats[0]
        assert "tasksIterations" in stats[0]
