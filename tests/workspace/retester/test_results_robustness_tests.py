"""Unit tests for ResultsRobustnessTestsService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.retester.results_robustness_tests import (
    ResultsRobustnessTestsService,
    RobustnessViewDefinition,
)


class TestResultsRobustnessTestsService:
    """Test suite for ResultsRobustnessTestsService."""

    def test_views_crud(self) -> None:
        """Assert list, add, update, and remove views."""
        service = ResultsRobustnessTestsService()
        views = service.list_views("p1")
        assert len(views) == 1
        assert views[0].view_id == "default"

        # Add custom view
        new_view = RobustnessViewDefinition(
            view_id="v_custom",
            name="Custom Risk",
            is_default=False,
            column_ids=("ConfidenceLevel", "DrawdownPct"),
        )
        service.add_view("p1", new_view)
        views = service.list_views("p1")
        assert len(views) == 2

        # Update view
        updated_view = RobustnessViewDefinition(
            view_id="v_custom",
            name="Custom Risk Updated",
            is_default=False,
            column_ids=("ConfidenceLevel", "DrawdownPct", "NetProfit"),
        )
        service.update_view("p1", updated_view)
        assert service.list_views("p1")[1].name == "Custom Risk Updated"

        # Remove custom view
        service.remove_view("p1", "v_custom")
        assert len(service.list_views("p1")) == 1

        # Attempting to remove default raises error
        with pytest.raises(DomainError) as exc_info:
            service.remove_view("p1", "default")
        assert exc_info.value.code == "RESULTS_ROBUSTNESS_VIEW_PROTECTED"

    def test_get_methods(self) -> None:
        """Assert get_methods lists supported robustness test types."""
        service = ResultsRobustnessTestsService()
        methods = service.get_methods("p1", "Results", "strat1")
        assert "MC_Manipulation" in methods
        assert "MC_Retest" in methods
        assert "WalkForward" in methods

    def test_get_projection_golden_fixture(self) -> None:
        """Assert get_projection returns confidence bands 50%..99% and fan curves."""
        service = ResultsRobustnessTestsService()
        response = service.get_projection(
            "p1", "Results", "strat1", "Main", "MC_Manipulation"
        )

        projection = response.data
        assert projection["strategy_id"] == "strat1"
        assert projection["result_key"] == "Main"
        assert len(projection["confidence_bands"]) == 11
        assert projection["confidence_bands"][0]["confidence_pct"] == 50
        assert projection["confidence_bands"][-1]["confidence_pct"] == 99
        assert len(projection["equity_fan_curves"]) == 25
        assert len(projection["baseline_equity"]) == 20
