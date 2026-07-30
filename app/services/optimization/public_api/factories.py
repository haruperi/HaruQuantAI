"""Function-only construction and inspection boundary for Optimization values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, cast

from pydantic import BaseModel

from app.services.optimization.evidence.contracts import (
    EvidenceAssemblyRequest,
    OptimizationResult,
)
from app.services.optimization.execution.contracts import (
    BacktestExecutionContext,
    BacktestExecutionRequest,
    EngineOptimizationResult,
)
from app.services.optimization.parameters.contracts import (
    ParameterRange,
    ParameterSpace,
)
from app.services.optimization.public_api.contracts import (
    ExecutionStressAnalysisRequest,
    OptimizationComparison,
    OverfitParameterEvidence,
    ParameterStabilityEvidence,
    RobustnessAnalysisResult,
    RobustnessScore,
)
from app.services.optimization.robustness.contracts import (
    ExecutionStressRequest,
    MonteCarloRequest,
    MonteCarloResult,
)
from app.services.optimization.scoring.contracts import CandidateScore
from app.services.optimization.search.contracts import (
    CandidateResult,
    SearchRequest,
    SearchSummary,
)
from app.services.optimization.state.contracts import (
    OptimizationCheckpoint,
    OptimizationPersistenceReceipt,
)
from app.services.optimization.validation.contracts import (
    TimeSeriesSplit,
    WalkForwardFoldResult,
    WalkForwardRequest,
    WalkForwardResult,
)

_VALUE_TYPES: Mapping[str, type[BaseModel]] = {
    model.__name__: model
    for model in (
        BacktestExecutionContext,
        BacktestExecutionRequest,
        CandidateResult,
        CandidateScore,
        EngineOptimizationResult,
        EvidenceAssemblyRequest,
        ExecutionStressAnalysisRequest,
        ExecutionStressRequest,
        MonteCarloRequest,
        MonteCarloResult,
        OptimizationCheckpoint,
        OptimizationComparison,
        OptimizationPersistenceReceipt,
        OptimizationResult,
        OverfitParameterEvidence,
        ParameterRange,
        ParameterSpace,
        ParameterStabilityEvidence,
        RobustnessAnalysisResult,
        RobustnessScore,
        SearchRequest,
        SearchSummary,
        TimeSeriesSplit,
        WalkForwardFoldResult,
        WalkForwardRequest,
        WalkForwardResult,
    )
}


def create_optimization_value(value_type: str, /, **fields: object) -> object:
    """Create one documented opaque Optimization value.

    Args:
        value_type: Registered Optimization contract name.
        **fields: Contract fields validated by the owning model.

    Returns:
        Validated opaque Optimization value.

    Raises:
        ValueError: If ``value_type`` is not a registered public value contract.
    """
    model = _VALUE_TYPES.get(value_type)
    if model is None:
        message = f"Unknown Optimization value type: {value_type}"
        raise ValueError(message)
    return model.model_validate(fields)


def dump_optimization_value(value: object) -> dict[str, object]:
    """Return a bounded Python mapping for an opaque Optimization value.

    Args:
        value: Value returned by the Optimization public API.

    Returns:
        Public fields represented as ordinary Python values.

    Raises:
        ValueError: If ``value`` is not a registered Optimization value.
    """
    if isinstance(value, BaseModel) and type(value) in _VALUE_TYPES.values():
        return value.model_dump(mode="python", warnings=False)
    if is_dataclass(value) and type(value).__module__.startswith(
        "app.services.optimization."
    ):
        return cast("dict[str, object]", asdict(cast("Any", value)))
    raise ValueError("Value is not a registered Optimization value")


def get_optimization_value_field(value: object, field: str) -> object:
    """Return one public field from an opaque Optimization value.

    Args:
        value: Value returned by the Optimization public API.
        field: Non-private contract field name.

    Returns:
        The requested field value.

    Raises:
        ValueError: If the value or requested field is not public.
    """
    if not is_optimization_value(value) or not field or field.startswith("_"):
        raise ValueError("Optimization value does not expose the requested field")
    if not hasattr(value, field):
        raise ValueError("Optimization value does not expose the requested field")
    return getattr(value, field)


def is_optimization_value(value: object, value_type: str | None = None) -> bool:
    """Return whether a value is a registered Optimization contract.

    Args:
        value: Candidate opaque value.
        value_type: Optional registered contract name.

    Returns:
        Whether the candidate matches the requested Optimization contract.
    """
    if value_type is not None:
        model = _VALUE_TYPES.get(value_type)
        return isinstance(value, model) if model is not None else False
    return (
        isinstance(value, tuple(_VALUE_TYPES.values()))
        or (
            is_dataclass(value)
            and type(value).__module__.startswith("app.services.optimization.")
        )
        or (
            isinstance(value, Enum)
            and type(value).__module__.startswith("app.services.optimization.")
        )
    )
