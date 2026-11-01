"""Unit tests for AppPortfolioComposerService (PC Phase 10.5)."""

from __future__ import annotations

from app.workspace.portfolio_composer.app_portfolio_composer import (
    AppPortfolioComposerService,
)


class TestAppPortfolioComposerService:
    """Test suite for top-level AppPortfolioComposerService coordinator."""

    def test_golden_fixture_fresh_workspace_state(self) -> None:
        """Verify initializing fresh workspace state matches golden parameters."""
        service = AppPortfolioComposerService()
        resp = service.get_workspace_state("proj_1", today_label="2026-10-30")

        assert resp.data is not None
        state = resp.data
        assert state.project_id == "proj_1"
        assert state.defaults["initial_capital"] == 100000
        assert state.defaults["leverage"] == 1
        assert state.defaults["model_type"] == "markowitz"
        assert state.defaults["selection_type"] == "SharpRatio"
        assert state.defaults["conf_level"] == 95
        assert state.defaults["risk_free_rate"] == 0.7
        assert state.defaults["start_day"] == "2026-10-30"
        assert state.defaults["end_day"] == "2026-10-30"
        assert state.is_computing is False

    def test_state_persistence_for_project(self) -> None:
        """Verify repeated calls return the same stored state."""
        service = AppPortfolioComposerService()
        r1 = service.get_workspace_state("proj_abc", today_label="2026-01-01")
        r2 = service.get_workspace_state("proj_abc", today_label="2026-12-31")

        assert r1.data is r2.data
        assert r2.data.defaults["start_day"] == "2026-01-01"
