"""Walk-Forward and Walk-Forward Matrix results view and projection service.

Description:
    Implements ResultsWalkForwardService projecting stitched OOS equity curves,
    walk-forward window results, matrix robustness heatmaps, and applying latest
    re-optimization window parameters.

Purpose:
    FEAT-RESULTS-WALK-FORWARD: Walk-Forward and Walk-Forward Matrix results projection.

Key Capabilities:
    - FR-wf-results-projection: Project stitched equity, windows, and matrix.
    - FR-wf-apply-latest-params: Write final window optimal parameters to strategy.
    - FR-wf-export-csv: Export walk-forward window and matrix data to CSV.

Python API Usage:
    from app.workspace.optimizer.results_walk_forward import ResultsWalkForwardService
    service = ResultsWalkForwardService()
    resp = service.get_projection("Strat_01")

CLI Usage:
    python -m app.cli optimizer wf-projection --strategy-id Strat_01
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
from app.workspace.optimizer.common import wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class WFWindowResult:
    """Evaluation result for single walk-forward window."""

    window_index: int
    is_start: str
    is_end: str
    oos_start: str
    oos_end: str
    best_params: dict[str, float | int | bool]
    is_net_profit: float
    oos_net_profit: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert window result to dictionary."""
        return {
            "window_index": self.window_index,
            "is_start": self.is_start,
            "is_end": self.is_end,
            "oos_start": self.oos_start,
            "oos_end": self.oos_end,
            "best_params": dict(self.best_params),
            "is_net_profit": self.is_net_profit,
            "oos_net_profit": self.oos_net_profit,
            "passed": self.passed,
        }


