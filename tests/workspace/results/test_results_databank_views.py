"""Unit tests for ResultsDatabankViewsService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.results_databank_views import (
    DatabankColumnBinding,
    DatabankViewDefinition,
    ResultsDatabankViewsService,
)


class TestResultsDatabankViewsService:
    """Test suite for ResultsDatabankViewsService."""

    def test_golden_fixture_add_and_protect_default(self) -> None:
        """Verify adding CustomRisk view and preventing deletion of Default view."""
        service = ResultsDatabankViewsService()

        # Add custom view
        cols = (
            DatabankColumnBinding("NetProfit", width=120),
            DatabankColumnBinding("ReturnDDRatio", width=100),
            DatabankColumnBinding("SharpeRatio", width=100),
        )
        resp_add = service.add_view("CustomRisk", cols)
        v = resp_add.data
        assert v.name == "CustomRisk"
        assert len(v.columns) == 3

        # Change view
        resp_change = service.change_view("CustomRisk")
        assert resp_change.data.view_id == "CustomRisk"

        # Attempt to delete Default
        with pytest.raises(DomainError) as exc_info:
            service.remove_view("Default")
        assert exc_info.value.code == "RESULTS_DEFAULT_VIEW_PROTECTED"

    def test_unknown_column_rejection(self) -> None:
        """Verify adding view with invalid column ID raises DomainError."""
        service = ResultsDatabankViewsService()
        bad_cols = (DatabankColumnBinding("NonExistentColumn"),)
        with pytest.raises(DomainError) as exc_info:
            service.add_view("BadView", bad_cols)
        assert exc_info.value.code == "RESULTS_UNKNOWN_DATABANK_COLUMN"

    def test_update_and_remove_view(self) -> None:
        """Verify update and remove of custom view."""
        service = ResultsDatabankViewsService()
        service.add_view("MyView", (DatabankColumnBinding("NetProfit"),))

        # Update
        updated = service.update_view(
            "MyView", "MyViewRenamed", (DatabankColumnBinding("ProfitFactor"),)
        )
        assert updated.data.columns[0].column_id == "ProfitFactor"

        # Remove
        removed = service.remove_view("MyView")
        assert removed.data is True

    def test_to_dict_serialization(self) -> None:
        """Verify DatabankColumnBinding and DatabankViewDefinition to_dict."""
        binding = DatabankColumnBinding("NetProfit", width=110)
        d_b = binding.to_dict()
        assert d_b["column_id"] == "NetProfit"
        assert d_b["width"] == 110

        view = DatabankViewDefinition(
            view_id="v1", name="V1", is_default=False, columns=(binding,)
        )
        d_v = view.to_dict()
        assert d_v["view_id"] == "v1"
        assert len(d_v["columns"]) == 1
