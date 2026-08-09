"""Tests for the stress-profile calibration consumer port (TC-IMP-OPT-06)."""

from collections.abc import Mapping

from app.services.optimization import (
    get_stress_calibration_contract_version,
    resolve_stress_profile_calibration,
)


def test_stress_profile_fails_closed_without_provider() -> None:
    """Missing provider yields UNCALIBRATED, never a fabricated shock profile."""
    result = resolve_stress_profile_calibration(
        strategy_ref="strategy-v1",
        market_data_ref="data-1",
        provider=None,
    )
    assert result["status"] == "STRESS_PROFILE_UNCALIBRATED"
    assert result["deferred_to"] == "TC-IMP-RISK-12 / TC-IMP-RES-06"


def test_stress_profile_passes_through_provider_evidence() -> None:
    """A present provider's evidence is passed through."""

    class FakeProvider:
        def stress_profile_calibration(
            self, *, strategy_ref: str, market_data_ref: str
        ) -> Mapping[str, object]:
            del strategy_ref, market_data_ref
            return {"shock_magnitude": 0.05}
            return {"shock_magnitude": 0.05}

    result = resolve_stress_profile_calibration(
        strategy_ref="strategy-v1",
        market_data_ref="data-1",
        provider=FakeProvider(),
    )
    assert result["status"] == "STRESS_PROFILE_CALIBRATED"
    assert result["shock_magnitude"] == 0.05


def test_stress_calibration_contract_version() -> None:
    """Consumer version is canonical."""
    assert get_stress_calibration_contract_version() == "v1"
