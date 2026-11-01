"""Unit tests for SettingsCrossChecksService."""

from app.workspace.retester.settings_cross_checks import (
    CrossCheckCondition,
    CrossChecksSettingsSnapshot,
    GenericCheckConfig,
    SettingsCrossChecksService,
)


class TestSettingsCrossChecks:
    """Test suite for CrossChecksSettingsSnapshot and service resolution."""

    def test_mode_resolution_golden_fixture(self) -> None:
        """Assert golden fixture: enabled + mc_retest -> 0; disabled -> 1."""
        # Enabled + mc_retest enabled -> 0
        snap_enabled = CrossChecksSettingsSnapshot(
            enabled=True,
            mc_retest=GenericCheckConfig(enabled=True),
        )
        assert SettingsCrossChecksService.resolve_mode(snap_enabled) == 0

        # Disabled master flag -> 1 even if sub-check enabled
        snap_disabled = CrossChecksSettingsSnapshot(
            enabled=False,
            mc_retest=GenericCheckConfig(enabled=True),
        )
        assert SettingsCrossChecksService.resolve_mode(snap_disabled) == 1

        # Enabled master flag but no subjob check enabled -> 1
        snap_no_subjobs = CrossChecksSettingsSnapshot(
            enabled=True,
            what_if=GenericCheckConfig(
                enabled=True
            ),  # What-if manipulates trades, doesn't create subjobs
        )
        assert SettingsCrossChecksService.resolve_mode(snap_no_subjobs) == 1

    def test_default_conditions(self) -> None:
        """Assert default Walk Forward and SPP conditions."""
        wf_conds = SettingsCrossChecksService.get_default_wf_conditions()
        assert len(wf_conds) == 2
        assert wf_conds[0].metric == "ProfitableRunsPct"
        assert wf_conds[0].threshold == 70.0

        spp_conds = SettingsCrossChecksService.get_default_spp_conditions()
        assert len(spp_conds) == 2
        assert spp_conds[0].metric == "ProfitableRunsPct"
        assert spp_conds[1].metric == "StabilityScore"

    def test_condition_evaluation(self) -> None:
        """Assert CrossCheckCondition evaluation logic."""
        cond = CrossCheckCondition(
            name="Test", metric="Metric", operator=">=", threshold=50.0
        )
        assert cond.evaluate(50.0) is True
        assert cond.evaluate(60.0) is True
        assert cond.evaluate(49.9) is False

        disabled_cond = CrossCheckCondition(
            name="Test",
            metric="Metric",
            operator=">=",
            threshold=50.0,
            is_enabled=False,
        )
        assert disabled_cond.evaluate(10.0) is True

    def test_to_dict_serialization(self) -> None:
        """Assert to_dict produces valid dictionary."""
        snapshot = CrossChecksSettingsSnapshot(enabled=True)
        d = snapshot.to_dict()
        assert d["enabled"] is True
        assert "what_if" in d
        assert "mc_retest" in d
