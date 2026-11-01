"""Trade list column views management service.

Description:
    Implements ResultsTradelistViewsService managing column view definitions
    for the Trade List tab, enforcing immutability of the Default view and
    validating column bindings against known Columns/Trades definitions.

Purpose:
    FEAT-RESULTS-TRADELIST-VIEWS: Column view CRUD for trade lists.

Key Capabilities:
    - FR-results-tradelist-views-crud: List, add, update, remove, and switch views.
    - FR-results-tradelist-views-guard: Protect built-in Default view from removal.

Python API Usage:
    from app.workspace.results.results_tradelist_views import (
        ResultsTradelistViewsService,
        TradelistColumnBinding,
    )
    service = ResultsTradelistViewsService()
    views = service.list_views()

CLI Usage:
    python -m app.cli results tradelist-views --action list
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.results.app_results import wrap_response

logger = get_logger(__name__)

KNOWN_TRADELIST_COLUMNS: frozenset[str] = frozenset(
    {
        "Balance",
        "BarsInTrade",
        "ClosePrice",
        "CloseTime",
        "CloseType",
        "CommSwap",
        "Comment",
        "Drawdown",
        "MAE",
        "MAEPips",
        "MFE",
        "MFEPips",
        "NumberOfTrade",
        "OpenPrice",
        "OpenTime",
        "OriginalOpenPrice",
        "OriginalOpenTime",
        "PTLevel",
        "PctDrawdown",
        "ProfitLoss",
        "ProfitLossPct",
        "ProfitLossPips",
        "ResultName",
        "SLLevel",
        "SampleType",
        "Size",
        "SlippageInMoney",
        "Symbol",
        "Ticket",
        "TimeInTrade",
        "Type",
    }
)


@dataclass(frozen=True, slots=True)
class TradelistColumnBinding:
    """Individual column display binding within a trade list view."""

    column_id: str
    width: int = 90

    def to_dict(self) -> dict[str, Any]:
        """Convert binding to dictionary representation."""
        return {"column_id": self.column_id, "width": self.width}


@dataclass(frozen=True, slots=True)
class TradelistViewDefinition:
    """Named view configuration defining displayed trade columns."""

    view_id: str
    name: str
    is_default: bool
    columns: tuple[TradelistColumnBinding, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert view definition to dictionary representation."""
        return {
            "view_id": self.view_id,
            "name": self.name,
            "is_default": self.is_default,
            "columns": [c.to_dict() for c in self.columns],
        }


DEFAULT_TRADELIST_VIEW = TradelistViewDefinition(
    view_id="Default",
    name="Default",
    is_default=True,
    columns=(
        TradelistColumnBinding(column_id="NumberOfTrade", width=60),
        TradelistColumnBinding(column_id="Symbol", width=80),
        TradelistColumnBinding(column_id="Type", width=70),
        TradelistColumnBinding(column_id="OpenTime", width=140),
        TradelistColumnBinding(column_id="OpenPrice", width=90),
        TradelistColumnBinding(column_id="Size", width=70),
        TradelistColumnBinding(column_id="CloseTime", width=140),
        TradelistColumnBinding(column_id="ClosePrice", width=90),
        TradelistColumnBinding(column_id="ProfitLoss", width=90),
        TradelistColumnBinding(column_id="Balance", width=100),
        TradelistColumnBinding(column_id="Comment", width=120),
    ),
)


