"""Databank column view configuration service.

Description:
    Implements ResultsDatabankViewsService providing CRUD operations for
    databank column layouts (/dbviews/addView, /dbviews/updateView,
    /dbviews/removeView, /dbviews/changeView) with column validation and
    protection of the built-in 'Default' view.

Purpose:
    FEAT-RESULTS-DATABANK-VIEWS: Databank column view configurations.

Key Capabilities:
    - FR-results-dbviews-crud: Manage databank column views and active selection.

Python API Usage:
    from app.workspace.results.results_databank_views import (
        DatabankColumnBinding,
        ResultsDatabankViewsService,
    )
    service = ResultsDatabankViewsService()
    views = service.list_views()

CLI Usage:
    python -m app.cli results dbviews --list
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.results.app_results import wrap_response

logger = get_logger(__name__)

DEFAULT_VIEW_ID = "Default"

VALID_DATABANK_COLUMN_IDS = frozenset(
    {
        # Databanks (122)
        "AHPR",
        "ActualDD",
        "ActualDrawdownPct",
        "AmbiguousTrades",
        "AmbiguousTradesPct",
        "AnnualPctReturn",
        "AnnualPctReturnDDRatio",
        "AvgAbsTrade",
        "AvgBarsInTrade",
        "AvgBarsLoss",
        "AvgBarsWin",
        "AvgConsecLosses",
        "AvgConsecWins",
        "AvgDrawdown",
        "AvgLoss",
        "AvgParametersStability",
        "AvgPctDrawdown",
        "AvgPctProfitPerYear",
        "AvgProfitPerDay",
        "AvgProfitPerMonth",
        "AvgProfitPerYear",
        "AvgTrStddevRatio",
        "AvgTrade",
        "AvgTradesPerDay",
        "AvgTradesPerMonth",
        "AvgTradesPerYear",
        "AvgWin",
        "BacktestDuration",
        "BestWF",
        "BiggestMAE",
        "CAGR",
        "CalmarRatio",
        "Commission",
        "Complexity",
        "DateGenerated",
        "DateLastModified",
        "DegreesOfFreedom",
        "Drawdown",
        "DrawdownPct",
        "DrawdownPips",
        "EdgeRatioInPips",
        "Efficiency",
        "EntryIndicators",
        "EquityAngle",
        "EquitySlope",
        "ExitIndicators",
        "ExitQuality",
        "Expectancy",
        "Exposure",
        "ExposurePosition",
        "FiltersResult",
        "Fitness",
        "GrossLoss",
        "GrossProfit",
        "InitialDeposit",
        "KellyFormula",
        "LongestTrade",
        "MagicNumber",
        "MaxConsecLosses",
        "MaxConsecWins",
        "MaxIntradayDrawdown",
        "MaxLoss",
        "MaxNewHighDuration",
        "MaxProfit",
        "MaxTSIntradayDrawdown",
        "MiniEquityChart",
        "NSymmetry",
        "NetProfit",
        "NetProfitInPct",
        "NetProfitInPips",
        "Note",
        "NumberOfCanceled",
        "NumberOfLosses",
        "NumberOfProfits",
        "NumberOfTrades",
        "OpenDrawdown",
        "OpenDrawdownPct",
        "Outlier2",
        "Parameters",
        "PayoutRatio",
        "PriceIndicators",
        "ProfitFactor",
        "ProfitableMonths",
        "ProfitableMonthsPct",
        "RExpectancy",
        "RExpectancyScore",
        "RSquared",
        "RecoveryFactor",
        "ResultsName",
        "ReturnDDRatio",
        "ReturnOpenDDRatio",
        "SQN",
        "SQNScore",
        "SharpeRatio",
        "SlippageInMoney",
        "Stability",
        "StabilitySQ3",
        "Stagnation",
        "StagnationPct",
        "StandardDev",
        "Symbol",
        "Symmetry",
        "TSIndex",
        "TSWinLossRatio",
        "TimeFrame",
        "TotalDataDays",
        "TotalDataMonths",
        "TotalDataYears",
        "TotalMFE",
        "TotalTradingDays",
        "TotalTradingMonths",
        "TotalTradingYears",
        "TradesSymmetry",
        "UlcerIndex",
        "UlcerPerformanceIndex",
        "WinLossRatio",
        "WinningPct",
        "WorstParametersStability",
        "WorstYearProfit",
        "ZProbability",
        "ZScore",
        # WalkForward (8)
        "WFMaxDDbyRun",
        "WFMaxPctDDbyRun",
        "WFMaxProfitByRun",
        "WFMaxProfitByRunInPct",
        "WFMaxStagnationInPct",
        "WFMinTradesInRun",
        "WFPctOfProfitableRuns",
        "WFScore",
    }
)


@dataclass(frozen=True, slots=True)
class DatabankColumnBinding:
    """Binding specification for a single databank table column."""

    column_id: str
    sample_type: str = "FullSample"
    direction: str = "Both"
    market: str = "Main"
    width: int = 100

    def to_dict(self) -> dict[str, Any]:
        """Convert binding to dictionary."""
        return {
            "column_id": self.column_id,
            "sample_type": self.sample_type,
            "direction": self.direction,
            "market": self.market,
            "width": self.width,
        }


@dataclass(frozen=True, slots=True)
class DatabankViewDefinition:
    """Databank view configuration holding an ordered set of columns."""

    view_id: str
    name: str
    is_default: bool
    columns: tuple[DatabankColumnBinding, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert view definition to dictionary."""
        return {
            "view_id": self.view_id,
            "name": self.name,
            "is_default": self.is_default,
            "columns": [c.to_dict() for c in self.columns],
        }


