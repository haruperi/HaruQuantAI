"""Unit tests for AppRetesterService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.retester.app_retester import AppRetesterService
from app.workspace.retester.settings_cross_checks import (
    CrossChecksSettingsSnapshot,
    GenericCheckConfig,
)
from app.workspace.retester.settings_what_to_retest import WhatToRetestSettings


class TestAppRetesterService:
    """Test suite for AppRetesterService."""

    def test_golden_fixture_retest_two_strategies(self) -> None:
        """Starting Retester with 2 strategies in Input databank and WhatIf enabled reaches COMPLETED with processed=2."""
        service = AppRetesterService()
        project_id = "proj_test_golden"

        # Mock 2 strategies in "Input" databank
        service.set_mock_databank(project_id, "Input", ["strat_01", "strat_02"])

        # Configure what to retest and cross-checks
        what = WhatToRetestSettings(source_databank="Input", target_databank="Input")
        checks = CrossChecksSettingsSnapshot(
            enabled=True,
            what_if=GenericCheckConfig(enabled=True),
        )
        service.save_settings(project_id, what_to_retest=what, cross_checks=checks)

        # Start retest
        resp = service.start(project_id)
        state = resp.data

        assert state["project_id"] == project_id
        assert state["status"] == "COMPLETED"
        assert state["processed_count"] == 2
        assert state["accepted_count"] == 2
        assert state["rejected_count"] == 0
        assert state["progress_pct"] == 100.0

    def test_lifecycle_transitions(self) -> None:
        """Assert state transitions: get_state, pause, resume, stop."""
        service = AppRetesterService()
        project_id = "proj_lifecycle"

        # Initial IDLE
        res = service.get_state(project_id)
        assert res.data["status"] == "IDLE"

        # Pause
        res = service.pause(project_id)
        assert res.data["status"] == "PAUSED"

        # Resume
        res = service.resume(project_id)
        assert res.data["status"] == "RUNNING"

        # Stop
        res = service.stop(project_id)
        assert res.data["status"] == "STOPPED"

    def test_already_running_guard(self) -> None:
        """Starting an already running retester raises RETESTER_ALREADY_RUNNING."""
        service = AppRetesterService()
        project_id = "proj_guard"
        service.resume(project_id)  # sets status to RUNNING

        with pytest.raises(DomainError) as exc_info:
            service.start(project_id)
        assert exc_info.value.code == "RETESTER_ALREADY_RUNNING"