@dataclass(frozen=True, slots=True)
class WFMatrixCellResult:
    """Result cell in walk-forward matrix parameter grid."""

    runs_count: int
    oos_pct: int
    robustness_pct: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert matrix cell to dictionary."""
        return {
            "runs_count": self.runs_count,
            "oos_pct": self.oos_pct,
            "robustness_pct": self.robustness_pct,
            "passed": self.passed,
        }


@dataclass(frozen=True, slots=True)
class WalkForwardResultsProjection:
    """Complete walk-forward projection payload for UI rendering."""

    strategy_id: str
    is_matrix: bool
    selected_runs_count: int
    selected_oos_pct: int
    stitched_oos_equity: tuple[tuple[int, float], ...]
    baseline_equity: tuple[tuple[int, float], ...]
    windows: tuple[WFWindowResult, ...]
    matrix_cells: tuple[WFMatrixCellResult, ...]
    robustness_passed: int
    robustness_total: int
    overall_passed: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert projection to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "is_matrix": self.is_matrix,
            "selected_runs_count": self.selected_runs_count,
            "selected_oos_pct": self.selected_oos_pct,
            "stitched_oos_equity": [list(pt) for pt in self.stitched_oos_equity],
            "baseline_equity": [list(pt) for pt in self.baseline_equity],
            "windows": [w.to_dict() for w in self.windows],
            "matrix_cells": [c.to_dict() for c in self.matrix_cells],
            "robustness_passed": self.robustness_passed,
            "robustness_total": self.robustness_total,
            "overall_passed": self.overall_passed,
        }


class ResultsWalkForwardService:
    """Service managing Walk-Forward projections, views, and parameter scheduling."""

    def __init__(self) -> None:
        """Initialize service with in-memory stores."""
        self._projections: dict[str, WalkForwardResultsProjection] = {}
        self._strategy_parameters: dict[str, dict[str, float | int | bool]] = {}
        self._views: dict[str, dict[str, Any]] = {
            "default": {
                "id": "default",
                "name": "Default WF View",
                "show_matrix": True,
            }
        }
        self._conditions: list[dict[str, Any]] = [
            {"name": "MinProfitableRunsPct", "target": 60.0, "operator": ">="},
            {"name": "MinOOSNetProfit", "target": 0.0, "operator": ">"},
        ]

    def set_projection(
        self, strategy_id: str, projection: WalkForwardResultsProjection
    ) -> None:
        """Register precomputed walk-forward projection for testing/presentation."""
        self._projections[strategy_id] = projection

    def list_views(self) -> list[dict[str, Any]]:
        """List registered walk-forward views."""
        return list(self._views.values())

    def add_view(self, name: str, show_matrix: bool = True) -> dict[str, Any]:
        """Add new WF view."""
        v_id = str(uuid.uuid4())
        view = {"id": v_id, "name": name, "show_matrix": show_matrix}
        self._views[v_id] = view
        return view

    def update_view(self, view_id: str, **updates: Any) -> dict[str, Any]:
        """Update existing view."""
        if view_id not in self._views:
            raise DomainError(
                code="OPTIMIZER_VIEW_NOT_FOUND", message=f"View not found: {view_id}"
            )
        self._views[view_id].update(updates)
        return self._views[view_id]

    def remove_view(self, view_id: str) -> bool:
        """Remove view by ID."""
        if view_id == "default":
            raise DomainError(
                code="OPTIMIZER_DEFAULT_VIEW_PROTECTED",
                message="Cannot remove default view",
            )
        return self._views.pop(view_id, None) is not None

    def get_conditions(self) -> list[dict[str, Any]]:
        """Retrieve walk-forward acceptance conditions."""
        return list(self._conditions)

    def get_projection(
        self,
        strategy_id: str,
        *,
        runs_count: int | None = None,
        oos_pct: int | None = None,
    ) -> StandardResponse[WalkForwardResultsProjection]:
        """Retrieve Walk-Forward projection for strategy.

        Args:
            strategy_id: Strategy identifier.
            runs_count: Optional filter for runs count in matrix.
            oos_pct: Optional filter for out-of-sample percentage.

        Returns:
            StandardResponse containing WalkForwardResultsProjection.
        """
        proj = self._projections.get(strategy_id)
        if proj is None:
            # Construct empty projection
            proj = WalkForwardResultsProjection(
                strategy_id=strategy_id,
                is_matrix=False,
                selected_runs_count=runs_count or 10,
                selected_oos_pct=oos_pct or 30,
                stitched_oos_equity=(),
                baseline_equity=(),
                windows=(),
                matrix_cells=(),
                robustness_passed=0,
                robustness_total=0,
                overall_passed=False,
            )

        logger.info(
            "Retrieved WF projection for %s (windows: %d, matrix: %d)",
            strategy_id,
            len(proj.windows),
            len(proj.matrix_cells),
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_wf_proj",
            data=proj,
            json_payload=proj.to_dict(),
        )

    def apply_latest_window_parameters(
        self, project_id: str, databank_name: str, strategy_id: str
    ) -> StandardResponse[dict[str, float | int | bool]]:
        """Apply parameter values from final WF window to strategy parameters.

        Args:
            project_id: Project identifier.
            databank_name: Databank identifier.
            strategy_id: Strategy identifier.

        Returns:
            StandardResponse containing updated parameter dictionary.

        Raises:
            DomainError: If no windows exist to extract parameters from.
        """
        proj = self._projections.get(strategy_id)
        if not proj or not proj.windows:
            raise DomainError(
                code="OPTIMIZER_NO_WF_WINDOWS",
                message=f"No WF windows available for strategy: {strategy_id}",
            )

        latest_window = proj.windows[-1]
        best_params = latest_window.best_params
        self._strategy_parameters[strategy_id] = dict(best_params)

        logger.info(
            "Applied WF window #%d to %s in %s/%s: %s",
            latest_window.window_index,
            strategy_id,
            project_id,
            databank_name,
            best_params,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_apply_wf_params",
            data=dict(best_params),
            json_payload=dict(best_params),
        )

    def export_wf_csv(self, strategy_id: str) -> str:
        """Export walk-forward windows to CSV format."""
        proj = self._projections.get(strategy_id)
        if not proj or not proj.windows:
            return (
                "window_index,is_start,is_end,oos_start,oos_end,"
                "is_net_profit,oos_net_profit,passed\n"
            )

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            [
                "window_index",
                "is_start",
                "is_end",
                "oos_start",
                "oos_end",
                "is_net_profit",
                "oos_net_profit",
                "passed",
            ]
        )
        for w in proj.windows:
            writer.writerow(
                [
                    w.window_index,
                    w.is_start,
                    w.is_end,
                    w.oos_start,
                    w.oos_end,
                    w.is_net_profit,
                    w.oos_net_profit,
                    w.passed,
                ]
            )
        return output.getvalue()