class ResultsTradelistViewsService:
    """Trade list column views management service."""

    def __init__(self) -> None:
        """Initialize with default trade list view."""
        self._views: dict[str, TradelistViewDefinition] = {
            "Default": DEFAULT_TRADELIST_VIEW,
        }
        self._active_view_id: str = "Default"

    def list_views(self) -> StandardResponse[tuple[TradelistViewDefinition, ...]]:
        """List all configured trade list views.

        Returns:
            StandardResponse containing tuple of TradelistViewDefinition.
        """
        views = tuple(self._views.values())
        return wrap_response(
            request_id="req_list_tradelist_views",
            data=views,
            json_payload=[v.to_dict() for v in views],
        )

    def add_view(
        self, name: str, columns: tuple[TradelistColumnBinding, ...]
    ) -> StandardResponse[TradelistViewDefinition]:
        """Create a new custom trade list view.

        Args:
            name: View display name.
            columns: Bound trade columns.

        Returns:
            StandardResponse containing created TradelistViewDefinition.

        Raises:
            DomainError(code='RESULTS_UNKNOWN_TRADELIST_COLUMN'): If column_id invalid.
        """
        self._validate_columns(columns)
        view_id = name.replace(" ", "_")
        view = TradelistViewDefinition(
            view_id=view_id,
            name=name,
            is_default=False,
            columns=columns,
        )
        self._views[view_id] = view
        logger.info(
            "FR-results-tradelist-views-crud: added view %s (%d columns)",
            view_id,
            len(columns),
        )
        return wrap_response(
            request_id=f"req_add_view_{view_id}",
            data=view,
            json_payload=view.to_dict(),
        )

    def update_view(
        self, view_id: str, name: str, columns: tuple[TradelistColumnBinding, ...]
    ) -> StandardResponse[TradelistViewDefinition]:
        """Update an existing trade list view."""
        self._validate_columns(columns)
        if view_id not in self._views:
            raise DomainError(
                code="RESULTS_VIEW_NOT_FOUND",
                message=f"View '{view_id}' does not exist",
                details={"view_id": view_id},
            )
        is_default = self._views[view_id].is_default
        view = TradelistViewDefinition(
            view_id=view_id,
            name=name,
            is_default=is_default,
            columns=columns,
        )
        self._views[view_id] = view
        logger.info(
            "FR-results-tradelist-views-crud: updated view %s",
            view_id,
        )
        return wrap_response(
            request_id=f"req_update_view_{view_id}",
            data=view,
            json_payload=view.to_dict(),
        )

    def remove_view(self, view_id: str) -> StandardResponse[bool]:
        """Remove a user-created trade list view.

        Args:
            view_id: View identifier to remove.

        Returns:
            StandardResponse containing True on success.

        Raises:
            DomainError(code='RESULTS_DEFAULT_TRADELIST_VIEW_PROTECTED'): Default view.
        """
        if view_id == "Default" or (
            view_id in self._views and self._views[view_id].is_default
        ):
            raise DomainError(
                code="RESULTS_DEFAULT_TRADELIST_VIEW_PROTECTED",
                message="Built-in Default trade list view cannot be removed",
                details={"view_id": view_id},
            )
        if view_id not in self._views:
            raise DomainError(
                code="RESULTS_VIEW_NOT_FOUND",
                message=f"View '{view_id}' does not exist",
                details={"view_id": view_id},
            )
        del self._views[view_id]
        if self._active_view_id == view_id:
            self._active_view_id = "Default"
        logger.info(
            "FR-results-tradelist-views-guard: removed view %s",
            view_id,
        )
        return wrap_response(
            request_id=f"req_remove_view_{view_id}",
            data=True,
            json_payload={"removed": True},
        )

    def change_view(self, view_id: str) -> StandardResponse[TradelistViewDefinition]:
        """Switch the active trade list view."""
        if view_id not in self._views:
            raise DomainError(
                code="RESULTS_VIEW_NOT_FOUND",
                message=f"View '{view_id}' does not exist",
                details={"view_id": view_id},
            )
        self._active_view_id = view_id
        return wrap_response(
            request_id=f"req_change_view_{view_id}",
            data=self._views[view_id],
            json_payload=self._views[view_id].to_dict(),
        )

    def get_view(self, view_id: str) -> TradelistViewDefinition:
        """Get view definition by ID or return Default."""
        return self._views.get(view_id, self._views["Default"])

    def _validate_columns(self, columns: tuple[TradelistColumnBinding, ...]) -> None:
        for c in columns:
            if c.column_id not in KNOWN_TRADELIST_COLUMNS:
                raise DomainError(
                    code="RESULTS_UNKNOWN_TRADELIST_COLUMN",
                    message=f"Unknown trade list column: '{c.column_id}'",
                    details={"column_id": c.column_id},
                )
