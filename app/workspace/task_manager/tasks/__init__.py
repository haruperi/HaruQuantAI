"""Task coordinators package.

Description:
    Aggregates all concrete task coordinators and protocols for the Task Manager.
"""

from __future__ import annotations

from app.workspace.task_manager.tasks.apply_mass_config import (
    ApplyMassConfigResult,
    ApplyMassConfigTask,
)
from app.workspace.task_manager.tasks.automatic_portfolio_builder import (
    AutomaticPortfolioBuilderTask,
    AutoPortfolioResult,
)
from app.workspace.task_manager.tasks.automatic_retest import (
    AutomaticRetestTask,
    AutoRetestResult,
)
from app.workspace.task_manager.tasks.call_external_script import (
    CallExternalScriptTask,
    CallScriptResult,
)
from app.workspace.task_manager.tasks.clear_databanks import (
    ClearBank,
    ClearDatabanksTask,
    ClearProgress,
    ClearProject,
)
from app.workspace.task_manager.tasks.create_portfolio import (
    CreatePortfolioResult,
    CreatePortfolioTask,
)
from app.workspace.task_manager.tasks.custom_analysis import (
    CustomAnalysisResult,
    CustomAnalysisTask,
)
from app.workspace.task_manager.tasks.delete_file import (
    DeleteFileTask,
    DeleteProgress,
    FileOperations,
    TaskLogResult,
)
from app.workspace.task_manager.tasks.filtering import (
    FilteringResult,
    FilteringTask,
)
from app.workspace.task_manager.tasks.go_to_task import (
    GoToTaskCoordinator,
    GoToTaskResult,
)
from app.workspace.task_manager.tasks.load_from_files import (
    LoadFromFilesResult,
    LoadFromFilesTask,
)
from app.workspace.task_manager.tasks.log_databank_stats import (
    LogDatabankStatsResult,
    LogDatabankStatsTask,
)
from app.workspace.task_manager.tasks.notification import (
    NotificationTask,
    NotificationTaskResult,
)
from app.workspace.task_manager.tasks.save_to_files import (
    SaveToFilesResult,
    SaveToFilesTask,
)
from app.workspace.task_manager.tasks.stop_and_start import (
    StopAndStartResult,
    StopAndStartTaskCoordinator,
)
from app.workspace.task_manager.tasks.update_data import (
    UpdateDataResult,
    UpdateDataTask,
)
from app.workspace.task_manager.tasks.wait_for import (
    WaitForResult,
    WaitForTaskCoordinator,
)

__all__ = [
    "ApplyMassConfigResult",
    "ApplyMassConfigTask",
    "AutoPortfolioResult",
    "AutoRetestResult",
    "AutomaticPortfolioBuilderTask",
    "AutomaticRetestTask",
    "CallExternalScriptTask",
    "CallScriptResult",
    "ClearBank",
    "ClearDatabanksTask",
    "ClearProgress",
    "ClearProject",
    "CreatePortfolioResult",
    "CreatePortfolioTask",
    "CustomAnalysisResult",
    "CustomAnalysisTask",
    "DeleteFileTask",
    "DeleteProgress",
    "FileOperations",
    "FilteringResult",
    "FilteringTask",
    "GoToTaskCoordinator",
    "GoToTaskResult",
    "LoadFromFilesResult",
    "LoadFromFilesTask",
    "LogDatabankStatsResult",
    "LogDatabankStatsTask",
    "NotificationTask",
    "NotificationTaskResult",
    "SaveToFilesResult",
    "SaveToFilesTask",
    "StopAndStartResult",
    "StopAndStartTaskCoordinator",
    "TaskLogResult",
    "UpdateDataResult",
    "UpdateDataTask",
    "WaitForResult",
    "WaitForTaskCoordinator",
]
