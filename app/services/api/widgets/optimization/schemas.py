"""Optimization gateway request schemas."""

from collections.abc import Mapping

from pydantic import Field

from app.services.api.contracts.models import _BaseApiContract


class OptimizationParameterSweepRequest(_BaseApiContract):
    """Serialized API projection of one Optimization ``SearchRequest``.

    The bridge reconstructs the strict Optimization-owned request through the
    Optimization package-root value factory; the serialized payload is
    validated only for non-emptiness and bounded size at the API boundary.
    """

    request_id: str
    payload: Mapping[str, object]


class OptimizationWalkForwardRequest(_BaseApiContract):
    """Serialized API projection of one Optimization ``WalkForwardRequest``."""

    request_id: str
    payload: Mapping[str, object]


class OptimizationWalkForwardMatrixRequest(_BaseApiContract):
    """Serialized API projection of a bounded walk-forward matrix request."""

    request_id: str
    requests: tuple[Mapping[str, object], ...]
    max_requests: int = Field(ge=1, le=20)


class OptimizationRobustnessRequest(_BaseApiContract):
    """Serialized API projection of one Optimization robustness request.

    The Optimization robustness contract is a discriminated union of
    ``MonteCarloRequest`` and ``ExecutionStressAnalysisRequest``. The presence
    of the ``stress`` field in ``payload`` selects the stress variant; the
    bridge reconstructs the correct owner value.
    """

    request_id: str
    payload: Mapping[str, object]
    max_simulations: int = Field(default=2000, ge=1, le=10_000)


class OptimizationCompareRequest(_BaseApiContract):
    """Serialized API projection of one Optimization comparison request."""

    request_id: str
    results: tuple[Mapping[str, object], ...]


class OptimizationStabilityRequest(_BaseApiContract):
    """Serialized API projection of one parameter-stability request."""

    request_id: str
    ranked_candidates: tuple[Mapping[str, object], ...]


class OptimizationOverfitRequest(_BaseApiContract):
    """Serialized API projection of one overfit-parameter evidence request."""

    request_id: str
    in_sample: Mapping[str, float]
    out_of_sample: Mapping[str, float]
    threshold: float


class OptimizationRankRequest(_BaseApiContract):
    """Serialized API projection of one parameter-set ranking request."""

    request_id: str
    candidates: tuple[Mapping[str, object], ...]


class OptimizationRobustnessScoreRequest(_BaseApiContract):
    """Serialized API projection of one robustness-score request."""

    request_id: str
    checks: tuple[bool, ...]


class OptimizationHandoffRequest(_BaseApiContract):
    """Serialized API projection of one Optimization evidence handoff request."""

    request_id: str
    payload: Mapping[str, object]


__all__ = (
    "OptimizationCompareRequest",
    "OptimizationHandoffRequest",
    "OptimizationOverfitRequest",
    "OptimizationParameterSweepRequest",
    "OptimizationRankRequest",
    "OptimizationRobustnessRequest",
    "OptimizationRobustnessScoreRequest",
    "OptimizationStabilityRequest",
    "OptimizationWalkForwardMatrixRequest",
    "OptimizationWalkForwardRequest",
)
