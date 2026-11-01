"""Portfolio Composer chart and frontier projection service.

Description:
    Projects the Markowitz / CVaR efficient frontier scatter cloud, the selected
    optimal allocation point, and composite vs. member equity curves.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-chart: Project frontier scatter points and multi-strategy equity.
Python API Usage:
    from app.workspace.portfolio_composer.results_portfolio_composer_chart import (
        ResultsPortfolioComposerChartService,
        FrontierSimulationPoint,
        PortfolioComposerChartPayload,
    )
    resp = ResultsPortfolioComposerChartService.get_chart(receipt)
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, cast

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse
from app.workspace.portfolio_composer.selection import ComposerSelection

if TYPE_CHECKING:
    from app.workspace.portfolio_composer.portfolio_composer import ComposerRunReceipt

logger = get_logger(__name__)


def _to_json_compatible(value: Any) -> Any:
    """Recursively convert tuples and dataclasses to lists and JSON primitives."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, (list, tuple)):
        return [_to_json_compatible(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _to_json_compatible(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _to_json_compatible(asdict(value))
    return str(value)


def _build_typed_response[T](
    *,
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int | None = None,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data."""
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=_to_json_compatible(json_payload),
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)


@dataclass(frozen=True, slots=True)
class FrontierSimulationPoint:
    """A simulated portfolio candidate in the risk-return scatter cloud."""

    simulation_index: int
    weights: tuple[int, ...]
    risk_x: float
    return_y: float
    selection_score: float
    is_selected: bool


@dataclass(frozen=True, slots=True)
class PortfolioComposerChartPayload:
    """Chart data payload containing the efficient frontier points and equity series."""

    model_type: str
    selection_type: str
    frontier_points: tuple[FrontierSimulationPoint, ...]
    portfolio_equity: tuple[tuple[int, float], ...]
    member_equities: dict[str, tuple[tuple[int, float], ...]]


class ResultsPortfolioComposerChartService:
    """Service providing chart projections for a composed portfolio run."""

    @staticmethod
    def get_chart(
        receipt: ComposerRunReceipt,
    ) -> StandardResponse[PortfolioComposerChartPayload]:
        """Project the frontier points and equity curves from a composer run receipt.

        Args:
            receipt: Completed ComposerRunReceipt instance.

        Returns:
            StandardResponse containing PortfolioComposerChartPayload.
        """
        sel = ComposerSelection.parse(receipt.selection_type)
        decimals = sel.decimals()

        logger.info(
            "FR-composer-chart: chart run_id=%s (points=%d, decimals=%d)",
            receipt.run_id,
            len(receipt.simulation_points),
            decimals,
        )

        rounded_points: list[FrontierSimulationPoint] = []
        for pt in receipt.simulation_points:
            score = (
                round(pt.selection_score, decimals)
                if decimals > 0
                else round(pt.selection_score)
            )
            rounded_points.append(
                FrontierSimulationPoint(
                    simulation_index=pt.simulation_index,
                    weights=pt.weights,
                    risk_x=pt.risk_x,
                    return_y=pt.return_y,
                    selection_score=float(score),
                    is_selected=pt.is_selected,
                )
            )

        payload = PortfolioComposerChartPayload(
            model_type=receipt.model_type,
            selection_type=receipt.selection_type,
            frontier_points=tuple(rounded_points),
            portfolio_equity=receipt.portfolio_equity,
            member_equities=receipt.member_equities,
        )

        return _build_typed_response(
            request_id=f"chart-{receipt.run_id}",
            data=payload,
            json_payload=asdict(payload),
        )
