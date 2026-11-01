"""Unit tests for ResultsTradelistViewsService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.results_tradelist_views import (
    ResultsTradelistViewsService,
    TradelistColumnBinding,
)


class TestResultsTradelistViewsService:
    """Test suite for ResultsTradelistViewsService."""

    def test_default_view_exists_and_protected(self) -> None:
        """Verify Default view is present and protected against removal."""
        service = ResultsTradelistViewsService()
        list_resp = service.list_views()
        assert len(list_resp.data) >= 1
        default_view = list_resp.data[0]
        assert default_view.view_id == "Default"
        assert default_view.is_default is True

        with pytest.raises(DomainError) as exc_info:
            service.remove_view("Default")
        assert exc_info.value.code == "RESULTS_DEFAULT_TRADELIST_VIEW_PROTECTED"

    def test_add_and_remove_custom_view(self) -> None:
        """Verify adding and removing a valid custom view."""
        service = ResultsTradelistViewsService()
        add_resp = service.add_view(
            "ExcursionView",
            (
                TradelistColumnBinding("NumberOfTrade", 60),
                TradelistColumnBinding("MAE", 90),
                TradelistColumnBinding("MFE", 90),
                TradelistColumnBinding("ProfitLoss", 90),
            ),
        )
        assert add_resp.data.view_id == "ExcursionView"

        # Check unknown column validation
        with pytest.raises(DomainError) as exc_info:
            service.add_view(
                "InvalidView",
                (TradelistColumnBinding("UnknownCol", 100),),
            )
        assert exc_info.value.code == "RESULTS_UNKNOWN_TRADELIST_COLUMN"

        # Remove custom view
        rem_resp = service.remove_view("ExcursionView")
        assert rem_resp.data is True
