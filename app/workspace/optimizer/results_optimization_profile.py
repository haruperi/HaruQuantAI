"""Optimization Profile results view and surface projection service.

Description:
    Implements ResultsOptimizationProfileService projecting 1D, 2D, and 3D parameter
    sensitivity surfaces, chart grid matrices, run tables, and CSV exports.

Purpose:
    FEAT-RESULTS-OPTIMIZATION-PROFILE: Optimization profile results projection.

Key Capabilities:
    - FR-optimizer-profile-chart-grid: Project 2D/3D parameter surface grid matrix.
    - FR-optimizer-profile-table: Retrieve paginated or full optimization runs.
    - FR-optimizer-profile-export: Export optimization runs to CSV format.

Python API Usage:
    from app.workspace.optimizer.results_optimization_profile import (
        ResultsOptimizationProfileService,
    )
    service = ResultsOptimizationProfileService()
    grid = service.get_chart_grid("Strat_01", param_x="Period", param_y="Multiplier")

CLI Usage:
    python -m app.cli optimizer export-profile --strategy-id Strat_01
"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.optimizer.common import wrap_response

logger = get_logger(__name__)
_PROFILE_PAGE_SIZE = 1000


@dataclass(frozen=True, slots=True)
class OptimizationRunRow:
    """Single optimization parameter evaluation run."""

    run_index: int
    parameters: dict[str, float | int]
    metrics: dict[str, float]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert run row to dictionary."""
        return {
            "run_index": self.run_index,
            "parameters": dict(self.parameters),
            "metrics": dict(self.metrics),
            "passed": self.passed,
        }


