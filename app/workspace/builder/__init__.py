"""AppBuilder workspace package.

Description:
    Exposes top-level Builder workspace services, configuration models,
    genetic algorithm defaults, building blocks configuration, ranking filters,
    multi-objective fitness evaluation, and execution runners.
"""

from __future__ import annotations

from app.workspace.builder.app_builder import AppBuilderService, BuilderWorkspaceState
from app.workspace.builder.fitness_method_strategy_result import (
    FitnessCriterion,
    FitnessMethodStrategyResultConfig,
    FitnessMethodStrategyResultService,
)
from app.workspace.builder.genetic_defaults import (
    GeneticOptions,
    GeneticOptionsDefaults,
)
from app.workspace.builder.improvement_labels import improvement_label
from app.workspace.builder.servlet_builder import ServletBuilderDispatcher
from app.workspace.builder.settings_blocks import (
    BlocksSelectionSettings,
    BuildingBlockSelection,
    SettingsBlocksService,
)
from app.workspace.builder.settings_genetic_options import (
    SettingsGeneticOptionsService,
)
from app.workspace.builder.settings_parts_to_improve import (
    PartImprovementRule,
    PartsToImproveSettings,
    SettingsPartsToImproveService,
)
from app.workspace.builder.settings_rankings import (
    RankingFilterCondition,
    RankingsSettings,
    SettingsRankingsService,
)
from app.workspace.builder.settings_what_to_build import (
    SettingsWhatToBuildService,
    WhatToBuildSettings,
)
from app.workspace.builder.task_build import (
    BarRecord,
    TaskBuildRunner,
    TaskBuildSummary,
)

__all__ = [
    "AppBuilderService",
    "BarRecord",
    "BlocksSelectionSettings",
    "BuilderWorkspaceState",
    "BuildingBlockSelection",
    "FitnessCriterion",
    "FitnessMethodStrategyResultConfig",
    "FitnessMethodStrategyResultService",
    "GeneticOptions",
    "GeneticOptionsDefaults",
    "PartImprovementRule",
    "PartsToImproveSettings",
    "RankingFilterCondition",
    "RankingsSettings",
    "ServletBuilderDispatcher",
    "SettingsBlocksService",
    "SettingsGeneticOptionsService",
    "SettingsPartsToImproveService",
    "SettingsRankingsService",
    "SettingsWhatToBuildService",
    "TaskBuildRunner",
    "TaskBuildSummary",
    "WhatToBuildSettings",
    "improvement_label",
]
