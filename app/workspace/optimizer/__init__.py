"""AppOptimizer workspace package.

Description:
    Exposes top-level AppOptimizerService, task runner, settings calculation,
    walk-forward fitness evaluation, labels, and results projections.
"""

from __future__ import annotations

from app.workspace.optimizer.app_optimizer import (
    AppOptimizerService,
    OptimizerStatus,
    OptimizerWorkspaceState,
)
from app.workspace.optimizer.common import wrap_response
from app.workspace.optimizer.fitness_method_w_f_result import (
    FitnessMethodWFResultConfig,
    FitnessMethodWFResultService,
    WFFitnessCriterion,
)
from app.workspace.optimizer.labels import OptimizationLabels
from app.workspace.optimizer.results_optimization_profile import (
    OptimizationProfileChartGrid,
    OptimizationRunRow,
    ResultsOptimizationProfileService,
)
from app.workspace.optimizer.results_sequential_optimization import (
    ResultsSequentialOptimizationService,
    SequentialOptResultsPayload,
    SequentialOptStepProjection,
)
from app.workspace.optimizer.results_sys_param_permutation import (
    ResultsSysParamPermutationService,
    SPPMetricSummaryRow,
    SPPResultsProjection,
)
from app.workspace.optimizer.results_walk_forward import (
    ResultsWalkForwardService,
    WalkForwardResultsProjection,
    WFMatrixCellResult,
    WFWindowResult,
)
from app.workspace.optimizer.settings_optimization import (
    OptimizableParameterSpec,
    OptimizationSettingsSnapshot,
    OptimizationType,
    ParameterType,
    PeriodType,
    SettingsOptimizationService,
)
from app.workspace.optimizer.task_optimize import (
    TaskOptimizeRunner,
    TaskOptimizeSummary,
    TaskOptimizeVerifier,
)
from app.workspace.optimizer.wf_metric import first_wf_metric

__all__ = [
    "AppOptimizerService",
    "FitnessMethodWFResultConfig",
    "FitnessMethodWFResultService",
    "OptimizableParameterSpec",
    "OptimizationLabels",
    "OptimizationProfileChartGrid",
    "OptimizationRunRow",
    "OptimizationSettingsSnapshot",
    "OptimizationType",
    "OptimizerStatus",
    "OptimizerWorkspaceState",
    "ParameterType",
    "PeriodType",
    "ResultsOptimizationProfileService",
    "ResultsSequentialOptimizationService",
    "ResultsSysParamPermutationService",
    "ResultsWalkForwardService",
    "SPPMetricSummaryRow",
    "SPPResultsProjection",
    "SequentialOptResultsPayload",
    "SequentialOptStepProjection",
    "SettingsOptimizationService",
    "TaskOptimizeRunner",
    "TaskOptimizeSummary",
    "TaskOptimizeVerifier",
    "WFFitnessCriterion",
    "WFMatrixCellResult",
    "WFWindowResult",
    "WalkForwardResultsProjection",
    "first_wf_metric",
    "wrap_response",
]