@dataclass(frozen=True, slots=True)
class OptimizationProfileChartGrid:
    """2D/3D chart grid matrix for parameter sensitivity."""

    param_x: str
    param_y: str | None
    metric: str
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    z_matrix: tuple[tuple[float | None, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert chart grid to dictionary."""
        return {
            "param_x": self.param_x,
            "param_y": self.param_y,
            "metric": self.metric,
            "x_values": list(self.x_values),
            "y_values": list(self.y_values),
            "z_matrix": [list(row) for row in self.z_matrix],
        }


class ResultsOptimizationProfileService:
    """Service projecting parameter sensitivity profiles and surface charts."""

    def __init__(self, result_store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore.

        Args:
            result_store: Injected Core result owner; absent authority fails closed.
        """
        self._result_store = result_store
        self._views: dict[str, dict[str, Any]] = {
            "default": {
                "id": "default",
                "name": "Default 2D Profile",
                "param_x": "Period",
                "param_y": "Multiplier",
                "metric": "NetProfit",
            }
        }
        self._mock_runs: dict[str, list[OptimizationRunRow]] = {}

    def set_mock_runs(self, strategy_id: str, runs: list[OptimizationRunRow]) -> None:
        """Set in-memory runs for strategy testing."""
        self._mock_runs[strategy_id] = runs

    def list_views(self) -> list[dict[str, Any]]:
        """List registered optimization profile views."""
        return list(self._views.values())

    def add_view(
        self, name: str, param_x: str, param_y: str | None, metric: str = "NetProfit"
    ) -> dict[str, Any]:
        """Add new profile view definition."""
        view_id = str(uuid.uuid4())
        view = {
            "id": view_id,
            "name": name,
            "param_x": param_x,
            "param_y": param_y,
            "metric": metric,
        }
        self._views[view_id] = view
        logger.info("Added optimization profile view: %s (%s)", name, view_id)
        return view

    def update_view(self, view_id: str, **updates: Any) -> dict[str, Any]:
        """Update existing view definition."""
        if view_id not in self._views:
            raise DomainError(
                code="OPTIMIZER_VIEW_NOT_FOUND", message=f"View not found: {view_id}"
            )
        self._views[view_id].update(updates)
        return self._views[view_id]

    def remove_view(self, view_id: str) -> bool:
        """Remove view definition by ID."""
        if view_id == "default":
            raise DomainError(
                code="OPTIMIZER_DEFAULT_VIEW_PROTECTED",
                message="Cannot remove default view",
            )
        return self._views.pop(view_id, None) is not None

    def _get_runs_for_strategy(self, strategy_id: str) -> list[OptimizationRunRow]:
        """Retrieve runs from mock cache or result store metadata."""
        if strategy_id in self._mock_runs:
            return self._mock_runs[strategy_id]

        store = self._result_store
        if store is None:
            raise DomainError(
                code="RESULT_STORE_UNAVAILABLE",
                message="Inject the shared result store",
            )
        try:
            selected = store.get_result(strategy_id)
        except DomainError as error:
            if error.code != "RESULT_NOT_FOUND":
                raise
            logger.info("FR-optimizer-profile-results: selected result is unavailable")
            return []
        records = self._run_results(store, selected)
        runs: list[OptimizationRunRow] = []
        for index, result in enumerate(records):
            raw = result.parameters.get("parameters", {})
            parameters = (
                {
                    key: float(value)
                    for key, value in raw.items()
                    if isinstance(value, (int, float))
                }
                if isinstance(raw, dict)
                else {}
            )
            metrics = {
                key: float(value)
                for key, value in result.metrics.items()
                if isinstance(value, (int, float))
            }
            if "net_profit" in metrics:
                metrics["NetProfit"] = metrics["net_profit"]
            runs.append(OptimizationRunRow(index + 1, parameters, metrics, True))
        logger.info(
            "FR-optimizer-profile-results: projected %d stored evaluations", len(runs)
        )
        return runs

    @staticmethod
    def _run_results(store: ResultStore, selected: RunResult) -> list[RunResult]:
        """Read all parameter evaluations sharing the selected stored run identity."""
        run_id = selected.parameters.get("run_id")
        records = [selected]
        if run_id:
            records = []
            offset = 0
            while True:
                page = store.list_results(
                    selected.databank_id, limit=_PROFILE_PAGE_SIZE, offset=offset
                )
                for summary in page:
                    result = store.get_result(summary.result_id)
                    if result.parameters.get("run_id") == run_id:
                        records.append(result)
                if len(page) < _PROFILE_PAGE_SIZE:
                    break
                offset += len(page)
        return records

    def get_available_params(self, strategy_id: str) -> tuple[str, ...]:
        """Get parameter names available in strategy optimization runs."""
        runs = self._get_runs_for_strategy(strategy_id)
        if not runs:
            return ()
        params = sorted(runs[0].parameters.keys())
        return tuple(params)

    def get_chart_grid(
        self,
        strategy_id: str,
        *,
        param_x: str,
        param_y: str | None = None,
        metric: str = "NetProfit",
    ) -> StandardResponse[OptimizationProfileChartGrid]:
        """Compute 1D or 2D parameter grid with metric z-matrix.

        Args:
            strategy_id: Strategy identifier.
            param_x: X-axis parameter name.
            param_y: Optional Y-axis parameter name.
            metric: Target metric to map on Z-axis.

        Returns:
            StandardResponse containing OptimizationProfileChartGrid.
        """
        runs = self._get_runs_for_strategy(strategy_id)
        x_vals_set: set[float] = set()
        y_vals_set: set[float] = set()
        lookup: dict[tuple[float, float | None], float] = {}

        for r in runs:
            px = float(r.parameters.get(param_x, 0.0))
            x_vals_set.add(px)
            py = float(r.parameters.get(param_y, 0.0)) if param_y else None
            if py is not None:
                y_vals_set.add(py)
            val = float(r.metrics.get(metric, 0.0))
            lookup[(px, py)] = val

        x_sorted = tuple(sorted(x_vals_set))
        y_sorted = tuple(sorted(y_vals_set)) if param_y else (0.0,)

        matrix_rows: list[tuple[float | None, ...]] = []
        if param_y:
            for y in y_sorted:
                row = tuple(lookup.get((x, y)) for x in x_sorted)
                matrix_rows.append(row)
        else:
            row = tuple(lookup.get((x, None)) for x in x_sorted)
            matrix_rows.append(row)

        grid = OptimizationProfileChartGrid(
            param_x=param_x,
            param_y=param_y,
            metric=metric,
            x_values=x_sorted,
            y_values=y_sorted if param_y else (),
            z_matrix=tuple(matrix_rows),
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_chart_grid",
            data=grid,
            json_payload=grid.to_dict(),
        )

    def get_results_table(
        self, strategy_id: str
    ) -> StandardResponse[tuple[OptimizationRunRow, ...]]:
        """Retrieve full table of optimization runs."""
        runs = tuple(self._get_runs_for_strategy(strategy_id))
        return wrap_response(
            request_id=f"req_{strategy_id}_results_table",
            data=runs,
            json_payload=[r.to_dict() for r in runs],
        )

    def export_csv(self, strategy_id: str) -> str:
        """Export optimization runs for strategy to CSV formatted string."""
        runs = self._get_runs_for_strategy(strategy_id)
        if not runs:
            return "run_index,passed\n"

        param_names = sorted(runs[0].parameters.keys())
        metric_names = sorted(runs[0].metrics.keys())

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        header = ["run_index", *param_names, *metric_names, "passed"]
        writer.writerow(header)

        for r in runs:
            row_data: list[Any] = [
                r.run_index,
                *(r.parameters.get(p, "") for p in param_names),
                *(r.metrics.get(m, "") for m in metric_names),
                r.passed,
            ]
            writer.writerow(row_data)

        return output.getvalue()