class ResultsDatabankViewsService:
    """Service managing databank view configurations."""

    def __init__(self) -> None:
        """Initialize service with built-in Default view."""
        self._views: dict[str, DatabankViewDefinition] = {}
        self._active_view_id: str = DEFAULT_VIEW_ID

        # Initialize Default view
        default_cols = (
            DatabankColumnBinding("ResultsName", width=140),
            DatabankColumnBinding("NetProfit", width=100),
            DatabankColumnBinding("ProfitFactor", width=90),
            DatabankColumnBinding("ReturnDDRatio", width=90),
            DatabankColumnBinding("DrawdownPct", width=90),
            DatabankColumnBinding("NumberOfTrades", width=80),
            DatabankColumnBinding("SharpeRatio", width=90),
            DatabankColumnBinding("WinningPct", width=90),
        )
        self._views[DEFAULT_VIEW_ID] = DatabankViewDefinition(
            view_id=DEFAULT_VIEW_ID,
            name="Default",
            is_default=True,
            columns=default_cols,
        )

    def _validate_columns(self, columns: tuple[DatabankColumnBinding, ...]) -> None:
        for col in columns:
            if col.column_id not in VALID_DATABANK_COLUMN_IDS:
                raise DomainError(
                    code="RESULTS_UNKNOWN_DATABANK_COLUMN",
                    message=f"Unknown databank column ID '{col.column_id}'",
                    details={"column_id": col.column_id},
                )

    def list_views(self) -> StandardResponse[tuple[DatabankViewDefinition, ...]]:
        """List all configured databank views."""
        views_tuple = tuple(self._views.values())
        return wrap_response(
            request_id="req_list_dbviews",
            data=views_tuple,
            json_payload={"views": [v.to_dict() for v in views_tuple]},
        )

    def add_view(
        self, name: str, columns: tuple[DatabankColumnBinding, ...]
    ) -> StandardResponse[DatabankViewDefinition]:
        """Add a new custom databank view."""
        self._validate_columns(columns)
        view_id = name.strip().replace(" ", "_")
        if not view_id:
            raise DomainError(
                code="RESULTS_INVALID_VIEW_NAME",
                message="View name cannot be empty",
                details={"name": name},
            )

        new_view = DatabankViewDefinition(
            view_id=view_id,
            name=name.strip(),
            is_default=False,
            columns=columns,
        )
        self._views[view_id] = new_view
        logger.info(
            "FR-results-dbviews-crud: added view %s with %d columns",
            view_id,
            len(columns),
        )
        return wrap_response(
            request_id=f"req_add_dbview_{view_id}",
            data=new_view,
            json_payload=new_view.to_dict(),
        )

    def update_view(
        self, view_id: str, name: str, columns: tuple[DatabankColumnBinding, ...]
    ) -> StandardResponse[DatabankViewDefinition]:
        """Update column layout of an existing view."""
        if view_id not in self._views:
            raise DomainError(
                code="RESULTS_VIEW_NOT_FOUND",
                message=f"Databank view '{view_id}' not found",
                details={"view_id": view_id},
            )
        self._validate_columns(columns)
        is_default = self._views[view_id].is_default

        updated_view = DatabankViewDefinition(
            view_id=view_id,
            name=name.strip(),
            is_default=is_default,
            columns=columns,
        )
        self._views[view_id] = updated_view
        logger.info(
            "FR-results-dbviews-crud: updated view %s with %d columns",
            view_id,
            len(columns),
        )
        return wrap_response(
            request_id=f"req_update_dbview_{view_id}",
            data=updated_view,
            json_payload=updated_view.to_dict(),
        )

    def remove_view(self, view_id: str) -> StandardResponse[bool]:
        """Remove view, protecting the Default view."""
        if view_id == DEFAULT_VIEW_ID or (
            view_id in self._views and self._views[view_id].is_default
        ):
            raise DomainError(
                code="RESULTS_DEFAULT_VIEW_PROTECTED",
                message=f"Cannot remove protected default view '{view_id}'",
                details={"view_id": view_id},
            )
        if view_id not in self._views:
            raise DomainError(
                code="RESULTS_VIEW_NOT_FOUND",
                message=f"Databank view '{view_id}' not found",
                details={"view_id": view_id},
            )

        self._views.pop(view_id)
        if self._active_view_id == view_id:
            self._active_view_id = DEFAULT_VIEW_ID

        logger.info("FR-results-dbviews-crud: removed view %s", view_id)
        return wrap_response(
            request_id=f"req_remove_dbview_{view_id}",
            data=True,
            json_payload={"removed": True},
        )

    def change_view(self, view_id: str) -> StandardResponse[DatabankViewDefinition]:
        """Set the active databank view."""
        if view_id not in self._views:
            raise DomainError(
                code="RESULTS_VIEW_NOT_FOUND",
                message=f"Databank view '{view_id}' not found",
                details={"view_id": view_id},
            )
        self._active_view_id = view_id
        logger.info("FR-results-dbviews-crud: changed active view to %s", view_id)
        active_view = self._views[view_id]
        return wrap_response(
            request_id=f"req_change_dbview_{view_id}",
            data=active_view,
            json_payload=active_view.to_dict(),
        )
