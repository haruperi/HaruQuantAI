"""Task manager settings package.

Description:
    Aggregates all task configuration serialization and parsing modules
    for the Task Manager automation engine.
"""

from __future__ import annotations

from app.workspace.task_manager.settings.advanced_tm import (
    AdvancedTMConfig,
    AdvancedTMSettings,
)
from app.workspace.task_manager.settings.apply_mass_config import (
    ApplyMassConfigConfig,
    ApplyMassConfigSettings,
)
from app.workspace.task_manager.settings.automatic_portfolio_builder import (
    AutoPortfolioBuilderConfig,
    AutoPortfolioBuilderSettings,
)
from app.workspace.task_manager.settings.automatic_retest import (
    AutoRetestConfig,
    AutoRetestSettings,
)
from app.workspace.task_manager.settings.call_external_script import (
    CallExternalScriptConfig,
    CallExternalScriptSettings,
)
from app.workspace.task_manager.settings.clear_databanks import (
    ClearDatabanksConfig,
    ClearDatabanksSettings,
)
from app.workspace.task_manager.settings.create_portfolio import (
    CreatePortfolioConfig,
    CreatePortfolioSettings,
)
from app.workspace.task_manager.settings.custom_analysis import (
    CustomAnalysisConfig,
    CustomAnalysisSettings,
)
from app.workspace.task_manager.settings.delete_file import (
    DeleteFileConfig,
    DeleteFileSettings,
)
from app.workspace.task_manager.settings.filtering import (
    FilteringCondition,
    FilteringConfig,
    FilteringSettings,
)
from app.workspace.task_manager.settings.go_to_task import (
    GoToTaskConfig,
    GoToTaskSettings,
)
from app.workspace.task_manager.settings.load_from_files import (
    LoadFromFilesConfig,
    LoadFromFilesSettings,
)
from app.workspace.task_manager.settings.log_databank_stats import (
    LogDatabankStatsConfig,
    LogDatabankStatsSettings,
)
from app.workspace.task_manager.settings.notification import (
    NotificationConfig,
    NotificationSettings,
)
from app.workspace.task_manager.settings.save_to_files import (
    SaveToFilesConfig,
    SaveToFilesSettings,
)
from app.workspace.task_manager.settings.stop_and_start import (
    StopAndStartConfig,
    StopAndStartSettings,
)
from app.workspace.task_manager.settings.update_data import (
    UpdateDataConfig,
    UpdateDataSettings,
)
from app.workspace.task_manager.wait_for_settings import (
    WaitForConfig,
    WaitForSettings,
)

__all__ = [
    "AdvancedTMConfig",
    "AdvancedTMSettings",
    "ApplyMassConfigConfig",
    "ApplyMassConfigSettings",
    "AutoPortfolioBuilderConfig",
    "AutoPortfolioBuilderSettings",
    "AutoRetestConfig",
    "AutoRetestSettings",
    "CallExternalScriptConfig",
    "CallExternalScriptSettings",
    "ClearDatabanksConfig",
    "ClearDatabanksSettings",
    "CreatePortfolioConfig",
    "CreatePortfolioSettings",
    "CustomAnalysisConfig",
    "CustomAnalysisSettings",
    "DeleteFileConfig",
    "DeleteFileSettings",
    "FilteringCondition",
    "FilteringConfig",
    "FilteringSettings",
    "GoToTaskConfig",
    "GoToTaskSettings",
    "LoadFromFilesConfig",
    "LoadFromFilesSettings",
    "LogDatabankStatsConfig",
    "LogDatabankStatsSettings",
    "NotificationConfig",
    "NotificationSettings",
    "SaveToFilesConfig",
    "SaveToFilesSettings",
    "StopAndStartConfig",
    "StopAndStartSettings",
    "UpdateDataConfig",
    "UpdateDataSettings",
    "WaitForConfig",
    "WaitForSettings",
]
