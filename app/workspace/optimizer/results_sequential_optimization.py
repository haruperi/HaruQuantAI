"""Sequential Optimization results view and parameter application service.

Description:
    Implements ResultsSequentialOptimizationService projecting sequential parameter
    optimization curves, best candidate parameter selections, and updating nominal
    parameter values back to strategy documents and databank records.

Purpose:
    FEAT-RESULTS-SEQUENTIAL-OPTIMIZATION: Sequential optimization.

Key Capabilities:
    - FR-results-seq-curves: Retrieve step-by-step sequential optimization curves.
    - FR-results-seq-apply: Apply optimized parameter coordinates to strategy documents.

Python API Usage:
    from app.workspace.optimizer.results_sequential_optimization import (
        ResultsSequentialOptimizationService,
    )
    service = ResultsSequentialOptimizationService()
    resp = service.apply_params("proj_1", "Results", "Strat_01", {"Period": 25})

CLI Usage:
    python -m app.cli optimizer apply-seq-params --strategy-id Strat_01
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse
from app.workspace.optimizer.common import wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SequentialOptStepProjection:
    """Projection of single parameter optimization curve."""

    param_name: str
    original_value: float | int
    best_value: float | int
    tested_values: tuple[float, ...]
    metric_values: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert step projection to dictionary."""
        return {
            "param_name": self.param_name,
            "original_value": self.original_value,
            "best_value": self.best_value,
            "tested_values": list(self.tested_values),
            "metric_values": list(self.metric_values),
        }


@dataclass(frozen=True, slots=True)
class SequentialOptResultsPayload:
    """Payload containing all sequential optimization steps for a strategy."""

    strategy_id: str
    fitness_metric: str
    original_metric: float
    optimized_metric: float
    steps: tuple[SequentialOptStepProjection, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "fitness_metric": self.fitness_metric,
            "original_metric": self.original_metric,
            "optimized_metric": self.optimized_metric,
            "steps": [s.to_dict() for s in self.steps],
        }


class ResultsSequentialOptimizationService:
    """Service projecting sequential optimization curves and applying parameters."""

    def __init__(self) -> None:
        """Initialize service with in-memory payload and parameter stores."""
        self._payloads: dict[str, SequentialOptResultsPayload] = {}
        self._strategy_params: dict[str, dict[str, float | int]] = {}

    def set_mock_payload(
        self, strategy_id: str, payload: SequentialOptResultsPayload
    ) -> None:
        """Register sequential optimization results for a strategy."""
        self._payloads[strategy_id] = payload

    def get_results(
        self, strategy_id: str
    ) -> StandardResponse[SequentialOptResultsPayload]:
        """Retrieve sequential optimization results and curves.

        Args:
            strategy_id: Identifier of the strategy.

        Returns:
            StandardResponse containing SequentialOptResultsPayload.
        """
        payload = self._payloads.get(strategy_id)
        if payload is None:
            # Return empty default payload
            payload = SequentialOptResultsPayload(
                strategy_id=strategy_id,
                fitness_metric="NetProfit",
                original_metric=0.0,
                optimized_metric=0.0,
                steps=(),
            )

        logger.info(
            "Retrieved sequential optimization results for %s (%d steps)",
            strategy_id,
            len(payload.steps),
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_seq_results",
            data=payload,
            json_payload=payload.to_dict(),
        )

    def apply_params(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        params: Mapping[str, float | int],
    ) -> StandardResponse[dict[str, float | int]]:
        """Apply optimal parameter values back to the strategy.

        Args:
            project_id: Project identifier.
            databank_name: Databank containing the strategy.
            strategy_id: Strategy identifier.
            params: Dictionary of parameter names and chosen values.

        Returns:
            StandardResponse containing updated dictionary of strategy parameters.
        """
        if strategy_id not in self._strategy_params:
            self._strategy_params[strategy_id] = {}

        for k, v in params.items():
            self._strategy_params[strategy_id][k] = v

        updated_map = dict(self._strategy_params[strategy_id])
        logger.info(
            "Applied %d parameters for %s in %s/%s: %s",
            len(params),
            strategy_id,
            project_id,
            databank_name,
            updated_map,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_apply_params",
            data=updated_map,
            json_payload=updated_map,
        )
