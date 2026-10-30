"""Task manager workspace package.

Description:
    Core workspace package providing project lifecycle management, task graph
    manipulation, pipeline execution runtime, and condition checking.
"""

from __future__ import annotations

from app.workspace.task_manager.app_task_manager import AppTaskManager
from app.workspace.task_manager.app_task_manager_models import (
    ExecutionStatus,
    ProjectExecutionState,
    TaskIterationRecord,
)
from app.workspace.task_manager.routes import task_manager_router
from app.workspace.task_manager.task_manager_projects import (
    TaskManagerProjects,
    normalize_project_name,
    validate_project_name,
)
from app.workspace.task_manager.task_manager_projects_models import (
    ModifySymbolItem,
    ProjectInfo,
    ProjectSummary,
    ProjectValidationResult,
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
from app.workspace.task_manager.wait_for_settings import (
    WaitForConfig,
    WaitForSettings,
)

__all__ = [
    "AppTaskManager",
    "AvailableTask",
    "ExecutionStatus",
    "ModifySymbolItem",
    "ProjectExecutionState",
    "ProjectInfo",
    "ProjectSummary",
    "ProjectValidationResult",
    "TaskActivateRequest",
    "TaskCloneRequest",
    "TaskConfig",
    "TaskIterationRecord",
    "TaskManagerProjects",
    "TaskManagerTasks",
    "TaskMoveRequest",
    "TaskRenameRequest",
    "WaitForConfig",
    "WaitForSettings",
    "normalize_project_name",
    "task_manager_router",
    "validate_project_name",
]
