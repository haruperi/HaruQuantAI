"""App Task Manager pipeline execution orchestrator and progress publisher.

Description:
    Manages runtime execution of Task Manager project pipelines: step-by-step
    task execution, condition evaluation, loops and GoTo jumps, pause/stop/start
    lifecycle, and progress statistics publishing.

Purpose:
    FEAT-TM-APP-ENGINE: Project pipeline execution runtime for Task Manager.

Key Capabilities:
    FR-TM-APP-LIFECYCLE: Start, stop, pause, and step project execution.
    FR-TM-APP-CONDITIONS: Condition evaluation integrating Cycles, Runtime,
        Results, and GoTo cycle evaluators.
    FR-TM-APP-GOTO: Branching and loop orchestration for GoToTask transitions.
    FR-TM-APP-STATS: Progress publishing matching TaskManagerProgressPublisher.

Python API Usage:
    ```python
    from app.workspace.task_manager.app_task_manager import AppTaskManager
    from app.workspace.task_manager.task_manager_projects import (
        TaskManagerProjects,
    )

    proj_engine = TaskManagerProjects()
    proj_engine.create_project("Alpha")
    app_tm = AppTaskManager(proj_engine)
    app_tm.start_project("Alpha")
    app_tm.step_project("Alpha")
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/ -q
    ```
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

from app.workspace.task_manager.app_task_manager_models import (
    ExecutionStatus,
    ProjectExecutionState,
    TaskIterationRecord,
)
from app.workspace.task_manager.conditions.cycles import RunCyclesCondition
from app.workspace.task_manager.conditions.go_to_activated import (
    GoToActivatedCondition,
)
from app.workspace.task_manager.conditions.go_to_evaluated import (
    GoToEvaluatedCondition,
)
from app.workspace.task_manager.conditions.results import ResultsCountCondition
from app.workspace.task_manager.conditions.runtime import RuntimeCondition
from app.workspace.task_manager.task_manager_projects import (
    TaskManagerProjects,
)
from app.workspace.task_manager.tasks.apply_mass_config import (
    ApplyMassConfigTask,
)
from app.workspace.task_manager.tasks.automatic_portfolio_builder import (
    AutomaticPortfolioBuilderTask,
)
from app.workspace.task_manager.tasks.automatic_retest import (
    AutomaticRetestTask,
)
from app.workspace.task_manager.tasks.call_external_script import (
    CallExternalScriptTask,
)
from app.workspace.task_manager.tasks.clear_databanks import (
    ClearBank,
    ClearDatabanksTask,
)
from app.workspace.task_manager.tasks.create_portfolio import (
    CreatePortfolioTask,
)
from app.workspace.task_manager.tasks.custom_analysis import (
    CustomAnalysisTask,
)
from app.workspace.task_manager.tasks.delete_file import (
    DeleteFileTask,
)
from app.workspace.task_manager.tasks.filtering import (
    FilteringTask,
)
from app.workspace.task_manager.tasks.go_to_task import (
    GoToTaskCoordinator,
)
from app.workspace.task_manager.tasks.load_from_files import (
    LoadFromFilesTask,
)
from app.workspace.task_manager.tasks.log_databank_stats import (
    LogDatabankStatsTask,
)
from app.workspace.task_manager.tasks.notification import (
    NotificationTask,
)
from app.workspace.task_manager.tasks.save_to_files import (
    SaveToFilesTask,
)
from app.workspace.task_manager.tasks.stop_and_start import (
    StopAndStartTaskCoordinator,
)
from app.workspace.task_manager.tasks.update_data import (
    UpdateDataTask,
)
from app.workspace.task_manager.tasks.wait_for import (
    WaitForTaskCoordinator,
)

logger = logging.getLogger("haruquant.task_manager.app")


class _DefaultDeleteProgress:
    def set_log_prefix(self, _prefix: str) -> None:
        pass

    def log(self, message: str) -> None:
        logger.info("%s", message)

    def start(self) -> None:
        pass

    def finish(self) -> None:
        pass


class _DefaultFileOperations:
    def exists(self, _path: str) -> bool:
        return False

    def delete(self, _path: str) -> bool:
        return False

    def basename(self, path: str) -> str:
        return path


class _DefaultClearProgress:
    def set_log_prefix(self, _prefix: str) -> None:
        pass

    def log(self, message: str) -> None:
        logger.info("%s", message)

    def start(self) -> None:
        pass

    def finish(self) -> None:
        pass


class _DefaultClearProject:
    def list_banks(self) -> list[ClearBank]:
        return []

    def get_bank(self, _name: str) -> ClearBank | None:
        return None

    def on_memory_error(self, _error: MemoryError) -> None:
        pass


class AppTaskManager:
    """Pipeline execution coordinator for Task Manager projects."""

    def __init__(self, projects_engine: TaskManagerProjects) -> None:
        """Initialize AppTaskManager with reference to project engine."""
        self._projects_engine = projects_engine
        self._states: dict[str, ProjectExecutionState] = {}
        self._current_indices: dict[str, int] = {}
        self._project_cycles: dict[str, int] = {}
        self._start_times: dict[str, float] = {}
        self._evaluated_cycles: dict[str, dict[str, int]] = {}
        self._activated_cycles: dict[str, dict[str, int]] = {}
        self._databank_counts: dict[str, dict[str, int]] = {}
        logger.info("Initialized AppTaskManager execution engine")

    def _ensure_project_state(self, project_name: str) -> ProjectExecutionState:
        """Ensure execution state exists for project, initializing if absent."""
        project = self._projects_engine.get_project(project_name)
        if project_name not in self._states:
            records = [
                TaskIterationRecord(
                    task_name=str(t.get("task_name") or t.get("name")),
                    iterations=int(t.get("iterations", 0)),
                )
                for t in project.tasks
            ]
            self._states[project_name] = ProjectExecutionState(
                project_name=project_name,
                running_status=ExecutionStatus.STOPPED,
                active_task=None,
                tasks_iterations=records,
            )
            self._current_indices[project_name] = 0
            self._project_cycles[project_name] = 0
            self._evaluated_cycles[project_name] = {}
            self._activated_cycles[project_name] = {}
            self._databank_counts[project_name] = {"Results": 0}

        return self._states[project_name]

    def set_databank_counts(self, project_name: str, counts: Mapping[str, int]) -> None:
        """Set databank records counts for ResultsCount condition evaluation."""
        self._ensure_project_state(project_name)
        self._databank_counts[project_name] = dict(counts)
        logger.debug("Updated databank counts for %s: %s", project_name, counts)

    def start_project(self, project_name: str) -> None:
        """Transition project to RUNNING and initialize pipeline pointers.

        Args:
            project_name: Target project.
        """
        state = self._ensure_project_state(project_name)
        project = self._projects_engine.get_project(project_name)

        state.running_status = ExecutionStatus.RUNNING
        self._current_indices[project_name] = 0
        self._start_times[project_name] = time.time()

        active_tasks = [t for t in project.tasks if t.get("active", True)]
        if active_tasks:
            first_name = str(
                active_tasks[0].get("task_name") or active_tasks[0].get("name")
            )
            state.active_task = first_name
        else:
            state.active_task = None
            state.running_status = ExecutionStatus.FINISHED

        logger.info("Started project %s (active: %s)", project_name, state.active_task)

    def stop_project(self, project_name: str) -> None:
        """Halt execution of project and set status to STOPPED.

        Args:
            project_name: Target project.
        """
        state = self._ensure_project_state(project_name)
        state.running_status = ExecutionStatus.STOPPED
        state.active_task = None
        logger.info("Stopped project %s", project_name)

    def pause_project(self, project_name: str) -> None:
        """Pause execution of project at current task boundary.

        Args:
            project_name: Target project.
        """
        state = self._ensure_project_state(project_name)
        state.running_status = ExecutionStatus.PAUSED
        logger.info("Paused project %s", project_name)

    def get_project_status(self, project_name: str) -> ProjectExecutionState:
        """Retrieve current execution state of a project.

        Args:
            project_name: Target project.

        Returns:
            ProjectExecutionState snapshot.
        """
        return self._ensure_project_state(project_name)

    def get_custom_project_stats(self) -> list[dict[str, Any]]:
        """Return execution stats matching TaskManagerProgressPublisher."""
        stats: list[dict[str, Any]] = []
        for summary in self._projects_engine.list_projects():
            if summary.is_app_project:
                continue
            state = self._ensure_project_state(summary.project_name)
            stats.append(state.to_dict())
        return stats

    def _evaluate_single_condition(
        self, project_name: str, cond: dict[str, Any], task_name: str
    ) -> bool:
        """Evaluate one condition dictionary against engine state."""
        cond_type = cond.get("type", "")
        comparator = str(cond.get("comparator", "<"))

        if cond_type == "CyclesCount":
            cycles = self._project_cycles.get(project_name, 0)
            threshold = int(cond.get("number", 100))
            return RunCyclesCondition.evaluate(
                cycles, comparator=comparator, number=threshold
            ).met

        if cond_type == "RunTime":
            elapsed_sec = time.time() - self._start_times.get(project_name, time.time())
            elapsed_ms = int(elapsed_sec * 1000)
            minutes = int(cond.get("minutes", 120))
            return RuntimeCondition.evaluate(
                elapsed_ms, comparator=comparator, minutes=minutes
            ).met

        if cond_type == "ResultsCount":
            databank_counts = self._databank_counts.get(project_name, {})
            databank = str(cond.get("databank", "Results"))
            threshold = int(cond.get("number", 100))
            return ResultsCountCondition.evaluate(
                databank_counts,
                comparator=comparator,
                number=threshold,
                databank=databank,
            ).met

        if cond_type == "GoToActivated":
            activated = self._activated_cycles.get(project_name, {}).get(task_name, 0)
            threshold = int(cond.get("number", 100))
            return GoToActivatedCondition.evaluate(
                activated, comparator=comparator, number=threshold
            ).met

        if cond_type == "GoToEvaluated":
            evaluated = self._evaluated_cycles.get(project_name, {}).get(task_name, 0)
            threshold = int(cond.get("number", 100))
            return GoToEvaluatedCondition.evaluate(
                evaluated, comparator=comparator, number=threshold
            ).met

        # Unknown condition defaults to True
        return True

    def _evaluate_conditions(
        self,
        project_name: str,
        conditions: list[dict[str, Any]],
        task_name: str,
    ) -> bool:
        """Evaluate a list of conditions (conjunction AND)."""
        for cond in conditions:
            if not self._evaluate_single_condition(project_name, cond, task_name):
                return False
        return True

    def _increment_task_iterations(
        self, state: ProjectExecutionState, task_name: str
    ) -> None:
        """Increment iterations counter for the specified task."""
        for rec in state.tasks_iterations:
            if rec.task_name == task_name:
                rec.iterations += 1
                return
        state.tasks_iterations.append(
            TaskIterationRecord(task_name=task_name, iterations=1)
        )

    def _handle_goto_task(
        self,
        project_name: str,
        task: dict[str, Any],
        task_name: str,
        tasks: list[dict[str, Any]],
    ) -> int:
        """Evaluate GoToTask logic and return next task index."""
        eval_map = self._evaluated_cycles.setdefault(project_name, {})
        eval_map[task_name] = eval_map.get(task_name, 0) + 1

        cfg = task.get("config", {})
        conditions = cfg.get("conditions", [])
        target_name = cfg.get("task", "")

        conditions_met = self._evaluate_conditions(project_name, conditions, task_name)
        if conditions_met and target_name:
            act_map = self._activated_cycles.setdefault(project_name, {})
            act_map[task_name] = act_map.get(task_name, 0) + 1

        cur_idx = self._current_indices.get(project_name, 0)
        res = GoToTaskCoordinator.evaluate_jump(
            task_name=task_name,
            target_task_name=target_name,
            conditions_met=conditions_met,
            current_index=cur_idx,
            tasks_list=tasks,
            task_log_prefix=f"[{project_name}] ",
        )
        return res.next_index

    def _dispatch_portfolio_task(
        self, task_type: str, cfg: dict[str, Any], prefix: str
    ) -> None:
        """Dispatch portfolio-related tasks."""
        if task_type == "ApplyMassConfig":
            ApplyMassConfigTask.run(
                str(cfg.get("targetDatabank", "Results")),
                str(cfg.get("configType", "default")),
                dict(cfg.get("parameters", {})),
                task_log_prefix=prefix,
            )
        elif task_type == "AutomaticPortfolioBuilder":
            AutomaticPortfolioBuilderTask.run(
                str(cfg.get("sourceDatabank", "Results")),
                str(cfg.get("targetDatabank", "Portfolio")),
                int(cfg.get("portfolioSize", 5)),
                float(cfg.get("correlationThreshold", 0.7)),
                str(cfg.get("rankingMethod", "SharpeRatio")),
                task_log_prefix=prefix,
            )
        elif task_type == "AutomaticRetest":
            AutomaticRetestTask.run(
                str(cfg.get("databank", "Results")),
                str(cfg.get("retestProfile", "Default")),
                bool(cfg.get("filterResults", True)),
                bool(cfg.get("saveToTargetDatabank", False)),
                str(cfg.get("targetDatabank", "")),
                task_log_prefix=prefix,
            )
        elif task_type == "CreatePortfolio":
            CreatePortfolioTask.run(
                str(cfg.get("sourceDatabank", "Results")),
                str(cfg.get("portfolioName", "MyPortfolio")),
                str(cfg.get("selectionMode", "all")),
                int(cfg.get("topN", 10)),
                task_log_prefix=prefix,
            )

    def _dispatch_databank_task(
        self,
        task_type: str,
        cfg: dict[str, Any],
        prefix: str,
        project_name: str,
        task_name: str,
    ) -> None:
        """Dispatch databank operations."""
        if task_type == "ClearDatabanks":
            ClearDatabanksTask.run(
                list(cfg.get("databanks", ["Results"])),
                project_name=project_name,
                task_title=task_name,
                task_log_prefix=prefix,
                project=_DefaultClearProject(),
                progress=_DefaultClearProgress(),
            )
        elif task_type == "DeleteFile":
            DeleteFileTask.run(
                str(cfg.get("file", "") or cfg.get("filePath", "")),
                task_log_prefix=prefix,
                files=_DefaultFileOperations(),
                progress=_DefaultDeleteProgress(),
            )
        elif task_type == "Filtering":
            FilteringTask.run(
                str(cfg.get("sourceDatabank", "Results")),
                str(cfg.get("targetDatabank", "Filtered")),
                list(cfg.get("filterConditions", [])),
                task_log_prefix=prefix,
            )
        elif task_type == "LogDatabankStats":
            LogDatabankStatsTask.run(
                str(cfg.get("databank", "Results")),
                list(cfg.get("metrics", ["count"])),
                str(cfg.get("logLevel", "INFO")),
                task_log_prefix=prefix,
            )

    def _dispatch_external_task(
        self,
        task_type: str,
        cfg: dict[str, Any],
        prefix: str,
        project_name: str,
        task_name: str,
    ) -> None:
        """Dispatch external I/O and notification tasks."""
        if task_type == "CallExternalScript":
            CallExternalScriptTask.run(
                str(cfg.get("scriptPath", "")),
                list(cfg.get("arguments", [])),
                str(cfg.get("workingDirectory", "")),
                int(cfg.get("timeoutSeconds", 300)),
                bool(cfg.get("failOnError", True)),
                task_log_prefix=prefix,
            )
        elif task_type == "CustomAnalysis":
            CustomAnalysisTask.run(
                str(cfg.get("snippetName", "")),
                str(cfg.get("targetDatabank", "Results")),
                dict(cfg.get("parameters", {})),
                task_log_prefix=prefix,
            )
        elif task_type == "LoadFromFiles":
            LoadFromFilesTask.run(
                str(cfg.get("directoryPath", "")),
                str(cfg.get("filePattern", "*.sqx")),
                str(cfg.get("targetDatabank", "Results")),
                bool(cfg.get("clearBeforeLoad", False)),
                task_log_prefix=prefix,
            )
        elif task_type == "Notification":
            NotificationTask.run(
                str(cfg.get("channel", "email")),
                str(cfg.get("recipient", "")),
                str(cfg.get("subject", "Task Finished")),
                str(cfg.get("messageTemplate", "Project {projectName} finished.")),
                {"projectName": project_name, "taskName": task_name},
                task_log_prefix=prefix,
            )
        elif task_type == "SaveToFiles":
            SaveToFilesTask.run(
                str(cfg.get("sourceDatabank", "Results")),
                str(cfg.get("outputDirectory", "exports")),
                str(cfg.get("fileFormat", "sqx")),
                bool(cfg.get("saveAll", True)),
                task_log_prefix=prefix,
            )
        elif task_type == "UpdateData":
            UpdateDataTask.run(
                str(cfg.get("symbol", "EURUSD")),
                str(cfg.get("timeframe", "H1")),
                str(cfg.get("dataProvider", "Default")),
                bool(cfg.get("cleanHistory", False)),
                task_log_prefix=prefix,
            )

    def _execute_task_behavior(
        self,
        project_name: str,
        task: dict[str, Any],
        cur_idx: int,
        tasks: list[dict[str, Any]],
        *,
        state: ProjectExecutionState,
    ) -> tuple[int, bool]:
        """Dispatch task-specific behavior and return (next_index, should_continue)."""
        task_name = str(task.get("task_name") or task.get("name"))
        task_type = str(task.get("task_type") or task.get("type"))
        cfg = task.get("config", {})
        prefix = f"[{project_name}] "

        if task_type == "GoToTask":
            return self._handle_goto_task(project_name, task, task_name, tasks), True

        if task_type == "WaitFor":
            action = str(cfg.get("action", "user"))
            file_path = str(cfg.get("file", ""))
            res = WaitForTaskCoordinator.run(
                action=action,
                file_path=file_path,
                task_log_prefix=prefix,
            )
            if res.should_pause:
                state.running_status = ExecutionStatus.PAUSED
                logger.info(
                    "Project %s paused at WaitFor task '%s'",
                    project_name,
                    task_name,
                )
                return cur_idx + 1, False
            return cur_idx + 1, True

        if task_type == "StopAndStart":
            conditions = cfg.get("conditions", [])
            met = self._evaluate_conditions(project_name, conditions, task_name)
            action = str(cfg.get("action", "stop"))
            target_proj = str(cfg.get("targetProject", "") or cfg.get("project", ""))
            StopAndStartTaskCoordinator.run(
                action=action,
                target_project=target_proj,
                conditions_met=met,
                task_log_prefix=prefix,
            )
            if met and action == "stop":
                state.running_status = ExecutionStatus.STOPPED
                state.active_task = None
                return cur_idx + 1, False
            return cur_idx + 1, True

        self._dispatch_portfolio_task(task_type, cfg, prefix)
        self._dispatch_databank_task(task_type, cfg, prefix, project_name, task_name)
        self._dispatch_external_task(task_type, cfg, prefix, project_name, task_name)

        return cur_idx + 1, True

    def step_project(self, project_name: str) -> bool:
        """Execute a single task step in the project pipeline.

        Returns:
            True if execution continues; False if pipeline finished, stopped, or paused.
        """
        state = self._ensure_project_state(project_name)
        if state.running_status != ExecutionStatus.RUNNING:
            return False

        project = self._projects_engine.get_project(project_name)
        tasks = project.tasks
        if not tasks:
            state.running_status = ExecutionStatus.FINISHED
            state.active_task = None
            return False

        cur_idx = self._current_indices.get(project_name, 0)
        while cur_idx < len(tasks) and not tasks[cur_idx].get("active", True):
            cur_idx += 1

        if cur_idx >= len(tasks):
            self._project_cycles[project_name] = (
                self._project_cycles.get(project_name, 0) + 1
            )
            state.running_status = ExecutionStatus.FINISHED
            state.active_task = None
            logger.info("Project %s completed all tasks", project_name)
            return False

        task = tasks[cur_idx]
        task_name = str(task.get("task_name") or task.get("name"))
        state.active_task = task_name

        self._increment_task_iterations(state, task_name)

        next_idx, cont = self._execute_task_behavior(
            project_name, task, cur_idx, tasks, state=state
        )
        if not cont:
            return False

        # Advance past any inactive tasks for the next step
        while next_idx < len(tasks) and not tasks[next_idx].get("active", True):
            next_idx += 1

        self._current_indices[project_name] = next_idx
        if next_idx < len(tasks):
            state.active_task = str(
                tasks[next_idx].get("task_name") or tasks[next_idx].get("name")
            )
            return True

        # Reached the end of the task list
        self._project_cycles[project_name] = (
            self._project_cycles.get(project_name, 0) + 1
        )
        state.running_status = ExecutionStatus.FINISHED
        state.active_task = None
        logger.info("Project %s completed all tasks", project_name)
        return False

    def run_pipeline(self, project_name: str, max_steps: int = 100) -> int:
        """Run project pipeline continuously up to max_steps or completion."""
        steps = 0
        while steps < max_steps and self.step_project(project_name):
            steps += 1
        return steps
