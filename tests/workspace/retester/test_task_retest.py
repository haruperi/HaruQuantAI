"""Unit tests for TaskRetestRunner."""

from app.workspace.retester.settings_auto_retest_data import AutoRetestDataSettings
from app.workspace.retester.settings_cross_checks import (
    CrossChecksSettingsSnapshot,
    GenericCheckConfig,
)
from app.workspace.retester.settings_what_to_retest import WhatToRetestSettings
from app.workspace.retester.task_retest import TaskRetestRunner


class TestTaskRetestRunner:
    """Test suite for TaskRetestRunner."""

    def test_golden_fixture_empty_selection(self) -> None:
        """Assert running on selected_keys=() logs 'No strategies to retest' and processed=0."""
        what = WhatToRetestSettings(selected_keys=())
        data = AutoRetestDataSettings()
        checks = CrossChecksSettingsSnapshot()

        summary = TaskRetestRunner.execute("proj_empty", what, data, checks)

        assert summary.processed == 0
        assert summary.total_keys == 0
        assert "No strategies to retest" in summary.log_messages

    def test_golden_fixture_same_databank_clearing(self) -> None:
        """Same source/target databank clears previous results while keeping strategies in databank."""
        what = WhatToRetestSettings(
            source_databank="Results",
            target_databank="Results",
            selected_keys=("s1", "s2"),
        )
        data = AutoRetestDataSettings()
        checks = CrossChecksSettingsSnapshot(
            enabled=True,
            what_if=GenericCheckConfig(enabled=True),
        )

        db_strategies = {"Results": ["s1", "s2"]}
        stored_results = {
            "s1": {"Main": 100.0, "Sub": 50.0},
            "s2": {"Main": 80.0},
        }

        summary = TaskRetestRunner.execute(
            "proj_clear",
            what,
            data,
            checks,
            databank_strategies=db_strategies,
            stored_results=stored_results,
        )

        assert summary.processed == 2
        assert summary.passed == 2
        # Verify strategies were kept in databank
        assert db_strategies["Results"] == ["s1", "s2"]
        # Verify results were cleared
        assert stored_results["s1"] == {}
        assert stored_results["s2"] == {}
